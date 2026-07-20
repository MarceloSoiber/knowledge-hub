# Quickstart: Busca Hibrida

## 1. Prepare database

```bash
.venv/bin/python -m backend.app.db.init
```

Confirm `knowledge_chunks` has the full-text representation and GIN index:

```sql
\d knowledge_chunks
```

## 2. Ingest exact-token fixture

Create or ingest content containing identifiers such as:

- `ERR_CONN_RESET`
- `ABC-1234`
- `PETR4`

## 3. Validate API search

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"ERR_CONN_RESET","limit":5}'
```

Expected:

- The chunk containing `ERR_CONN_RESET` appears in the top 5.
- The response shape remains compatible with the existing search contract.
- No chunk id appears twice.

## 4. Validate semantic search

Run a paraphrased query from the Plano 12 dataset and compare with the vector-only baseline.

Expected:

- Recall@K and MRR equal or exceed the baseline.
- Exact-token improvements do not remove semantic matches.

## 5. Validate filters

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"ERR_CONN_RESET","limit":5,"category_ids":[1]}'
```

Expected:

- Only sources associated with category `1` are returned.
- Filtering happens before final result limit.

## 6. Validate query plan

Use `EXPLAIN (ANALYZE, BUFFERS)` on the text-search statement.

Expected:

- Text path uses `ix_knowledge_chunks_search_vector`.
- Vector path remains compatible with the pgvector ordering/index strategy.

## 7. Run tests

```bash
.venv/bin/python -m pytest tests/test_knowledge_service.py tests/test_knowledge_api_integration.py tests/test_mcp_knowledge.py
```

## 8. Acceptance gate

Run the Plano 12 evaluation dataset when available and compare:

- vector-only baseline
- hybrid candidate

Hybrid passes only if it equals or improves semantic metrics and improves exact-token cases.
