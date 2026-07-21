from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import exists, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.models import (
    DocumentSource,
    EmbeddingBatch,
    KnowledgeChunk,
    ReindexRun,
    document_source_categories,
)
from ..repositories.embeddings import complete_embedding_batch, create_embedding_batch
from ..repositories.reindex import (
    add_reindex_item,
    create_reindex_run,
    finish_reindex_run,
    get_reindex_run_by_public_id,
    list_retryable_items,
    mark_item_done,
    mark_item_failed,
    mark_item_processing,
    update_reindex_run_counters,
)
from ..schemas.operations import ReindexFilters, ReindexRunRead
from .embedding_versions import active_embedding_identity, compute_embedding_content_hash
from .embeddings import EmbeddingClient


DEFAULT_REINDEX_BATCH_SIZE = 50
SENSITIVE_PLACEHOLDER = "[redacted]"


class ReindexError(RuntimeError):
    pass


class ReindexRunNotFoundError(ReindexError):
    pass


@dataclass(frozen=True)
class ReindexCandidate:
    source_id: int
    source_public_id: str
    chunk_id: int
    content: str
    reason: str


def sanitize_operational_message(message: object) -> str:
    text = str(message).replace("\n", " ")
    for marker in ("Bearer ", "api_key=", "password=", "token="):
        if marker in text:
            return SENSITIVE_PLACEHOLDER
    return text[:1000]


def build_target_config_payload(identity: object) -> dict[str, Any]:
    return {
        "provider": getattr(identity, "provider"),
        "model": getattr(identity, "model"),
        "dimension": getattr(identity, "dimension"),
        "version": getattr(identity, "version"),
        "config_hash": getattr(identity, "config_hash"),
    }


async def run_reindex(
    session: AsyncSession,
    embedding_client: EmbeddingClient,
    *,
    dry_run: bool = False,
    source_ids: list[str] | None = None,
    categories: list[str] | None = None,
    batch_size: int = DEFAULT_REINDEX_BATCH_SIZE,
    resume_run_id: str | None = None,
) -> ReindexRunRead:
    if batch_size < 1:
        raise ValueError("batch_size must be greater than zero.")

    filters = ReindexFilters(
        source_ids=source_ids or [],
        categories=categories or [],
        batch_size=batch_size,
    )
    identity = active_embedding_identity()
    if resume_run_id:
        return await resume_reindex_run(
            session,
            embedding_client,
            resume_run_id=resume_run_id,
            batch_size=batch_size,
        )

    candidates = await list_reindex_candidates(
        session,
        source_ids=filters.source_ids,
        categories=filters.categories,
    )
    reasons = Counter(candidate.reason for candidate in candidates)
    sources_total = len({candidate.source_id for candidate in candidates})
    run = await create_reindex_run(
        session,
        identity,
        filters.model_dump(),
        dry_run=dry_run,
    )
    selected_candidates = candidates if dry_run else candidates[:batch_size]
    for candidate in selected_candidates:
        add_reindex_item(
            session,
            run.id,
            candidate.source_id,
            candidate.chunk_id,
            candidate.reason,
            status="skipped" if dry_run else "pending",
        )

    if dry_run:
        await finish_reindex_run(
            session,
            run.id,
            "dry_run_completed",
            sources_total=sources_total,
            chunks_total=len(candidates),
        )
        await session.commit()
        return build_reindex_read(
            run,
            identity,
            status="dry_run_completed",
            sources_total=sources_total,
            chunks_total=len(candidates),
            reasons=dict(reasons),
        )

    result = await execute_reindex_candidates(
        session,
        embedding_client,
        run,
        selected_candidates,
    )
    await session.commit()
    return build_reindex_read(
        run,
        identity,
        status=result["status"],
        sources_total=sources_total,
        chunks_total=len(selected_candidates),
        chunks_reindexed=result["chunks_reindexed"],
        chunks_reused=result["chunks_reused"],
        chunks_failed=result["chunks_failed"],
        reasons=dict(reasons),
    )


