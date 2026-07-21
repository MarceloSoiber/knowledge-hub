# Contract: Reindexacao e Backup Operations

## CLI: `reindex-embeddings`

### Dry-run

```bash
reindex-embeddings --dry-run --category notes --batch-size 50
```

Expected behavior:

- Creates a `ReindexRun` with `dry_run=true`.
- Lists candidate counts grouped by reason and source.
- Does not modify `knowledge_chunks.embedding`, `embedding_batch_id`, `embedding_status` or `embedding_batches`.
- Prints no full source content and no secrets.

Example output shape:

```text
run_id: 550e8400-e29b-41d4-a716-446655440000
target_config: local/text-embedding-nomic-embed-text-v1.5/768/default
dry_run: true
sources_total: 3
chunks_total: 42
reasons:
  config_changed: 40
  failed: 2
```

### Execution

```bash
reindex-embeddings --source-id SOURCE_PUBLIC_ID --batch-size 25
```

Expected behavior:

- Selects only matching sources/chunks.
- Processes at most `batch-size` chunks in one execution slice unless resume mode explicitly continues.
- Records per-item status.
- Recomputes compatibility before embedding so repeated runs are idempotent.
- Reports sanitized counters.
- Default `--batch-size` is 50 when not supplied.
- Items that fail during provider calls are marked `failed_retryable`.

### Resume

```bash
reindex-embeddings --resume-run-id 550e8400-e29b-41d4-a716-446655440000 --batch-size 25
```

Expected behavior:

- Loads pending/retryable items for the run.
- Skips chunks that are already compatible.
- Does not duplicate chunks.
- Preserves previous failure records and increments attempts for retried items.

### Current reuse behavior

The implementation always rechecks whether a chunk is already compatible before
embedding. Already-compatible chunks are marked `reused` during resume. Cross-run
copying of compatible vectors by content hash is not implemented in this slice.

## CLI: `knowledge-backup`

The MVP may implement this as a helper that prints redacted commands and validates prerequisites instead of executing shell commands itself.

### Backup command shape

```bash
pg_dump --format=custom --no-owner --file "$BACKUP_PATH" "$DATABASE_URL"
```

Requirements:

- Use PostgreSQL-native dump format.
- Store artifact outside the primary database volume.
- Encrypt before off-host transfer when the destination is not already encrypted.
- Record or display checksum instructions.
- Do not print `DATABASE_URL` when it contains credentials.

### Restore command shape

```bash
createdb "$RESTORE_DATABASE"
psql "$RESTORE_DATABASE" -c "CREATE EXTENSION IF NOT EXISTS vector;"
pg_restore --no-owner --dbname "$RESTORE_DATABASE" "$BACKUP_PATH"
```

Validation checklist:

- Source count matches original environment.
- Chunk count matches expected strategy.
- Category/tag/project relation counts match.
- At least one search query returns expected restored content.
- If embeddings were omitted or intentionally invalidated, reindex dry-run reports expected candidates.

## Scheduled Backup Gate

Scheduling is allowed only when restore validation exists. The validation can be:

- a persisted `RestoreValidation` row, or
- a dated operations log entry with backup id/path, target empty database, counts and sample search result.

Without validation, scheduling documentation must say "blocked until restore test passes".

## Error Semantics

- Missing pgvector during restore: fail before reporting restore success.
- Provider failure during reindex: mark affected item/source failed, continue independent items when safe.
- Destination write failure: backup status is failed; do not record success.
- Sensitive values in errors must be redacted before storage/output.
