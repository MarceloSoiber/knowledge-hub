# Data Model: Indice Vetorial HNSW

## Database Objects

### HNSW Index

- **Name**: `ix_knowledge_chunks_embedding_hnsw_cosine`
- **Table**: `knowledge_chunks`
- **Column**: `embedding`
- **Access Method**: `hnsw`
- **Operator Class**: `vector_cosine_ops`
- **Purpose**: Accelerate cosine-distance ordering for compatible embedded chunks.

No new application table is required for MVP.

## Report Objects

### VectorIndexValidationReport

Operator-facing JSON/file artifact.

- `generated_at`: ISO timestamp.
- `pgvector_version`: detected extension version.
- `embedding_config_hash`: active embedding identity hash.
- `chunk_count`: total chunks considered.
- `embedded_chunk_count`: compatible embedded chunks considered.
- `index_name`: HNSW index name.
- `index_size_bytes`: optional index size after creation.
- `baseline`: latency and exact ids before HNSW or with exact mode.
- `hnsw`: latency, ids and plan summary after HNSW.
- `recall_at_k`: per-query and aggregate recall.
- `filters_covered`: unfiltered/category/project/tag coverage flags.
- `write_impact`: insertion/reindex timing summary when measured.
- `decision`: `accepted`, `rejected`, or `inconclusive`.
- `reasons`: list of concise decision reasons.
- `rollback_sql`: concrete rollback statement.

### EvaluationQuery

- `query`: query text, sanitized in logs if needed.
- `limit`: top-k limit.
- `category_ids`: optional category filters.
- `tag_ids`: optional tag filters.
- `project_ids`: optional project filters.
- `exact_chunk_ids`: expected or measured exact top-k ids.
- `hnsw_chunk_ids`: approximate top-k ids.
- `recall_at_k`: overlap ratio.

## Existing Entities Used

- `KnowledgeChunk`: source of vectors, status, metadata and source relationship.
- `EmbeddingBatch`: filters vector search to the active compatible embedding config.
- `DocumentSource`: joins category/tag/project relationships used by filtered validation.
- `ReindexRun`/`ReindexItem`: existing operational reindex objects used when measuring write/reindex impact; no schema change expected.
