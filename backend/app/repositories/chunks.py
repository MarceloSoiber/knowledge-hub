from __future__ import annotations

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import DocumentSource, KnowledgeChunk, document_source_categories
from ..schemas.knowledge import KnowledgeChunkRead


async def delete_chunks_for_source(session: AsyncSession, source_id: int) -> None:
    await session.execute(delete(KnowledgeChunk).where(KnowledgeChunk.source_id == source_id))


def add_source_chunks(
    session: AsyncSession,
    source_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
    metadata: list[str],
) -> None:
    for chunk, embedding, metadata_json in zip(chunks, embeddings, metadata, strict=True):
        session.add(
            KnowledgeChunk(
                source_id=source_id,
                content=chunk,
                metadata_json=metadata_json,
                embedding=embedding,
            )
        )


async def search_similar_chunks(
    session: AsyncSession,
    query_embedding: list[float],
    limit: int,
    category_ids: list[int] | None = None,
) -> list[KnowledgeChunkRead]:
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
    if category_ids is not None:
        statement = statement.where(
            exists()
            .where(document_source_categories.c.document_source_id == DocumentSource.id)
            .where(document_source_categories.c.category_id.in_(category_ids))
        )
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
