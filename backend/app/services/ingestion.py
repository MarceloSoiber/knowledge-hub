from __future__ import annotations

import json
from hashlib import sha256

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Category, DocumentSource
from ..repositories.chunks import add_source_chunks
from ..repositories.sources import get_source_by_content_hash
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


class DuplicateSourceContentError(KnowledgeIngestionError):
    def __init__(self, existing_source: DocumentSource) -> None:
        self.existing_source = existing_source
        super().__init__(
            "A source with identical content already exists: "
            f"{existing_source.public_id}."
        )


def compute_content_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


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
    content_hash = compute_content_hash(text)
    existing_source = await get_source_by_content_hash(session, content_hash)
    if existing_source is not None:
        raise DuplicateSourceContentError(existing_source)

    chunks = chunk_text(text)
    embeddings = await embedding_client.embed_texts(chunks)

    source = DocumentSource(
        title=title,
        source_type=source_type,
        uri=uri,
        content_text=text,
        content_hash=content_hash,
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
    return source, len(chunks)
