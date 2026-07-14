from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import DocumentSource


async def get_source_by_uri(session: AsyncSession, uri: str) -> DocumentSource | None:
    return await session.scalar(select(DocumentSource).where(DocumentSource.uri == uri))


async def list_sources(session: AsyncSession) -> list[dict[str, str | int]]:
    rows = (
        await session.execute(
            select(
                DocumentSource.id,
                DocumentSource.title,
                DocumentSource.category_id,
                DocumentSource.source_type,
                DocumentSource.uri,
            )
            .order_by(DocumentSource.created_at.desc())
        )
    ).all()

    return [
        {
            "id": row.id,
            "title": row.title,
            "category_id": row.category_id,
            "source_type": row.source_type,
            "uri": row.uri,
        }
        for row in rows
    ]
