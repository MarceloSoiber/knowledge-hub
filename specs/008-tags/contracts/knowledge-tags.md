# Contract: Knowledge Tags

## Tag Object

```json
{
  "id": 1,
  "name": "postgres"
}
```

## Endpoints

### List Tags

`GET /api/v1/knowledge/tags`

Response `200`:

```json
[
  {"id": 1, "name": "postgres"},
  {"id": 2, "name": "python"}
]
```

### Autocomplete Tags

`GET /api/v1/knowledge/tags/autocomplete?q=po&limit=10`

Response `200`:

```json
[
  {"id": 1, "name": "postgres"}
]
```

Rules:

- `q` is trimmed and normalized for matching.
- `limit` defaults to 10 and must have an upper bound.

### Create Tag

`POST /api/v1/knowledge/tags`

Request:

```json
{
  "name": "Postgres"
}
```

Response `201`:

```json
{
  "id": 1,
  "name": "postgres"
}
```

Errors:

- `409 Conflict` when normalized tag already exists.
- `422 Unprocessable Entity` when name is empty or invalid.

### Update Tag

`PATCH /api/v1/knowledge/tags/{tag_id}`

Request:

```json
{
  "name": "postgresql"
}
```

Response `200`:

```json
{
  "id": 1,
  "name": "postgresql"
}
```

Errors:

- `404 Not Found` when tag id does not exist.
- `409 Conflict` when normalized new name collides with another tag.

### Delete Tag

`DELETE /api/v1/knowledge/tags/{tag_id}`

Response `204`.

Errors:

- `404 Not Found` when tag id does not exist.
- `409 Conflict` when tag is associated with any source.

## Source Payloads

Source reads include tags:

```json
{
  "source_id": "7b198e0c-0000-0000-0000-000000000000",
  "title": "Notas de RAG",
  "categories": [{"id": 1, "name": "software"}],
  "tags": [{"id": 2, "name": "rag"}],
  "source_type": "text",
  "uri": "text://...",
  "content_hash": "..."
}
```

## Ingestion

Text ingestion:

```json
{
  "title": "Notas de Postgres",
  "category_ids": [1],
  "tag_ids": [1, 2],
  "content": "..."
}
```

Upload ingestion uses repeated multipart fields:

```text
category_ids=1
tag_ids=1
tag_ids=2
file=@notes.md
```

Rules:

- `category_ids` remains required.
- `tag_ids` is optional.
- Duplicate ids are invalid.
- Missing tag ids return `404`.
- v1 accepts tag ids only. Clients should create, list or autocomplete tags
  before assigning them.

## Source Patch

```json
{
  "tag_ids": [1, 2]
}
```

Rules:

- Updating only `tag_ids` must not regenerate embeddings.
- Empty `tag_ids` clears all tags from the source.

## Search and Answer Filters

Search request:

```json
{
  "query": "indice hnsw postgres",
  "category_ids": [1],
  "tag_ids": [1, 2],
  "limit": 5
}
```

Rules:

- `tag_ids` uses ANY semantics for MVP.
- `category_ids` and `tag_ids` combine as AND dimensions.
- Results must not duplicate chunks when a source matches more than one requested tag.

## MCP

MCP `search_knowledge` accepts optional `tag_ids`.

MCP source and hit models include:

```json
{
  "tags": [{"id": 1, "name": "postgres"}]
}
```
