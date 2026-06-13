from __future__ import annotations

import io
import json
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


def validate_upload(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError("Only .txt, .md and .pdf files are supported.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise FileTooLargeError("Uploaded file is larger than 10MB.")
    return extension


def extract_text(filename: str, content: bytes) -> str:
    extension = validate_upload(filename, content)

    if extension in {".txt", ".md"}:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise KnowledgeIngestionError("File must be encoded as UTF-8.") from exc
    else:
        reader = build_pdf_reader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not text:
        raise EmptyDocumentError("Uploaded document does not contain readable text.")
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap.")

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = end - overlap
    return chunks


async def ingest_uploaded_file(
    session: AsyncSession,
    filename: str,
    content: bytes,
    embedding_client: EmbeddingClient,
) -> tuple[DocumentSource, int]:
    text = extract_text(filename, content)
    chunks = chunk_text(text)
    embeddings = await embedding_client.embed_texts(chunks)
    uri = f"upload:{filename}"

    existing_source = await session.scalar(
        select(DocumentSource).where(DocumentSource.uri == uri)
    )
    if existing_source is not None:
        await session.execute(
            delete(KnowledgeChunk).where(KnowledgeChunk.source_id == existing_source.id)
        )
        source = existing_source
        source.title = filename
        source.source_type = "upload"
    else:
        source = DocumentSource(title=filename, source_type="upload", uri=uri)
        session.add(source)
        await session.flush()

    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
        session.add(
            KnowledgeChunk(
                source_id=source.id,
                content=chunk,
                metadata_json=json.dumps({"filename": filename, "chunk_index": index}),
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
        .where(KnowledgeChunk.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    )

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
) -> tuple[str, list[KnowledgeChunkRead]]:
    sources = await search_knowledge(session, query, limit, embedding_client)
    answer = await answer_client.answer(query, sources)
    return answer, sources


async def list_sources(session: AsyncSession) -> list[dict[str, str | int]]:
    rows = (
        await session.execute(
            select(
                DocumentSource.id,
                DocumentSource.title,
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
            "source_type": row.source_type,
            "uri": row.uri,
        }
        for row in rows
    ]
