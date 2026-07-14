from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Category, DocumentSource
from ..repositories.chunks import add_source_chunks, delete_chunks_for_source
from ..repositories.sources import get_source_by_uri
from .categories import get_categories
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
    category_ids: list[int],
    embedding_client: EmbeddingClient,
) -> tuple[DocumentSource, int]:
    categories = await get_categories(session, category_ids)

    try:
        text = extract_text(filename, content)
    except (EmptyDocumentError, FileTooLargeError, UnsupportedFileTypeError):
        raise
    except DocumentExtractionError as exc:
        raise KnowledgeIngestionError(str(exc)) from exc

    uri = f"upload:{filename}"
    return await ingest_text_source(
        session=session,
        title=filename,
        text=text,
        categories=categories,
        source_type="upload",
        uri=uri,
        embedding_client=embedding_client,
    )


async def ingest_plain_text(
    session: AsyncSession,
    title: str,
    content: str,
    category_ids: list[int],
    embedding_client: EmbeddingClient,
    source_type: str = "text",
    metadata: dict[str, str] | None = None,
) -> tuple[DocumentSource, int]:
    normalized_title = title.strip()
    if not normalized_title:
        raise KnowledgeIngestionError("Title must not be empty.")
    categories = await get_categories(session, category_ids)
    text = normalize_text(content)
    if not text:
        raise EmptyDocumentError("Text content does not contain readable text.")

    uri = f"{source_type}:{normalized_title}"
    return await ingest_text_source(
        session=session,
        title=normalized_title,
        text=text,
        categories=categories,
        source_type=source_type,
        uri=uri,
        embedding_client=embedding_client,
        extra_metadata=metadata,
    )


async def ingest_text_source(
    session: AsyncSession,
    title: str,
    text: str,
    categories: list[Category],
    source_type: str,
    uri: str,
    embedding_client: EmbeddingClient,
    extra_metadata: dict[str, str] | None = None,
) -> tuple[DocumentSource, int]:
    chunks = chunk_text(text)
    embeddings = await embedding_client.embed_texts(chunks)

    existing_source = await get_source_by_uri(session, uri)
    if existing_source is not None:
        await delete_chunks_for_source(session, existing_source.id)
        source = existing_source
        source.title = title
        source.source_type = source_type
        source.categories = categories
    else:
        source = DocumentSource(
            title=title,
            source_type=source_type,
            uri=uri,
        )
        source.categories = categories
        session.add(source)
        await session.flush()

    category_payload = [{"id": category.id, "name": category.name} for category in categories]
    metadata = []
    for index, _ in enumerate(chunks):
        chunk_metadata = {
            "title": title,
            "category_ids": [category.id for category in categories],
            "categories": category_payload,
            "source_type": source_type,
            "chunk_index": index,
        }
        if extra_metadata:
            chunk_metadata["metadata"] = extra_metadata
        metadata.append(json.dumps(chunk_metadata))
    add_source_chunks(session, source.id, chunks, embeddings, metadata)

    await session.commit()
    await session.refresh(source)
    return source, len(chunks)
