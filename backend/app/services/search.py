from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.settings import get_settings
from ..repositories.chunks import search_similar_chunks
from ..repositories.sources import list_sources as list_source_records
from ..schemas.knowledge import KnowledgeChunkRead
from .categories import get_categories
from .embeddings import EmbeddingClient
from .rag import AnswerClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolvedSearchThreshold:
    value: float
    source: str


async def search_knowledge(
    session: AsyncSession,
    query: str,
    limit: int,
    embedding_client: EmbeddingClient,
    category_ids: list[int] | None = None,
    min_score: float | None = None,
) -> list[KnowledgeChunkRead]:
    if category_ids is not None:
        await get_categories(session, category_ids)
    query_embedding = (await embedding_client.embed_texts([query]))[0]
    results = await search_similar_chunks(
        session=session,
        query_embedding=query_embedding,
        limit=limit,
        category_ids=category_ids,
    )
    threshold = resolve_search_threshold(min_score)
    filtered_results = filter_results_by_score(results, threshold.value)
    log_search_filtering(results, filtered_results, threshold)
    return filtered_results


async def answer_knowledge(
    session: AsyncSession,
    query: str,
    limit: int,
    embedding_client: EmbeddingClient,
    answer_client: AnswerClient,
    category_ids: list[int] | None = None,
    min_score: float | None = None,
) -> tuple[str, list[KnowledgeChunkRead]]:
    sources = await search_knowledge(
        session,
        query,
        limit,
        embedding_client,
        category_ids=category_ids,
        min_score=min_score,
    )
    answer = await answer_client.answer(query, sources)
    return answer, sources


async def list_sources(session: AsyncSession) -> list[dict[str, object]]:
    return await list_source_records(session)


def resolve_search_threshold(min_score: float | None) -> ResolvedSearchThreshold:
    if min_score is not None:
        return ResolvedSearchThreshold(value=min_score, source="request")
    return ResolvedSearchThreshold(
        value=get_settings().search_min_score,
        source="settings",
    )


def filter_results_by_score(
    results: list[KnowledgeChunkRead],
    min_score: float,
) -> list[KnowledgeChunkRead]:
    return [result for result in results if score_reaches_threshold(result.score, min_score)]


def score_reaches_threshold(score: object, min_score: float) -> bool:
    if not isinstance(score, int | float):
        return False
    score_value = float(score)
    return math.isfinite(score_value) and score_value >= min_score


def log_search_filtering(
    raw_results: list[KnowledgeChunkRead],
    filtered_results: list[KnowledgeChunkRead],
    threshold: ResolvedSearchThreshold,
) -> None:
    valid_scores = [
        float(result.score)
        for result in raw_results
        if isinstance(result.score, int | float) and math.isfinite(float(result.score))
    ]
    logger.info(
        "knowledge_search_relevance_filter",
        extra={
            "threshold": threshold.value,
            "threshold_source": threshold.source,
            "raw_count": len(raw_results),
            "filtered_count": len(filtered_results),
            "min_score": min(valid_scores) if valid_scores else None,
            "max_score": max(valid_scores) if valid_scores else None,
        },
    )
