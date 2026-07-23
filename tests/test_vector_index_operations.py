from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from backend.app.cli.hnsw import build_parser, run_command
from backend.app.repositories.vector_index import (
    HNSW_INDEX_NAME,
    build_vector_search_sql,
    create_hnsw_index_sql,
    drop_hnsw_index_sql,
    plan_uses_hnsw,
    supports_hnsw,
)
from backend.app.services.vector_index import (
    EvaluationQuery,
    QueryMeasurement,
    VectorIndexReport,
    compare_recall,
    decide_hnsw,
    load_evaluation_queries,
    percentile,
)
from backend.app.services import vector_index as vector_index_service


def test_hnsw_sql_is_idempotent_and_uses_cosine_operator_class() -> None:
    assert create_hnsw_index_sql() == (
        "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding_hnsw_cosine "
        "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
    )
    assert "CONCURRENTLY" in create_hnsw_index_sql(concurrently=True)


@pytest.mark.parametrize(
    ("version", "expected"),
    [(None, False), ("0.4.4", False), ("0.5.0", True), ("0.8.1", True), ("unknown", False)],
)
def test_pgvector_hnsw_capability(version: str | None, expected: bool) -> None:
    assert supports_hnsw(version) is expected


def test_vector_query_preserves_all_filter_semantics() -> None:
    sql = build_vector_search_sql(category_ids=[1], tag_ids=[2], project_ids=[3])

    assert "embedding_batches" in sql
    assert "batch.config_hash = :config_hash" in sql
    assert "document_source_categories" in sql
    assert "document_source_tags" in sql
    assert "document_source_projects" in sql
    assert "<=>" in sql


def test_json_plan_detection_finds_hnsw_at_any_depth() -> None:
    plan = [{"Plan": {"Plans": [{"Index Name": HNSW_INDEX_NAME}]}}]

    assert plan_uses_hnsw(plan) is True
    assert plan_uses_hnsw([{"Plan": {"Node Type": "Seq Scan"}}]) is False


def test_load_evaluation_queries_validates_filters(tmp_path: Path) -> None:
    path = tmp_path / "queries.json"
    path.write_text(json.dumps({"queries": [{"query": "status", "category_ids": [1]}]}))

    assert load_evaluation_queries(path, 10) == [
        EvaluationQuery(query="status", limit=10, category_ids=[1])
    ]

    path.write_text(json.dumps([{"query": "status", "project_ids": ["bad"]}]))
    with pytest.raises(ValueError, match="project_ids"):
        load_evaluation_queries(path, 10)


def test_recall_latency_decision_accepts_only_quality_and_speed() -> None:
    exact = [QueryMeasurement(query="a", result_ids=[1, 2], latency_ms=50)]
    hnsw = [QueryMeasurement(query="a", result_ids=[2, 1], latency_ms=10, uses_hnsw=True)]

    assert compare_recall(exact, hnsw) == [1.0]
    assert percentile([5, 10, 100], 95) == 100
    assert decide_hnsw(1.0, 0.95, 50, 10, hnsw)[0] == "accepted"
    assert decide_hnsw(0.8, 0.95, 50, 10, hnsw)[0] == "rejected"
    assert decide_hnsw(1.0, 0.95, 50, 55, hnsw)[0] == "rejected"


@pytest.mark.asyncio
async def test_cli_drop_is_dry_run_without_execute() -> None:
    args = argparse.Namespace(command="drop", execute=False)

    result = await run_command(args)

    assert result == {"rollback_sql": drop_hnsw_index_sql(), "executed": False}


def test_cli_parses_hnsw_options() -> None:
    args = build_parser().parse_args(
        ["validate", "--queries", "queries.json", "--baseline", "baseline.json", "--output", "report.json", "--hnsw-ef-search", "80"]
    )

    assert args.command == "validate"
    assert args.hnsw_ef_search == 80


def test_report_serializes_stable_contract_fields() -> None:
    report = VectorIndexReport(
        generated_at="2026-07-21T12:00:00Z",
        pgvector_version="0.8.1",
        embedding_config_hash="hash",
        chunk_count=12,
    )

    payload = report.to_dict()
    assert payload["index_name"] == HNSW_INDEX_NAME
    assert payload["rollback_sql"] == drop_hnsw_index_sql()


@pytest.mark.asyncio
async def test_create_enforces_chunk_threshold_unless_forced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(vector_index_service.vector_index, "assert_hnsw_supported", AsyncMock(return_value="0.8.1"))
    monkeypatch.setattr(vector_index_service.vector_index, "count_compatible_embedded_chunks", AsyncMock(return_value=3))
    monkeypatch.setattr(vector_index_service.vector_index, "create_hnsw_index", AsyncMock())
    monkeypatch.setattr(vector_index_service.vector_index, "analyze_knowledge_chunks", AsyncMock())
    monkeypatch.setattr(vector_index_service.vector_index, "get_hnsw_index_size_bytes", AsyncMock(return_value=99))

    with pytest.raises(ValueError, match="only 3"):
        await vector_index_service.create_hnsw_index(object(), min_chunks=10)  # type: ignore[arg-type]

    report = await vector_index_service.create_hnsw_index(  # type: ignore[arg-type]
        object(), min_chunks=10, force=True
    )
    assert report.chunk_count == 3
    assert report.index_size_bytes == 99
