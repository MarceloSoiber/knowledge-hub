from __future__ import annotations

import hashlib
import json
import subprocess
import time
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.settings import Settings, get_settings
from ..schemas.evaluation import (
    EvaluationCase,
    EvaluationCaseResult,
    EvaluationDataset,
    EvaluationReport,
    EvaluationRunConfig,
    LatencyMetrics,
    RetrievedChunkRef,
    ThresholdConfig,
)
from ..schemas.knowledge import KnowledgeChunkRead
from .embedding_versions import active_embedding_identity, compute_embedding_content_hash
from .embeddings import EmbeddingClient
from .rag import AnswerClient
from .search import search_knowledge

DEFAULT_REFUSAL_PATTERNS = (
    "nao encontrei essa informacao",
    "nao encontrei esta informacao",
    "nao tenho informacao",
    "nao tenho essa informacao",
    "nao disponho de informacao",
    "i don't know",
    "cannot find",
    "not enough information",
)

SearchRunner = Callable[[EvaluationCase], Awaitable[list[KnowledgeChunkRead]]]
AnswerRunner = Callable[[EvaluationCase, list[KnowledgeChunkRead]], Awaitable[str]]


def load_dataset(path: Path) -> tuple[EvaluationDataset, str]:
    raw = path.read_bytes()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid evaluation dataset JSON: {path}") from exc
    return EvaluationDataset.model_validate(payload), dataset_hash(raw)


def load_thresholds(path: Path | None) -> ThresholdConfig:
    if path is None:
        return ThresholdConfig()
    try:
        return ThresholdConfig.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"invalid threshold configuration: {path}") from exc


def read_report(path: Path) -> EvaluationReport:
    try:
        return EvaluationReport.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"invalid evaluation report: {path}") from exc


def write_report(path: Path, report: EvaluationReport | dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump(mode="json") if isinstance(report, EvaluationReport) else report
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dataset_hash(raw: bytes) -> str:
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def expected_chunk_matches(chunk: KnowledgeChunkRead, expected: object) -> bool:
    source_id = getattr(expected, "source_public_id", None)
    source_title = getattr(expected, "source_title", None)
    chunk_index = getattr(expected, "chunk_index", None)
    page = getattr(expected, "page", None)
    section = getattr(expected, "section", None)
    content_hash = getattr(expected, "content_hash", None)
    snippet = getattr(expected, "snippet", None)
    if source_id is not None and chunk.source_id != source_id:
        return False
    if source_title is not None and normalize_text(chunk.source_title) != normalize_text(
        source_title
    ):
        return False
    if chunk_index is not None and chunk.location.chunk_index != chunk_index:
        return False
    if page is not None and chunk.location.page != page:
        return False
    if section is not None and normalize_text(chunk.location.section or "") != normalize_text(
        section
    ):
        return False
    if content_hash is not None and compute_embedding_content_hash(chunk.content) != content_hash:
        return False
    if snippet is not None and normalize_text(snippet) not in normalize_text(chunk.content):
        return False
    return True


def recall_at_k(results: Sequence[KnowledgeChunkRead], case: EvaluationCase) -> float | None:
    if not case.expected_chunks:
        return None
    found = sum(
        any(expected_chunk_matches(chunk, expected) for chunk in results)
        for expected in case.expected_chunks
    )
    return found / len(case.expected_chunks)


def reciprocal_rank(results: Sequence[KnowledgeChunkRead], case: EvaluationCase) -> float | None:
    if not case.expected_chunks:
        return None
    for index, chunk in enumerate(results, start=1):
        if any(expected_chunk_matches(chunk, expected) for expected in case.expected_chunks):
            return 1 / index
    return 0.0


def answer_point_result(
    answer: str, expected_points: Sequence[str]
) -> tuple[bool | None, list[str]]:
    if not expected_points:
        return None, []
    normalized_answer = normalize_text(answer)
    missing = [point for point in expected_points if normalize_text(point) not in normalized_answer]
    return not missing, missing


def refusal_result(answer: str, expected_refusal: bool | None) -> bool | None:
    if expected_refusal is None:
        return None
    normalized_answer = normalize_text(answer)
    was_refusal = any(
        normalize_text(pattern) in normalized_answer for pattern in DEFAULT_REFUSAL_PATTERNS
    )
    return was_refusal == expected_refusal


def retrieved_chunk_ref(chunk: KnowledgeChunkRead) -> RetrievedChunkRef:
    return RetrievedChunkRef(
        source_public_id=chunk.source_id,
        source_title=chunk.source_title,
        chunk_index=chunk.location.chunk_index,
        page=chunk.location.page,
        section=chunk.location.section,
        content_hash=compute_embedding_content_hash(chunk.content),
        score=chunk.score,
    )


def citations_in_answer(answer: str, chunks: Sequence[KnowledgeChunkRead]) -> list[str]:
    normalized_answer = normalize_text(answer)
    citations: list[str] = []
    for chunk in chunks:
        if (
            normalize_text(chunk.source_id) in normalized_answer
            or normalize_text(chunk.source_title) in normalized_answer
        ):
            if chunk.source_id not in citations:
                citations.append(chunk.source_id)
    return citations


def citation_result(
    answer: str, results: Sequence[KnowledgeChunkRead], case: EvaluationCase
) -> tuple[bool | None, list[str]]:
    if not case.expected_chunks:
        return None, []
    cited = citations_in_answer(answer, results)
    expected_results = [
        chunk
        for chunk in results
        if any(expected_chunk_matches(chunk, expected) for expected in case.expected_chunks)
    ]
    expected_ids = {chunk.source_id for chunk in expected_results}
    if not cited:
        return False, ["answer does not cite a retrieved expected source"]
    mismatches = [source_id for source_id in cited if source_id not in expected_ids]
    return not mismatches and bool(expected_ids), mismatches


def answer_supported_by_sources(
    case: EvaluationCase, results: Sequence[KnowledgeChunkRead]
) -> bool | None:
    if not case.expected_answer_points:
        return None
    context = normalize_text(" ".join(chunk.content for chunk in results))
    return all(normalize_text(point) in context for point in case.expected_answer_points)


def percentile(values: Sequence[float], percent: int = 95) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((percent / 100) * len(ordered) + 0.5) - 1))
    return ordered[index]


