# Contract: Knowledge Categories

## Categories

- `GET /api/v1/knowledge/categories` returns `[{ "id": 1, "name": "docs" }]`.
- `POST /api/v1/knowledge/categories` accepts `{ "name": "Docs" }` and returns the normalized category with `201`.
- `PATCH /api/v1/knowledge/categories/{id}` accepts `{ "name": "manuals" }`.
- `DELETE /api/v1/knowledge/categories/{id}` returns `204` when unused, `409` when in use and `404` when missing.

## Ingestion

- `POST /api/v1/knowledge/uploads` accepts multipart `file` and repeated `category_ids` fields.
- `POST /api/v1/knowledge/texts` accepts `{ "title": "...", "category_ids": [1, 2], "content": "..." }`.
- Responses include `{ "source_id": 1, "title": "...", "categories": [{ "id": 1, "name": "docs" }], "chunks_created": 3 }`.

## Search and Answer

- `POST /api/v1/knowledge/search` accepts optional `"category_ids": [1, 2]`.
- `POST /api/v1/knowledge/answer` accepts optional `"category_ids": [1, 2]`.
- Filter semantics are ANY: a source matching at least one requested category is eligible.

## Sources

- `GET /api/v1/knowledge/sources` returns source objects with `categories` and no `category_id`.

## MCP

- `search(query, limit=5, category_ids=None)` mirrors API search filtering.
- `sources()` returns source objects with `categories`.
- `categories()` lists category objects.
