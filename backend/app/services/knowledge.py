from __future__ import annotations

import io
import json
import re
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import DocumentSource, KnowledgeChunk
from ..schemas.knowledge import KnowledgeChunkRead
from .embeddings import EmbeddingClient
from .rag import AnswerClient


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


class KnowledgeIngestionError(ValueError):
    pass


class UnsupportedFileTypeError(KnowledgeIngestionError):
    pass


class FileTooLargeError(KnowledgeIngestionError):
    pass


class EmptyDocumentError(KnowledgeIngestionError):
    pass


def build_pdf_reader(stream: io.BytesIO):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise KnowledgeIngestionError("pypdf is required to extract text from PDF files.") from exc

    return PdfReader(stream)


def extract_pdf_page_text(page: object) -> str:
    extract_text_method = getattr(page, "extract_text")
    try:
        return extract_text_method(extraction_mode="layout") or ""
    except TypeError:
        return extract_text_method() or ""


def validate_upload(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError("Only .txt, .md and .pdf files are supported.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise FileTooLargeError("Uploaded file is larger than 10MB.")
    return extension


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def normalize_pdf_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)

    paragraphs = re.split(r"\n{2,}", text)
    normalized: list[str] = []
    for paragraph in paragraphs:
        lines = [" ".join(line.split()) for line in paragraph.splitlines()]
        paragraph_text = " ".join(line for line in lines if line)
        if paragraph_text:
            normalized.append(paragraph_text)
    return "\n\n".join(normalized)


def extract_text(filename: str, content: bytes) -> str:
    extension = validate_upload(filename, content)

    if extension in {".txt", ".md"}:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise KnowledgeIngestionError("File must be encoded as UTF-8.") from exc
    else:
        reader = build_pdf_reader(io.BytesIO(content))
        text = "\n\n".join(extract_pdf_page_text(page) for page in reader.pages)
        text = normalize_pdf_text(text)

    if extension in {".txt", ".md"}:
        text = normalize_text(text)
    if not text:
        raise EmptyDocumentError("Uploaded document does not contain readable text.")
    return text


def find_chunk_end(text: str, start: int, max_end: int, chunk_size: int) -> int:
    if max_end == len(text):
        return max_end

    min_end = start + max(chunk_size // 2, 1)
    for separator in ("\n\n", "\n", ". ", "; ", ", ", " "):
        boundary = text.rfind(separator, min_end, max_end)
        if boundary != -1:
            return boundary + len(separator)
    return max_end


def find_chunk_start(text: str, start: int) -> int:
    while start < len(text) and text[start].isspace():
        start += 1
    return start


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap.")

    chunks: list[str] = []
    start = 0
    while start < len(text):
        max_end = min(start + chunk_size, len(text))
        end = find_chunk_end(text, start, max_end, chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = find_chunk_start(text, max(end - overlap, 0))
    return chunks


async def ingest_uploaded_file(
    session: AsyncSession,
    filename: str,
    content: bytes,
    category: str,
    embedding_client: EmbeddingClient,
) -> tuple[DocumentSource, int]:
    normalized_category = category.strip()
    if not normalized_category:
        raise KnowledgeIngestionError("Category must not be empty.")

    text = extract_text(filename, content)
    uri = f"upload:{normalized_category}:{filename}"
    return await ingest_text_source(
        session=session,
        title=filename,
        text=text,
        category=normalized_category,
        source_type="upload",
        uri=uri,
        embedding_client=embedding_client,
    )


async def ingest_plain_text(
    session: AsyncSession,
    title: str,
    content: str,
    category: str,
    embedding_client: EmbeddingClient,
) -> tuple[DocumentSource, int]:
    normalized_title = title.strip()
    normalized_category = category.strip()
    if not normalized_title:
        raise KnowledgeIngestionError("Title must not be empty.")
    if not normalized_category:
        raise KnowledgeIngestionError("Category must not be empty.")
    text = normalize_text(content)
    if not text:
        raise EmptyDocumentError("Text content does not contain readable text.")

    uri = f"text:{normalized_category}:{normalized_title}"
    return await ingest_text_source(
        session=session,
        title=normalized_title,
        text=text,
        category=normalized_category,
        source_type="text",
        uri=uri,
        embedding_client=embedding_client,
    )


async def ingest_text_source(
    session: AsyncSession,
    title: str,
    text: str,
    category: str,
    source_type: str,
    uri: str,
    embedding_client: EmbeddingClient,
) -> tuple[DocumentSource, int]:
    chunks = chunk_text(text)
    embeddings = await embedding_client.embed_texts(chunks)

    existing_source = await session.scalar(
        select(DocumentSource).where(DocumentSource.uri == uri)
    )
    if existing_source is not None:
        await session.execute(
            delete(KnowledgeChunk).where(KnowledgeChunk.source_id == existing_source.id)
        )
        source = existing_source
        source.title = title
        source.category = category
        source.source_type = source_type
    else:
        source = DocumentSource(
            title=title,
            category=category,
            source_type=source_type,
            uri=uri,
        )
        session.add(source)
        await session.flush()

    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
        session.add(
            KnowledgeChunk(
                source_id=source.id,
                content=chunk,
                metadata_json=json.dumps(
                    {
                        "title": title,
                        "category": category,
                        "source_type": source_type,
                        "chunk_index": index,
                    }
                ),
                embedding=embedding,
            )
        )

    await session.commit()
    await session.refresh(source)
    return source, len(chunks)


async def search_knowledge(
    session: AsyncSession,
    query: str,
    limit: int,
    embedding_client: EmbeddingClient,
    category: str | None = None,
) -> list[KnowledgeChunkRead]:
    query_embedding = (await embedding_client.embed_texts([query]))[0]
    distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)

    statement = (
        select(
            KnowledgeChunk.id,
            KnowledgeChunk.source_id,
            KnowledgeChunk.content,
            distance.label("distance"),
        )
        .join(DocumentSource, KnowledgeChunk.source_id == DocumentSource.id)
        .where(KnowledgeChunk.embedding.is_not(None))
    )
    if category is not None:
        statement = statement.where(DocumentSource.category == category.strip())
    statement = statement.order_by(distance).limit(limit)

    rows = (await session.execute(statement)).all()
    return [
        KnowledgeChunkRead(
            id=row.id,
            source_id=row.source_id,
            content=row.content,
            score=1 - float(row.distance),
        )
        for row in rows
    ]


async def answer_knowledge(
    session: AsyncSession,
    query: str,
    limit: int,
    embedding_client: EmbeddingClient,
    answer_client: AnswerClient,
    category: str | None = None,
) -> tuple[str, list[KnowledgeChunkRead]]:
    sources = await search_knowledge(
        session, query, limit, embedding_client, category=category
    )
    answer = await answer_client.answer(query, sources)
    return answer, sources


async def list_sources(session: AsyncSession) -> list[dict[str, str | int]]:
    rows = (
        await session.execute(
            select(
                DocumentSource.id,
                DocumentSource.title,
                DocumentSource.category,
                DocumentSource.source_type,
                DocumentSource.uri,
            )
            .order_by(DocumentSource.created_at.desc())
        )
    ).all()

    return [
        {
            "id": row.id,
            "title": row.title,
            "category": row.category,
            "source_type": row.source_type,
            "uri": row.uri,
        }
        for row in rows
    ]
