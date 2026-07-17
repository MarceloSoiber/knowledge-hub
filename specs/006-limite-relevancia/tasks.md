# Tasks: Limite Minimo de Relevancia

**Input**: Design documents from `/specs/006-limite-relevancia/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/relevance-threshold.md

**Tests**: Tests are required because the feature changes search safety behavior.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when it touches different files or does not depend on another task.
- **[Story]**: Which user story the task supports.

## Phase 1: Setup

**Purpose**: Confirm baseline and expose configuration.

- [ ] T001 Inspect current search, answer and MCP tests for expected fixtures in `tests/test_knowledge_service.py`, `tests/test_knowledge_api_integration.py` and `tests/test_mcp_knowledge.py`
- [ ] T002 Add `search_min_score` setting with default `0.35` and bounds in `backend/app/core/settings.py`

---

## Phase 2: Foundational

**Purpose**: Shared relevance threshold behavior required by all user stories.

- [ ] T003 [P] Add optional `min_score` validation to `KnowledgeSearchRequest` and `KnowledgeAnswerRequest` in `backend/app/schemas/knowledge.py`
- [ ] T004 Implement threshold resolution and score filtering helpers in `backend/app/services/search.py`
- [ ] T005 Add non-sensitive search filtering logs in `backend/app/services/search.py`
- [ ] T006 Thread `min_score` from `backend/app/api/routes/knowledge.py` into `search_knowledge()` and `answer_knowledge()`
- [ ] T007 Thread `min_score` through `mcp_server/tools/knowledge.py::search_knowledge`

**Checkpoint**: API, answer and MCP call paths can pass or omit an effective threshold.

---

## Phase 3: User Story 1 - Filtrar Resultados Fracos (Priority: P1)

**Goal**: Search returns only chunks whose score reaches the effective threshold.

**Independent Test**: Service-level search with fake chunks above, equal to and below the threshold.

### Tests for User Story 1

- [ ] T008 [P] [US1] Add service test for below-threshold chunks being removed in `tests/test_knowledge_service.py`
- [ ] T009 [P] [US1] Add service test for score equal to threshold being retained in `tests/test_knowledge_service.py`
- [ ] T010 [P] [US1] Add API test that valid `min_score` is forwarded in `tests/test_knowledge_api_integration.py`
- [ ] T011 [P] [US1] Add MCP test that valid `min_score` is forwarded in `tests/test_mcp_knowledge.py`

### Implementation for User Story 1

- [ ] T012 [US1] Apply filtering in `backend/app/services/search.py` after repository results are converted to `KnowledgeChunkRead`
- [ ] T013 [US1] Ensure filtered search still returns the existing `KnowledgeSearchResponse` contract from `backend/app/api/routes/knowledge.py`
- [ ] T014 [US1] Ensure MCP search still returns `KnowledgeHit` items with the existing contract in `mcp_server/tools/knowledge.py`

**Checkpoint**: `/search` and MCP search hide weak chunks without changing response shape.

---

## Phase 4: User Story 2 - Ausencia Explicita de Informacao (Priority: P2)

**Goal**: No result above threshold produces empty source lists and absence-oriented RAG behavior.

**Independent Test**: Answer flow with all candidate scores below threshold.

### Tests for User Story 2

- [ ] T015 [P] [US2] Add service test that `answer_knowledge()` calls the answer client with zero sources when all candidates are filtered in `tests/test_knowledge_service.py`
- [ ] T016 [P] [US2] Add API test for `/knowledge/search` returning `results: []` when backend search returns no approved results in `tests/test_knowledge_api_integration.py`

### Implementation for User Story 2

- [ ] T017 [US2] Pass `min_score` through `answer_knowledge()` in `backend/app/services/search.py`
- [ ] T018 [US2] Confirm `backend/app/services/rag.py` context formatting handles an empty sources list without errors

**Checkpoint**: A question outside the base can produce an empty result set and no weak context.

---

## Phase 5: User Story 3 - Calibracao Controlada (Priority: P3)

**Goal**: Operators can tune the threshold safely through settings or request override.

**Independent Test**: Invalid threshold values are rejected by API/MCP validation.

### Tests for User Story 3

- [ ] T019 [P] [US3] Add schema tests for invalid `min_score` values in `tests/test_knowledge_service.py`
- [ ] T020 [P] [US3] Add API validation test for invalid `min_score` in `tests/test_knowledge_api_integration.py`
- [ ] T021 [P] [US3] Add MCP validation test for invalid `min_score` in `tests/test_mcp_knowledge.py`

### Implementation for User Story 3

- [ ] T022 [US3] Ensure request override takes precedence over `SEARCH_MIN_SCORE` in `backend/app/services/search.py`
- [ ] T023 [US3] Ensure invalid `SEARCH_MIN_SCORE` fails settings validation through `backend/app/core/settings.py`

**Checkpoint**: Calibration is possible without accepting invalid thresholds.

---

## Phase 6: Documentation & Verification

**Purpose**: Document changed behavior and verify the implementation.

- [ ] T024 [P] Update `doc/API.md` with `min_score`, default `SEARCH_MIN_SCORE`, empty-result behavior and calibration notes
- [ ] T025 [P] Update examples in `doc/API.md` for search and answer requests
- [ ] T026 Run `.venv/bin/python -m pytest tests/test_knowledge_service.py tests/test_knowledge_api_integration.py tests/test_mcp_knowledge.py`
- [ ] T027 Review logs to confirm they contain scores/counts but not query text

---

## Dependencies & Execution Order

- Phase 1 must complete before implementation tasks.
- Phase 2 blocks all user stories because API, MCP and answer flows depend on shared threshold resolution.
- US1 is the MVP and should be completed before US2/US3.
- US2 depends on US1 filtering behavior.
- US3 can proceed after Phase 2, but validation tests are clearer after US1 wiring exists.
- Documentation and verification happen after desired stories are implemented.

## Parallel Opportunities

- T003 can run after T002 while T004/T005 are drafted.
- Tests T008-T011 can be written in parallel because they touch separate test concerns.
- Tests T015-T016 can be written in parallel.
- Tests T019-T021 can be written in parallel.
- Documentation tasks T024-T025 can run while final verification is prepared.

## Implementation Strategy

1. Complete settings and schema validation.
2. Implement service-level threshold resolution and filtering.
3. Wire API and MCP parameters.
4. Validate MVP search filtering.
5. Validate empty-source RAG behavior.
6. Document calibration and run targeted tests.
