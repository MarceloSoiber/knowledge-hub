from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.cli.evaluate_rag import build_parser
from backend.app.schemas.evaluation import (
    EvaluationCase,
    EvaluationDataset,
    ExpectedChunkRef,
    ThresholdConfig,
)
from backend.app.schemas.knowledge import KnowledgeChunkRead
from backend.app.services.evaluation import (
    compare_reports,
    read_report,
    run_evaluation,
    summarize_report,
    write_report,
)


def chunk() -> KnowledgeChunkRead:
    return KnowledgeChunkRead.model_validate(
        {
            "id": 1,
            "source_id": "source-1",
            "source_title": "Runbook",
            "source_type": "text",
            "uri": "text:Runbook",
            "categories": [],
            "location": {"chunk_index": 0, "start_char": 0, "end_char": 40},
            "content": "Run knowledge-hnsw create after reviewing the baseline.",
            "score": 0.9,
        }
    )


def dataset() -> EvaluationDataset:
    return EvaluationDataset(
        dataset_version="v1",
        cases=[
            EvaluationCase(
                id="known",
                question="Create HNSW",
                kind="known_answer",
                expected_chunks=[ExpectedChunkRef(source_public_id="source-1", chunk_index=0)],
                expected_answer_points=["knowledge-hnsw create"],
            ),
            EvaluationCase(id="missing", question="private data", kind="unanswered"),
        ],
    )


@pytest.mark.asyncio
async def test_runner_records_case_metrics_and_provider_errors(tmp_path: Path) -> None:
    async def search(case: EvaluationCase) -> list[KnowledgeChunkRead]:
        if case.id == "missing":
            return []
        return [chunk()]

    async def answer(case: EvaluationCase, _: list[KnowledgeChunkRead]) -> str:
        if case.id == "missing":
            return "Nao encontrei essa informacao."
        return "According to Runbook, use knowledge-hnsw create."

    report = await run_evaluation(
        dataset(),
        "sha256:test",
        ThresholdConfig(min_recall_at_k=1.0),
        search_runner=search,
        answer_runner=answer,
    )

    assert report.decision == "passed"
    assert report.case_results[0].answer_correct is True
    assert report.case_results[0].citations_correct is True
    assert report.case_results[1].refusal_correct is True
    assert summarize_report(report)["case_count"] == 2
    report_path = tmp_path / "rag-evaluation-report.json"
    write_report(report_path, report)
    assert read_report(report_path).run_config.dataset_hash == "sha256:test"


@pytest.mark.asyncio
async def test_runner_keeps_runtime_failures_out_of_answer_grading() -> None:
    async def failing_search(_: EvaluationCase) -> list[KnowledgeChunkRead]:
        raise RuntimeError("embedding unavailable")

    report = await run_evaluation(
        dataset(), "sha256:test", search_runner=failing_search, search_only=True
    )

    assert report.decision == "failed"
    assert report.metrics["runtime_error_count"] == 2
    assert all(result.answer_correct is None and result.errors for result in report.case_results)


@pytest.mark.asyncio
async def test_compare_fails_thresholds_and_lists_regressed_cases() -> None:
    async def baseline_search(case: EvaluationCase) -> list[KnowledgeChunkRead]:
        return [] if case.id == "missing" else [chunk()]

    async def candidate_search(_: EvaluationCase) -> list[KnowledgeChunkRead]:
        return []

    async def answer(case: EvaluationCase, _: list[KnowledgeChunkRead]) -> str:
        return (
            "Nao encontrei essa informacao."
            if case.id == "missing"
            else "According to Runbook, use knowledge-hnsw create."
        )

    baseline = await run_evaluation(
        dataset(), "sha256:test", search_runner=baseline_search, answer_runner=answer
    )
    candidate = await run_evaluation(
        dataset(), "sha256:test", search_runner=candidate_search, answer_runner=answer
    )
    comparison = compare_reports(baseline, candidate, ThresholdConfig(min_recall_at_k=1.0))

    assert comparison["decision"] == "failed"
    assert comparison["regressed_cases"] == ["known"]


def test_cli_parses_runner_and_comparison_commands() -> None:
    parser = build_parser()
    baseline = parser.parse_args(
        ["baseline", "--dataset", "dataset.json", "--output", "baseline.json", "--search-only"]
    )
    compare = parser.parse_args(
        [
            "compare",
            "--baseline",
            "baseline.json",
            "--candidate",
            "candidate.json",
            "--output",
            "comparison.json",
        ]
    )

    assert baseline.command == "baseline"
    assert baseline.search_only is True
    assert compare.command == "compare"
    assert compare.output == Path("comparison.json")