def aggregate_metrics(case_results: Sequence[EvaluationCaseResult]) -> dict[str, float | None]:
    def average(field: str) -> float | None:
        values = [getattr(item, field) for item in case_results if getattr(item, field) is not None]
        return mean(values) if values else None

    def rate(field: str) -> float | None:
        values = [getattr(item, field) for item in case_results if getattr(item, field) is not None]
        return mean(float(value) for value in values) if values else None

    return {
        "recall_at_k": average("recall_at_k"),
        "mrr": average("reciprocal_rank"),
        "answer_correct_rate": rate("answer_correct"),
        "refusal_correct_rate": rate("refusal_correct"),
        "citation_correct_rate": rate("citations_correct"),
        "embedding_latency_p95_ms": percentile(
            [item.latency_ms.embedding_ms for item in case_results]
        ),
        "search_latency_p95_ms": percentile([item.latency_ms.search_ms for item in case_results]),
        "answer_latency_p95_ms": percentile([item.latency_ms.answer_ms for item in case_results]),
        "total_latency_p95_ms": percentile([item.latency_ms.total_ms for item in case_results]),
        "runtime_error_count": float(sum(bool(item.errors) for item in case_results)),
    }


def threshold_failures(metrics: dict[str, float | None], thresholds: ThresholdConfig) -> list[str]:
    mappings = (
        ("recall_at_k", thresholds.min_recall_at_k, "minimum"),
        ("mrr", thresholds.min_mrr, "minimum"),
        ("answer_correct_rate", thresholds.min_answer_correct_rate, "minimum"),
        ("refusal_correct_rate", thresholds.min_refusal_correct_rate, "minimum"),
        ("citation_correct_rate", thresholds.min_citation_correct_rate, "minimum"),
        ("embedding_latency_p95_ms", thresholds.max_embedding_latency_p95_ms, "maximum"),
        ("search_latency_p95_ms", thresholds.max_search_latency_p95_ms, "maximum"),
        ("answer_latency_p95_ms", thresholds.max_answer_latency_p95_ms, "maximum"),
    )
    failures: list[str] = []
    for metric_name, boundary, mode in mappings:
        value = metrics.get(metric_name)
        if boundary is None or value is None:
            continue
        failed = value < boundary if mode == "minimum" else value > boundary
        if failed:
            failures.append(f"{metric_name}={value:.3f} violates {mode} {boundary:.3f}")
    return failures


