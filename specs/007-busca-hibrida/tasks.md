# Tasks: Busca Hibrida

**Input**: Design documents from `/specs/007-busca-hibrida/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/hybrid-search.md

**Tests**: Tests are required because this changes core retrieval behavior.

## Phase 1: Setup and Research Gate

**Purpose**: Confirm current contracts and lock the text-search configuration before implementation.

- [x] T001 Inspect current search, answer and MCP fixtures in `tests/test_knowledge_service.py`, `tests/test_knowledge_api_integration.py` and `tests/test_mcp_knowledge.py`.
- [x] T002 Confirm PostgreSQL full-text SQL syntax for the supported database version and record any deviation in `specs/007-busca-hibrida/research.md`.
- [x] T003 Define exact-token and paraphrase fixtures aligned with `plan/12-avaliacao-rag.md`.

---

## Phase 2: Foundational Database Support

**Purpose**: Add text-search persistence and indexing before changing retrieval behavior.

- [x] T004 Add `search_vector` representation for `KnowledgeChunk` in `backend/app/db/models.py`.
- [x] T005 Add idempotent schema/backfill/index setup in `backend/app/db/init.py`.
- [ ] T006 [P] Add repository or integration test coverage proving existing chunks get searchable text vectors.
- [ ] T007 Validate with SQL/EXPLAIN that the GIN index is used for text search and capture the command in `specs/007-busca-hibrida/quickstart.md` if it changes.

**Checkpoint**: Database can serve indexed text candidates without changing public search behavior.

---

## Phase 3: User Story 1 - Recuperar termos exatos e identificadores (Priority: P1) MVP

**Goal**: Exact identifiers, tickers, names, numbers and error messages are retrievable through the text path and fused into final results.

**Independent Test**: Search exact-token fixtures and confirm expected chunks appear in the top 5 with no duplicate ids.

### Tests for User Story 1

- [x] T008 [P] [US1] Add exact identifier search tests in `tests/test_knowledge_service.py`.
- [x] T009 [P] [US1] Add deduplication test for chunks returned by both retrieval paths in `tests/test_knowledge_service.py`.

### Implementation for User Story 1

- [x] T010 [US1] Add text candidate retrieval helper in `backend/app/repositories/chunks.py`.
- [x] T011 [US1] Ensure category filters apply inside both vector and text candidate statements in `backend/app/repositories/chunks.py`.
- [x] T012 [US1] Implement RRF candidate fusion and deterministic tie-breaks in `backend/app/services/search.py`.
- [x] T013 [US1] Update `search_knowledge()` in `backend/app/services/search.py` to retrieve expanded vector/text candidates and return fused final results.
- [x] T014 [US1] Preserve existing citation mapping through `build_chunk_read()` in `backend/app/repositories/chunks.py`.

**Checkpoint**: Hybrid search improves exact-token recall while keeping the existing response shape.

---

## Phase 4: User Story 2 - Preservar recuperacao semantica (Priority: P2)

**Goal**: Semantic paraphrase queries continue to work at least as well as vector-only search.

**Independent Test**: Run paraphrase fixtures and compare hybrid ordering against the vector-only baseline.

### Tests for User Story 2

- [x] T015 [P] [US2] Add paraphrase regression test in `tests/test_knowledge_service.py`.
- [x] T016 [P] [US2] Add min_score interaction tests for vector-backed and text-only candidates in `tests/test_knowledge_service.py`.

### Implementation for User Story 2

- [x] T017 [US2] Keep vector similarity as public `score` when a candidate has a vector match in `backend/app/services/search.py`.
- [x] T018 [US2] Define and implement text-only score behavior without breaking Pydantic schemas in `backend/app/schemas/knowledge.py` and `backend/app/services/search.py`.
- [x] T019 [US2] Add non-sensitive hybrid retrieval logs in `backend/app/services/search.py`.

**Checkpoint**: Semantic behavior is preserved and threshold semantics are documented.

---

## Phase 5: User Story 3 - Diagnosticar por que um resultado apareceu (Priority: P3)

**Goal**: Operators can opt into match reasons for evaluation and calibration.

**Independent Test**: Call search with diagnostics enabled and confirm results identify `vector`, `text` or both.

### Tests for User Story 3

- [x] T020 [P] [US3] Add API integration test for default response compatibility in `tests/test_knowledge_api_integration.py`.
- [x] T021 [P] [US3] Add API integration test for optional `match_reasons` forwarding in `tests/test_knowledge_api_integration.py`.
- [x] T022 [P] [US3] Add MCP test for optional diagnostics if MCP exposes the flag in `tests/test_mcp_knowledge.py`.

### Implementation for User Story 3

- [x] T023 [US3] Add optional diagnostic request fields to `backend/app/schemas/knowledge.py`.
- [x] T024 [US3] Thread diagnostic flags through `backend/app/api/routes/knowledge.py` and `backend/app/services/search.py`.
- [x] T025 [US3] Thread diagnostic flags through `mcp_server/tools/knowledge.py` and `mcp_server/server.py` if exposed to MCP clients.
- [x] T026 [US3] Add `match_reasons` only when requested, preserving default result compatibility.

**Checkpoint**: Diagnostics are available opt-in and absent by default.

---

## Phase 6: Documentation and Verification

**Purpose**: Document contract changes and validate release gates.

- [x] T027 [P] Update `doc/API.md` for hybrid ranking, optional diagnostics and score semantics.
- [x] T028 [P] Update `specs/007-busca-hibrida/contracts/hybrid-search.md` if implementation chooses a different diagnostic field shape.
- [x] T029 Run `.venv/bin/python -m pytest tests/test_knowledge_service.py tests/test_knowledge_api_integration.py tests/test_mcp_knowledge.py`.
- [ ] T030 Run or simulate Plano 12 evaluation comparing vector-only baseline and hybrid candidate.
- [x] T031 Record final configuration choice (`simple` or `portuguese`) and evaluation result in `specs/007-busca-hibrida/research.md`.

---

## Dependencies & Execution Order

- **Phase 1**: Starts immediately.
- **Phase 2**: Depends on Phase 1 configuration decision and blocks hybrid retrieval.
- **US1 (Phase 3)**: Depends on Phase 2 and delivers MVP value.
- **US2 (Phase 4)**: Depends on US1 fusion path.
- **US3 (Phase 5)**: Depends on US1 internal match reason data; can proceed after US1 if API shape is stable.
- **Phase 6**: Depends on selected user stories.

## Parallel Opportunities

- T006 can run after T004/T005 while service-level tests are prepared.
- T008 and T009 can be written in parallel.
- T015 and T016 can be written in parallel.
- T020, T021 and T022 can be written in parallel once diagnostic contract is decided.
- T027 and T028 can run in parallel after implementation details settle.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1.
3. Validate exact-token retrieval and deduplication.
4. Stop and compare response compatibility before adding diagnostics.

### Incremental Delivery

1. Add indexed text candidates.
2. Fuse exact-token and vector candidates.
3. Preserve semantic/paraphrase quality.
4. Add opt-in diagnostics.
5. Validate with tests and Plano 12 evaluation.
