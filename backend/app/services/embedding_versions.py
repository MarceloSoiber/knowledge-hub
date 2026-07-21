from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from ..core.settings import Settings, get_settings


class EmbeddingDimensionMismatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class EmbeddingConfigIdentity:
    provider: str
    model: str
    dimension: int
    version: str

    @property
    def config_hash(self) -> str:
        payload = {
            "provider": self.provider,
            "model": self.model,
            "dimension": self.dimension,
            "version": self.version,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def active_embedding_identity(settings: Settings | None = None) -> EmbeddingConfigIdentity:
    resolved = settings or get_settings()
    return EmbeddingConfigIdentity(
        provider=resolved.llm_provider.strip().lower(),
        model=resolved.embedding_model.strip(),
        dimension=resolved.vector_dim,
        version=resolved.embedding_version.strip() or "default",
    )


def compute_embedding_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def get_pgvector_column_dimension(
    connection: AsyncConnection,
    table_name: str = "knowledge_chunks",
    column_name: str = "embedding",
) -> int | None:
    result = await connection.execute(
        text(
            "SELECT atttypmod "
            "FROM pg_attribute "
            "WHERE attrelid = to_regclass(:table_name) "
            "AND attname = :column_name "
            "AND NOT attisdropped"
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    typmod = result.scalar_one_or_none()
    if typmod is None or int(typmod) < 0:
        return None
    return int(typmod)


async def assert_pgvector_dimension(
    connection: AsyncConnection,
    expected_dimension: int,
    table_name: str = "knowledge_chunks",
    column_name: str = "embedding",
) -> None:
    actual_dimension = await get_pgvector_column_dimension(connection, table_name, column_name)
    if actual_dimension is None:
        return
    if actual_dimension != expected_dimension:
        raise EmbeddingDimensionMismatchError(
            f"Configured VECTOR_DIM={expected_dimension} differs from "
            f"{table_name}.{column_name} vector({actual_dimension}). "
            "Apply an explicit vector dimension migration and reindex embeddings before startup."
        )
