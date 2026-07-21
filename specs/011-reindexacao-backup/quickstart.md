# Quickstart: Reindexacao e Backup

## 1. Prepare

1. Ensure feature `010-versionamento-embeddings` migrations/init have run.
2. Confirm the active embedding config:

```bash
python - <<'PY'
from backend.app.services.embedding_versions import active_embedding_identity
print(active_embedding_identity())
PY
```

3. Ensure the database has pgvector enabled.

## 2. Reindex Dry-run

```bash
reindex-embeddings --dry-run --batch-size 25
```

Expected:

- Candidate counts are printed.
- No chunks or embedding batches are mutated.
- Output contains ids/counts/status only.

## 3. Bounded Reindex

```bash
reindex-embeddings --batch-size 25
```

Expected:

- At most 25 chunks are processed.
- A run id is printed.
- Failed items are recorded without stopping unrelated sources when safe.

Resume with:

```bash
reindex-embeddings --resume-run-id "$RUN_ID" --batch-size 25
```

## 4. Validate Reindex

Run tests:

```bash
.venv/bin/python -m pytest tests/test_reindex_operations.py tests/test_embedding_versioning.py tests/test_knowledge_service.py
```

Manual checks:

- Pending count for the target filters reaches zero or expected blocked count.
- Vector dimensions match `VECTOR_DIM`.
- A sample search returns expected content through compatible vectors.
- Logs do not contain auth tokens or full source text.

## 5. Backup

Use PostgreSQL custom format:

```bash
pg_dump --format=custom --no-owner --file "$BACKUP_PATH" "$DATABASE_URL"
sha256sum "$BACKUP_PATH" > "$BACKUP_PATH.sha256"
```

Encrypt before external transfer when required by the destination:

```bash
gpg --symmetric --cipher-algo AES256 "$BACKUP_PATH"
```

Store the backup outside the primary database volume.

## 6. Restore Test

Restore into an empty database:

```bash
createdb "$RESTORE_DATABASE"
psql "$RESTORE_DATABASE" -c "CREATE EXTENSION IF NOT EXISTS vector;"
pg_restore --no-owner --dbname "$RESTORE_DATABASE" "$BACKUP_PATH"
```

Validate:

- Source count.
- Chunk count.
- Category/tag/project relation counts.
- One sample search.
- If embeddings were excluded or invalidated, run reindex dry-run and confirm expected candidates.

## 7. Scheduling Gate

Do not enable scheduled backup until the restore test above is documented with date, backup id/path, target database label, counts and sample search result.
