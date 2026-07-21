# Research: Indice Vetorial HNSW

## Decision 1: HNSW is operator-gated, not blindly created on startup

**Decision**: Provide an operator CLI/runbook to create and validate HNSW. Keep any startup/init behavior limited to capability checks or non-concurrent dev-only idempotent helpers.

**Rationale**: HNSW creation can be expensive, may not help small datasets, and `CREATE INDEX CONCURRENTLY` cannot run inside the existing `engine.begin()` initialization transaction.

**Alternatives Considered**:

- Always create in `init_db()`: rejected because it can slow startup and is not safe for production-sized tables.
- Manual SQL only: rejected because it loses repeatable validation/reporting.

## Decision 2: Use `vector_cosine_ops`

**Decision**: Create `USING hnsw (embedding vector_cosine_ops)` for the existing `KnowledgeChunk.embedding` column.

**Rationale**: Current repository search uses `KnowledgeChunk.embedding.cosine_distance(query_embedding)` and returns `1 - distance` as score. The index operator class must match this semantics.

**Alternatives Considered**:

- `vector_l2_ops`: rejected because it changes ranking semantics.
- `vector_ip_ops`: rejected unless embedding normalization and scoring contract are revisited.

## Decision 3: Compare against exact search before accepting

**Decision**: Treat exact/current search as baseline and compare HNSW top-k ids with recall@k, plus p50/p95 latency.

**Rationale**: HNSW is approximate. Latency improvement alone is insufficient if search quality drops above the agreed threshold.

**Alternatives Considered**:

- Validate only with `EXPLAIN`: rejected because index usage does not prove acceptable recall.
- Validate only with application tests: rejected because synthetic unit tests cannot capture corpus-specific quality.

## Decision 4: Use JSON explain plans for parsing

**Decision**: Capture `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` for machine-readable validation, with a text summary in CLI output.

**Rationale**: JSON plans allow deterministic tests for index-name detection and latency extraction while preserving human-readable runbook summaries.

**Alternatives Considered**:

- Parse text explain output: rejected because it is brittle.

## Decision 5: Keep API/MCP unchanged

**Decision**: Do not expose HNSW controls through REST/MCP in MVP.

**Rationale**: This is an operational performance change, not a user-facing search feature. Existing API contracts should remain stable.

**Alternatives Considered**:

- Add admin endpoints: deferred until there is an authentication/authorization story for operational mutations.
