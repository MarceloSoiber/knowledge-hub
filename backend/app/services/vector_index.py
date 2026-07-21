from __future__ import annotations

import json
import math
import statistics
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import vector_index
from .embedding_versions import EmbeddingConfigIdentity, active_embedding_identity

DEFAULT_MIN_CHUNKS = 10_000


class EmbeddingClient(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class EvaluationQuery:
    query: str
    limit: int
    category_ids: list[int] | None = None
    tag_ids: list[int] | None = None
    project_ids: list[int] | None = None


@dataclass
class QueryMeasurement:
    query: str
    result_ids: list[int]
    latency_ms: float
    category_ids: list[int] | None = None
    tag_ids: list[int] | None = None
    project_ids: list[int] | None = None
    plan: list[dict[str, Any]] | None = None
    uses_hnsw: bool = False


@dataclass
class VectorIndexReport:
    generated_at: str
    pgvector_version: str | None
    embedding_config_hash: str
    chunk_count: int
    index_name: str = vector_index.HNSW_INDEX_NAME
    queries: list[QueryMeasurement] = field(default_factory=list)
    recall_at_k: float | None = None
    latency: dict[str, float] = field(default_factory=dict)
    decision: str = "inconclusive"
    reasons: list[str] = field(default_factory=list)
    index_size_bytes: int | None = None
    rollback_sql: str = field(default_factory=vector_index.drop_hnsw_index_sql)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_evaluation_queries(path: Path, default_limit: int) -> list[EvaluationQuery]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("queries", payload) if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not records:
        raise ValueError("evaluation file must contain a non-empty queries list")
    queries: list[EvaluationQuery] = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("query"), str):
            raise ValueError("each evaluation query must contain a non-empty query string")
        query = record["query"].strip()
        if not query:
            raise ValueError("each evaluation query must contain a non-empty query string")
        limit = int(record.get("limit", default_limit))
        if limit < 1:
            raise ValueError("query limit must be greater than zero")
        filters = {key: _optional_int_list(record.get(key), key) for key in _FILTER_KEYS}
        queries.append(EvaluationQuery(query=query, limit=limit, **filters))
    return queries


_FILTER_KEYS = ("category_ids", "tag_ids", "project_ids")


def _optional_int_list(value: Any, key: str) -> list[int] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, int) and item > 0 for item in value):
        raise ValueError(f"{key} must be a list of positive integers")
    return value


async def measure_queries(
    session: AsyncSession,
    embedding_client: EmbeddingClient,
    queries: Sequence[EvaluationQuery],
    identity: EmbeddingConfigIdentity,
    *,
    exact: bool = False,
    hnsw_ef_search: int | None = None,
) -> list[QueryMeasurement]:
    if hnsw_ef_search is not None:
        if hnsw_ef_search < 1:
            raise ValueError("hnsw ef_search must be greater than zero")
        await session.execute(text(f"SET LOCAL hnsw.ef_search = {hnsw_ef_search}"))
    if exact:
        await session.execute(text("SET LOCAL enable_indexscan = off"))
        await session.execute(text("SET LOCAL enable_bitmapscan = off"))
    measurements: list[QueryMeasurement] = []
    for query in queries:
        embedding = (await embedding_client.embed_texts([query.query]))[0]
        options = {
            "query_embedding": embedding,
            "limit": query.limit,
            "config_hash": identity.config_hash,
            "category_ids": query.category_ids,
            "tag_ids": query.tag_ids,
            "project_ids": query.project_ids,
        }
        started = time.perf_counter()
        result_ids = await vector_index.execute_vector_search(session, **options)
        latency_ms = (time.perf_counter() - started) * 1000
        plan = await vector_index.explain_vector_search(session, **options)
        measurements.append(
            QueryMeasurement(
                query=query.query,
                result_ids=result_ids,
                latency_ms=round(latency_ms, 3),
                category_ids=query.category_ids,
                tag_ids=query.tag_ids,
                project_ids=query.project_ids,
                plan=plan,
                uses_hnsw=vector_index.plan_uses_hnsw(plan),
            )
        )
    return measurements


async def create_hnsw_index(
    session: AsyncSession,
    *,
    min_chunks: int = DEFAULT_MIN_CHUNKS,
    force: bool = False,
    identity: EmbeddingConfigIdentity | None = None,
) -> VectorIndexReport:
    if min_chunks < 1:
        raise ValueError("min_chunks must be greater than zero")
    resolved_identity = identity or active_embedding_identity()
    version = await vector_index.assert_hnsw_supported(session)
    count = await vector_index.count_compatible_embedded_chunks(session, resolved_identity.config_hash)
    if count < min_chunks and not force:
        raise ValueError(
            f"only {count} compatible embedded chunks found; use --force or lower --min-chunks"
        )
    await vector_index.create_hnsw_index(session)
    await vector_index.analyze_knowledge_chunks(session)
    size = await vector_index.get_hnsw_index_size_bytes(session)
    return VectorIndexReport(
        generated_at=_timestamp(),
        pgvector_version=version,
        embedding_config_hash=resolved_identity.config_hash,
        chunk_count=count,
        index_size_bytes=size,
        decision="inconclusive",
        reasons=["Index created; run validate before accepting it for production."],
    )


