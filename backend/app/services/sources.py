from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import DocumentSource
from ..repositories.chunks import add_source_chunks, delete_chunks_for_source
from ..repositories.sources import (
    delete_source_by_id,
    get_source_by_content_hash,
    get_source_by_public_id,
    serialize_source,
)
from .categories import get_categories
from .documents.chunker import chunk_text_with_locations, detect_markdown_sections
from .documents.extractors import EmptyDocumentError
from .documents.normalizer import normalize_text
from .embeddings import EmbeddingClient
from .ingestion import (
    DuplicateSourceContentError,
    KnowledgeIngestionError,
    build_chunk_metadata,
    compute_content_hash,
)
from .tags import get_tags


class SourceNotFoundError(LookupError):
    pass


class SourceDeleteConfirmationError(ValueError):
    pass


async def get_source_detail(session: AsyncSession, source_id: str) -> dict[str, object]:
    source = await _get_source_or_raise(session, source_id)
    return serialize_source(source, include_content=True)


async def update_source(
    session: AsyncSession,
    source_id: str,
    embedding_client: EmbeddingClient,
    title: str | None = None,
    category_ids: list[int] | None = None,
    tag_ids: list[int] | None = None,
    content: str | None = None,
) -> tuple[dict[str, object], int | None]:
    source = await _get_source_or_raise(session, source_id)
    categories = (
        await get_categories(session, category_ids)
        if category_ids is not None
        else list(source.categories)
    )
    tags = (
        await get_tags(session, tag_ids)
        if tag_ids is not None
        else list(source.tags)
    )
    normalized_title = title.strip() if title is not None else source.title
    if not normalized_title:
        raise KnowledgeIngestionError("Title must not be empty.")

    if content is None:
        source.title = normalized_title
        source.categories = categories
        source.tags = tags
        await session.commit()
        await session.refresh(source)
        return serialize_source(source, include_content=True), None

    text = normalize_text(content)
    if not text:
        raise EmptyDocumentError("Text content does not contain readable text.")

    content_hash = compute_content_hash(text)
    duplicate = await get_source_by_content_hash(
        session, content_hash, exclude_source_id=source.id
    )
    if duplicate is not None:
        raise DuplicateSourceContentError(duplicate)

    chunks = chunk_text_with_locations(text, section_spans=detect_markdown_sections(text))
    chunk_contents = [chunk.content for chunk in chunks]
    embeddings = await embedding_client.embed_texts(chunk_contents)

    source.title = normalized_title
    source.categories = categories
    source.tags = tags
    source.content_text = text
    source.content_hash = content_hash
    await delete_chunks_for_source(session, source.id)
    add_source_chunks(
        session,
        source.id,
        chunk_contents,
        embeddings,
        build_chunk_metadata(
            title=normalized_title,
            categories=categories,
            tags=tags,
            source_type=source.source_type,
            chunks=chunks,
        ),
    )
    await session.commit()
    await session.refresh(source)
    return serialize_source(source, include_content=True), len(chunks)


async def delete_source(session: AsyncSession, source_id: str, confirm: bool) -> None:
    if not confirm:
        raise SourceDeleteConfirmationError("Use confirm=true to delete a source.")
    source = await _get_source_or_raise(session, source_id)
    await delete_source_by_id(session, source.id)
    await session.commit()


async def _get_source_or_raise(session: AsyncSession, source_id: str) -> DocumentSource:
    source = await get_source_by_public_id(session, source_id)
    if source is None:
        raise SourceNotFoundError(f"Source {source_id} does not exist.")
    return source
