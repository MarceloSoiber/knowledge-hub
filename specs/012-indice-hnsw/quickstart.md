# Quickstart: Indice Vetorial HNSW

## Preconditions

1. PostgreSQL has pgvector installed.
2. Active embedding model, dimension and cosine-distance semantics are stable.
3. A representative corpus is loaded and embedded.
4. Evaluation queries include at least:
   - one unfiltered query;
   - one category-filtered query;
   - one project-filtered query.

## Baseline

```bash
.venv/bin/python -m pytest tests/test_knowledge_service.py
knowledge-hnsw baseline --queries evaluation/hnsw-queries.json --limit 10 --output reports/hnsw-baseline.json
```

Review:

- p50/p95 latency;
- exact top-k ids;
- `EXPLAIN (ANALYZE, BUFFERS)` plan;
- whether corpus size justifies HNSW.

## Create Index

```bash
knowledge-hnsw create --min-chunks 10000
```

Expected SQL shape:

```sql
CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding_hnsw_cosine
ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);

ANALYZE knowledge_chunks;
```

For production-sized tables, use the documented concurrent path outside a transaction.

## Validate

```bash
knowledge-hnsw validate \
  --baseline reports/hnsw-baseline.json \
  --queries evaluation/hnsw-queries.json \
  --recall-threshold 0.95 \
  --output reports/hnsw-validation.json
```

Accept only if:

- p95 latency improves on representative queries;
- recall@k is at or above the agreed threshold;
- filtered queries still return correct category/project results;
- write/reindex impact is recorded;
- rollback command is documented.

## Rollback

Dry-run:

```bash
knowledge-hnsw drop
```

Execute:

```bash
knowledge-hnsw drop --execute
```

Expected rollback SQL:

```sql
DROP INDEX CONCURRENTLY IF EXISTS ix_knowledge_chunks_embedding_hnsw_cosine;
```

Use the non-concurrent equivalent only in controlled dev/test transactions.

## Validation status

The repository test suite validates the command, report and SQL construction.
Manual execution of this quickstart is deferred because no PostgreSQL service is
running in the local compose environment and HNSW acceptance needs a populated,
representative corpus rather than an empty database.