async def baseline_hnsw_index(
    session: AsyncSession,
    embedding_client: EmbeddingClient,
    queries: Sequence[EvaluationQuery],
    identity: EmbeddingConfigIdentity | None = None,
) -> VectorIndexReport:
    resolved_identity = identity or active_embedding_identity()
    version = await vector_index.get_pgvector_version(session)
    count = await vector_index.count_compatible_embedded_chunks(session, resolved_identity.config_hash)
    measurements = await measure_queries(
        session, embedding_client, queries, resolved_identity, exact=True
    )
    return VectorIndexReport(
        generated_at=_timestamp(),
        pgvector_version=version,
        embedding_config_hash=resolved_identity.config_hash,
        chunk_count=count,
        queries=measurements,
        latency={"baseline_p50_ms": percentile([item.latency_ms for item in measurements], 50), "baseline_p95_ms": percentile([item.latency_ms for item in measurements], 95)},
        reasons=["Exact baseline captured with index scans disabled for this session."],
    )


async def validate_hnsw_index(
    session: AsyncSession,
    embedding_client: EmbeddingClient,
    queries: Sequence[EvaluationQuery],
    baseline: VectorIndexReport,
    *,
    recall_threshold: float,
    hnsw_ef_search: int | None = None,
    identity: EmbeddingConfigIdentity | None = None,
) -> VectorIndexReport:
    if not 0 <= recall_threshold <= 1:
        raise ValueError("recall threshold must be between zero and one")
    resolved_identity = identity or active_embedding_identity()
    await vector_index.analyze_knowledge_chunks(session)
    measurements = await measure_queries(
        session, embedding_client, queries, resolved_identity, hnsw_ef_search=hnsw_ef_search
    )
    recalls = compare_recall(baseline.queries, measurements)
    latency = [item.latency_ms for item in measurements]
    report = VectorIndexReport(
        generated_at=_timestamp(),
        pgvector_version=await vector_index.get_pgvector_version(session),
        embedding_config_hash=resolved_identity.config_hash,
        chunk_count=await vector_index.count_compatible_embedded_chunks(session, resolved_identity.config_hash),
        queries=measurements,
        recall_at_k=round(statistics.fmean(recalls), 4) if recalls else None,
        latency={"baseline_p95_ms": baseline.latency.get("baseline_p95_ms", 0.0), "hnsw_p50_ms": percentile(latency, 50), "hnsw_p95_ms": percentile(latency, 95)},
        index_size_bytes=await vector_index.get_hnsw_index_size_bytes(session),
    )
    report.decision, report.reasons = decide_hnsw(
        report.recall_at_k, recall_threshold, baseline.latency.get("baseline_p95_ms"), report.latency["hnsw_p95_ms"], measurements
    )
    return report


def compare_recall(exact: Sequence[QueryMeasurement], approximate: Sequence[QueryMeasurement]) -> list[float]:
    approximate_by_query = {item.query: item for item in approximate}
    recalls: list[float] = []
    for expected in exact:
        actual = approximate_by_query.get(expected.query)
        if actual is None:
            continue
        if not expected.result_ids:
            recalls.append(1.0)
            continue
        recalls.append(len(set(expected.result_ids) & set(actual.result_ids)) / len(expected.result_ids))
    return recalls


def decide_hnsw(
    recall: float | None,
    recall_threshold: float,
    baseline_p95_ms: float | None,
    hnsw_p95_ms: float,
    measurements: Sequence[QueryMeasurement],
) -> tuple[str, list[str]]:
    if recall is None or baseline_p95_ms is None:
        return "inconclusive", ["Baseline data is missing for one or more evaluation queries."]
    if recall < recall_threshold:
        return "rejected", [f"recall@k {recall:.4f} is below threshold {recall_threshold:.4f}."]
    if hnsw_p95_ms >= baseline_p95_ms:
        return "rejected", ["HNSW p95 latency did not improve over the exact baseline."]
    missing_plans = sum(not item.uses_hnsw for item in measurements)
    reasons = ["Recall and p95 latency meet the acceptance criteria."]
    if missing_plans:
        reasons.append(f"HNSW was not selected by the planner for {missing_plans} evaluation queries.")
    return "accepted", reasons


def percentile(values: Sequence[float], percentile_value: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil((percentile_value / 100) * len(ordered)) - 1))
    return round(ordered[index], 3)


def write_report(path: Path, report: VectorIndexReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_report(path: Path) -> VectorIndexReport:
    payload = json.loads(path.read_text(encoding="utf-8"))
    measurements = [QueryMeasurement(**item) for item in payload.pop("queries", [])]
    return VectorIndexReport(queries=measurements, **payload)


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
