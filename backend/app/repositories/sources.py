from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.models import DocumentSource


def _source_options() -> tuple[object, ...]:
    return (
        selectinload(DocumentSource.categories),
        selectinload(DocumentSource.tags),
        selectinload(DocumentSource.projects),
    )


async def get_source_by_public_id(
    session: AsyncSession, public_id: str
) -> DocumentSource | None:
    return await session.scalar(
        select(DocumentSource)
        .options(*_source_options())
        .where(DocumentSource.public_id == public_id)
    )


async def get_source_by_content_hash(
    session: AsyncSession, content_hash: str, exclude_source_id: int | None = None
) -> DocumentSource | None:
    statement = (
        select(DocumentSource)
        .options(*_source_options())
        .where(DocumentSource.content_hash == content_hash)
    )
    if exclude_source_id is not None:
        statement = statement.where(DocumentSource.id != exclude_source_id)
    return await session.scalar(statement)


async def delete_source_by_id(session: AsyncSession, source_id: int) -> None:
    await session.execute(delete(DocumentSource).where(DocumentSource.id == source_id))


def serialize_source(source: DocumentSource, include_content: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_id": source.public_id,
        "title": source.title,
        "categories": [
            {"id": category.id, "name": category.name}
            for category in sorted(source.categories, key=lambda category: category.name)
        ],
        "tags": [
            {"id": tag.id, "name": tag.name}
            for tag in sorted(source.tags, key=lambda tag: tag.name)
        ],
        "projects": [
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
            }
            for project in sorted(source.projects, key=lambda project: project.name)
        ],
        "source_type": source.source_type,
        "uri": source.uri,
        "content_hash": source.content_hash,
        "created_at": source.created_at,
        "updated_at": source.updated_at,
    }
    if include_content:
        payload["content"] = source.content_text
    return payload


async def list_sources(session: AsyncSession) -> list[dict[str, object]]:
    rows = (
        (
            await session.execute(
                select(DocumentSource)
                .options(*_source_options())
                .order_by(DocumentSource.created_at.desc())
            )
        )
        .scalars()
        .all()
    )

    return [serialize_source(source) for source in rows]
