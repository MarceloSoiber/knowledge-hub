from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Tag


async def get_tag(session: AsyncSession, tag_id: int) -> Tag | None:
    return await session.get(Tag, tag_id)


async def get_tag_by_normalized_name(
    session: AsyncSession, normalized_name: str
) -> Tag | None:
    return await session.scalar(
        select(Tag).where(Tag.normalized_name == normalized_name)
    )


async def list_tags_by_ids(session: AsyncSession, tag_ids: list[int]) -> list[Tag]:
    rows = (
        (
            await session.execute(
                select(Tag).where(Tag.id.in_(tag_ids))
            )
        )
        .scalars()
        .all()
    )
    return list(rows)


async def list_tags(session: AsyncSession) -> list[dict[str, str | int]]:
    rows = (
        (
            await session.execute(select(Tag).order_by(Tag.name))
        )
        .scalars()
        .all()
    )
    return [{"id": tag.id, "name": tag.name} for tag in rows]


async def autocomplete_tags(
    session: AsyncSession,
    normalized_prefix: str,
    limit: int,
) -> list[dict[str, str | int]]:
    rows = (
        (
            await session.execute(
                select(Tag)
                .where(Tag.normalized_name.startswith(normalized_prefix))
                .order_by(Tag.name)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return [{"id": tag.id, "name": tag.name} for tag in rows]
