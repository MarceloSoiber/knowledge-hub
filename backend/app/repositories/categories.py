from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Category


async def get_category(session: AsyncSession, category_id: int) -> Category | None:
    return await session.get(Category, category_id)


async def get_category_by_name(session: AsyncSession, name: str) -> Category | None:
    return await session.scalar(select(Category).where(func.lower(Category.name) == name))


async def list_categories_by_ids(session: AsyncSession, category_ids: list[int]) -> list[Category]:
    rows = (
        await session.execute(select(Category).where(Category.id.in_(category_ids)))
    ).scalars()
    return list(rows)


async def list_categories(session: AsyncSession) -> list[dict[str, str | int]]:
    rows = (
        await session.execute(select(Category.id, Category.name).order_by(Category.name))
    ).all()
    return [{"id": row.id, "name": row.name} for row in rows]
