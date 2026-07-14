from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.models import DocumentSource


async def get_source_by_uri(session: AsyncSession, uri: str) -> DocumentSource | None:
    return await session.scalar(
        select(DocumentSource)
        .options(selectinload(DocumentSource.categories))
        .where(DocumentSource.uri == uri)
    )


async def list_sources(session: AsyncSession) -> list[dict[str, object]]:
    rows = (
        (
            await session.execute(
                select(DocumentSource)
                .options(selectinload(DocumentSource.categories))
                .order_by(DocumentSource.created_at.desc())
            )
        )
        .scalars()
        .all()
    )

    return [
        {
            "id": source.id,
            "title": source.title,
            "categories": [
                {"id": category.id, "name": category.name}
                for category in sorted(source.categories, key=lambda category: category.name)
            ],
            "source_type": source.source_type,
            "uri": source.uri,
        }
        for source in rows
    ]
