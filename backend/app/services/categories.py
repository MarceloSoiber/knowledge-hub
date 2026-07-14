from __future__ import annotations

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Category, document_source_categories
from ..repositories.categories import get_category as get_category_record
from ..repositories.categories import get_category_by_name
from ..repositories.categories import list_categories_by_ids
from ..repositories.categories import list_categories as list_category_records


class CategoryNotFoundError(ValueError):
    pass


class CategoryConflictError(ValueError):
    pass


class CategoryInUseError(ValueError):
    pass


def normalize_category_name(name: str) -> str:
    return name.strip().lower()


async def get_category(session: AsyncSession, category_id: int) -> Category:
    category = await get_category_record(session, category_id)
    if category is None:
        raise CategoryNotFoundError(f"Category {category_id} does not exist.")
    return category


async def get_categories(session: AsyncSession, category_ids: list[int]) -> list[Category]:
    categories = await list_categories_by_ids(session, category_ids)
    categories_by_id = {category.id: category for category in categories}
    missing_ids = [category_id for category_id in category_ids if category_id not in categories_by_id]
    if missing_ids:
        raise CategoryNotFoundError(f"Category {missing_ids[0]} does not exist.")
    return [categories_by_id[category_id] for category_id in category_ids]


async def list_categories(session: AsyncSession) -> list[dict[str, str | int]]:
    return await list_category_records(session)


async def create_category(session: AsyncSession, name: str) -> Category:
    normalized_name = normalize_category_name(name)
    if await get_category_by_name(session, normalized_name) is not None:
        raise CategoryConflictError(f"Category '{normalized_name}' already exists.")

    category = Category(name=normalized_name)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def update_category(session: AsyncSession, category_id: int, name: str) -> Category:
    category = await get_category(session, category_id)
    normalized_name = normalize_category_name(name)
    existing = await get_category_by_name(session, normalized_name)
    if existing is not None and existing.id != category.id:
        raise CategoryConflictError(f"Category '{normalized_name}' already exists.")

    category.name = normalized_name
    await session.commit()
    await session.refresh(category)
    return category


async def delete_category(session: AsyncSession, category_id: int) -> None:
    category = await get_category(session, category_id)
    in_use = await session.scalar(
        select(
            exists().where(document_source_categories.c.category_id == category.id)
        )
    )
    if in_use:
        raise CategoryInUseError(f"Category {category_id} is in use.")

    await session.execute(delete(Category).where(Category.id == category.id))
    await session.commit()
