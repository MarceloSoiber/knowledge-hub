# Tasks: Reindexacao e Backup

**Input**: Design documents from `/specs/011-reindexacao-backup/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/operations.md

**Tests**: Tests are required because this changes operational recovery, persistence safety and backup/restore guarantees.

## Phase 1: Setup and Operational Decisions

**Purpose**: Lock the CLI/runbook surface and storage strategy before implementation.

- [x] T001 Confirm whether `BackupArtifact` and `RestoreValidation` are persisted in v1 or kept as runbook evidence in `specs/011-reindexacao-backup/research.md`.
- [x] T002 Confirm default `--batch-size`, retry policy and whether compatible hash reuse is enabled in `specs/011-reindexacao-backup/contracts/operations.md`.
- [x] T003 Inspect current pending/reindex helpers from `specs/010-versionamento-embeddings/tasks.md` and complete or adapt any prerequisite unfinished tasks.
- [x] T004 Inspect current source/chunk regeneration flow in `backend/app/services/ingestion.py`, `backend/app/services/sources.py` and `backend/app/repositories/chunks.py`.

---

## Phase 2: Foundational Reindex Data Model

**Purpose**: Add persisted progress and resume state.

- [x] T005 Add `ReindexRun` and `ReindexItem` SQLAlchemy models in `backend/app/db/models.py`.
- [x] T006 Add idempotent table/index creation for reindex tracking in `backend/app/db/init.py`.
- [x] T007 [P] Add Pydantic/internal operation schemas in `backend/app/schemas/operations.py`.
- [x] T008 [P] Add `backend/app/repositories/reindex.py` with run create/update, item upsert, pending-item and counter helpers.
- [x] T009 Add tests for model defaults/index-safe init behavior in `tests/test_reindex_operations.py`.

**Checkpoint**: Reindex progress can be persisted, queried and resumed independently of provider calls.

---

## Phase 3: User Story 1 - Reindexar embeddings com seguranca (Priority: P1) MVP

**Goal**: Operator can dry-run and execute bounded reindex from preserved source content.

**Independent Test**: Dry-run selected sources/categories, then execute a small batch and verify only target candidates mutate into compatible embeddings.

### Tests for User Story 1

- [x] T010 [P] [US1] Add dry-run no-mutation test in `tests/test_reindex_operations.py`.
- [ ] T011 [P] [US1] Add source/category filter test in `tests/test_reindex_operations.py`.
- [ ] T012 [P] [US1] Add batch-size limit test in `tests/test_reindex_operations.py`.
- [ ] T013 [P] [US1] Add validation test for counts, dimensions and sample search in `tests/test_reindex_operations.py`.

### Implementation for User Story 1

- [x] T014 [US1] Implement candidate discovery from `DocumentSource.content_text` and chunk compatibility in `backend/app/services/reindex.py`.
- [x] T015 [US1] Implement dry-run run/item creation without chunk or batch mutation in `backend/app/services/reindex.py`.
- [x] T016 [US1] Implement bounded execution that creates compatible embeddings and updates chunk provenance in `backend/app/services/reindex.py`.
- [x] T017 [US1] Add `backend/app/cli/reindex.py` with `--dry-run`, `--source-id`, `--category` and `--batch-size`.
- [x] T018 [US1] Add `reindex-embeddings` console script to `pyproject.toml`.
- [ ] T019 [US1] Add post-run validation helper in `backend/app/services/reindex.py`.

**Checkpoint**: Reindex dry-run and bounded execution are functional and testable from the CLI/service layer.

---

## Phase 4: User Story 2 - Retomar reindexacao interrompida (Priority: P2)

**Goal**: Interrupted or partially failed runs can resume safely and idempotently.

**Independent Test**: Simulate interruption/failure, rerun with `--resume-run-id`, and verify only remaining incompatible chunks are processed.

### Tests for User Story 2

- [ ] T020 [P] [US2] Add interrupted-run resume test in `tests/test_reindex_operations.py`.
- [ ] T021 [P] [US2] Add no-duplicate-chunks regression test in `tests/test_reindex_operations.py`.
- [ ] T022 [P] [US2] Add per-source provider failure isolation test in `tests/test_reindex_operations.py`.
- [ ] T023 [P] [US2] Add compatible-reuse/no-redundant-provider-call test in `tests/test_reindex_operations.py` if reuse is enabled.

### Implementation for User Story 2

- [x] T024 [US2] Implement `--resume-run-id` loading and retryable-item selection in `backend/app/cli/reindex.py` and `backend/app/services/reindex.py`.
- [x] T025 [US2] Recompute compatibility before each provider call and skip/reuse already compatible chunks in `backend/app/services/reindex.py`.
- [ ] T026 [US2] Commit per source or bounded unit and record sanitized item errors in `backend/app/services/reindex.py`.
- [x] T027 [US2] Update run counters/status transitions for partial failure, completed and failed states in `backend/app/repositories/reindex.py`.

**Checkpoint**: Reindex can be paused, resumed and retried without duplicate chunks or cross-source corruption.

---

## Phase 5: User Story 3 - Fazer backup e restaurar a base (Priority: P3)

**Goal**: Operators have documented, validated backup and restore commands for the PostgreSQL/pgvector database.

**Independent Test**: Follow the runbook against an empty database and verify restored counts/relations/search.

### Tests for User Story 3

- [x] T028 [P] [US3] Add tests for redacted backup command rendering in `tests/test_backup_restore_plan.py` if helper CLI is implemented.
- [x] T029 [P] [US3] Add restore checklist validation tests in `tests/test_backup_restore_plan.py`.
- [x] T030 [P] [US3] Add no-secret/no-content output test for backup/reindex helpers in `tests/test_backup_restore_plan.py`.

### Implementation for User Story 3

- [x] T031 [US3] Create `doc/OPERATIONS.md` with backup, restore, pgvector prerequisite and validation checklist.
- [x] T032 [US3] Document include-embeddings vs regenerate-embeddings strategies in `doc/OPERATIONS.md`.
- [x] T033 [US3] Add `backend/app/services/backup.py` helper functions for redaction/checklist/command rendering if selected.
- [x] T034 [US3] Add `backend/app/cli/backup.py` and `knowledge-backup` script if helper CLI is selected.
- [x] T035 [US3] Update `doc/API.md` to reference operational reindex/backup behavior when relevant.

**Checkpoint**: Backup and restore can be executed from documented commands and validated manually or with helper checks.

---

## Phase 6: User Story 4 - Automatizar backup apos prova de restauracao (Priority: P4)

**Goal**: Scheduling is planned and gated by restore evidence, retention, encryption and off-volume destination.

**Independent Test**: Attempt scheduling without restore evidence and confirm documentation/helper blocks it; provide evidence and confirm schedule instructions become allowed.

### Tests for User Story 4

- [x] T036 [P] [US4] Add restore-gate test in `tests/test_backup_restore_plan.py`.
- [x] T037 [P] [US4] Add retention/encryption/off-volume checklist test in `tests/test_backup_restore_plan.py`.

### Implementation for User Story 4

- [x] T038 [US4] Add scheduling gate/checklist to `doc/OPERATIONS.md`.
- [x] T039 [US4] Add optional `BackupArtifact`/`RestoreValidation` models, repository and init support if persisted evidence is selected. Not selected for v1; evidence remains runbook-based.
- [x] T040 [US4] Add systemd timer or cron examples to `doc/OPERATIONS.md` marked blocked until restore evidence exists.

**Checkpoint**: Backup scheduling cannot be treated as enabled until restore validation is recorded.

---

## Phase 7: Verification and Documentation Alignment

**Purpose**: Prove the implementation and docs match the feature.

- [x] T041 [P] Update `specs/011-reindexacao-backup/contracts/operations.md` if final CLI flags or output shape change.
- [ ] T042 [P] Update `specs/011-reindexacao-backup/quickstart.md` with final commands.
- [x] T043 Run `.venv/bin/python -m pytest tests/test_reindex_operations.py tests/test_backup_restore_plan.py tests/test_embedding_versioning.py tests/test_knowledge_service.py`.
- [ ] T044 Execute and document a real restore test result before marking backup automation complete.
- [ ] T045 Review logs/output samples to confirm no tokens or full source content are printed.

---

## Dependencies & Execution Order

- **Phase 1**: Starts immediately and clarifies storage/CLI decisions.
- **Phase 2**: Depends on Phase 1 and blocks resumable reindex.
- **US1 (Phase 3)**: Depends on reindex run/item persistence.
- **US2 (Phase 4)**: Depends on US1 execution path.
- **US3 (Phase 5)**: Can run after Phase 1, but final restore validation benefits from US1/US2 when embeddings are regenerated.
- **US4 (Phase 6)**: Depends on backup runbook and chosen evidence strategy.
- **Phase 7**: Depends on all selected implementation slices.

## Parallel Opportunities

- T007 and T008 can run in parallel after T005/T006 decisions.
- T010, T011, T012 and T013 can be written in parallel.
- T020, T021, T022 and T023 can be written in parallel.
- T028, T029 and T030 can be written in parallel.
- T036 and T037 can be written in parallel.

## Implementation Strategy

### MVP First

1. Complete setup decisions and reindex tracking tables.
2. Implement dry-run and bounded execution for source/category filters.
3. Add resume/idempotency and failure isolation.
4. Add backup/restore runbook with manual restore validation.
5. Gate scheduling until restore evidence exists.

### Incremental Delivery

1. Persist progress without changing embeddings.
2. Execute bounded reindex safely.
3. Resume interrupted runs.
4. Document and validate backup/restore.
5. Add scheduling examples only after restore validation.
