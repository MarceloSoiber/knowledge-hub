from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Category


async def get_category(session: AsyncSession, category_id: int) -> Category | None:
    return await session.get(Category, category_id)


async def list_categories(session: AsyncSession) -> list[dict[str, str | int]]:
    rows = (
        await session.execute(select(Category.id, Category.name).order_by(Category.name))
    ).all()
    return [{"id": row.id, "name": row.name} for row in rows]
