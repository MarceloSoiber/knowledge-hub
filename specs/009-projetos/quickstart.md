# Quickstart: Projetos

## Prerequisites

- PostgreSQL + pgvector services running.
- Backend configuration points to the local database and embedding provider.
- Existing categories available for ingestion.

## 1. Run Tests

```bash
.venv/bin/python -m pytest tests/test_knowledge_service.py tests/test_knowledge_api_integration.py tests/test_mcp_knowledge.py
```

## 2. Create a Project

```bash
curl -sS -X POST http://localhost:8000/api/v1/knowledge/projects \
  -H 'Content-Type: application/json' \
  -d '{"name":"MCP Knowledge Hub","description":"Contexto do projeto"}'
```

Expected: response includes `"status": "active"`.

## 3. Ingest Text Into a Project

```bash
curl -sS -X POST http://localhost:8000/api/v1/knowledge/texts \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Notas do projeto",
    "category_ids": [1],
    "project_ids": [1],
    "content": "Decisoes especificas do projeto MCP Knowledge Hub."
  }'
```

Expected: response includes `projects`.

## 4. Associate the Same Source With Another Project

```bash
curl -sS -X POST http://localhost:8000/api/v1/knowledge/projects \
  -H 'Content-Type: application/json' \
  -d '{"name":"Agentes"}'
```

```bash
curl -sS -X PATCH http://localhost:8000/api/v1/knowledge/sources/<source_id> \
  -H 'Content-Type: application/json' \
  -d '{"project_ids":[1,2]}'
```

Expected: the same source has both projects and keeps the same `source_id`.

## 5. Search Within a Project

```bash
curl -sS -X POST http://localhost:8000/api/v1/knowledge/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "decisoes especificas",
    "project_ids": [1],
    "limit": 5
  }'
```

Expected: results include only chunks whose source is associated with project `1`.

## 6. List Sources for a Project

```bash
curl -sS http://localhost:8000/api/v1/knowledge/projects/1/sources
```

Expected: response includes sources associated with project `1`.

## 7. Archive Without Deleting Knowledge

```bash
curl -sS -X POST http://localhost:8000/api/v1/knowledge/projects/1/archive
```

Expected: project status becomes `archived`; source and chunks still exist.

## 8. Verify Database Shape

```sql
SELECT normalized_name, COUNT(*)
FROM projects
GROUP BY normalized_name
HAVING COUNT(*) > 1;
```

Expected: zero rows.

```sql
SELECT document_source_id, project_id, COUNT(*)
FROM document_source_projects
GROUP BY document_source_id, project_id
HAVING COUNT(*) > 1;
```

Expected: zero rows.
