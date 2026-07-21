from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import EmbeddingBatch, KnowledgeChunk
from ..services.embedding_versions import EmbeddingConfigIdentity


async def create_embedding_batch(
    session: AsyncSession,
    identity: EmbeddingConfigIdentity,
    chunks_total: int,
) -> EmbeddingBatch:
    batch = EmbeddingBatch(
        provider=identity.provider,
        model=identity.model,
        dimension=identity.dimension,
        version=identity.version,
        config_hash=identity.config_hash,
        status="running",
        chunks_total=chunks_total,
        chunks_embedded=0,
    )
    session.add(batch)
    await session.flush()
    return batch


async def complete_embedding_batch(
    session: AsyncSession,
    batch_id: int,
    chunks_embedded: int,
) -> None:
    await session.execute(
        update(EmbeddingBatch)
        .where(EmbeddingBatch.id == batch_id)
        .values(
            status="completed",
            completed_at=datetime.now(UTC),
            chunks_embedded=chunks_embedded,
            error_message=None,
        )
    )


async def fail_embedding_batch(
    session: AsyncSession,
    batch_id: int,
    error_message: str,
) -> None:
    await session.execute(
        update(EmbeddingBatch)
        .where(EmbeddingBatch.id == batch_id)
        .values(
            status="failed",
            completed_at=datetime.now(UTC),
            error_message=error_message[:2000],
        )
    )


async def get_completed_batch_for_identity(
    session: AsyncSession,
    identity: EmbeddingConfigIdentity,
) -> EmbeddingBatch | None:
    return (
        await session.execute(
            select(EmbeddingBatch)
            .where(EmbeddingBatch.config_hash == identity.config_hash)
            .where(EmbeddingBatch.status == "completed")
            .order_by(EmbeddingBatch.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def count_pending_chunks(
    session: AsyncSession,
    identity: EmbeddingConfigIdentity,
) -> int:
    result = await session.execute(
        select(KnowledgeChunk.id)
        .outerjoin(EmbeddingBatch, KnowledgeChunk.embedding_batch_id == EmbeddingBatch.id)
        .where(
            (KnowledgeChunk.embedding_status != "embedded")
            | (KnowledgeChunk.embedding_batch_id.is_(None))
            | (EmbeddingBatch.config_hash != identity.config_hash)
        )
    )
    return len(result.scalars().all())
