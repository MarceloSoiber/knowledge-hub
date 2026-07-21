# Data Model: Versionamento de Embeddings

## EmbeddingBatch

Represents one effective embedding configuration and indexing/reindexing run.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key |
| `provider` | varchar(50) | Effective provider, e.g. `local` or external API provider |
| `model` | varchar(255) | Effective embedding model name |
| `dimension` | integer | Expected vector dimension |
| `version` | varchar(255) | Explicit revision or deterministic configuration fingerprint |
| `config_hash` | varchar(64) | SHA-256 of normalized provider/model/dimension/version payload |
| `status` | varchar(32) | `running`, `completed`, `failed`, `adopted_legacy` |
| `started_at` | timestamptz | Batch start |
| `completed_at` | timestamptz nullable | Batch completion |
| `error_message` | text nullable | Failure reason, sanitized |
| `chunks_total` | integer | Number of chunks attempted |
| `chunks_embedded` | integer | Number of chunks successfully attached |

### Constraints and Indexes

- Unique/index on `config_hash` when used as reusable active configuration lookup.
- Index on `(provider, model, dimension, version)`.
- Check `dimension > 0`.
- Check `status` in known status values.

## KnowledgeChunk changes

Existing chunk row gains embedding-specific provenance fields.

| Field | Type | Notes |
| --- | --- | --- |
| `embedding_batch_id` | integer nullable FK | References `embedding_batches.id`; nullable for legacy chunks |
| `embedding_content_hash` | varchar(64) nullable | Hash of normalized chunk content at embedding time |
| `embedding_status` | varchar(32) | `embedded`, `pending`, `unversioned`, `failed` |
| `embedded_at` | timestamptz nullable | Time this chunk vector was generated |
| `embedding_error` | text nullable | Sanitized last failure, if any |

### Constraints and Indexes

- Index on `embedding_batch_id`.
- Index on `(embedding_status, embedding_batch_id)`.
- Index on `(embedding_content_hash, embedding_batch_id)` to support reuse/idempotency.
- `embedding_status='embedded'` requires non-null `embedding`, `embedding_batch_id`, `embedding_content_hash` and `embedded_at`.

## EmbeddingCompatibility

Runtime value object, not necessarily a table.

| Field | Meaning |
| --- | --- |
| `provider` | Active provider from settings/client |
| `model` | Active embedding model |
| `dimension` | Active vector dimension |
| `version` | Active version or derived fingerprint |
| `config_hash` | Stable hash for lookup/filtering |

## ReindexCandidate

Read model for pending work.

| Field | Meaning |
| --- | --- |
| `source_id` | Public source id |
| `chunk_id` | Internal chunk id |
| `current_status` | `pending`, `unversioned`, `failed`, or incompatible existing batch |
| `reason` | `missing_batch`, `config_changed`, `content_hash_changed`, `embedding_failed`, `dimension_mismatch` |
| `current_batch` | Stored batch metadata when available |
| `target_config` | Active embedding compatibility identity |

## Relationships

```text
EmbeddingBatch 1 -- * KnowledgeChunk
DocumentSource 1 -- * KnowledgeChunk
```

## Migration Notes

- Add `embedding_batches` first.
- Add nullable chunk columns with safe defaults.
- Existing chunks:
  - If `embedding` is non-null and no explicit legacy adoption is requested, set `embedding_status='unversioned'`.
  - If `embedding` is null, set `embedding_status='pending'`.
- Do not rewrite the pgvector column dimension in idempotent init.
- Add a separate explicit migration/reindex path for dimension changes.
