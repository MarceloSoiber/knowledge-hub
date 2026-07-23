# Tasks: Tags

**Input**: Design documents from `/specs/008-tags/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/knowledge-tags.md

**Tests**: Tests are required because this changes persistence, public API/MCP contracts and search filtering.

## Phase 1: Setup and Decision Gate

**Purpose**: Confirm that tags are needed beyond multi-category classification and lock the v1 API shape.

- [x] T001 Confirm at least one real classification case where categories are too broad and record it in `specs/008-tags/research.md`.
- [x] T002 Decide whether v1 ingestion accepts only `tag_ids` or also `tag_names`, then update `specs/008-tags/contracts/knowledge-tags.md` if needed.
- [x] T003 Inspect current category, source patch, search and MCP tests in `tests/test_knowledge_service.py`, `tests/test_knowledge_api_integration.py` and `tests/test_mcp_knowledge.py`.

---

## Phase 2: Foundational Database and Domain Support

**Purpose**: Add tag persistence, normalization and validation before changing public flows.

- [x] T004 Add `document_source_tags` and `Tag` to `backend/app/db/models.py`.
- [x] T005 Add idempotent schema/index setup for `tags` and `document_source_tags` in `backend/app/db/init.py`.
- [x] T006 [P] Add `backend/app/repositories/tags.py` with get/list/list-by-ids/name/autocomplete helpers.
- [x] T007 [P] Add `backend/app/services/tags.py` with normalization, create, update, delete, in-use and missing-id errors.
- [x] T008 Add tag relationship loading and serialization to `backend/app/repositories/sources.py`.
- [x] T009 Add tag serialization to chunk read mapping in `backend/app/repositories/chunks.py`.

**Checkpoint**: Tags can be persisted, normalized, looked up and serialized internally.

---

## Phase 3: User Story 1 - Classificar documentos com tags livres (Priority: P1) MVP

**Goal**: Sources can be associated with reusable tags during ingest and patch, and tag-only changes do not regenerate embeddings.

**Independent Test**: Create tags, ingest a source with tag ids, patch only tags and verify chunks/embedding calls are unchanged.

### Tests for User Story 1

- [x] T010 [P] [US1] Add tag normalization and duplicate-equivalence tests in `tests/test_knowledge_service.py`.
- [x] T011 [P] [US1] Add text/upload ingestion tests with tag associations in `tests/test_knowledge_api_integration.py`.
- [x] T012 [P] [US1] Add source patch test proving tag-only update does not call embeddings in `tests/test_knowledge_service.py`.

### Implementation for User Story 1

- [x] T013 [US1] Add `TagRead`, `TagWrite` and tag id validators to `backend/app/schemas/knowledge.py`.
- [x] T014 [US1] Add optional tag fields to `KnowledgeTextIngestRequest`, `KnowledgeUploadRequest`, `KnowledgeUploadResponse`, `KnowledgeSourceRead` and `KnowledgeSourceDetail` in `backend/app/schemas/knowledge.py`.
- [x] T015 [US1] Update `backend/app/services/ingestion.py` to validate and persist tag associations during text/upload ingestion.
- [x] T016 [US1] Update `backend/app/services/sources.py` to patch tags independently from content/chunk regeneration.
- [x] T017 [US1] Ensure duplicate tag ids in requests fail validation and duplicate-equivalent tag names reuse/conflict per contract.

**Checkpoint**: MVP tagging works for source classification and metadata-only edits.

---

## Phase 4: User Story 2 - Encontrar e gerenciar tags existentes (Priority: P2)

**Goal**: Users can manage and discover reusable tags.

**Independent Test**: Create, list, autocomplete, rename and delete tags while validating duplicate and in-use behavior.

### Tests for User Story 2

- [x] T018 [P] [US2] Add API integration tests for tag CRUD status codes in `tests/test_knowledge_api_integration.py`.
- [x] T019 [P] [US2] Add autocomplete tests for normalized prefix matching and result limits in `tests/test_knowledge_api_integration.py`.
- [x] T020 [P] [US2] Add service tests for deleting tags in use and renaming to duplicate-normalized names in `tests/test_knowledge_service.py`.

### Implementation for User Story 2

- [x] T021 [US2] Add `/knowledge/tags` list/create/update/delete endpoints to `backend/app/api/routes/knowledge.py`.
- [x] T022 [US2] Add `/knowledge/tags/autocomplete` endpoint to `backend/app/api/routes/knowledge.py`.
- [x] T023 [US2] Map tag service errors to `404`, `409` and validation responses in `backend/app/api/routes/knowledge.py`.
- [x] T024 [US2] Ensure autocomplete queries use normalized matching and deterministic ordering in `backend/app/repositories/tags.py`.

**Checkpoint**: Tags are manageable and discoverable through API.

---

## Phase 5: User Story 3 - Filtrar busca por tags combinadas com categorias (Priority: P3)

**Goal**: Search and answer can filter by tags together with categories, with ANY semantics and no duplicate chunks.

**Independent Test**: Search with tag filters and category+tag filters, confirming correct narrowing and unique chunk ids.

### Tests for User Story 3

- [x] T025 [P] [US3] Add service tests for tag ANY filtering and category+tag AND combination in `tests/test_knowledge_service.py`.
- [x] T026 [P] [US3] Add API integration tests for search and answer `tag_ids` filters in `tests/test_knowledge_api_integration.py`.
- [x] T027 [P] [US3] Add regression test for no duplicate chunk ids when a source matches multiple requested tags in `tests/test_knowledge_service.py`.

### Implementation for User Story 3

- [x] T028 [US3] Add optional `tag_ids` to `KnowledgeSearchRequest` and `KnowledgeAnswerRequest` in `backend/app/schemas/knowledge.py`.
- [x] T029 [US3] Extend `search_knowledge()` and `answer_knowledge()` in `backend/app/services/search.py` to validate and pass tag filters.
- [x] T030 [US3] Extend vector and text search queries in `backend/app/repositories/chunks.py` to apply tag filters before candidate limits.
- [x] T031 [US3] Thread `tag_ids` through `backend/app/api/routes/knowledge.py` search and answer endpoints.

**Checkpoint**: Tags participate in retrieval without breaking category behavior.

---

## Phase 6: MCP, Documentation and Verification

**Purpose**: Keep non-REST clients and documentation aligned with the new contract.

- [x] T032 [P] Add tags to MCP source/hit/result models and optional `tag_ids` search input in `mcp_server/tools/knowledge.py`.
- [x] T033 [P] Register or expose tag list/autocomplete MCP helpers in `mcp_server/server.py` if useful for clients.
- [x] T034 [P] Add MCP tests for tag fields and filters in `tests/test_mcp_knowledge.py`.
- [x] T035 [P] Update `doc/API.md` with tag endpoints, source/chunk response fields, ingestion fields and search/answer filter semantics.
- [x] T036 [P] Update `specs/008-tags/contracts/knowledge-tags.md` if implementation chooses a different clear-tags or name-upsert behavior.
- [x] T037 Run `.venv/bin/python -m pytest tests/test_knowledge_service.py tests/test_knowledge_api_integration.py tests/test_mcp_knowledge.py`.
- [ ] T038 Run the quickstart checks from `specs/008-tags/quickstart.md`.

---

## Dependencies & Execution Order

- **Phase 1**: Starts immediately and must resolve v1 contract ambiguity.
- **Phase 2**: Depends on Phase 1 decisions and blocks every user story.
- **US1 (Phase 3)**: Depends on persistence and delivers MVP tagging.
- **US2 (Phase 4)**: Depends on service/repository support from Phase 2; can proceed alongside US1 after schema stabilizes.
- **US3 (Phase 5)**: Depends on tag serialization and validation; can start after US1 models are stable.
- **Phase 6**: Depends on the implemented public behavior.

## Parallel Opportunities

- T006 and T007 can run in parallel after T004/T005 are defined.
- T010, T011 and T012 can be written in parallel.
- T018, T019 and T020 can be written in parallel.
- T025, T026 and T027 can be written in parallel.
- T032, T034 and T035 can run in parallel once final API field names settle.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1.
3. Validate tag creation, reuse, source association and metadata-only patch.
4. Stop and confirm the feature has real value over categories before broadening filters and MCP.

### Incremental Delivery

1. Add tables, normalization and service layer.
2. Add source association and serialization.
3. Add management/autocomplete endpoints.
4. Add search/answer filtering.
5. Add MCP and documentation.
6. Run tests and quickstart verification.
