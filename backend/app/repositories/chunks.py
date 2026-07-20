from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from sqlalchemy import delete, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.models import (
    DocumentSource,
    KnowledgeChunk,
    document_source_categories,
    document_source_projects,
    document_source_tags,
)
from ..schemas.knowledge import KnowledgeChunkRead

PUBLIC_METADATA_KEYS = {"client_id", "note_type"}
TEXT_SEARCH_CONFIG = "simple"


@dataclass(frozen=True)
class TextSearchChunk:
    chunk: KnowledgeChunkRead
    text_rank: float


async def delete_chunks_for_source(session: AsyncSession, source_id: int) -> None:
    await session.execute(delete(KnowledgeChunk).where(KnowledgeChunk.source_id == source_id))


def add_source_chunks(
    session: AsyncSession,
    source_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
    metadata: list[dict[str, Any]],
) -> None:
    for chunk, embedding, metadata_json in zip(chunks, embeddings, metadata, strict=True):
        session.add(
            KnowledgeChunk(
                source_id=source_id,
                content=chunk,
                metadata_json=metadata_json,
                embedding=embedding,
            )
        )


async def search_similar_chunks(
    session: AsyncSession,
    query_embedding: list[float],
    limit: int,
    category_ids: list[int] | None = None,
    tag_ids: list[int] | None = None,
    project_ids: list[int] | None = None,
) -> list[KnowledgeChunkRead]:
    distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)

    statement = (
        select(
            KnowledgeChunk,
            DocumentSource,
            distance.label("distance"),
        )
        .join(DocumentSource, KnowledgeChunk.source_id == DocumentSource.id)
        .options(
            selectinload(DocumentSource.categories),
            selectinload(DocumentSource.tags),
            selectinload(DocumentSource.projects),
        )
        .where(KnowledgeChunk.embedding.is_not(None))
    )
    if category_ids is not None:
        statement = statement.where(
            exists()
            .where(document_source_categories.c.document_source_id == DocumentSource.id)
            .where(document_source_categories.c.category_id.in_(category_ids))
        )
    if tag_ids is not None:
        statement = statement.where(
            exists()
            .where(document_source_tags.c.document_source_id == DocumentSource.id)
            .where(document_source_tags.c.tag_id.in_(tag_ids))
        )
    if project_ids is not None:
        statement = statement.where(
            exists()
            .where(document_source_projects.c.document_source_id == DocumentSource.id)
            .where(document_source_projects.c.project_id.in_(project_ids))
        )
    statement = statement.order_by(distance).limit(limit)

    rows = (await session.execute(statement)).all()
    return [
        build_chunk_read(row)
        for row in rows
    ]


async def search_text_chunks(
    session: AsyncSession,
    query: str,
    limit: int,
    category_ids: list[int] | None = None,
    tag_ids: list[int] | None = None,
    project_ids: list[int] | None = None,
) -> list[TextSearchChunk]:
    ts_query = func.plainto_tsquery(TEXT_SEARCH_CONFIG, query)
    text_rank = func.ts_rank_cd(KnowledgeChunk.search_vector, ts_query)

    statement = (
        select(
            KnowledgeChunk,
            DocumentSource,
            text_rank.label("text_rank"),
        )
        .join(DocumentSource, KnowledgeChunk.source_id == DocumentSource.id)
        .options(
            selectinload(DocumentSource.categories),
            selectinload(DocumentSource.tags),
            selectinload(DocumentSource.projects),
        )
        .where(KnowledgeChunk.search_vector.op("@@")(ts_query))
    )
    if category_ids is not None:
        statement = statement.where(
            exists()
            .where(document_source_categories.c.document_source_id == DocumentSource.id)
            .where(document_source_categories.c.category_id.in_(category_ids))
        )
    if tag_ids is not None:
        statement = statement.where(
            exists()
            .where(document_source_tags.c.document_source_id == DocumentSource.id)
            .where(document_source_tags.c.tag_id.in_(tag_ids))
        )
    if project_ids is not None:
        statement = statement.where(
            exists()
            .where(document_source_projects.c.document_source_id == DocumentSource.id)
            .where(document_source_projects.c.project_id.in_(project_ids))
        )
    statement = statement.order_by(text_rank.desc(), KnowledgeChunk.id).limit(limit)

    rows = (await session.execute(statement)).all()
    return [
        TextSearchChunk(
            chunk=build_text_chunk_read(row),
            text_rank=float(get_row_value(row, "text_rank", 2) or 0.0),
        )
        for row in rows
    ]