def make_run_config(
    dataset: EvaluationDataset,
    dataset_digest: str,
    mode: str,
    limit: int | None = None,
    min_score: float | None = None,
    settings: Settings | None = None,
) -> EvaluationRunConfig:
    resolved = settings or get_settings()
    identity = active_embedding_identity(resolved)
    return EvaluationRunConfig(
        dataset_version=dataset.dataset_version,
        dataset_hash=dataset_digest,
        git_revision=git_revision(),
        retrieval_limit=limit or dataset.defaults.limit,
        min_score=min_score if min_score is not None else dataset.defaults.min_score,
        embedding_provider=identity.provider,
        embedding_model=identity.model,
        embedding_version=identity.version,
        embedding_config_hash=identity.config_hash,
        llm_provider=resolved.llm_provider,
        llm_model=resolved.local_llm_model
        if resolved.llm_provider == "local"
        else resolved.api_llm_model,
        mode=mode,  # type: ignore[arg-type]
    )


def git_revision() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


async def run_evaluation(
    dataset: EvaluationDataset,
    dataset_digest: str,
    thresholds: ThresholdConfig | None = None,
    *,
    mode: str = "baseline",
    session: AsyncSession | None = None,
    embedding_client: EmbeddingClient | None = None,
    answer_client: AnswerClient | None = None,
    search_only: bool = False,
    limit: int | None = None,
    min_score: float | None = None,
    search_runner: SearchRunner | None = None,
    answer_runner: AnswerRunner | None = None,
    settings: Settings | None = None,
) -> EvaluationReport:
    effective_thresholds = thresholds or ThresholdConfig()
    config = make_run_config(
        dataset, dataset_digest, "search_only" if search_only else mode, limit, min_score, settings
    )
    if search_runner is None:
        if session is None or embedding_client is None:
            raise ValueError(
                "session and embedding_client are required for the default search runner"
            )

        search_timings: dict[str, dict[str, float]] = {}

        async def search_runner(case: EvaluationCase) -> list[KnowledgeChunkRead]:
            case_limit = case.limit or config.retrieval_limit
            case_score = case.min_score if case.min_score is not None else config.min_score
            filters = case.filters
            timings: dict[str, float] = {}
            search_timings[case.id] = timings
            return await search_knowledge(
                session,
                case.question,
                case_limit,
                embedding_client,
                category_ids=filters.category_ids or dataset.defaults.filters.category_ids,
                tag_ids=filters.tag_ids or dataset.defaults.filters.tag_ids,
                project_ids=filters.project_ids or dataset.defaults.filters.project_ids,
                min_score=case_score,
                latency_ms=timings,
            )
    else:
        search_timings = {}
    if not search_only and answer_runner is None:
        if answer_client is None:
            raise ValueError("answer_client is required when search_only is false")

        async def answer_runner(case: EvaluationCase, chunks: list[KnowledgeChunkRead]) -> str:
            return await answer_client.answer(case.question, chunks)

    results: list[EvaluationCaseResult] = []
    for case in dataset.cases:
        started_at = time.perf_counter()
        try:
            search_started_at = time.perf_counter()
            chunks = await search_runner(case)
            measured_search = search_timings.get(case.id, {})
            search_ms = measured_search.get("search", elapsed_ms(search_started_at))
            answer: str | None = None
            answer_ms = 0.0
            if not search_only:
                answer_started_at = time.perf_counter()
                answer = await answer_runner(case, chunks)  # type: ignore[misc]
                answer_ms = elapsed_ms(answer_started_at)
            answer_correct, missing_points = answer_point_result(
                answer or "", case.expected_answer_points
            )
            refusal_correct = (
                refusal_result(answer or "", case.expected_refusal) if answer is not None else None
            )
            citations_correct, citation_mismatches = (
                citation_result(answer or "", chunks, case) if answer is not None else (None, [])
            )
            results.append(
                EvaluationCaseResult(
                    case_id=case.id,
                    retrieved_chunks=[retrieved_chunk_ref(chunk) for chunk in chunks],
                    answer=answer,
                    citations=citations_in_answer(answer or "", chunks),
                    recall_at_k=recall_at_k(chunks, case),
                    reciprocal_rank=reciprocal_rank(chunks, case),
                    answer_correct=answer_correct,
                    refusal_correct=refusal_correct,
                    citations_correct=citations_correct,
                    supported_by_sources=answer_supported_by_sources(case, chunks),
                    missing_answer_points=missing_points,
                    citation_mismatches=citation_mismatches,
                    latency_ms=LatencyMetrics(
                        embedding_ms=measured_search.get("embedding", 0.0),
                        search_ms=search_ms,
                        answer_ms=answer_ms,
                        total_ms=elapsed_ms(started_at),
                    ),
                )
            )
        except Exception as exc:  # Provider failures are part of the report, not answer failures.
            results.append(
                EvaluationCaseResult(
                    case_id=case.id,
                    latency_ms=LatencyMetrics(total_ms=elapsed_ms(started_at)),
                    errors=[f"{type(exc).__name__}: {exc}"],
                )
            )
    metrics = aggregate_metrics(results)
    failures = threshold_failures(metrics, effective_thresholds)
    failures.extend(f"{result.case_id}: {result.errors[0]}" for result in results if result.errors)
    return EvaluationReport(
        created_at=datetime.now(UTC),
        run_config=config,
        case_results=results,
        metrics=metrics,
        thresholds=effective_thresholds,
        decision="failed" if failures else "passed",
        failures=failures,
    )


