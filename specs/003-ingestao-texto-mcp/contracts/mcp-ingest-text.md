# Contract: MCP ingest_text

## Tool

`ingest_text(title, content, category_ids, metadata=None)`

### Description

Persists a user-confirmed text note in the Knowledge Hub. The tool description must instruct agents to ask the user for explicit confirmation before calling it.

### Required Authorization

- Requires `knowledge:write`.
- Existing read tools continue to require `knowledge:read`.
- If per-tool scope enforcement is unavailable, the tool must remain disabled or move to a write-only MCP server/configuration.

### Input

```json
{
  "title": "Architecture note",
  "content": "Normalized text to chunk and embed.",
  "category_ids": [1, 2],
  "metadata": {
    "note_type": "decision"
  }
}
```

### Success Output

```json
{
  "source_id": 42,
  "title": "Architecture note",
  "categories": [
    { "id": 1, "name": "docs" }
  ],
  "chunks_created": 3
}
```

## Error Mapping

- Invalid title/content/category list: validation error with a short corrective message.
- Missing category: category-not-found message; no data persisted.
- Embedding configuration unavailable: service-unavailable style message; no data persisted.
- Embedding provider failure: upstream-failure style message; no data persisted.
- Read-only credentials: authorization error before ingestion starts.

## Catalog Requirements

The MCP catalog entry must make these points clear:

- The tool writes persistent knowledge.
- The agent must get explicit user confirmation before use.
- The tool is for user-provided notes or summaries, not automatic conversation archiving.
- `category_ids` should come from the `categories` tool.
