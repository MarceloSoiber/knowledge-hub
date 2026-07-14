from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Category, DocumentSource
from ..repositories.chunks import add_source_chunks, delete_chunks_for_source
from ..repositories.sources import get_source_by_uri
from .categories import CategoryNotFoundError, get_category
from .documents.chunker import chunk_text
from .documents.extractors import (
    DocumentExtractionError,
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    extract_text,
)
from .documents.normalizer import normalize_text
from .embeddings import EmbeddingClient


class KnowledgeIngestionError(ValueError):
    pass


async def ingest_uploaded_file(
    session: AsyncSession,
    filename: str,
    content: bytes,
    category_id: int,
    embedding_client: EmbeddingClient,
) -> tuple[DocumentSource, int]:
    category = await get_category(session, category_id)

    try:
        text = extract_text(filename, content)
    except (EmptyDocumentError, FileTooLargeError, UnsupportedFileTypeError):
        raise
    except DocumentExtractionError as exc:
        raise KnowledgeIngestionError(str(exc)) from exc

    uri = f"upload:{category.name}:{filename}"
    return await ingest_text_source(
        session=session,
        title=filename,
        text=text,
        category=category,
        source_type="upload",
        uri=uri,
        embedding_client=embedding_client,
    )


async def ingest_plain_text(
    session: AsyncSession,
    title: str,
    content: str,
    category_id: int,
    embedding_client: EmbeddingClient,
) -> tuple[DocumentSource, int]:
    normalized_title = title.strip()
    if not normalized_title:
        raise KnowledgeIngestionError("Title must not be empty.")
    category = await get_category(session, category_id)
    text = normalize_text(content)
    if not text:
        raise EmptyDocumentError("Text content does not contain readable text.")

    uri = f"text:{category.name}:{normalized_title}"
    return await ingest_text_source(
        session=session,
        title=normalized_title,
        text=text,
        category=category,
        source_type="text",
        uri=uri,
        embedding_client=embedding_client,
    )


async def ingest_text_source(
    session: AsyncSession,
    title: str,
    text: str,
    category: Category,
    source_type: str,
    uri: str,
    embedding_client: EmbeddingClient,
) -> tuple[DocumentSource, int]:
    chunks = chunk_text(text)
    embeddings = await embedding_client.embed_texts(chunks)

    existing_source = await get_source_by_uri(session, uri)
    if existing_source is not None:
        await delete_chunks_for_source(session, existing_source.id)
        source = existing_source
        source.title = title
        source.category_id = category.id
        source.source_type = source_type
    else:
        source = DocumentSource(
            title=title,
            category_id=category.id,
            source_type=source_type,
            uri=uri,
        )
        session.add(source)
        await session.flush()

    metadata = [
        json.dumps(
            {
                "title": title,
                "category_id": category.id,
                "category": category.name,
                "source_type": source_type,
                "chunk_index": index,
            }
        )
        for index, _ in enumerate(chunks)
    ]
    add_source_chunks(session, source.id, chunks, embeddings, metadata)

    await session.commit()
    await session.refresh(source)
    return source, len(chunks)
