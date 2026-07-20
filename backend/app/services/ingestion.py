from __future__ import annotations

from typing import Any
from hashlib import sha256

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Category, DocumentSource, Tag
from ..repositories.chunks import add_source_chunks
from ..repositories.sources import get_source_by_content_hash
from .categories import get_categories
from .documents.chunker import (
    PageSpan,
    SectionSpan,
    TextChunk,
    chunk_text_with_locations,
    detect_markdown_sections,
)
from .documents.extractors import (
    DocumentExtractionError,
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    extract_document,
)
from .documents.normalizer import normalize_text
from .embeddings import EmbeddingClient
from .tags import get_tags


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
    tag_ids: list[int] | None = None,
) -> tuple[DocumentSource, int]:
    categories = await get_categories(session, category_ids)
    tags = await get_tags(session, tag_ids) if tag_ids is not None else []

    try:
        document = extract_document(filename, content)
    except (EmptyDocumentError, FileTooLargeError, UnsupportedFileTypeError):
        raise
    except DocumentExtractionError as exc:
        raise KnowledgeIngestionError(str(exc)) from exc

    uri = f"upload:{filename}"
    return await ingest_text_source(
        session=session,
        title=filename,
        text=document.text,
        categories=categories,
        tags=tags,
        source_type="upload",
        uri=uri,
        embedding_client=embedding_client,
        page_spans=document.page_spans,
        section_spans=detect_markdown_sections(document.text)
        if document.document_type == "md"
        else None,
    )


async def ingest_plain_text(
    session: AsyncSession,
    title: str,
    content: str,
    category_ids: list[int],
    embedding_client: EmbeddingClient,
    tag_ids: list[int] | None = None,
    source_type: str = "text",
    metadata: dict[str, str] | None = None,
) -> tuple[DocumentSource, int]:
    normalized_title = title.strip()
    if not normalized_title:
        raise KnowledgeIngestionError("Title must not be empty.")
    categories = await get_categories(session, category_ids)
    tags = await get_tags(session, tag_ids) if tag_ids is not None else []
    text = normalize_text(content)
    if not text:
        raise EmptyDocumentError("Text content does not contain readable text.")

    uri = f"{source_type}:{normalized_title}"
    return await ingest_text_source(
        session=session,
        title=normalized_title,
        text=text,
        categories=categories,
        tags=tags,
        source_type=source_type,
        uri=uri,
        embedding_client=embedding_client,
        extra_metadata=metadata,
        section_spans=detect_markdown_sections(text),
    )


async def ingest_text_source(
    session: AsyncSession,
    title: str,
    text: str,
    categories: list[Category],
    tags: list[Tag],
    source_type: str,
    uri: str,
    embedding_client: EmbeddingClient,
    extra_metadata: dict[str, str] | None = None,
    page_spans: list[PageSpan] | None = None,
    section_spans: list[SectionSpan] | None = None,
) -> tuple[DocumentSource, int]:
    content_hash = compute_content_hash(text)
    existing_source = await get_source_by_content_hash(session, content_hash)
    if existing_source is not None:
        raise DuplicateSourceContentError(existing_source)

    chunks = chunk_text_with_locations(
        text,
        page_spans=page_spans,
        section_spans=section_spans,
    )
    chunk_contents = [chunk.content for chunk in chunks]
    embeddings = await embedding_client.embed_texts(chunk_contents)

    source = DocumentSource(
        title=title,
        source_type=source_type,
        uri=uri,
        content_text=text,
        content_hash=content_hash,
    )
    source.categories = categories
    source.tags = tags
    session.add(source)
    await session.flush()

    add_source_chunks(
        session,
        source.id,
        chunk_contents,
        embeddings,
        build_chunk_metadata(
            title=title,
            categories=categories,
            tags=tags,
            source_type=source_type,
            chunks=chunks,
            extra_metadata=extra_metadata,
        ),
    )

    await session.commit()
    return source, len(chunks)


def build_chunk_metadata(
    title: str,
    categories: list[object],
    tags: list[object] | None,
    source_type: str,
    chunks: list[TextChunk],
    extra_metadata: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    category_payload = [
        {"id": category.id, "name": category.name}  # type: ignore[attr-defined]
        for category in categories
    ]
    tag_payload = [
        {"id": tag.id, "name": tag.name}  # type: ignore[attr-defined]
        for tag in (tags or [])
    ]
    metadata = []
    for chunk in chunks:
        location = {
            "chunk_index": chunk.location.chunk_index,
            "page": chunk.location.page,
            "section": chunk.location.section,
            "start_char": chunk.location.start_char,
            "end_char": chunk.location.end_char,
        }
        metadata_payload: dict[str, Any] = {
            "title": title,
            "category_ids": [category["id"] for category in category_payload],
            "categories": category_payload,
            "tag_ids": [tag["id"] for tag in tag_payload],
            "tags": tag_payload,
            "source_type": source_type,
            "chunk_index": chunk.location.chunk_index,
            "location": location,
        }
        if extra_metadata:
            metadata_payload["metadata"] = extra_metadata
        metadata.append(metadata_payload)
    return metadata