def build_chunk_read(row: object) -> KnowledgeChunkRead:
    chunk = get_row_value(row, "KnowledgeChunk", 0)
    source = get_row_value(row, "DocumentSource", 1)
    distance = get_row_value(row, "distance", 2)
    metadata = normalize_metadata(getattr(chunk, "metadata_json", None))
    return KnowledgeChunkRead(
        id=getattr(chunk, "id"),
        source_id=getattr(source, "public_id"),
        source_title=getattr(source, "title"),
        source_type=getattr(source, "source_type"),
        uri=sanitize_uri(
            getattr(source, "uri"),
            getattr(source, "source_type"),
            getattr(source, "title"),
        ),
        categories=[
            {"id": category.id, "name": category.name}
            for category in sorted(getattr(source, "categories", []), key=lambda category: category.name)
        ],
        tags=[
            {"id": tag.id, "name": tag.name}
            for tag in sorted(getattr(source, "tags", []), key=lambda tag: tag.name)
        ],
        projects=[
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
            }
            for project in sorted(getattr(source, "projects", []), key=lambda project: project.name)
        ],
        location=build_location(metadata, getattr(chunk, "content")),
        content=getattr(chunk, "content"),
        score=1 - float(distance),
        metadata=public_metadata(metadata),
    )


def build_text_chunk_read(row: object) -> KnowledgeChunkRead:
    chunk = get_row_value(row, "KnowledgeChunk", 0)
    source = get_row_value(row, "DocumentSource", 1)
    metadata = normalize_metadata(getattr(chunk, "metadata_json", None))
    return KnowledgeChunkRead(
        id=getattr(chunk, "id"),
        source_id=getattr(source, "public_id"),
        source_title=getattr(source, "title"),
        source_type=getattr(source, "source_type"),
        uri=sanitize_uri(
            getattr(source, "uri"),
            getattr(source, "source_type"),
            getattr(source, "title"),
        ),
        categories=[
            {"id": category.id, "name": category.name}
            for category in sorted(getattr(source, "categories", []), key=lambda category: category.name)
        ],
        tags=[
            {"id": tag.id, "name": tag.name}
            for tag in sorted(getattr(source, "tags", []), key=lambda tag: tag.name)
        ],
        projects=[
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
            }
            for project in sorted(getattr(source, "projects", []), key=lambda project: project.name)
        ],
        location=build_location(metadata, getattr(chunk, "content")),
        content=getattr(chunk, "content"),
        score=None,
        metadata=public_metadata(metadata),
    )


def get_row_value(row: object, name: str, index: int) -> object:
    if hasattr(row, name):
        return getattr(row, name)
    try:
        return row[index]  # type: ignore[index]
    except (IndexError, TypeError):
        return getattr(row, name.lower())


def normalize_metadata(value: object) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def build_location(metadata: dict[str, Any], content: str) -> dict[str, Any]:
    location = metadata.get("location")
    if not isinstance(location, dict):
        location = {}
    return {
        "chunk_index": int(location.get("chunk_index", metadata.get("chunk_index", 0)) or 0),
        "page": optional_int(location.get("page")),
        "section": optional_str(location.get("section")),
        "start_char": int(location.get("start_char", 0) or 0),
        "end_char": int(location.get("end_char", len(content)) or len(content)),
    }


def public_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    raw = metadata.get("metadata", {})
    if not isinstance(raw, dict):
        return {}
    return {
        key: value
        for key, value in raw.items()
        if key in PUBLIC_METADATA_KEYS and isinstance(value, str)
    }


def optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def optional_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def sanitize_uri(uri: str, source_type: str, title: str) -> str:
    if uri.startswith("file:"):
        return f"{source_type}:{Path(uri.removeprefix('file:')).name or title}"
    if uri.startswith("/"):
        return f"{source_type}:{Path(uri).name or title}"
    return uri
