from __future__ import annotations

from dataclasses import dataclass

import pytest

from backend.app.db.models import DocumentSource, EmbeddingBatch, KnowledgeChunk, ReindexItem
from backend.app.services.reindex import (
    ReindexCandidate,
    classify_reindex_reason,
    run_reindex,
    sanitize_operational_message,
)


class NeverCalledEmbeddingClient:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise AssertionError(f"embed_texts should not be called: {texts}")


@dataclass
class FakeExecuteResult:
    rows: list[object]

    def all(self) -> list[object]:
        return self.rows

    def scalar_one_or_none(self) -> object | None:
        return self.rows[0] if self.rows else None

    def scalars(self) -> "FakeExecuteResult":
        return self


class FakeDryRunSession:
    def __init__(self) -> None:
        self.source = DocumentSource(
            id=10,
            public_id="11111111-1111-4111-8111-111111111111",
            title="Source",
            source_type="text",
            uri="text:Source",
            content_text="private source body",
            content_hash="hash",
        )
        self.chunk = KnowledgeChunk(
            id=20,
            source_id=10,
            content="chunk body",
            embedding=[0.1, 0.2, 0.3],
            embedding_status="unversioned",
        )
        self.added: list[object] = []
        self.committed = False

    async def execute(self, statement: object) -> FakeExecuteResult:
        statement_text = str(statement)
        if "knowledge_chunks" in statement_text and "document_sources" in statement_text:
            return FakeExecuteResult([(self.chunk, self.source, None)])
        return FakeExecuteResult([])

    def add(self, entity: object) -> None:
        if entity.__class__.__name__ == "ReindexRun":
            entity.id = 1
            entity.public_id = "22222222-2222-4222-8222-222222222222"
        if isinstance(entity, ReindexItem):
            entity.id = len([item for item in self.added if isinstance(item, ReindexItem)]) + 1
        self.added.append(entity)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True


def test_sanitize_operational_message_redacts_sensitive_markers() -> None:
    assert sanitize_operational_message("Bearer abc123") == "[redacted]"
    assert sanitize_operational_message("token=abc123") == "[redacted]"
    assert sanitize_operational_message("plain error\nwith newline") == "plain error with newline"


def test_classify_reindex_reason_for_legacy_and_changed_config() -> None:
    legacy = KnowledgeChunk(id=1, source_id=1, content="legacy", embedding=[0.1])
    assert classify_reindex_reason(legacy, None, "target") == "unversioned"

    pending = KnowledgeChunk(id=2, source_id=1, content="pending", embedding=None)
    assert classify_reindex_reason(pending, None, "target") == "missing_batch"

    batch = EmbeddingBatch(
        id=1,
        provider="local",
        model="old",
        dimension=768,
        version="default",
        config_hash="old",
        status="completed",
    )
    changed = KnowledgeChunk(
        id=3,
        source_id=1,
        content="changed",
        embedding=[0.1],
        embedding_batch_id=1,
        embedding_status="embedded",
    )
    assert classify_reindex_reason(changed, batch, "target") == "config_changed"


@pytest.mark.asyncio
async def test_reindex_dry_run_persists_run_and_does_not_embed() -> None:
    session = FakeDryRunSession()

    result = await run_reindex(
        session,  # type: ignore[arg-type]
        NeverCalledEmbeddingClient(),
        dry_run=True,
        batch_size=10,
    )

    assert result.status == "dry_run_completed"
    assert result.chunks_total == 1
    assert result.chunks_reindexed == 0
    assert result.reasons == {"unversioned": 1}
    assert session.committed is True
    assert any(entity.__class__.__name__ == "ReindexRun" for entity in session.added)
    assert any(isinstance(entity, ReindexItem) for entity in session.added)


def test_reindex_candidate_does_not_store_full_source_content() -> None:
    candidate = ReindexCandidate(
        source_id=1,
        source_public_id="public",
        chunk_id=2,
        content="chunk only",
        reason="config_changed",
    )

    assert "private source body" not in repr(candidate)
