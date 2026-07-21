# Tasks: Versionamento de Embeddings

**Input**: Design documents from `/specs/010-versionamento-embeddings/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/embedding-versioning.md

**Tests**: Tests are required because this changes persistence, ingestion, search correctness and startup safety.

## Phase 1: Setup and Contract Decisions

**Purpose**: Lock compatibility and legacy-data semantics before implementation.

- [x] T001 Confirm `EMBEDDING_VERSION` default and document the final identity fields in `specs/010-versionamento-embeddings/research.md`.
- [x] T002 Confirm whether REST operational endpoints are in MVP and update `specs/010-versionamento-embeddings/contracts/embedding-versioning.md`.
- [x] T003 Inspect current ingestion/search/source-update tests in `tests/test_knowledge_service.py`, `tests/test_knowledge_api_integration.py` and `tests/test_mcp_knowledge.py`.
- [x] T004 Inspect current `backend/app/db/init.py` dimension mutation and decide exact startup error type/message.

---

## Phase 2: Foundational Data Model and Configuration

**Purpose**: Add persisted provenance and active compatibility identity.

- [x] T005 Add `embedding_version` setting to `backend/app/core/settings.py`.
- [x] T006 [P] Add `EmbeddingConfigIdentity`, config hash helpers and compatibility checks in `backend/app/services/embedding_versions.py`.
- [x] T007 Add `EmbeddingBatch` and chunk provenance fields to `backend/app/db/models.py`.
- [x] T008 Add idempotent schema/index creation for `embedding_batches` and chunk provenance columns in `backend/app/db/init.py`.
- [x] T009 Replace automatic vector dimension ALTER block in `backend/app/db/init.py` with configured-vs-database dimension validation.
- [x] T010 [P] Add `backend/app/repositories/embeddings.py` with batch create/complete/fail lookup and compatible-batch helpers.

**Checkpoint**: The app can represent active embedding configuration and persist/query batch metadata.

---

## Phase 3: User Story 1 - Rastrear origem de cada embedding (Priority: P1) MVP

**Goal**: Every newly embedded chunk is attributable to a provider/model/dimension/version batch.

**Independent Test**: Ingest one text source and verify chunks point to a completed batch with active config and chunk content hashes.

### Tests for User Story 1

- [x] T011 [P] [US1] Add config identity/hash tests in `tests/test_embedding_versioning.py`.
- [x] T012 [P] [US1] Add ingestion provenance test in `tests/test_knowledge_service.py`.
- [x] T013 [P] [US1] Add legacy chunk classification test for unversioned rows in `tests/test_embedding_versioning.py`.
- [x] T014 [P] [US1] Add provider failure test proving no completed batch is committed in `tests/test_knowledge_service.py`.

### Implementation for User Story 1

- [x] T015 [US1] Update `backend/app/services/ingestion.py` to start/complete/fail embedding batches around provider calls.
- [x] T016 [US1] Update `backend/app/repositories/chunks.py:add_source_chunks` to accept batch id, embedded timestamp, status and content hashes.
- [x] T017 [US1] Add optional embedding status/config serialization to `backend/app/schemas/knowledge.py` and chunk read builders if public exposure is chosen.
- [x] T018 [US1] Ensure `backend/app/services/sources.py` content regeneration writes new batch metadata for replacement chunks.

**Checkpoint**: New ingestion and content updates produce attributable embeddings.

---

## Phase 4: User Story 2 - Evitar mistura em busca e resposta (Priority: P2)

**Goal**: Vector search only considers chunks embedded with the active compatible configuration.

**Independent Test**: Create compatible, incompatible and unversioned chunks; vector search returns only compatible chunks while text search remains explicitly text-only.

### Tests for User Story 2

- [x] T019 [P] [US2] Add repository test proving `search_similar_chunks()` excludes incompatible batches in `tests/test_knowledge_service.py`.
- [ ] T020 [P] [US2] Add search service test proving unversioned chunks do not reach vector candidates in `tests/test_embedding_versioning.py`.
- [ ] T021 [P] [US2] Add hybrid search test proving text-only incompatible results do not include `vector` in `match_reasons`.
- [ ] T022 [P] [US2] Add answer test proving RAG context follows the same compatible vector semantics in `tests/test_knowledge_service.py`.

### Implementation for User Story 2

- [x] T023 [US2] Extend `backend/app/repositories/chunks.py:search_similar_chunks` with compatible batch/status filters.
- [x] T024 [US2] Thread active embedding identity through `backend/app/services/search.py`.
- [x] T025 [US2] Preserve category/tag/project filters together with compatibility filters in chunk queries.
- [x] T026 [US2] Update hybrid result building so text-only incompatible results remain distinguishable.

**Checkpoint**: Search and answer no longer mix incompatible embedding spaces.

---

## Phase 5: User Story 3 - Identificar pendencias de reindexacao (Priority: P3)

**Goal**: Operators can list and reindex chunks that are unversioned, failed or incompatible with active config.

**Independent Test**: Change active embedding model and verify existing chunks are pending; run bounded reindex and verify they become compatible.

### Tests for User Story 3

- [ ] T027 [P] [US3] Add pending detection tests for missing batch, config changed and failed chunks in `tests/test_embedding_versioning.py`.
- [ ] T028 [P] [US3] Add reindex dry-run and bounded execution tests in `tests/test_embedding_versioning.py`.
- [ ] T029 [P] [US3] Add idempotent hash reuse test proving duplicate provider calls are avoided when compatible embedding already exists.
- [x] T030 [P] [US3] Add metadata-only source patch test proving embeddings are not marked pending in `tests/test_knowledge_service.py`.

### Implementation for User Story 3

- [x] T031 [US3] Add pending candidate queries to `backend/app/repositories/embeddings.py`.
- [ ] T032 [US3] Add pending detection and bounded reindex orchestration to `backend/app/services/embedding_versions.py`.
- [x] T033 [US3] Update `backend/app/services/sources.py` so metadata-only changes do not alter embedding status.
- [ ] T034 [US3] Implement compatible hash reuse if selected for MVP.

**Checkpoint**: Configuration changes produce actionable reindex work and reindex is idempotent.

---

## Phase 6: User Story 4 - Bloquear dimensao divergente no startup (Priority: P4)

**Goal**: A mismatched `VECTOR_DIM` fails before serving traffic.

**Independent Test**: Simulate database column `vector(768)` with `VECTOR_DIM=1024` and assert startup/init raises an actionable error.

### Tests for User Story 4

- [x] T035 [P] [US4] Add dimension introspection tests for matching and mismatching typmod in `tests/test_embedding_versioning.py`.
- [x] T036 [P] [US4] Add regression test proving `init_db()` no longer emits automatic `ALTER COLUMN embedding TYPE vector(768)`.

### Implementation for User Story 4

- [x] T037 [US4] Add pgvector dimension introspection helper in `backend/app/services/embedding_versions.py` or `backend/app/db/init.py`.
- [x] T038 [US4] Wire dimension guard into `backend/app/db/init.py` before API/MCP startup completes.
- [x] T039 [US4] Update error messages to mention explicit migration/reindex requirement.

**Checkpoint**: Dimension drift is blocked early and explicitly.

---

## Phase 7: API, MCP, Documentation and Verification

**Purpose**: Align public contracts, operational docs and agent behavior.

- [ ] T040 [P] Add REST schemas/endpoints for active config, pending list and reindex in `backend/app/schemas/knowledge.py` and `backend/app/api/routes/knowledge.py` if included in MVP.
- [ ] T041 [P] Add API integration tests for config/pending/reindex endpoints in `tests/test_knowledge_api_integration.py` if included.
- [ ] T042 [P] Update MCP response models/tests in `mcp_server/tools/knowledge.py`, `mcp_server/server.py` and `tests/test_mcp_knowledge.py` if embedding state becomes public there.
- [x] T043 [P] Update `doc/API.md` with embedding compatibility, dimension migration and reindex behavior.
- [ ] T044 [P] Update `specs/010-versionamento-embeddings/contracts/embedding-versioning.md` if implementation changes public endpoint shape.
- [x] T045 Run `.venv/bin/python -m pytest tests/test_embedding_versioning.py tests/test_knowledge_service.py tests/test_knowledge_api_integration.py tests/test_mcp_knowledge.py`.
- [ ] T046 Run quickstart checks from `specs/010-versionamento-embeddings/quickstart.md`.

---

## Dependencies & Execution Order

- **Phase 1**: Starts immediately; locks MVP scope and exact public surface.
- **Phase 2**: Depends on Phase 1 decisions and blocks all stories.
- **US1 (Phase 3)**: Depends on data model/config foundation; delivers provenance MVP.
- **US2 (Phase 4)**: Depends on batch metadata and active identity; protects search/answer.
- **US3 (Phase 5)**: Depends on compatibility checks; adds operational recovery.
- **US4 (Phase 6)**: Can run after identity/dimension helper exists; should land before deployment.
- **Phase 7**: Depends on final implementation decisions.

## Parallel Opportunities

- T006 and T010 can run in parallel after T005 is defined.
- T011, T012, T013 and T014 can be written in parallel.
- T019, T020, T021 and T022 can be written in parallel.
- T027, T028, T029 and T030 can be written in parallel.
- T040, T041, T042 and T043 can run in parallel after endpoint/public surface is final.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 to make new embeddings attributable.
3. Complete US2 to stop vector mixing.
4. Complete US4 before deployment to avoid dimension drift.
5. Validate ingestion and search independently.

### Incremental Delivery

1. Add configuration identity and persistence.
2. Attach new chunks to embedding batches.
3. Filter vector search by active compatible batch.
4. Add pending/reindex visibility.
5. Add optional operational endpoints/MCP exposure.
6. Update docs and run tests.
