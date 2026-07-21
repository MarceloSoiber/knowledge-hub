# Tasks: Avaliacao do RAG

**Input**: Design documents from `/specs/013-avaliacao-rag/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/rag-evaluation.md

**Tests**: Required for metric calculations, dataset validation, decision logic, runner orchestration and CLI behavior.

## Phase 1: Setup

**Purpose**: Establish file structure, models and operator entry point.

- [X] T001 Create `backend/app/schemas/evaluation.py` with Pydantic models from `specs/013-avaliacao-rag/data-model.md`.
- [X] T002 Create `backend/app/services/evaluation.py` with initial dataclasses/functions for dataset loading, metric output and report serialization.
- [X] T003 Create `backend/app/cli/evaluate_rag.py` with argparse subcommands `baseline`, `candidate`, `compare` and `summarize`.
- [X] T004 Add `rag-eval = "backend.app.cli.evaluate_rag:main"` to `pyproject.toml`.
- [X] T005 [P] Create `evaluation/rag-dataset.example.json` and `evaluation/thresholds.example.json` with non-sensitive sample cases.

---

## Phase 2: Foundational

**Purpose**: Implement validation and pure metric logic that block all user-story work.

- [X] T006 [P] Implement dataset file loading, dataset hash calculation and duplicate-case validation in `backend/app/services/evaluation.py`.
- [X] T007 [P] Implement schema validation rules for known-answer, semantic, exact-term and unanswered cases in `backend/app/schemas/evaluation.py`.
- [X] T008 [P] Implement Recall@K and MRR calculations in `backend/app/services/evaluation.py`.
- [X] T009 [P] Implement deterministic answer essential-point matching and refusal-pattern checks in `backend/app/services/evaluation.py`.
- [X] T010 [P] Implement citation/chunk-reference matching by source public id, chunk index, page, section and optional hash/snippet in `backend/app/services/evaluation.py`.
- [X] T011 Implement aggregate metric and latency p95 calculation in `backend/app/services/evaluation.py`.

**Checkpoint**: Dataset validation and all metrics can be tested without database, embeddings or LLM.

---

## Phase 3: User Story 1 - Executar baseline reproduzivel (Priority: P1)

**Goal**: Produce a reproducible baseline report for the current RAG implementation.

**Independent Test**: Run `rag-eval baseline` with mocked search/answer dependencies and verify report metadata, per-case results, metrics and decision.

### Tests for User Story 1

- [X] T012 [P] [US1] Add dataset validation and metric unit tests in `tests/test_rag_evaluation_metrics.py`.
- [X] T013 [P] [US1] Add baseline runner tests with mocked search/answer outputs in `tests/test_rag_evaluation_runner.py`.

### Implementation for User Story 1

- [X] T014 [US1] Implement evaluation run configuration capture in `backend/app/services/evaluation.py`, including dataset version/hash, git revision when available and active embedding/LLM settings.
- [X] T015 [US1] Implement baseline orchestration using existing `search_knowledge()` and `answer_knowledge()` paths in `backend/app/services/evaluation.py`.
- [X] T016 [US1] Record per-case embedding/search/answer/total latency in `backend/app/services/evaluation.py`.
- [X] T017 [US1] Wire `rag-eval baseline` and `rag-eval summarize` in `backend/app/cli/evaluate_rag.py`.

**Checkpoint**: Baseline report can be generated independently and public API/MCP behavior remains unchanged.

---

## Phase 4: User Story 2 - Comparar candidato contra baseline (Priority: P2)

**Goal**: Compare a candidate run with a baseline and fail when critical thresholds regress.

**Independent Test**: Feed saved baseline/candidate fixtures to comparison logic and verify pass/fail decisions plus regressed-case output.

### Tests for User Story 2

- [X] T018 [P] [US2] Add threshold pass/fail tests in `tests/test_rag_evaluation_metrics.py`.
- [X] T019 [P] [US2] Add report comparison fixture tests in `tests/test_rag_evaluation_runner.py`.

### Implementation for User Story 2

- [X] T020 [US2] Implement threshold config loading and defaults in `backend/app/services/evaluation.py`.
- [X] T021 [US2] Implement candidate report generation mode in `backend/app/services/evaluation.py`.
- [X] T022 [US2] Implement baseline-vs-candidate comparison, metric deltas, regressed case listing and final decision in `backend/app/services/evaluation.py`.
- [X] T023 [US2] Wire `rag-eval candidate` and `rag-eval compare` with exit codes `0`, `1` and `2` in `backend/app/cli/evaluate_rag.py`.

**Checkpoint**: A retrieval change can be gated by comparing reports before merge.

---

## Phase 5: User Story 3 - Auditar respostas, recusas e citacoes (Priority: P3)

**Goal**: Make qualitative failures reviewable without reading raw provider logs.

**Independent Test**: Run fixture cases that include correct answer, missing point, correct refusal, incorrect refusal, valid citation and invalid citation outcomes.

### Tests for User Story 3

- [X] T024 [P] [US3] Add answer/refusal/citation classification tests in `tests/test_rag_evaluation_metrics.py`.
- [X] T025 [P] [US3] Add per-case error reporting tests for provider/search failures in `tests/test_rag_evaluation_runner.py`.

### Implementation for User Story 3

- [X] T026 [US3] Add per-case audit fields for missing answer points, refusal evidence, citation mismatches and support status in `backend/app/schemas/evaluation.py`.
- [X] T027 [US3] Include raw answer text, retrieved chunk references and concise failure reasons in report serialization in `backend/app/services/evaluation.py`.
- [X] T028 [US3] Ensure provider/runtime errors are aggregated separately from incorrect answers in `backend/app/services/evaluation.py`.
- [X] T029 [US3] Add `--search-only` mode so retrieval metrics can run without answer generation in `backend/app/cli/evaluate_rag.py`.

**Checkpoint**: Reports identify why a case failed and separate retrieval, answer, refusal, citation and runtime errors.

---

## Phase 6: Documentation & Verification

**Purpose**: Finalize operator docs and validation.

- [X] T030 [P] Update `doc/OPERATIONS.md` with dataset authoring, baseline/candidate/compare commands, threshold guidance and report review workflow.
- [X] T031 [P] Update `specs/013-avaliacao-rag/quickstart.md` if command names or flags changed during implementation.
- [X] T032 [P] Add a note to `doc/API.md` only if operator tooling documentation there needs to mention that API contracts are unchanged.
- [X] T033 Run `.venv/bin/python -m pytest tests/test_rag_evaluation_metrics.py tests/test_rag_evaluation_runner.py`.
- [X] T034 Run `.venv/bin/python -m pytest tests/test_knowledge_service.py` to confirm search/answer regression coverage still passes.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; blocks all user stories.
- **US1 Baseline (Phase 3)**: depends on Foundational and is the MVP.
- **US2 Comparison (Phase 4)**: depends on US1 because comparison needs reports.
- **US3 Auditability (Phase 5)**: depends on US1 and can proceed alongside US2 after report shape stabilizes.
- **Documentation & Verification (Phase 6)**: depends on desired user stories.

### Parallel Opportunities

- T005 can run in parallel with CLI/service scaffolding after paths exist.
- T006 through T010 are pure validation/metric work and can run in parallel.
- T012 and T013 can run in parallel.
- T018 and T019 can run in parallel.
- T024 and T025 can run in parallel.
- T030 through T032 can run in parallel.

## Implementation Strategy

1. Deliver MVP with dataset validation, pure metrics and `rag-eval baseline`.
2. Add candidate report and baseline comparison gates.
3. Enrich per-case answer/refusal/citation audit details.
4. Document the workflow and run focused tests.

## Notes

- Keep evaluation provider calls out of unit tests through dependency injection or mocked clients.
- Do not add REST/MCP endpoints in this feature.
- Do not commit datasets with personal or sensitive data.
- Treat thresholds as project evidence and revise them only with comparison reports.