async def resume_reindex_run(
    session: AsyncSession,
    embedding_client: EmbeddingClient,
    *,
    resume_run_id: str,
    batch_size: int,
) -> ReindexRunRead:
    run = await get_reindex_run_by_public_id(session, resume_run_id)
    if run is None:
        raise ReindexRunNotFoundError(f"Reindex run {resume_run_id} does not exist.")
    identity = active_embedding_identity()
    items = await list_retryable_items(session, run.id, batch_size)
    candidates = await candidates_from_items(session, items, identity.config_hash)
    result = await execute_reindex_candidates(session, embedding_client, run, candidates, items)
    await session.commit()
    return build_reindex_read(
        run,
        identity,
        status=result["status"],
        sources_total=run.sources_total,
        chunks_total=len(candidates),
        chunks_reindexed=result["chunks_reindexed"],
        chunks_reused=result["chunks_reused"],
        chunks_failed=result["chunks_failed"],
        reasons=Counter(candidate.reason for candidate in candidates),
    )


async def list_reindex_candidates(
    session: AsyncSession,
    *,
    source_ids: list[str],
    categories: list[str],
) -> list[ReindexCandidate]:
    identity = active_embedding_identity()
    statement = (
        select(KnowledgeChunk, DocumentSource, EmbeddingBatch)
        .join(DocumentSource, KnowledgeChunk.source_id == DocumentSource.id)
        .outerjoin(EmbeddingBatch, KnowledgeChunk.embedding_batch_id == EmbeddingBatch.id)
        .options(selectinload(DocumentSource.categories))
        .where(DocumentSource.content_text != "")
        .where(
            or_(
                KnowledgeChunk.embedding.is_(None),
                KnowledgeChunk.embedding_status != "embedded",
                KnowledgeChunk.embedding_batch_id.is_(None),
                EmbeddingBatch.config_hash.is_(None),
                EmbeddingBatch.config_hash != identity.config_hash,
                EmbeddingBatch.status != "completed",
            )
        )
        .order_by(DocumentSource.id, KnowledgeChunk.id)
    )
    if source_ids:
        statement = statement.where(DocumentSource.public_id.in_(source_ids))
    if categories:
        normalized_categories = [category.strip().lower() for category in categories]
        statement = statement.where(
            exists()
            .where(document_source_categories.c.document_source_id == DocumentSource.id)
            .where(document_source_categories.c.category_id.in_(
                select_column_category_ids(normalized_categories)
            ))
        )

    rows = (await session.execute(statement)).all()
    return [
        ReindexCandidate(
            source_id=source.id,
            source_public_id=source.public_id,
            chunk_id=chunk.id,
            content=chunk.content,
            reason=classify_reindex_reason(chunk, batch, identity.config_hash),
        )
        for chunk, source, batch in rows
    ]


def select_column_category_ids(normalized_categories: list[str]):
    from ..db.models import Category

    return select(Category.id).where(Category.name.in_(normalized_categories))


def classify_reindex_reason(
    chunk: KnowledgeChunk,
    batch: EmbeddingBatch | None,
    target_config_hash: str,
) -> str:
    if chunk.embedding_batch_id is None or batch is None:
        return "missing_batch" if chunk.embedding is None else "unversioned"
    if chunk.embedding_status == "failed":
        return "failed"
    if chunk.embedding_status != "embedded":
        return chunk.embedding_status or "pending"
    if batch.status != "completed":
        return "batch_not_completed"
    if batch.config_hash != target_config_hash:
        return "config_changed"
    return "pending"


async def candidates_from_items(
    session: AsyncSession,
    items: list[object],
    target_config_hash: str,
) -> list[ReindexCandidate]:
    candidates: list[ReindexCandidate] = []
    for item in items:
        chunk = await session.get(KnowledgeChunk, item.chunk_id)
        if chunk is None:
            continue
        source = await session.get(DocumentSource, item.source_id)
        if source is None or not source.content_text:
            continue
        batch = None
        if chunk.embedding_batch_id is not None:
            batch = await session.get(EmbeddingBatch, chunk.embedding_batch_id)
        if is_chunk_compatible(chunk, batch, target_config_hash):
            await mark_item_done(session, item, "reused")
            continue
        candidates.append(
            ReindexCandidate(
                source_id=source.id,
                source_public_id=source.public_id,
                chunk_id=chunk.id,
                content=chunk.content,
                reason=classify_reindex_reason(chunk, batch, target_config_hash),
            )
        )
    return candidates


