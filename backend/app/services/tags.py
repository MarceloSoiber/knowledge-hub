from __future__ import annotations

import unicodedata

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Tag, document_source_tags
from ..repositories.tags import autocomplete_tags as autocomplete_tag_records
from ..repositories.tags import get_tag as get_tag_record
from ..repositories.tags import get_tag_by_normalized_name
from ..repositories.tags import list_tags as list_tag_records
from ..repositories.tags import list_tags_by_ids


class TagNotFoundError(ValueError):
    pass


class TagConflictError(ValueError):
    pass


class TagInUseError(ValueError):
    pass


def normalize_tag_name(name: str) -> str:
    collapsed = " ".join(name.strip().lower().split())
    decomposed = unicodedata.normalize("NFKD", collapsed)
    return "".join(character for character in decomposed if not unicodedata.combining(character))


async def get_tag(session: AsyncSession, tag_id: int) -> Tag:
    tag = await get_tag_record(session, tag_id)
    if tag is None:
        raise TagNotFoundError(f"Tag {tag_id} does not exist.")
    return tag


async def get_tags(session: AsyncSession, tag_ids: list[int]) -> list[Tag]:
    tags = await list_tags_by_ids(session, tag_ids)
    tags_by_id = {tag.id: tag for tag in tags}
    missing_ids = [tag_id for tag_id in tag_ids if tag_id not in tags_by_id]
    if missing_ids:
        raise TagNotFoundError(f"Tag {missing_ids[0]} does not exist.")
    return [tags_by_id[tag_id] for tag_id in tag_ids]


async def list_tags(session: AsyncSession) -> list[dict[str, str | int]]:
    return await list_tag_records(session)


async def autocomplete_tags(
    session: AsyncSession, query: str, limit: int
) -> list[dict[str, str | int]]:
    normalized_query = normalize_tag_name(query)
    if not normalized_query:
        return []
    return await autocomplete_tag_records(session, normalized_query, limit)


async def create_tag(session: AsyncSession, name: str) -> Tag:
    normalized_name = normalize_tag_name(name)
    if not normalized_name:
        raise ValueError("Tag name must not be empty.")
    if await get_tag_by_normalized_name(session, normalized_name) is not None:
        raise TagConflictError(f"Tag '{normalized_name}' already exists.")

    tag = Tag(name=normalized_name, normalized_name=normalized_name)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag


async def update_tag(session: AsyncSession, tag_id: int, name: str) -> Tag:
    tag = await get_tag(session, tag_id)
    normalized_name = normalize_tag_name(name)
    if not normalized_name:
        raise ValueError("Tag name must not be empty.")
    existing = await get_tag_by_normalized_name(session, normalized_name)
    if existing is not None and existing.id != tag.id:
        raise TagConflictError(f"Tag '{normalized_name}' already exists.")

    tag.name = normalized_name
    tag.normalized_name = normalized_name
    await session.commit()
    await session.refresh(tag)
    return tag


async def delete_tag(session: AsyncSession, tag_id: int) -> None:
    tag = await get_tag(session, tag_id)
    in_use = await session.scalar(
        select(exists().where(document_source_tags.c.tag_id == tag.id))
    )
    if in_use:
        raise TagInUseError(f"Tag {tag_id} is in use.")

    await session.execute(delete(Tag).where(Tag.id == tag.id))
    await session.commit()
