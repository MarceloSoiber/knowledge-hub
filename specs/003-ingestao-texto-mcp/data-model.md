# Data Model: Ingestao de Texto pelo MCP

## MCPTextIngestRequest

- `title`: required string, trimmed, 1 to 255 characters.
- `content`: required non-empty text content.
- `category_ids`: required list of unique positive category IDs.
- `metadata`: optional object limited to allowlisted keys.

Validation:

- Reject empty title or content.
- Reject empty, duplicated or non-positive category IDs.
- Reject unsupported metadata keys.

## MCPTextIngestResult

- `source_id`: persisted source ID.
- `title`: persisted source title.
- `categories`: list of `{ id, name }` category objects.
- `chunks_created`: number of chunks generated for the source.

## DocumentSource

- Created through the existing ingestion service.
- `source_type`: should be `mcp` for MCP-created sources when backend changes are made for this feature.
- `uri`: should remain deterministic for recadastro until Plano 03 defines lifecycle/identity changes.
- Relationships: one or more categories and generated chunks.

## MCPAccessScope

- `knowledge:read`: permits `search`, `sources`, `categories` and read resources.
- `knowledge:write`: required for `ingest_text`.

## Metadata Allowlist

Initial safe keys:

- `client_id`: MCP client identity when provided by trusted auth context.
- `note_type`: short caller-provided label for the note kind.

Metadata must not store bearer tokens, full prompts, hidden chain-of-thought or unconfirmed conversation transcripts.
