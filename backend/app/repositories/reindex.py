from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import ReindexItem, ReindexRun
from ..services.embedding_versions import EmbeddingConfigIdentity


def _sanitize_error(message: str | None) -> str | None:
    if not message:
        return None
    return message.replace("\n", " ")[:1000]


async def create_reindex_run(
    session: AsyncSession,
    identity: EmbeddingConfigIdentity,
    filters: dict[str, Any],
    dry_run: bool,
) -> ReindexRun:
    run = ReindexRun(
        target_provider=identity.provider,
        target_model=identity.model,
        target_dimension=identity.dimension,
        target_version=identity.version,
        target_config_hash=identity.config_hash,
        filters_json=filters,
        dry_run=dry_run,
        status="running",
    )
    session.add(run)
    await session.flush()
    return run


async def get_reindex_run_by_public_id(
    session: AsyncSession,
    public_id: str,
) -> ReindexRun | None:
    return (
        await session.execute(select(ReindexRun).where(ReindexRun.public_id == public_id))
    ).scalar_one_or_none()


def add_reindex_item(
    session: AsyncSession,
    run_id: int,
    source_id: int,
    chunk_id: int | None,
    reason: str,
    status: str = "pending",
) -> ReindexItem:
    item = ReindexItem(
        run_id=run_id,
        source_id=source_id,
        chunk_id=chunk_id,
        reason=reason,
        status=status,
    )
    session.add(item)
    return item


async def list_retryable_items(
    session: AsyncSession,
    run_id: int,
    limit: int,
) -> list[ReindexItem]:
    rows = await session.execute(
        select(ReindexItem)
        .where(ReindexItem.run_id == run_id)
        .where(ReindexItem.status.in_(["pending", "failed_retryable"]))
        .where(ReindexItem.chunk_id.is_not(None))
        .order_by(ReindexItem.id)
        .limit(limit)
    )
    return list(rows.scalars().all())


async def mark_item_processing(session: AsyncSession, item: ReindexItem) -> None:
    item.status = "processing"
    item.attempts += 1
    item.started_at = datetime.now(UTC)
    item.error_message = None
    await session.flush()


async def mark_item_done(session: AsyncSession, item: ReindexItem, status: str) -> None:
    item.status = status
    item.completed_at = datetime.now(UTC)
    item.error_message = None
    await session.flush()


async def mark_item_failed(session: AsyncSession, item: ReindexItem, error_message: str) -> None:
    item.status = "failed_retryable"
    item.completed_at = datetime.now(UTC)
    item.error_message = _sanitize_error(error_message)
    await session.flush()


async def finish_reindex_run(
    session: AsyncSession,
    run_id: int,
    status: str,
    *,
    sources_total: int,
    chunks_total: int,
    chunks_reindexed: int = 0,
    chunks_reused: int = 0,
    chunks_failed: int = 0,
    error_message: str | None = None,
) -> None:
    await session.execute(
        update(ReindexRun)
        .where(ReindexRun.id == run_id)
        .values(
            status=status,
            completed_at=datetime.now(UTC),
            sources_total=sources_total,
            chunks_total=chunks_total,
            chunks_reindexed=chunks_reindexed,
            chunks_reused=chunks_reused,
            chunks_failed=chunks_failed,
            error_message=_sanitize_error(error_message),
        )
    )


async def update_reindex_run_counters(
    session: AsyncSession,
    run_id: int,
    *,
    status: str,
    chunks_reindexed: int,
    chunks_reused: int,
    chunks_failed: int,
    error_message: str | None = None,
) -> None:
    await session.execute(
        update(ReindexRun)
        .where(ReindexRun.id == run_id)
        .values(
            status=status,
            completed_at=datetime.now(UTC),
            chunks_reindexed=chunks_reindexed,
            chunks_reused=chunks_reused,
            chunks_failed=chunks_failed,
            error_message=_sanitize_error(error_message),
        )
    )
