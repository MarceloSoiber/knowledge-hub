from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Category
from ..repositories.categories import get_category as get_category_record
from ..repositories.categories import list_categories as list_category_records


class CategoryNotFoundError(ValueError):
    pass


async def get_category(session: AsyncSession, category_id: int) -> Category:
    category = await get_category_record(session, category_id)
    if category is None:
        raise CategoryNotFoundError(f"Category {category_id} does not exist.")
    return category


async def list_categories(session: AsyncSession) -> list[dict[str, str | int]]:
    return await list_category_records(session)
