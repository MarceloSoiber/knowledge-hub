# Implementation Plan: Reindexacao e Backup

**Branch**: `011-reindexacao-backup` | **Date**: 2026-07-21 | **Spec**: `specs/011-reindexacao-backup/spec.md`

**Input**: Feature specification from `/specs/011-reindexacao-backup/spec.md`

## Summary

Add operational recovery around embedding changes and database durability. Implement a resumable reindex service plus CLI that can dry-run, filter by source/category and process bounded batches using preserved `DocumentSource.content_text`. Add persisted run/item progress so interruptions and per-source failures are recoverable. Provide backup/restore runbooks and optional CLI helpers around `pg_dump`/restore, with restore validation required before scheduled automation.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, SQLAlchemy async, Pydantic v2, PostgreSQL + pgvector, argparse-based project scripts

**Storage**: PostgreSQL with pgvector; add operational tables for reindex runs/items and optional backup artifact/restore validation records.

**Testing**: `.venv/bin/python -m pytest`

**Target Platform**: Linux backend service and local/operator CLI.

**Project Type**: Backend API/services plus console scripts; no frontend required for MVP.

**Performance Goals**: Reindex must process bounded batches without loading the full corpus into memory; normal vector search must remain under the existing 500ms target after reindex metadata is added.

**Constraints**: Keep routes thin; business logic in `backend/app/services`; query/data helpers in `backend/app/repositories`; never log tokens or full source content; scheduled backups are not enabled before documented restore validation.

**Scale/Scope**: Existing document sources/chunks, categories/tags/projects, embedding batches, ingestion/search/RAG paths, CLI entry points, `doc/API.md` and operational docs.

## Constitution Check

- Code Quality: Pass. Reindex orchestration belongs in services and repositories, with CLI and optional routes as thin entry points.
- Testing Standards: Pass. Reindex resumability, backup restore validation and no-duplicate behavior are critical paths and require pytest coverage.
- Performance: Pass with gate. Reindex must use explicit `batch_size` and candidate queries with filters/indexes; no full-table in-memory loop.
- Documentation: Pass. Backup/restore behavior must be documented because correctness depends on operator runbook steps.
- Security/Sensitivity: Pass with gate. Logs must use ids/counts/status only and avoid auth tokens or full source content.

## Project Structure

### Documentation (this feature)

```text
specs/011-reindexacao-backup/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- operations.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/app/
|-- cli/
|   |-- config.py
|   |-- reindex.py
|   `-- backup.py
|-- db/
|   |-- init.py
|   `-- models.py
|-- repositories/
|   |-- embeddings.py
|   |-- reindex.py
|   `-- backups.py
|-- schemas/
|   `-- operations.py
`-- services/
    |-- embedding_versions.py
    |-- reindex.py
    |-- backup.py
    `-- search.py

tests/
|-- test_reindex_operations.py
|-- test_backup_restore_plan.py
|-- test_embedding_versioning.py
`-- test_knowledge_service.py

doc/
|-- API.md
`-- OPERATIONS.md

pyproject.toml
```

**Structure Decision**: Add dedicated `services/reindex.py` and `repositories/reindex.py` for job orchestration/progress. Keep backup helpers in `services/backup.py` and `cli/backup.py`, with actual database dump/restore documented as operator commands rather than hidden behind API routes. Add scripts in `pyproject.toml` for `reindex-embeddings` and `knowledge-backup`.

## Implementation Details

### Reindex CLI

- Add `backend/app/cli/reindex.py` with argparse options:
  - `--dry-run`
  - `--source-id` repeatable public ids
  - `--category` repeatable category names
  - `--batch-size` positive integer defaulting to a conservative value such as 50
  - `--resume-run-id` for explicit resume when needed
  - `--reuse-compatible/--no-reuse-compatible` if reuse is configurable
- Command output must print counts, source public ids, statuses and sanitized errors only.
- Add `reindex-embeddings = "backend.app.cli.reindex:reindex_main"` to `pyproject.toml`.

### Reindex Service

