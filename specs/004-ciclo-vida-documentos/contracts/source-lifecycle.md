# Source Lifecycle Contract

## Source Identity

Source management endpoints use the public UUID string exposed as `source_id`.
Chunk search responses may continue exposing internal integer IDs for compatibility.

## Endpoints

- `GET /api/v1/knowledge/sources/{source_id}` returns one source with content.
- `PATCH /api/v1/knowledge/sources/{source_id}` accepts `title`, `category_ids` and/or `content`.
- `DELETE /api/v1/knowledge/sources/{source_id}?confirm=true` permanently deletes the source.

## Duplicate Policy

Canonical normalized content is hashed with SHA-256. Creating or updating a source with content already present in another source returns `409 Conflict` and identifies the existing public source ID.

## MCP

- `source(source_id)` returns detailed source data by UUID.
- MCP does not expose source update or delete tools in this feature.