def is_chunk_compatible(
    chunk: KnowledgeChunk,
    batch: EmbeddingBatch | None,
    target_config_hash: str,
) -> bool:
    return (
        chunk.embedding is not None
        and chunk.embedding_status == "embedded"
        and batch is not None
        and batch.status == "completed"
        and batch.config_hash == target_config_hash
    )


async def execute_reindex_candidates(
    session: AsyncSession,
    embedding_client: EmbeddingClient,
    run: ReindexRun,
    candidates: list[ReindexCandidate],
    existing_items: list[object] | None = None,
) -> dict[str, int | str]:
    identity = active_embedding_identity()
    batch = await create_embedding_batch(session, identity, len(candidates))
    items_by_chunk = {getattr(item, "chunk_id"): item for item in (existing_items or [])}
    chunks_reindexed = 0
    chunks_reused = 0
    chunks_failed = 0

    for candidate in candidates:
        item = items_by_chunk.get(candidate.chunk_id)
        if item is None:
            item = add_reindex_item(
                session,
                run.id,
                candidate.source_id,
                candidate.chunk_id,
                candidate.reason,
            )
            await session.flush()
        await mark_item_processing(session, item)

        chunk = await session.get(KnowledgeChunk, candidate.chunk_id)
        current_batch = None
        if chunk is not None and chunk.embedding_batch_id is not None:
            current_batch = await session.get(EmbeddingBatch, chunk.embedding_batch_id)
        if chunk is None:
            chunks_failed += 1
            await mark_item_failed(session, item, "Chunk no longer exists.")
            continue
        if is_chunk_compatible(chunk, current_batch, identity.config_hash):
            chunks_reused += 1
            await mark_item_done(session, item, "reused")
            continue

        try:
            vectors = await embedding_client.embed_texts([candidate.content])
            vector = vectors[0]
        except Exception as exc:  # pragma: no cover - exercised by service tests
            chunks_failed += 1
            sanitized = sanitize_operational_message(exc)
            await mark_item_failed(session, item, sanitized)
            await session.execute(
                update(KnowledgeChunk)
                .where(KnowledgeChunk.id == candidate.chunk_id)
                .values(embedding_status="failed", embedding_error=sanitized)
            )
            continue

        await session.execute(
            update(KnowledgeChunk)
            .where(KnowledgeChunk.id == candidate.chunk_id)
            .values(
                embedding=vector,
                embedding_batch_id=batch.id,
                embedding_content_hash=compute_embedding_content_hash(candidate.content),
                embedding_status="embedded",
                embedded_at=datetime.now(UTC),
                embedding_error=None,
            )
        )
        chunks_reindexed += 1
        await mark_item_done(session, item, "reindexed")

    await complete_embedding_batch(session, batch.id, chunks_reindexed)
    status = "completed" if chunks_failed == 0 else "failed"
    await update_reindex_run_counters(
        session,
        run.id,
        status=status,
        chunks_reindexed=chunks_reindexed,
        chunks_reused=chunks_reused,
        chunks_failed=chunks_failed,
        error_message=None if chunks_failed == 0 else "Some chunks failed to reindex.",
    )
    return {
        "status": status,
        "chunks_reindexed": chunks_reindexed,
        "chunks_reused": chunks_reused,
        "chunks_failed": chunks_failed,
    }


def build_reindex_read(
    run: ReindexRun,
    identity: object,
    *,
    status: str,
    sources_total: int,
    chunks_total: int,
    chunks_reindexed: int = 0,
    chunks_reused: int = 0,
    chunks_failed: int = 0,
    reasons: dict[str, int] | Counter[str] | None = None,
) -> ReindexRunRead:
    return ReindexRunRead(
        run_id=run.public_id,
        dry_run=run.dry_run,
        status=status,
        target_config=build_target_config_payload(identity),
        sources_total=sources_total,
        chunks_total=chunks_total,
        chunks_reindexed=chunks_reindexed,
        chunks_reused=chunks_reused,
        chunks_failed=chunks_failed,
        reasons=dict(reasons or {}),
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_message=run.error_message,
    )
