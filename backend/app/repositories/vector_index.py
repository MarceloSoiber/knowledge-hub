from __future__ import annotations

import json
import math
from collections.abc import Sequence
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

HNSW_INDEX_NAME = "ix_knowledge_chunks_embedding_hnsw_cosine"
HNSW_OPERATOR_CLASS = "vector_cosine_ops"
KNOWLEDGE_CHUNKS_TABLE = "knowledge_chunks"


class PgvectorUnsupportedError(RuntimeError):
    """Raised when the installed pgvector extension cannot build an HNSW index."""


def create_hnsw_index_sql(*, concurrently: bool = False) -> str:
    concurrent = " CONCURRENTLY" if concurrently else ""
    return (
        f"CREATE INDEX{concurrent} IF NOT EXISTS {HNSW_INDEX_NAME} "
        f"ON {KNOWLEDGE_CHUNKS_TABLE} USING hnsw (embedding {HNSW_OPERATOR_CLASS})"
    )


def drop_hnsw_index_sql(*, concurrently: bool = True) -> str:
    concurrent = " CONCURRENTLY" if concurrently else ""
    return f"DROP INDEX{concurrent} IF EXISTS {HNSW_INDEX_NAME}"


async def get_pgvector_version(session: AsyncSession | AsyncConnection) -> str | None:
    result = await session.execute(
        text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
    )
    value = result.scalar_one_or_none()
    return str(value) if value is not None else None


def supports_hnsw(pgvector_version: str | None) -> bool:
    if pgvector_version is None:
        return False
    try:
        major, minor, *_ = (int(part) for part in pgvector_version.split("."))
    except ValueError:
        return False
    return (major, minor) >= (0, 5)


async def assert_hnsw_supported(session: AsyncSession | AsyncConnection) -> str:
    version = await get_pgvector_version(session)
    if not supports_hnsw(version):
        readable = version or "not installed"
        raise PgvectorUnsupportedError(
            "HNSW requires pgvector 0.5 or newer; installed version is " f"{readable}."
        )
    return version


async def count_compatible_embedded_chunks(
    session: AsyncSession,
    config_hash: str,
) -> int:
    result = await session.execute(
        text(
            "SELECT count(*) "
            "FROM knowledge_chunks AS chunk "
            "JOIN embedding_batches AS batch ON batch.id = chunk.embedding_batch_id "
            "WHERE chunk.embedding IS NOT NULL "
            "AND chunk.embedding_status = 'embedded' "
            "AND batch.status = 'completed' "
            "AND batch.config_hash = :config_hash"
        ),
        {"config_hash": config_hash},
    )
    return int(result.scalar_one())


async def create_hnsw_index(session: AsyncSession) -> None:
    await session.execute(text(create_hnsw_index_sql()))


async def create_hnsw_index_concurrently(connection: AsyncConnection) -> None:
    await connection.execute(text(create_hnsw_index_sql(concurrently=True)))


async def drop_hnsw_index(session: AsyncSession) -> None:
    await session.execute(text(drop_hnsw_index_sql(concurrently=False)))


async def drop_hnsw_index_concurrently(connection: AsyncConnection) -> None:
    await connection.execute(text(drop_hnsw_index_sql(concurrently=True)))


async def analyze_knowledge_chunks(session: AsyncSession) -> None:
    await session.execute(text("ANALYZE knowledge_chunks"))


async def get_hnsw_index_size_bytes(session: AsyncSession) -> int | None:
    result = await session.execute(
        text("SELECT pg_relation_size(to_regclass(:index_name))"),
        {"index_name": HNSW_INDEX_NAME},
    )
    value = result.scalar_one_or_none()
    return int(value) if value is not None else None


def vector_literal(embedding: Sequence[float]) -> str:
    if not embedding:
        raise ValueError("query embedding must not be empty")
    values = [float(value) for value in embedding]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("query embedding must contain only finite values")
    return "[" + ",".join(str(value) for value in values) + "]"


def build_vector_search_sql(
    *,
    category_ids: Sequence[int] | None = None,
    tag_ids: Sequence[int] | None = None,
    project_ids: Sequence[int] | None = None,
) -> str:
    clauses = [
        "chunk.embedding IS NOT NULL",
        "chunk.embedding_status = 'embedded'",
        "batch.status = 'completed'",
        "batch.config_hash = :config_hash",
    ]
    if category_ids is not None:
        clauses.append(
            "EXISTS (SELECT 1 FROM document_source_categories AS category_link "
            "WHERE category_link.document_source_id = source.id "
            "AND category_link.category_id = ANY(:category_ids))"
        )
    if tag_ids is not None:
        clauses.append(
            "EXISTS (SELECT 1 FROM document_source_tags AS tag_link "
            "WHERE tag_link.document_source_id = source.id "
            "AND tag_link.tag_id = ANY(:tag_ids))"
        )
    if project_ids is not None:
        clauses.append(
            "EXISTS (SELECT 1 FROM document_source_projects AS project_link "
            "WHERE project_link.document_source_id = source.id "
            "AND project_link.project_id = ANY(:project_ids))"
        )
    return (
        "SELECT chunk.id "
        "FROM knowledge_chunks AS chunk "
        "JOIN document_sources AS source ON source.id = chunk.source_id "
        "JOIN embedding_batches AS batch ON batch.id = chunk.embedding_batch_id "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY chunk.embedding <=> CAST(:query_embedding AS vector), chunk.id "
        "LIMIT :limit"
    )


async def execute_vector_search(
    session: AsyncSession,
    *,
    query_embedding: Sequence[float],
    limit: int,
    config_hash: str,
    category_ids: Sequence[int] | None = None,
    tag_ids: Sequence[int] | None = None,
    project_ids: Sequence[int] | None = None,
) -> list[int]:
    sql = build_vector_search_sql(
        category_ids=category_ids, tag_ids=tag_ids, project_ids=project_ids
    )
    params: dict[str, Any] = {
        "query_embedding": vector_literal(query_embedding),
        "limit": limit,
        "config_hash": config_hash,
    }
    if category_ids is not None:
        params["category_ids"] = list(category_ids)
    if tag_ids is not None:
        params["tag_ids"] = list(tag_ids)
    if project_ids is not None:
        params["project_ids"] = list(project_ids)
    result = await session.execute(text(sql), params)
    return [int(value) for value in result.scalars().all()]


async def explain_vector_search(
    session: AsyncSession,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    sql = build_vector_search_sql(
        category_ids=kwargs.get("category_ids"),
        tag_ids=kwargs.get("tag_ids"),
        project_ids=kwargs.get("project_ids"),
    )
    params: dict[str, Any] = {
        "query_embedding": vector_literal(kwargs["query_embedding"]),
        "limit": kwargs["limit"],
        "config_hash": kwargs["config_hash"],
    }
    for key in ("category_ids", "tag_ids", "project_ids"):
        if kwargs.get(key) is not None:
            params[key] = list(kwargs[key])
    result = await session.execute(
        text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}"), params
    )
    value = result.scalar_one()
    return json.loads(value) if isinstance(value, str) else value


def plan_uses_hnsw(plan: Any) -> bool:
    if isinstance(plan, dict):
        if plan.get("Index Name") == HNSW_INDEX_NAME:
            return True
        return any(plan_uses_hnsw(value) for value in plan.values())
    if isinstance(plan, list):
        return any(plan_uses_hnsw(value) for value in plan)
    return False
