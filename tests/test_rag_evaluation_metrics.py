from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.schemas.evaluation import (
    EvaluationCase,
    EvaluationDataset,
    ExpectedChunkRef,
    LatencyMetrics,
)
from backend.app.schemas.knowledge import KnowledgeChunkRead
from backend.app.services.evaluation import (
    aggregate_metrics,
    answer_point_result,
    citation_result,
    recall_at_k,
    reciprocal_rank,
    refusal_result,
)
from backend.app.schemas.evaluation import EvaluationCaseResult


def chunk(
    source_id: str = "source-1", title: str = "Runbook", index: int = 0
) -> KnowledgeChunkRead:
    return KnowledgeChunkRead.model_validate(
        {
            "id": index + 1,
            "source_id": source_id,
            "source_title": title,
            "source_type": "text",
            "uri": f"text:{title}",
            "categories": [],
            "location": {"chunk_index": index, "start_char": 0, "end_char": 40, "page": 1},
            "content": "Run knowledge-hnsw create after reviewing the baseline.",
            "score": 0.9,
        }
    )


def known_case() -> EvaluationCase:
    return EvaluationCase(
        id="known",
        question="How do I create HNSW?",
        kind="known_answer",
        expected_chunks=[ExpectedChunkRef(source_public_id="source-1", chunk_index=0)],
        expected_answer_points=["knowledge-hnsw create"],
    )


def test_dataset_requires_unique_cases_and_an_unanswered_case() -> None:
    with pytest.raises(ValidationError, match="unanswered"):
        EvaluationDataset(dataset_version="v1", cases=[known_case()])

    unanswered = EvaluationCase(id="missing", question="private data", kind="unanswered")
    with pytest.raises(ValidationError, match="unique"):
        EvaluationDataset(dataset_version="v1", cases=[known_case(), known_case(), unanswered])


def test_unanswered_case_rejects_retrieval_or_answer_expectations() -> None:
    with pytest.raises(ValidationError, match="cannot require"):
        EvaluationCase(
            id="missing",
            question="private data",
            kind="unanswered",
            expected_answer_points=["secret"],
        )


def test_recall_and_mrr_use_stable_chunk_references() -> None:
    case = known_case()
    results = [chunk(source_id="other"), chunk()]

    assert recall_at_k(results, case) == 1.0
    assert reciprocal_rank(results, case) == 0.5
    assert recall_at_k([], case) == 0.0
    assert reciprocal_rank([], case) == 0.0


def test_answer_refusal_and_citation_checks_are_deterministic() -> None:
    case = known_case()
    result = chunk()

    assert answer_point_result("Use knowledge-hnsw create.", case.expected_answer_points) == (
        True,
        [],
    )
    assert answer_point_result("Use another command.", case.expected_answer_points) == (
        False,
        ["knowledge-hnsw create"],
    )
    assert refusal_result("Nao encontrei essa informacao.", True) is True
    assert refusal_result("Nao encontrei essa informacao.", False) is False
    assert citation_result("According to Runbook, use the command.", [result], case) == (True, [])
    assert citation_result("Use the command.", [result], case)[0] is False


def test_aggregate_metrics_reports_rates_and_p95_latency() -> None:
    results = [
        EvaluationCaseResult(
            case_id="a",
            recall_at_k=1,
            reciprocal_rank=1,
            answer_correct=True,
            refusal_correct=True,
            citations_correct=True,
            latency_ms=LatencyMetrics(search_ms=20, answer_ms=50, total_ms=70),
        ),
        EvaluationCaseResult(
            case_id="b",
            recall_at_k=0,
            reciprocal_rank=0,
            answer_correct=False,
            refusal_correct=None,
            citations_correct=False,
            latency_ms=LatencyMetrics(search_ms=100, answer_ms=200, total_ms=300),
        ),
    ]

    metrics = aggregate_metrics(results)
    assert metrics["recall_at_k"] == 0.5
    assert metrics["mrr"] == 0.5
    assert metrics["answer_correct_rate"] == 0.5
    assert metrics["refusal_correct_rate"] == 1.0
    assert metrics["citation_correct_rate"] == 0.5
    assert metrics["search_latency_p95_ms"] == 100