- Build candidates from `DocumentSource.content_text` and current chunk state.
- Reuse pending detection and `EmbeddingConfigIdentity` from `services/embedding_versions.py`.
- Persist a `ReindexRun` before execution, including filters, target config hash, dry-run flag and status.
- Persist `ReindexItem` records per selected chunk/source with reason and status.
- For dry-run, collect candidates and mark the run as `dry_run_completed` without mutating chunk embeddings.
- For execution, process items in deterministic order up to `batch_size`, create new embedding batch records, compute vectors, update chunk embedding fields and mark each item.
- Commit per source or small bounded unit so one source failure does not corrupt other sources.
- Resume by querying items whose status is `pending` or `failed_retryable` and recomputing compatibility before provider calls.
- Validate completion with:
  - candidates remaining for target filters/config;
  - chunk status counts;
  - vector dimension equality;
  - small sample search using active config.

### Data Model and Init

- Add `ReindexRun` with target provider/model/dimension/version/config_hash, filters JSON, dry-run flag, status, counters, started/completed timestamps and sanitized error.
- Add `ReindexItem` with run id, source id, chunk id, reason, status, attempts, timestamps and sanitized error.
- Optional: Add `BackupArtifact` and `RestoreValidation` tables if the team wants persisted evidence of restore tests. Otherwise keep restore evidence as markdown/runbook initially.
- Add idempotent schema creation/indexes in `backend/app/db/init.py`.

### Backup and Restore

- Add `doc/OPERATIONS.md` with:
  - `pg_dump` custom-format command;
  - restore into empty database;
  - pgvector prerequisite;
  - include-embeddings vs regenerate-embeddings decision;
  - validation checklist;
  - retention/encryption/off-volume destination requirements;
  - log sensitivity rules.
- Add optional `backend/app/cli/backup.py` for rendering commands/checklists and recording restore validation metadata; avoid shelling out with secrets in process args unless intentionally documented.
- Scheduled automation remains a documented later step until a restore validation record/evidence exists.

### API/MCP

- No public API or MCP tool is required for MVP.
- If operational endpoints are later added, keep routes thin and mirror CLI service functions:
  - `GET /knowledge/embeddings/reindex/runs/{run_id}`
  - `POST /knowledge/embeddings/reindex`
  - backup status endpoints only if persisted evidence is needed.
- MCP search inherits compatible vector semantics from feature 010 and should not change for backup.

### Documentation

- Update `doc/API.md` only for public endpoint changes or to reference operational docs for reindex/search behavior.
- Add `doc/OPERATIONS.md` as the canonical runbook for reindex, backup, restore and scheduling prerequisites.
- Keep `specs/011-reindexacao-backup/quickstart.md` executable enough for a human operator to validate in a local/dev database.

## Data Model / API Implications

- Database gains operational reindex tracking tables.
- Backup evidence tables are optional; if added, they should not store secrets or raw source text.
- CLI becomes the primary public surface for reindex and backup operations.
- Existing search/answer APIs should continue using compatibility filtering from `010-versionamento-embeddings`.

## Test Strategy

- Unit tests for CLI argument validation and sanitized output formatting.
- Service tests for dry-run no mutation, batch-size limit, source/category filtering and resume behavior.
- Service tests for provider failure isolation and no duplicate chunks.
- Tests proving full source content and auth tokens are not included in log/output helpers.
- Backup runbook tests can validate generated commands/checklists and restore-gate behavior.
- Integration/manual quickstart must include a real restore into an empty database before scheduled backup is considered enabled.

## Risk Notes

- True "create new vectors before removing old ones" is limited by the current model having one embedding column per chunk. Full blue/green vector swaps may require an additional vector table if strict old/new coexistence is required.
- `pg_dump` can include sensitive source content by design; encryption and destination controls are operational requirements, not optional polish.
- Running dump commands through CLI can expose secrets via environment/process args if implemented carelessly; prefer documented commands with `.pgpass`/service files and redacted output.
- Reindexing large corpora synchronously may be slow; batch limits and resumability mitigate this without adding a worker in MVP.
- Restore validation may require local database lifecycle tooling outside pytest; document the manual acceptance step if CI cannot run it.

## Complexity Tracking

No constitution violations identified. The only notable complexity is resumable operational state, justified by the explicit acceptance criterion that interrupted reindexation must resume safely.
