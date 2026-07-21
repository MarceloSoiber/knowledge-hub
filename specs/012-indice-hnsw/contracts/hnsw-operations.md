# Contract: HNSW Operations

## CLI Surface

Console script:

```bash
knowledge-hnsw <subcommand> [options]
```

### `baseline`

Captures exact/current vector search metrics before HNSW acceptance.

```bash
knowledge-hnsw baseline --queries evaluation.json --limit 10 --output reports/hnsw-baseline.json
```

Expected behavior:

- Reads evaluation queries.
- Uses active embedding config.
- Captures latency and exact/current result ids.
- Captures `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` when database access supports it.
- Does not mutate schema.

### `create`

Creates the HNSW index when preconditions pass.

```bash
knowledge-hnsw create --min-chunks 10000
```

Expected behavior:

- Verifies pgvector extension and HNSW support.
- Verifies compatible embedded chunk count is at least `--min-chunks`, unless `--force` is passed.
- Creates `ix_knowledge_chunks_embedding_hnsw_cosine`.
- Runs `ANALYZE knowledge_chunks`.
- Prints index name, duration and rollback command.

### `validate`

Compares HNSW against exact/current baseline.

```bash
knowledge-hnsw validate --baseline reports/hnsw-baseline.json --queries evaluation.json --recall-threshold 0.95 --output reports/hnsw-validation.json
```

Expected behavior:

- Runs representative queries with HNSW available.
- Captures plans and detects whether the HNSW index appears.
- Computes recall@k against baseline/exact ids.
- Reports p50/p95 latency and decision.
- Includes unfiltered and filtered query coverage in the report.

### `drop`

Rolls back the HNSW index.

```bash
knowledge-hnsw drop --execute
```

Expected behavior:

- Without `--execute`, prints the rollback SQL only.
- With `--execute`, drops `ix_knowledge_chunks_embedding_hnsw_cosine`.
- Prefer `DROP INDEX CONCURRENTLY IF EXISTS` in operator context.

## Report Contract

Reports are JSON objects with stable top-level keys:

```json
{
  "generated_at": "2026-07-21T12:00:00Z",
  "decision": "accepted",
  "index_name": "ix_knowledge_chunks_embedding_hnsw_cosine",
  "recall_at_k": 0.98,
  "latency": {
    "baseline_p95_ms": 430.0,
    "hnsw_p95_ms": 95.0
  },
  "plans": [],
  "queries": [],
  "rollback_sql": "DROP INDEX CONCURRENTLY IF EXISTS ix_knowledge_chunks_embedding_hnsw_cosine"
}
```

Additional fields are allowed. Existing fields should remain backward-compatible once introduced.
