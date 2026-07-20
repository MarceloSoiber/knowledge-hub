# Tasks: Projetos

**Input**: Design documents from `/specs/009-projetos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/knowledge-projects.md

**Tests**: Tests are required because this changes persistence, public API/MCP contracts and search filtering.

## Phase 1: Setup and Contract Decisions

**Purpose**: Lock lifecycle and filtering semantics before implementation.

- [x] T001 Confirm project list behavior for archived projects and record final decision in `specs/009-projetos/research.md`.
- [x] T002 Confirm project deletion is out of MVP and archive/reactivate is the lifecycle path in `specs/009-projetos/contracts/knowledge-projects.md`.
- [x] T003 Inspect current category/tag/source/search/MCP tests in `tests/test_knowledge_service.py`, `tests/test_knowledge_api_integration.py` and `tests/test_mcp_knowledge.py`.

---

## Phase 2: Foundational Database and Domain Support

**Purpose**: Add project persistence, lifecycle rules and source serialization before public flows change.

- [x] T004 Add `document_source_projects` and `Project` to `backend/app/db/models.py`.
- [x] T005 Add idempotent schema/index setup for `projects` and `document_source_projects` in `backend/app/db/init.py`.
- [x] T006 [P] Add `backend/app/repositories/projects.py` with get/list/list-by-ids/name/project-sources helpers.
- [x] T007 [P] Add `backend/app/services/projects.py` with normalization, create, update, archive, reactivate and missing/conflict errors.
- [x] T008 Add project relationship loading and serialization to `backend/app/repositories/sources.py`.
- [x] T009 Add project serialization to chunk read mapping in `backend/app/repositories/chunks.py`.

**Checkpoint**: Projects can be persisted, associated and serialized internally.

---

## Phase 3: User Story 1 - Agrupar fontes por contexto de projeto (Priority: P1) MVP

**Goal**: Sources can be associated with zero, one or many projects without duplicating content/chunks.

**Independent Test**: Associate one source with two projects and verify a single source id/chunk set appears in both project source lists.

### Tests for User Story 1

- [x] T010 [P] [US1] Add project normalization and duplicate-name tests in `tests/test_knowledge_service.py`.
- [x] T011 [P] [US1] Add text/upload ingestion tests with `project_ids` in `tests/test_knowledge_api_integration.py`.
- [x] T012 [P] [US1] Add source patch test proving project-only update does not call embeddings in `tests/test_knowledge_service.py`.
- [x] T013 [P] [US1] Add project source listing test proving one source can appear in multiple projects without duplicate source ids in `tests/test_knowledge_service.py`.

### Implementation for User Story 1

- [x] T014 [US1] Add `ProjectRead`, `ProjectWrite`, `ProjectPatch` and project id validators to `backend/app/schemas/knowledge.py`.
- [x] T015 [US1] Add optional project fields to `KnowledgeTextIngestRequest`, `KnowledgeUploadRequest`, `KnowledgeUploadResponse`, `KnowledgeSourceRead` and `KnowledgeSourceDetail` in `backend/app/schemas/knowledge.py`.
- [x] T016 [US1] Update `backend/app/services/ingestion.py` to validate and persist project associations during text/upload ingestion.
- [x] T017 [US1] Update `backend/app/services/sources.py` to patch projects independently from content/chunk regeneration.
- [x] T018 [US1] Add project source listing service/repository path for `GET /projects/{project_id}/sources`.

**Checkpoint**: MVP project grouping works for source classification and metadata-only edits.

---

## Phase 4: User Story 2 - Gerenciar ciclo de vida de projetos (Priority: P2)

**Goal**: Users can create, list, update, archive and reactivate projects without deleting knowledge.

**Independent Test**: Archive a project with sources, then verify sources and chunks still exist and project status is archived.

### Tests for User Story 2

- [x] T019 [P] [US2] Add API integration tests for project CRUD/status-code mapping in `tests/test_knowledge_api_integration.py`.
- [x] T020 [P] [US2] Add archive/reactivate API integration tests in `tests/test_knowledge_api_integration.py`.
- [x] T021 [P] [US2] Add service tests proving archive does not delete source/chunk associations in `tests/test_knowledge_service.py`.

### Implementation for User Story 2

- [x] T022 [US2] Add `/knowledge/projects` list/create/update endpoints to `backend/app/api/routes/knowledge.py`.
- [x] T023 [US2] Add `/knowledge/projects/{project_id}/archive` and `/reactivate` endpoints to `backend/app/api/routes/knowledge.py`.
- [x] T024 [US2] Add `/knowledge/projects/{project_id}/sources` endpoint to `backend/app/api/routes/knowledge.py`.
- [x] T025 [US2] Map project service errors to `404`, `409` and validation responses in `backend/app/api/routes/knowledge.py`.

**Checkpoint**: Project lifecycle is manageable through API.

---

## Phase 5: User Story 3 - Restringir busca e IA ao projeto atual (Priority: P3)

**Goal**: Search and answer can filter by projects together with categories and tags, without duplicate chunks.

**Independent Test**: Search with project filters and project+category/tag filters, confirming strict narrowing and unique chunk ids.

### Tests for User Story 3

- [x] T026 [P] [US3] Add service/repository tests for project ANY filtering and project+category/tag AND combination in `tests/test_knowledge_service.py`.
- [x] T027 [P] [US3] Add API integration tests for search and answer `project_ids` filters in `tests/test_knowledge_api_integration.py`.
- [x] T028 [P] [US3] Add regression test for no duplicate chunk ids when a source matches multiple requested projects in `tests/test_knowledge_service.py`.
- [x] T029 [P] [US3] Add missing project rejection test proving no embedding call happens in `tests/test_knowledge_service.py`.

### Implementation for User Story 3

- [x] T030 [US3] Add optional `project_ids` to `KnowledgeSearchRequest` and `KnowledgeAnswerRequest` in `backend/app/schemas/knowledge.py`.
- [x] T031 [US3] Extend `search_knowledge()` and `answer_knowledge()` in `backend/app/services/search.py` to validate and pass project filters.
- [x] T032 [US3] Extend vector and text search queries in `backend/app/repositories/chunks.py` to apply project filters before candidate limits.
- [x] T033 [US3] Thread `project_ids` through `backend/app/api/routes/knowledge.py` search and answer endpoints.

**Checkpoint**: Project filters restrict retrieval and RAG context.

---

## Phase 6: MCP, Documentation and Verification

**Purpose**: Keep agents and documentation aligned with the new project context.

- [x] T034 [P] Add projects to MCP source/hit/result models and optional `project_ids` search input in `mcp_server/tools/knowledge.py`.
- [x] T035 [P] Add optional `project_ids` to MCP `ingest_text` in `mcp_server/tools/knowledge.py` and `mcp_server/server.py`.
- [x] T036 [P] Register project list/source helper MCP tools in `mcp_server/server.py`.
- [x] T037 [P] Add MCP tests for project fields, filters and project listing in `tests/test_mcp_knowledge.py`.
- [x] T038 [P] Update `doc/API.md` with project endpoints, source/chunk response fields, ingestion fields and search/answer filter semantics.
- [x] T039 [P] Update `specs/009-projetos/contracts/knowledge-projects.md` if implementation chooses different archived-list or clear-project behavior.
- [x] T040 Run `.venv/bin/python -m pytest tests/test_knowledge_service.py tests/test_knowledge_api_integration.py tests/test_mcp_knowledge.py`.
- [ ] T041 Run the quickstart checks from `specs/009-projetos/quickstart.md`.

---

## Dependencies & Execution Order

- **Phase 1**: Starts immediately and resolves lifecycle/listing semantics.
- **Phase 2**: Depends on Phase 1 decisions and blocks every user story.
- **US1 (Phase 3)**: Depends on persistence and delivers MVP project grouping.
- **US2 (Phase 4)**: Depends on service/repository support from Phase 2; can proceed alongside US1 after schema stabilizes.
- **US3 (Phase 5)**: Depends on project serialization and validation; can start after US1 models are stable.
- **Phase 6**: Depends on implemented public behavior.

## Parallel Opportunities

- T006 and T007 can run in parallel after T004/T005 are defined.
- T010, T011, T012 and T013 can be written in parallel.
- T019, T020 and T021 can be written in parallel.
- T026, T027, T028 and T029 can be written in parallel.
- T034, T035, T037 and T038 can run in parallel once final field names settle.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1.
3. Validate one source associated with multiple projects and project-only patch without embeddings.
4. Stop and verify project context is distinct from category/tag classification.

### Incremental Delivery

1. Add tables, normalization and service layer.
2. Add source association and serialization.
3. Add lifecycle and project source list endpoints.
4. Add search/answer filtering.
5. Add MCP and documentation.
6. Run tests and quickstart verification.
