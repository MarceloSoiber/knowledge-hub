from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.chunks import search_similar_chunks
from ..repositories.sources import list_sources as list_source_records
from ..schemas.knowledge import KnowledgeChunkRead
from .categories import get_categories
from .embeddings import EmbeddingClient
from .rag import AnswerClient


async def search_knowledge(
    session: AsyncSession,
    query: str,
    limit: int,
    embedding_client: EmbeddingClient,
    category_ids: list[int] | None = None,
) -> list[KnowledgeChunkRead]:
    if category_ids is not None:
        await get_categories(session, category_ids)
    query_embedding = (await embedding_client.embed_texts([query]))[0]
    return await search_similar_chunks(
        session=session,
        query_embedding=query_embedding,
        limit=limit,
        category_ids=category_ids,
    )


async def answer_knowledge(
    session: AsyncSession,
    query: str,
    limit: int,
    embedding_client: EmbeddingClient,
    answer_client: AnswerClient,
    category_ids: list[int] | None = None,
) -> tuple[str, list[KnowledgeChunkRead]]:
    sources = await search_knowledge(
        session, query, limit, embedding_client, category_ids=category_ids
    )
    answer = await answer_client.answer(query, sources)
    return answer, sources


async def list_sources(session: AsyncSession) -> list[dict[str, object]]:
    return await list_source_records(session)
