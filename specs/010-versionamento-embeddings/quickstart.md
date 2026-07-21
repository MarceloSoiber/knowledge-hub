# Quickstart: Versionamento de Embeddings

## 1. Start with matching dimension

Use the current default dimension:

```bash
VECTOR_DIM=768 npm run dev:up
```

Expected:

- API starts.
- `knowledge_chunks.embedding` dimension check passes.

## 2. Ingest a document

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -d '{
    "title": "embedding version smoke",
    "category_ids": [1],
    "content": "Embeddings must record model provenance."
  }'
```

Expected:

- Source is created.
- Chunks have `embedding_status=embedded`.
- Chunks point to an `embedding_batches` row with active provider/model/dimension/version.

## 3. Search with compatible configuration

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -d '{"query":"model provenance","include_match_reasons":true}'
```

Expected:

- Compatible chunks can include `vector` in `match_reasons`.

## 4. Change embedding model

Change `EMBEDDING_MODEL` or `EMBEDDING_VERSION`, recreate backend/MCP, and inspect pending status.

Expected:

- Existing chunks from the old config no longer participate in vector search for the new config.
- Pending/reindex view reports `config_changed`.

## 5. Validate dimension guard

Run startup with a mismatched dimension against the same database:

```bash
VECTOR_DIM=1024 npm run backend:up
```

Expected:

- Startup fails with an explicit message requiring a migration/reindex.
- The init flow must not silently alter `knowledge_chunks.embedding` to another dimension.
