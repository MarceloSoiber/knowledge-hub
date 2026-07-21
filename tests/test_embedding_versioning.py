from __future__ import annotations

import inspect

import pytest

from backend.app.core.settings import Settings
from backend.app.services.embedding_versions import (
    EmbeddingDimensionMismatchError,
    active_embedding_identity,
    assert_pgvector_dimension,
    compute_embedding_content_hash,
)


def test_init_db_no_longer_forces_vector_768() -> None:
    init_source = __import__("backend.app.db.init", fromlist=["init_db"])

    assert "ALTER COLUMN embedding TYPE vector(768)" not in inspect.getsource(init_source.init_db)


class FakeScalarResult:
    def __init__(self, value: int | None) -> None:
        self.value = value

    def scalar_one_or_none(self) -> int | None:
        return self.value


class FakeConnection:
    def __init__(self, typmod: int | None) -> None:
        self.typmod = typmod
        self.statements: list[str] = []

    async def execute(self, statement: object, params: dict[str, object]) -> FakeScalarResult:
        self.statements.append(str(statement))
        assert params["table_name"] == "knowledge_chunks"
        assert params["column_name"] == "embedding"
        return FakeScalarResult(self.typmod)


def test_active_embedding_identity_uses_effective_settings() -> None:
    identity = active_embedding_identity(
        Settings(
            llm_provider="LOCAL",
            embedding_model=" text-embedding-nomic-embed-text-v1.5 ",
            embedding_version="rev-a",
            vector_dim=768,
        )
    )

    assert identity.provider == "local"
    assert identity.model == "text-embedding-nomic-embed-text-v1.5"
    assert identity.dimension == 768
    assert identity.version == "rev-a"
    assert len(identity.config_hash) == 64


def test_embedding_identity_hash_changes_with_version() -> None:
    first = active_embedding_identity(Settings(embedding_version="rev-a"))
    second = active_embedding_identity(Settings(embedding_version="rev-b"))

    assert first.config_hash != second.config_hash


def test_embedding_content_hash_is_stable() -> None:
    assert compute_embedding_content_hash("same chunk") == compute_embedding_content_hash("same chunk")
    assert compute_embedding_content_hash("same chunk") != compute_embedding_content_hash("other chunk")


@pytest.mark.asyncio
async def test_pgvector_dimension_guard_accepts_matching_dimension() -> None:
    connection = FakeConnection(typmod=768)

    await assert_pgvector_dimension(connection, expected_dimension=768)  # type: ignore[arg-type]

    assert "pg_attribute" in connection.statements[0]


@pytest.mark.asyncio
async def test_pgvector_dimension_guard_rejects_mismatch() -> None:
    connection = FakeConnection(typmod=768)

    with pytest.raises(EmbeddingDimensionMismatchError, match="VECTOR_DIM=1024"):
        await assert_pgvector_dimension(connection, expected_dimension=1024)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_pgvector_dimension_guard_allows_missing_typmod() -> None:
    connection = FakeConnection(typmod=None)

    await assert_pgvector_dimension(connection, expected_dimension=1024)  # type: ignore[arg-type]
