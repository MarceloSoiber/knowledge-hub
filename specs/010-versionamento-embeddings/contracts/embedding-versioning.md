# Contract: Embedding Versioning

## Public/API Behavior

This feature primarily protects ingestion/search internals. Public fields should be added only where they help operators understand indexing state.

### Chunk Read Additions

Search and detail responses MAY include an `embedding` metadata block when the API chooses to expose operational state:

```json
{
  "embedding": {
    "status": "embedded",
    "provider": "local",
    "model": "text-embedding-nomic-embed-text-v1.5",
    "dimension": 768,
    "version": "default",
    "embedded_at": "2026-07-21T12:00:00Z"
  }
}
```

For unversioned chunks:

```json
{
  "embedding": {
    "status": "unversioned",
    "provider": null,
    "model": null,
    "dimension": null,
    "version": null,
    "embedded_at": null
  }
}
```

### Search/Answer Semantics

- Vector candidates MUST require `embedding_status='embedded'`.
- Vector candidates MUST require batch provider/model/dimension/version to match the active embedding config.
- Text candidates MAY include unversioned/incompatible chunks.
- When `include_match_reasons=true`, incompatible chunks returned via text MUST NOT include `vector` in `match_reasons`.
- `score` for text-only chunks remains nullable or text-derived according to existing hybrid-search behavior; it must not pretend to be vector similarity.

### Operational Endpoints

Not included in the first implementation slice. The backend now persists
provenance, filters compatible vector candidates, exposes internal pending-count
helpers and blocks dimension drift on startup. A later slice may expose:

```http
GET /api/v1/knowledge/embeddings/config
```

Returns active compatibility identity and database vector dimension.

```http
GET /api/v1/knowledge/embeddings/pending?limit=50
```

Returns chunks/sources requiring reindex.

```http
POST /api/v1/knowledge/embeddings/reindex
```

Runs a bounded reindex operation for pending chunks. Request body:

```json
{
  "source_ids": ["public-source-id"],
  "limit": 100,
  "dry_run": false
}
```

Response:

```json
{
  "target_config": {
    "provider": "local",
    "model": "text-embedding-nomic-embed-text-v1.5",
    "dimension": 768,
    "version": "default"
  },
  "chunks_scanned": 12,
  "chunks_embedded": 12,
  "chunks_reused": 0,
  "chunks_failed": 0
}
```

## MCP Behavior

- MCP search inherits REST/backend search compatibility semantics.
- MCP may expose a short `embedding_status` resource/tool later, but MVP can keep this backend-only unless operational clients need it.

## Error Behavior

- Startup dimension mismatch: fail with a configuration error before serving requests.
- Missing/unknown active embedding configuration: return `503` for ingestion/search paths that require embeddings.
- Reindex failure for one chunk must not mark the whole batch completed; batch status becomes `failed` or partial status is visible.
