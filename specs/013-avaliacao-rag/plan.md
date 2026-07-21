# Implementation Plan: Avaliacao do RAG

**Branch**: `013-avaliacao-rag` | **Date**: 2026-07-21 | **Spec**: `specs/013-avaliacao-rag/spec.md`

**Input**: Feature specification from `/specs/013-avaliacao-rag/spec.md`

## Summary

Add an operator-facing RAG evaluation workflow that loads a versioned dataset, runs the existing search/answer pipeline, computes retrieval, answer, refusal, citation and latency metrics, and compares candidate runs against an approved baseline. The feature is delivered as backend services plus an argparse CLI and file-based reports. It does not change the public API, MCP tools or frontend.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI service modules, SQLAlchemy async, Pydantic v2, existing embedding/LLM clients, argparse CLI, pytest

**Storage**: PostgreSQL with pgvector for existing knowledge data; evaluation datasets and reports are versioned JSON/Markdown file artifacts.

**Testing**: `.venv/bin/python -m pytest`

**Target Platform**: Linux backend service and local/operator CLI.

**Project Type**: Backend service/CLI feature with documentation; no frontend change.

**Performance Goals**: Evaluation must report embedding, retrieval and answer latency separately. Normal search remains subject to the constitution target of typical queries under 500ms.

**Constraints**: Keep FastAPI routes thin and unchanged; keep business logic in `backend/app/services`; use Pydantic v2 schemas for dataset/report validation; avoid external provider calls in unit tests; update `doc/OPERATIONS.md` and only update `doc/API.md` if public behavior is documented.

**Scale/Scope**: Existing `search_knowledge()` and `answer_knowledge()` flows, retrieval filters, source/chunk citation metadata, baseline/candidate report files, local CI-friendly metric tests.

## Constitution Check

- Code Quality: Pass. Evaluation orchestration stays in services; CLI is a thin operator surface.
- Testing Standards: Pass with gate. Metric calculation, dataset validation and decision logic need pytest coverage without external network calls.
- Performance: Pass. The feature measures RAG latency and preserves the existing API performance target.
- Documentation: Pass. Operator commands, dataset format and acceptance gates must be documented.
- UX: N/A for frontend. CLI output must be concise and reports must be reviewable.

## Project Structure

### Documentation (this feature)

```text
specs/013-avaliacao-rag/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- rag-evaluation.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/app/
|-- cli/
|   `-- evaluate_rag.py
|-- schemas/
|   `-- evaluation.py
`-- services/
    `-- evaluation.py

evaluation/
|-- rag-dataset.example.json
`-- thresholds.example.json

tests/
|-- test_rag_evaluation_metrics.py
`-- test_rag_evaluation_runner.py

doc/
`-- OPERATIONS.md

pyproject.toml
```

**Structure Decision**: Add `schemas/evaluation.py` for strict dataset/report models, `services/evaluation.py` for metrics and orchestration, and `cli/evaluate_rag.py` for `rag-eval` commands. Keep API/MCP routes untouched.

## Implementation Details

### Dataset and Validation

- Add a JSON dataset format with:
  - `dataset_version`;
  - optional defaults for `limit`, `min_score`, category/tag/project filters and expected thresholds;
  - case `id`, `question`, `kind`, expected source/chunk references, expected category/project, expected answer points, refusal expectation and tags.
- Prefer stable expected chunk references: `source_public_id`, `chunk_index`, `page`, `section` and optional content hash/snippet. Avoid raw database integer ids in committed datasets.
- Validate the dataset before provider calls. Fail fast for missing version, duplicate case ids, known-answer cases without answer expectations, and unanswered cases with incompatible expectations.
- Include a small `evaluation/rag-dataset.example.json` that has known-answer, exact-term, semantic and unanswered cases without personal data.

### Runner and Metrics

- Add service models/functions for:
  - loading datasets and thresholds;
  - executing search-only and answer runs;
  - matching retrieved chunks to expected references;
  - computing Recall@K and MRR;
  - checking answer essential points with deterministic text matching for MVP;
  - checking refusal text against configured refusal patterns;
  - checking citations against retrieved/expected sources;
  - recording latency for query embedding/search/answer.
- For MVP, answer correctness should be deterministic and testable: normalize text and require configured essential points. A future judge model can be added only behind an explicit evaluator mode.
- Use existing `search_knowledge()` and `answer_knowledge()` behavior as the system under test. If latency decomposition requires finer instrumentation, add a dedicated evaluation path that calls the same lower-level search functions without changing public API behavior.
- Capture provider/runtime errors per case and aggregate them separately from incorrect answers.

### Baseline and Candidate Comparison

- Add CLI subcommands:
  - `baseline`: run dataset and save a report marked as baseline.
  - `candidate`: run dataset and save a candidate report.
  - `compare`: compare two saved reports and apply thresholds.
  - `summarize`: print a compact table from a report.
- Report fields should include timestamp, git revision when available, dataset version/hash, evaluated settings, case results, aggregate metrics, latency summary, errors and final decision.
- Thresholds should be configurable in a JSON file and include minimums for Recall@K, MRR, known-answer correctness, refusal correctness, citation correctness and maximum latency p95.
- Candidate comparison should list regressed cases and metric deltas, not only a final boolean.

### Documentation

- Update `doc/OPERATIONS.md` with:
  - how to author/extend datasets without sensitive personal data;
  - baseline command;
  - candidate command;
  - compare command;
  - recommended thresholds and how to adjust them with evidence;
  - guidance that retrieval changes should include a comparison report.
- `doc/API.md` does not need a contract update because the feature adds no endpoint. Add a short note only if the project already documents operator tooling in API docs.

## Data Model / API Implications

- No PostgreSQL schema changes are required.
- No REST or MCP request/response contract changes are required.
- New Pydantic models represent file artifacts, not persisted application records.
- Reports are intended for version control, CI artifacts or manual review.

## Test Strategy

- Unit tests for dataset validation, including duplicate ids, unanswered cases, missing expected points and invalid expected chunks.
- Unit tests for Recall@K, MRR, refusal correctness, answer point matching, citation correctness and aggregate latency calculation.
- Service tests for baseline/candidate decision logic using mocked search/answer outputs.
- CLI tests for argument parsing and JSON report writing where practical.
- Regression coverage ensuring `search_knowledge()` and `answer_knowledge()` public behavior is not changed by evaluation support.
- Manual verification with `.venv/bin/python -m pytest tests/test_rag_evaluation_metrics.py tests/test_rag_evaluation_runner.py` and one documented sample run.

## Risk Notes

- LLM-generated answers are not fully deterministic; MVP grading should use essential points and refusal patterns, while preserving raw answer text for review.
- Dataset chunk references may drift after ingestion/chunking changes; using public source ids and chunk metadata reduces but does not eliminate this risk.
- Running full answer evaluation can be slow and can consume provider quota; search-only mode should remain available.
- Metrics can create false confidence if the dataset is too small or homogeneous; docs must treat thresholds as project evidence, not universal truth.
- Provider/network failures must be visible in reports so they are not mistaken for quality regressions.

## Complexity Tracking

No constitution violations identified. A separate runner and file-based report model are required by the source plan and keep evaluation concerns out of the API runtime path.
