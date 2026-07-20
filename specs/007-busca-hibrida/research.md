# Research: Busca Hibrida

## Decision 1: Use PostgreSQL full-text search on chunks

**Decision**: Add a `tsvector` representation to `knowledge_chunks` and query it with PostgreSQL full-text search.

**Rationale**: The knowledge base already depends on PostgreSQL and pgvector. Keeping text retrieval in the same database preserves category filtering, citation joins and transaction boundaries.

**Alternatives considered**:

- External search engine: rejected for v1 because it adds operational complexity and a second indexing pipeline.
- `ILIKE` fallback only: rejected because it does not scale well and cannot provide ranked textual candidates with index support.

## Decision 2: Start with `simple` text search configuration

**Decision**: Use `simple` for the initial `to_tsvector`/query configuration.

**Rationale**: The plan prioritizes codes, numbers, tickers, names and error messages. `simple` avoids stemming surprises and is safer for code-like tokens.

**Alternatives considered**:

- `portuguese`: useful for natural-language Portuguese stemming, but riskier for identifiers. Reconsider only if Plano 12 shows a quality gain without exact-token regression.
- Dual vectors (`simple` and `portuguese`): stronger but more schema/query complexity than v1 needs.

## Decision 3: Fuse rankings with Reciprocal Rank Fusion

**Decision**: Combine vector and text candidate positions with RRF, using `k=60` as the initial constant.

**Rationale**: Vector similarity and full-text rank are not comparable scales. RRF uses rank positions and is robust when one retrieval path finds candidates the other misses.

**Alternatives considered**:

- Weighted score sum: rejected because cosine similarity and text rank are not calibrated to the same range.
- Text-first fallback after vector search: rejected because it cannot promote strong exact matches that should beat weaker semantic matches.

## Decision 4: Preserve public score semantics

**Decision**: Keep the public `score` as vector similarity when available. Treat fused rank as internal ordering unless a later contract explicitly exposes it.

**Rationale**: Existing docs already explain `score` as a similarity signal. Reusing it for RRF would silently change meaning and break calibration around `min_score`.

**Alternatives considered**:

- Return RRF as `score`: rejected because it is not a similarity probability and would invalidate current threshold interpretation.
- Add a new `hybrid_score` by default: rejected for compatibility; diagnostics can expose reasons opt-in.

## Decision 5: Optional diagnostics only

**Decision**: Add match reasons only behind an explicit request flag.

**Rationale**: Operators need diagnostics for evaluation, but normal API and MCP clients should keep the current concise response shape.

**Alternatives considered**:

- Always include reasons: rejected due to response noise and public-contract churn.
- No diagnostics: rejected because Plano 06 calls out match reason exposure for calibration.

## Implementation Note: 2026-07-20

The implemented configuration remains `simple`.

Focused automated tests simulate exact-token retrieval, semantic/vector preservation,
deduplication, text-only matches and optional diagnostics. The full Plano 12 runner
and live PostgreSQL `EXPLAIN` validation remain release gates for a database-backed
acceptance pass.