def elapsed_ms(started_at: float) -> float:
    return round((time.perf_counter() - started_at) * 1000, 3)


def compare_reports(
    baseline: EvaluationReport,
    candidate: EvaluationReport,
    thresholds: ThresholdConfig | None = None,
) -> dict[str, Any]:
    if baseline.run_config.dataset_hash != candidate.run_config.dataset_hash:
        raise ValueError("reports use different dataset hashes")
    effective_thresholds = thresholds or candidate.thresholds
    failures = threshold_failures(candidate.metrics, effective_thresholds)
    baseline_by_case = {result.case_id: result for result in baseline.case_results}
    regressed_cases: list[str] = []
    for candidate_result in candidate.case_results:
        previous = baseline_by_case.get(candidate_result.case_id)
        if previous is None:
            continue
        if (previous.recall_at_k or 0) > (candidate_result.recall_at_k or 0):
            regressed_cases.append(candidate_result.case_id)
            continue
        for field in ("answer_correct", "refusal_correct", "citations_correct"):
            if getattr(previous, field) is True and getattr(candidate_result, field) is False:
                regressed_cases.append(candidate_result.case_id)
                break
    deltas = {
        name: metric_delta(baseline.metrics.get(name), candidate.metrics.get(name))
        for name in candidate.metrics
        if name in baseline.metrics
    }
    return {
        "comparison_version": "1",
        "baseline_created_at": baseline.created_at.isoformat(),
        "candidate_created_at": candidate.created_at.isoformat(),
        "dataset_hash": candidate.run_config.dataset_hash,
        "metrics": candidate.metrics,
        "metric_deltas": deltas,
        "thresholds": effective_thresholds.model_dump(mode="json"),
        "regressed_cases": sorted(set(regressed_cases)),
        "decision": "failed" if failures else "passed",
        "failures": failures,
    }


def metric_delta(baseline: float | None, candidate: float | None) -> float | None:
    if baseline is None or candidate is None:
        return None
    return round(candidate - baseline, 6)


def summarize_report(report: EvaluationReport) -> dict[str, Any]:
    return {
        "dataset_version": report.run_config.dataset_version,
        "dataset_hash": report.run_config.dataset_hash,
        "mode": report.run_config.mode,
        "decision": report.decision,
        "metrics": report.metrics,
        "case_count": len(report.case_results),
        "error_count": sum(bool(case.errors) for case in report.case_results),
        "failures": report.failures,
    }
