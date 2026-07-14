from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.chunks import search_similar_chunks
from ..repositories.sources import list_sources as list_source_records
from ..schemas.knowledge import KnowledgeChunkRead
from .embeddings import EmbeddingClient
from .rag import AnswerClient


async def search_knowledge(
    session: AsyncSession,
    query: str,
    limit: int,
    embedding_client: EmbeddingClient,
    category_id: int | None = None,
) -> list[KnowledgeChunkRead]:
    query_embedding = (await embedding_client.embed_texts([query]))[0]
    return await search_similar_chunks(
        session=session,
        query_embedding=query_embedding,
        limit=limit,
        category_id=category_id,
    )


async def answer_knowledge(
    session: AsyncSession,
    query: str,
    limit: int,
    embedding_client: EmbeddingClient,
    answer_client: AnswerClient,
    category_id: int | None = None,
) -> tuple[str, list[KnowledgeChunkRead]]:
    sources = await search_knowledge(
        session, query, limit, embedding_client, category_id=category_id
    )
    answer = await answer_client.answer(query, sources)
    return answer, sources


async def list_sources(session: AsyncSession) -> list[dict[str, str | int]]:
    return await list_source_records(session)
