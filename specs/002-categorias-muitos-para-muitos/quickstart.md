# Quickstart: Categorias Muitos-Para-Muitos

## Prerequisites

- PostgreSQL service running.
- Backend dependencies installed.
- Auth token configured or auth disabled in local test database.

## Validate

```bash
.venv/bin/python -m pytest
```

## Manual API Flow

1. Create categories:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/categories \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Financas"}'
```

2. Ingest text with multiple categories:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/texts \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"relatorio","category_ids":[1,2],"content":"conteudo"}'
```

3. Search with ANY category filter:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"relatorio","category_ids":[1,2]}'
```
