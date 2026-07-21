# Research: Versionamento de Embeddings

## Decision 1: Store embedding metadata by batch, with chunk-level hash/status

**Decision**: Add an `embedding_batches` table for effective provider/model/dimension/version and attach chunks to a batch through `knowledge_chunks.embedding_batch_id`. Store `embedding_content_hash` and `embedding_status` on each chunk.

**Rationale**: Provider/model/dimension metadata repeats for every chunk in a single ingest/reindex run. A batch table avoids duplication and still answers "which model produced this embedding" for every chunk through the FK.

**Alternatives considered**:

- Store all metadata directly on `knowledge_chunks`: simpler queries, but repeats provider/model/version data on every row and makes batch-level counters/status harder.
- Store only a global `app_config`: insufficient because historical chunks can be produced by different configurations.

## Decision 2: Treat legacy chunks as unversioned until explicit adoption or reindex

**Decision**: Existing chunks without `embedding_batch_id` are not considered compatible. They are reported as `unversioned`/pending until reindexed or explicitly adopted by an operator-provided legacy batch.

**Rationale**: The system cannot know exactly which model generated old vectors. Assuming current settings would violate the acceptance criterion that every embedding can be attributed exactly.

**Alternatives considered**:

- Backfill old chunks with current settings automatically: unsafe because it can lie about model provenance.
- Delete old embeddings automatically: too destructive for startup/init and removes potential full-text utility.

## Decision 3: Compatibility identity includes provider, model, dimension and version

**Decision**: A stored embedding is vector-compatible only when provider, model, dimension and version/fingerprint match the active embedding configuration.

**Rationale**: Model names can collide across providers, and a revision/fingerprint is the only stable way to separate provider-side model updates or local model swaps under the same display name.

**Alternatives considered**:

- Compare only dimension: vectors may have the same shape but incompatible semantic spaces.
- Compare provider/model/dimension but ignore version: acceptable for some deployments, but the feature goal explicitly includes version/revision.

## Decision 4: Search remains hybrid, but vector candidates are strict

**Decision**: Vector search filters to compatible chunks. Text search may still return unversioned/incompatible chunks, with `match_reasons` and `score` behavior making it clear that a result came from text-only matching.

**Rationale**: Full-text search does not rely on embedding comparability. Keeping it available preserves discoverability while preventing vector pollution.

**Alternatives considered**:

- Exclude incompatible chunks from both vector and text search: stricter but can hide useful documents until reindex completes.
- Include incompatible vectors with lower score: still mixes incomparable spaces and defeats the objective.

## Decision 5: Startup validates pgvector typmod instead of mutating dimension automatically

**Decision**: Replace automatic `ALTER COLUMN embedding TYPE vector(768)` behavior with a runtime check that compares the configured vector dimension against the actual pgvector column dimension. Mismatches fail startup with an explicit migration message.

**Rationale**: Changing vector dimension is a data migration/reindexing event, not routine init. Automatic mutation can corrupt assumptions or fail late.

**Alternatives considered**:

- Keep forcing vector(768): conflicts with configurable `VECTOR_DIM`.
- Auto-migrate to configured dimension: unsafe because existing vectors cannot be reshaped without reembedding.

## Decision 6: Add reindex planning before full background worker

**Decision**: MVP should provide deterministic pending detection and a synchronous/service-level reindex path. A background job queue can be added later if volume requires it.

**Rationale**: The repo currently has service functions and CLI-like utilities, not a worker system. Planning and tests can validate correctness without adding operational complexity.

**Alternatives considered**:

- Add a new worker/queue now: unnecessary infrastructure for current stack.
- Only mark pending with no reindex service: leaves the feature unable to recover compatible vectors.
