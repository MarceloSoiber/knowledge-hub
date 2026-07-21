# Data Model: Reindexacao e Backup

## ReindexRun

Represents one operator-triggered reindex dry-run or execution.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key |
| `public_id` | varchar(36) | Stable id for CLI output/resume |
| `target_provider` | varchar(50) | Active embedding provider at run start |
| `target_model` | varchar(255) | Active embedding model |
| `target_dimension` | integer | Active vector dimension |
| `target_version` | varchar(255) | Active embedding version |
| `target_config_hash` | varchar(64) | Active identity hash |
| `filters_json` | jsonb | Source/category selection and batch size |
| `dry_run` | boolean | True when no mutation should occur |
| `status` | varchar(32) | `running`, `dry_run_completed`, `completed`, `failed`, `cancelled` |
| `started_at` | timestamptz | Run creation/start |
| `completed_at` | timestamptz nullable | Run completion/failure |
| `sources_total` | integer | Selected sources |
| `chunks_total` | integer | Selected chunks |
| `chunks_reindexed` | integer | Chunks updated with compatible embeddings |
| `chunks_reused` | integer | Chunks skipped/reused because compatible embedding existed |
| `chunks_failed` | integer | Failed chunks |
| `error_message` | text nullable | Sanitized run-level error |

### Constraints and Indexes

- Index on `public_id`.
- Index on `(target_config_hash, status)`.
- Check `target_dimension > 0`.
- Check `status` in known values.

## ReindexItem

Represents per-source/per-chunk work and resume state.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key |
| `run_id` | integer FK | References `reindex_runs.id` |
| `source_id` | integer FK | References `document_sources.id` |
| `chunk_id` | integer nullable FK | References `knowledge_chunks.id` when item is chunk-specific |
| `reason` | varchar(64) | `missing_batch`, `config_changed`, `failed`, `unversioned`, `content_changed` |
| `status` | varchar(32) | `pending`, `processing`, `reindexed`, `reused`, `failed_retryable`, `failed_final`, `skipped` |
| `attempts` | integer | Retry attempts |
| `started_at` | timestamptz nullable | Current/last attempt start |
| `completed_at` | timestamptz nullable | Completion/failure time |
| `error_message` | text nullable | Sanitized item-level error |

### Constraints and Indexes

- Unique candidate identity per run, such as `(run_id, chunk_id)` when `chunk_id` is present.
- Index on `(run_id, status)`.
- Index on `(source_id, status)`.

## BackupArtifact (optional persisted evidence)

Represents a backup produced by the runbook or helper CLI.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key |
| `public_id` | varchar(36) | Stable id |
| `created_at` | timestamptz | Backup timestamp |
| `format` | varchar(32) | e.g. `pg_dump_custom` |
| `destination` | text | Redacted/off-volume destination descriptor |
| `include_embeddings` | boolean | Whether vector data is included |
| `encrypted` | boolean | Whether artifact was encrypted before storage |
| `checksum_sha256` | varchar(64) nullable | Artifact checksum |
| `retention_days` | integer nullable | Retention policy used |
| `status` | varchar(32) | `created`, `validated`, `failed` |
| `error_message` | text nullable | Sanitized error |

## RestoreValidation (optional persisted evidence)

Represents evidence that a backup was restored and validated.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key |
| `backup_artifact_id` | integer FK nullable | Backup artifact when persisted |
| `validated_at` | timestamptz | Validation time |
| `database_label` | varchar(255) | Redacted target database label |
| `source_count` | integer | Restored source count |
| `chunk_count` | integer | Restored chunk count |
| `relation_counts_json` | jsonb | Category/tag/project relation counts |
| `search_checked` | boolean | Whether a sample search was run |
| `status` | varchar(32) | `passed`, `failed` |
| `notes` | text nullable | Sanitized operator notes |

## Existing Entity Dependencies

- `DocumentSource.content_text` is the source of truth for reprocessing.
- `KnowledgeChunk.embedding_*` fields are updated only after a successful compatible embedding is available.
- `EmbeddingBatch` records the target embedding configuration and batch completion state.
- Category, tag and project association tables must survive backup/restore unchanged.

## Migration Notes

- Add reindex tables without changing existing source/chunk semantics.
- Add indexes before large reindex operations.
- If backup evidence tables are deferred, capture restore evidence in `doc/OPERATIONS.md` or a dated operations log instead.
- Do not store secrets, raw connection URLs with passwords or full source text in operational tracking tables.
