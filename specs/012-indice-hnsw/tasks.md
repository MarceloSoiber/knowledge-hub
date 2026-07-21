# Tasks: Indice Vetorial HNSW

**Input**: Design documents from `/specs/012-indice-hnsw/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/hnsw-operations.md

**Tests**: Required for service decision logic, SQL/query construction, CLI behavior and regression coverage around filters/search.

## Phase 1: Setup

**Purpose**: Establish constants, file structure and CLI entry point.

- [X] T001 Create `backend/app/repositories/vector_index.py` with canonical index/report constants from `specs/012-indice-hnsw/data-model.md`.
- [X] T002 Create `backend/app/services/vector_index.py` with dataclasses/Pydantic-friendly structures for benchmark queries, reports and decisions.
- [X] T003 Create `backend/app/cli/hnsw.py` with argparse subcommands `baseline`, `create`, `validate` and `drop`.
- [X] T004 Add `knowledge-hnsw = "backend.app.cli.hnsw:main"` to `pyproject.toml`.

---

## Phase 2: Foundational

**Purpose**: Implement reusable database helpers that block user-story work.

- [X] T005 [P] Implement pgvector version/capability detection in `backend/app/repositories/vector_index.py`.
- [X] T006 [P] Implement compatible embedded chunk counting using `EmbeddingBatch.config_hash` in `backend/app/repositories/vector_index.py`.
- [X] T007 Implement idempotent non-concurrent HNSW creation helper and explicit concurrent SQL rendering in `backend/app/repositories/vector_index.py`.
- [X] T008 Implement `ANALYZE knowledge_chunks`, index-size lookup and rollback SQL helpers in `backend/app/repositories/vector_index.py`.
- [X] T009 Implement JSON `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` helper for representative vector queries in `backend/app/repositories/vector_index.py`.
- [X] T010 Refactor shared vector-query construction only if needed so `backend/app/repositories/chunks.py` and `vector_index.py` preserve identical compatibility/filter semantics.

**Checkpoint**: HNSW DDL and measurement primitives exist without changing public search behavior.

---

## Phase 3: User Story 1 - Medir busca vetorial atual (Priority: P1)

**Goal**: Produce a reliable baseline before index creation.

**Independent Test**: Run `knowledge-hnsw baseline` against fixtures/mocked repository output and verify a report with latency, plans and exact ids.

### Tests for User Story 1

- [X] T011 [P] [US1] Add unit tests for baseline report assembly in `tests/test_vector_index_operations.py`.
- [X] T012 [P] [US1] Add tests proving baseline honors category/tag/project filters in `tests/test_vector_index_operations.py`.

### Implementation for User Story 1

- [X] T013 [US1] Implement evaluation-query loading and validation in `backend/app/services/vector_index.py`.
- [X] T014 [US1] Implement baseline orchestration with active embedding identity, exact/current ids, latency samples and explain capture in `backend/app/services/vector_index.py`.
- [X] T015 [US1] Wire `knowledge-hnsw baseline` in `backend/app/cli/hnsw.py` with JSON output and sanitized console summary.

**Checkpoint**: Baseline can be generated independently and does not mutate schema.

---

## Phase 4: User Story 2 - Criar e validar indice HNSW (Priority: P2)

**Goal**: Create the HNSW index safely and prove representative queries can use it.

**Independent Test**: Run create/validate helpers against test database or mocked SQL layer and assert idempotent index creation plus plan-index detection.

### Tests for User Story 2

- [X] T016 [P] [US2] Add tests for row-count threshold, force behavior and pgvector unsupported errors in `tests/test_vector_index_operations.py`.
- [X] T017 [P] [US2] Add tests for parsing JSON explain plans and detecting `ix_knowledge_chunks_embedding_hnsw_cosine` in `tests/test_vector_index_operations.py`.

### Implementation for User Story 2

- [X] T018 [US2] Implement `create_hnsw_index` service flow with capability check, threshold check, DDL, `ANALYZE` and index metadata in `backend/app/services/vector_index.py`.
- [X] T019 [US2] Implement `validate_hnsw_index` service flow with explain capture for unfiltered/category/project queries in `backend/app/services/vector_index.py`.
- [X] T020 [US2] Wire `knowledge-hnsw create` and `knowledge-hnsw validate` in `backend/app/cli/hnsw.py`.
- [X] T021 [US2] Keep `backend/app/db/init.py` unchanged: index creation remains explicitly operator-gated.

**Checkpoint**: HNSW can be created and validated without API/MCP contract changes.

---

## Phase 5: User Story 3 - Calibrar recall, parametros e rollback (Priority: P3)

**Goal**: Compare quality/performance and document operational rollback.

**Independent Test**: Feed known exact/HNSW result sets to decision logic and verify accepted/rejected/inconclusive outcomes.

### Tests for User Story 3

- [X] T022 [P] [US3] Add recall@k and latency-decision tests in `tests/test_vector_index_operations.py`.
- [X] T023 [P] [US3] Add CLI dry-run/drop tests for rollback SQL in `tests/test_vector_index_operations.py`.
- [X] T024 [P] [US3] Verify existing regression tests that `search_knowledge()` result shape and filters remain unchanged in `tests/test_knowledge_service.py`.

### Implementation for User Story 3

- [X] T025 [US3] Implement recall@k comparison and aggregate decision logic in `backend/app/services/vector_index.py`.
- [X] T026 [US3] Add optional session-local query parameter handling, such as `--hnsw-ef-search`, in `backend/app/cli/hnsw.py` and repository execution helpers.
- [X] T027 [US3] Implement `knowledge-hnsw drop` dry-run/execute behavior in `backend/app/cli/hnsw.py`.
- [X] T028 [US3] Document reindex impact measurement using the existing reindex CLI in `doc/OPERATIONS.md`.

**Checkpoint**: Feature has a measured accept/reject decision path and rollback.

---

## Phase 6: Documentation & Verification

**Purpose**: Finalize runbooks, docs and test execution.

- [X] T029 [P] Update `doc/OPERATIONS.md` with HNSW preconditions, baseline/create/validate/drop commands, memory/build/write cost notes and rollback.
- [X] T030 [P] Update `doc/API.md` to note the no-contract-change CLI workflow.
- [X] T031 [P] Add evaluation fixture example `evaluation/hnsw-queries.example.json`.
- [X] T032 Run `.venv/bin/python -m pytest tests/test_vector_index_operations.py tests/test_knowledge_service.py tests/test_reindex_operations.py`.
- [X] T033 Record manual validation deferral in `quickstart.md`: local compose has no PostgreSQL service or representative corpus.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; blocks user stories.
- **US1 Baseline (Phase 3)**: depends on Foundational and should be delivered first.
- **US2 Create/Validate (Phase 4)**: depends on US1 because validation needs baseline context.
- **US3 Calibration/Rollback (Phase 5)**: depends on US1 and US2.
- **Documentation & Verification (Phase 6)**: depends on implemented stories.

### Parallel Opportunities

- T005 and T006 can run in parallel.
- T011 and T012 can run in parallel.
- T016 and T017 can run in parallel.
- T022, T023 and T024 can run in parallel.
- T029, T030 and T031 can run in parallel.

## Implementation Strategy

1. Deliver MVP with US1 baseline only, proving measurement works without schema mutation.
2. Add HNSW creation and plan validation.
3. Add recall/parameter/rollback decisions.
4. Update operational docs and run full verification.

## Notes

- Do not tune HNSW parameters by guesswork; report measured defaults first.
- Do not expose mutation endpoints through API/MCP in MVP.
- Prefer production index creation through explicit operator command/runbook because concurrent index creation cannot run inside the existing transactional init flow.
