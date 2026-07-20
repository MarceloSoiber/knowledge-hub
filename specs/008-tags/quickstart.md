# Quickstart: Tags

## Prerequisites

- PostgreSQL + pgvector services running.
- Backend configuration points to the local database and embedding provider.
- Existing categories available for ingestion.

## 1. Run Tests

```bash
.venv/bin/python -m pytest tests/test_knowledge_service.py tests/test_knowledge_api_integration.py tests/test_mcp_knowledge.py
```

## 2. Create Tags

```bash
curl -sS -X POST http://localhost:8000/api/v1/knowledge/tags \
  -H 'Content-Type: application/json' \
  -d '{"name":"Postgres"}'
```

Repeat with an equivalent name:

```bash
curl -sS -X POST http://localhost:8000/api/v1/knowledge/tags \
  -H 'Content-Type: application/json' \
  -d '{"name":" pósTgres "}'
```

Expected: the second request returns `409 Conflict`.

## 3. Autocomplete Tags

```bash
curl -sS 'http://localhost:8000/api/v1/knowledge/tags/autocomplete?q=po&limit=10'
```

Expected: response includes `postgres`.

## 4. Ingest Text With Tags

```bash
curl -sS -X POST http://localhost:8000/api/v1/knowledge/texts \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Notas de Postgres",
    "category_ids": [1],
    "tag_ids": [1],
    "content": "Postgres usa indices GIN e HNSW em cenarios diferentes."
  }'
```

Expected: response includes `tags`.

## 5. Search With Category and Tag Filters

```bash
curl -sS -X POST http://localhost:8000/api/v1/knowledge/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "indices postgres",
    "category_ids": [1],
    "tag_ids": [1],
    "limit": 5
  }'
```

Expected: results include only sources that satisfy the category filter and at least one requested tag, with no duplicate chunk ids.

## 6. Patch Only Tags

```bash
curl -sS -X PATCH http://localhost:8000/api/v1/knowledge/sources/<source_id> \
  -H 'Content-Type: application/json' \
  -d '{"tag_ids":[1,2]}'
```

Expected: source tags change and embeddings are not regenerated.

## 7. Verify Database Shape

```sql
SELECT normalized_name, COUNT(*)
FROM tags
GROUP BY normalized_name
HAVING COUNT(*) > 1;
```

Expected: zero rows.

```sql
SELECT document_source_id, tag_id, COUNT(*)
FROM document_source_tags
GROUP BY document_source_id, tag_id
HAVING COUNT(*) > 1;
```

Expected: zero rows.
