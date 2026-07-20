# Contract: Knowledge Projects

## Project Object

```json
{
  "id": 1,
  "name": "mcp-knowledge-hub",
  "description": "Contexto de desenvolvimento do hub",
  "status": "active",
  "created_at": "2026-07-20T12:00:00Z",
  "updated_at": "2026-07-20T12:00:00Z"
}
```

## Endpoints

### List Projects

`GET /api/v1/knowledge/projects?status=active`

Rules:

- `status` is optional.
- Allowed statuses: `active`, `archived`.
- If no status is supplied, recommended MVP behavior is to return all projects and expose status explicitly.

Response `200`:

```json
[
  {
    "id": 1,
    "name": "mcp-knowledge-hub",
    "description": "Contexto de desenvolvimento do hub",
    "status": "active",
    "created_at": "2026-07-20T12:00:00Z",
    "updated_at": "2026-07-20T12:00:00Z"
  }
]
```

### Create Project

`POST /api/v1/knowledge/projects`

Request:

```json
{
  "name": "MCP Knowledge Hub",
  "description": "Contexto de desenvolvimento do hub"
}
```

Response `201`:

```json
{
  "id": 1,
  "name": "mcp knowledge hub",
  "description": "Contexto de desenvolvimento do hub",
  "status": "active",
  "created_at": "2026-07-20T12:00:00Z",
  "updated_at": "2026-07-20T12:00:00Z"
}
```

Errors:

- `409 Conflict` when normalized project name already exists.
- `422 Unprocessable Entity` when name is empty or invalid.

### Update Project

`PATCH /api/v1/knowledge/projects/{project_id}`

Request:

```json
{
  "name": "mcp knowledge hub",
  "description": "Novo resumo"
}
```

Response `200`: project object.

Errors:

- `404 Not Found` when project id does not exist.
- `409 Conflict` when normalized name collides with another project.

### Archive Project

`POST /api/v1/knowledge/projects/{project_id}/archive`

Response `200`: project object with `"status": "archived"`.

Rules:

- Does not delete sources, chunks or associations.
- Archived projects remain filterable by explicit id.

### Reactivate Project

`POST /api/v1/knowledge/projects/{project_id}/reactivate`

Response `200`: project object with `"status": "active"`.

### List Project Sources

`GET /api/v1/knowledge/projects/{project_id}/sources`

Response `200`:

```json
[
  {
    "source_id": "7b198e0c-0000-0000-0000-000000000000",
    "title": "Notas do projeto",
    "categories": [{"id": 1, "name": "software"}],
    "tags": [{"id": 2, "name": "rag"}],
    "projects": [{"id": 1, "name": "mcp knowledge hub", "status": "active"}],
    "source_type": "text",
    "uri": "text:Notas do projeto",
    "content_hash": "..."
  }
]
```

## Source Payloads

Source reads include projects:

```json
{
  "source_id": "7b198e0c-0000-0000-0000-000000000000",
  "title": "Notas do projeto",
  "categories": [{"id": 1, "name": "software"}],
  "tags": [{"id": 2, "name": "rag"}],
  "projects": [{"id": 1, "name": "mcp knowledge hub", "status": "active"}],
  "source_type": "text",
  "uri": "text:Notas do projeto",
  "content_hash": "..."
}
```

## Ingestion

Text ingestion:

```json
{
  "title": "Notas de arquitetura",
  "category_ids": [1],
  "tag_ids": [2],
  "project_ids": [1],
  "content": "..."
}
```

Upload ingestion uses repeated multipart fields:

```text
category_ids=1
tag_ids=2
project_ids=1
file=@notes.md
```

Rules:

- `category_ids` remains required.
- `tag_ids` and `project_ids` are optional.
- Duplicate ids are invalid.
- Missing project ids return `404`.

## Source Patch

```json
{
  "project_ids": [1, 2]
}
```

Rules:

- Updating only `project_ids` must not regenerate embeddings.
- Empty `project_ids` clears all project associations.

## Search and Answer Filters

Search request:

```json
{
  "query": "decisao do projeto",
  "project_ids": [1],
  "category_ids": [1],
  "tag_ids": [2],
  "limit": 5
}
```

Rules:

- `project_ids` uses ANY semantics for MVP.
- `project_ids`, `category_ids` and `tag_ids` combine as AND dimensions.
- General sources with no project are excluded when `project_ids` is provided.
- Results must not duplicate chunks when a source matches more than one requested project.

## MCP

MCP `search` accepts optional `project_ids`.

MCP `ingest_text` accepts optional `project_ids`.

MCP source and hit models include:

```json
{
  "projects": [{"id": 1, "name": "mcp knowledge hub", "status": "active"}]
}
```

MCP should expose a `projects()` helper for id discovery.
