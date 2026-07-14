# Quickstart: Ingestao de Texto pelo MCP

## Preconditions

- Database is initialized and has at least one category.
- MCP auth token/scopes are configured for a write-capable client.
- Embedding provider is reachable.

## Manual Validation Flow

1. Start backend, database and MCP server.
2. List MCP categories and choose at least one category ID.
3. Ask the user to confirm the exact text note that will be saved.
4. Call `ingest_text` with `title`, `content` and `category_ids`.
5. Confirm the response includes `source_id`, `title`, `categories` and `chunks_created`.
6. Call `sources()` and verify the source appears with `source_type`/origin `mcp` when implemented.
7. Call `search()` with text from the note and confirm a chunk is returned.
8. Repeat with read-only credentials and confirm `ingest_text` is denied.

## Test Commands

```bash
.venv/bin/python -m pytest tests/test_knowledge_service.py tests/test_mcp_knowledge.py
```

Run the broader suite after focused tests pass:

```bash
.venv/bin/python -m pytest
```
