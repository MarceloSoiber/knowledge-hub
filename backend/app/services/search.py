from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.settings import get_settings
from ..repositories.chunks import TextSearchChunk, search_similar_chunks, search_text_chunks
from ..repositories.sources import list_sources as list_source_records
from ..schemas.knowledge import KnowledgeChunkRead
from .categories import get_categories
from .embeddings import EmbeddingClient
from .rag import AnswerClient
from .tags import get_tags

logger = logging.getLogger(__name__)
RRF_K = 60
MIN_CANDIDATE_LIMIT = 20


@dataclass(frozen=True)
class ResolvedSearchThreshold:
    value: float
    source: str


@dataclass
class HybridSearchCandidate:
    chunk: KnowledgeChunkRead
    vector_rank: int | None = None
    text_rank: int | None = None
    vector_score: float | None = None
    text_score: float | None = None

    @property
    def rrf_score(self) -> float:
        score = 0.0
        if self.vector_rank is not None:
            score += reciprocal_rank_score(self.vector_rank)
        if self.text_rank is not None:
            score += reciprocal_rank_score(self.text_rank)
        return score

    @property
    def match_reasons(self) -> list[str]:
        reasons: list[str] = []
        if self.vector_rank is not None:
            reasons.append("vector")
        if self.text_rank is not None:
            reasons.append("text")
        return reasons


async def search_knowledge(
    session: AsyncSession,
    query: str,
    limit: int,
    embedding_client: EmbeddingClient,
    category_ids: list[int] | None = None,
    tag_ids: list[int] | None = None,
    min_score: float | None = None,
    include_match_reasons: bool = False,
) -> list[KnowledgeChunkRead]:
    if category_ids is not None:
        await get_categories(session, category_ids)
    if tag_ids is not None:
        await get_tags(session, tag_ids)
    query_embedding = (await embedding_client.embed_texts([query]))[0]
    candidate_limit = resolve_candidate_limit(limit)
    vector_results = await search_similar_chunks(
        session=session,
        query_embedding=query_embedding,
        limit=candidate_limit,
        category_ids=category_ids,
        tag_ids=tag_ids,
    )
    text_results = await search_text_chunks(
        session=session,
        query=query,
        limit=candidate_limit,
        category_ids=category_ids,
        tag_ids=tag_ids,
    )
    threshold = resolve_search_threshold(min_score)
    results = fuse_hybrid_results(
        vector_results=vector_results,
        text_results=text_results,
        limit=limit,
        min_score=threshold.value,
        include_match_reasons=include_match_reasons,
    )
    log_search_filtering(vector_results, results, threshold)
    log_hybrid_search(
        vector_results=vector_results,
        text_results=text_results,
        final_results=results,
        threshold=threshold,
        include_match_reasons=include_match_reasons,
    )
    return results


async def answer_knowledge(
    session: AsyncSession,
    query: str,
    limit: int,
    embedding_client: EmbeddingClient,
    answer_client: AnswerClient,
    category_ids: list[int] | None = None,
    tag_ids: list[int] | None = None,
    min_score: float | None = None,
    include_match_reasons: bool = False,
) -> tuple[str, list[KnowledgeChunkRead]]:
    sources = await search_knowledge(
        session,
        query,
        limit,
        embedding_client,
        category_ids=category_ids,
        tag_ids=tag_ids,
        min_score=min_score,
        include_match_reasons=include_match_reasons,
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


def resolve_candidate_limit(limit: int) -> int:
    return max(limit * 4, MIN_CANDIDATE_LIMIT)


def reciprocal_rank_score(rank: int) -> float:
    return 1 / (RRF_K + rank)


def fuse_hybrid_results(
    vector_results: list[KnowledgeChunkRead],
    text_results: list[TextSearchChunk],
    limit: int,
    min_score: float,
    include_match_reasons: bool = False,
) -> list[KnowledgeChunkRead]:
    candidates = build_hybrid_candidates(vector_results, text_results)
    ranked_candidates = sorted(
        (
            candidate
            for candidate in candidates.values()
            if candidate_reaches_threshold(candidate, min_score)
        ),
        key=hybrid_sort_key,
        reverse=True,
    )
    return [
        build_hybrid_result(candidate, include_match_reasons)
        for candidate in ranked_candidates[:limit]
    ]


def build_hybrid_candidates(
    vector_results: list[KnowledgeChunkRead],
    text_results: list[TextSearchChunk],
) -> dict[int, HybridSearchCandidate]:
    candidates: dict[int, HybridSearchCandidate] = {}
    for rank, chunk in enumerate(vector_results, start=1):
        candidates[chunk.id] = HybridSearchCandidate(
            chunk=chunk,
            vector_rank=rank,
            vector_score=chunk.score,
        )
    for rank, text_result in enumerate(text_results, start=1):
        candidate = candidates.get(text_result.chunk.id)
        if candidate is None:
            candidates[text_result.chunk.id] = HybridSearchCandidate(
                chunk=text_result.chunk,
                text_rank=rank,
                text_score=text_result.text_rank,
            )
            continue
        candidate.text_rank = rank
        candidate.text_score = text_result.text_rank
    return candidates


def candidate_reaches_threshold(candidate: HybridSearchCandidate, min_score: float) -> bool:
    if candidate.vector_rank is None:
        return True
    return score_reaches_threshold(candidate.vector_score, min_score)


def hybrid_sort_key(candidate: HybridSearchCandidate) -> tuple[float, bool, float, float, int]:
    return (
        candidate.rrf_score,
        candidate.vector_rank is not None and candidate.text_rank is not None,
        candidate.vector_score if candidate.vector_score is not None else float("-inf"),
        candidate.text_score if candidate.text_score is not None else float("-inf"),
        -candidate.chunk.id,
    )


def build_hybrid_result(
    candidate: HybridSearchCandidate,
    include_match_reasons: bool,
) -> KnowledgeChunkRead:
    update: dict[str, object] = {"score": candidate.vector_score}
    if include_match_reasons:
        update["match_reasons"] = candidate.match_reasons
    return candidate.chunk.model_copy(update=update)


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


def log_hybrid_search(
    vector_results: list[KnowledgeChunkRead],
    text_results: list[TextSearchChunk],
    final_results: list[KnowledgeChunkRead],
    threshold: ResolvedSearchThreshold,
    include_match_reasons: bool,
) -> None:
    logger.info(
        "knowledge_search_hybrid_fusion",
        extra={
            "threshold": threshold.value,
            "threshold_source": threshold.source,
            "vector_candidate_count": len(vector_results),
            "text_candidate_count": len(text_results),
            "final_count": len(final_results),
            "include_match_reasons": include_match_reasons,
        },
    )
