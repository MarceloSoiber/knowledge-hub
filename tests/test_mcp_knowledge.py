from __future__ import annotations

from types import SimpleNamespace

import pytest
from mcp.server.auth.provider import AccessToken
from pydantic import ValidationError

from backend.app.services.categories import CategoryNotFoundError
from backend.app.services.documents.extractors import EmptyDocumentError
from backend.app.services.embeddings import EmbeddingError
from backend.app.schemas.knowledge import KnowledgeChunkRead
from mcp_server.tools.knowledge import (
    MCP_ALLOWED_METADATA_KEYS,
    MCPAuthorizationError,
    MCPIngestionError,
    MCPSourceNotFoundError,
    MCPTextIngestRequest,
    get_knowledge_source,
    ingest_mcp_text,
    search_knowledge,
)


def access_token_with_scopes(scopes: list[str]) -> AccessToken:
    return AccessToken(
        token="test-token",
        client_id="test-client",
        scopes=scopes,
    )


def authorize(monkeypatch: pytest.MonkeyPatch, scopes: list[str]) -> None:
    monkeypatch.setattr(
        "mcp_server.tools.knowledge.get_access_token",
        lambda: access_token_with_scopes(scopes),
    )


def test_mcp_text_ingest_schema_validates_fields() -> None:
    payload = MCPTextIngestRequest(
        title="  Sprint notes  ",
        content="  Decision log  ",
        category_ids=[1, 2],
        metadata={"note_type": " decision "},
    )

    assert payload.title == "Sprint notes"
    assert payload.content == "Decision log"
    assert payload.category_ids == [1, 2]
    assert payload.metadata == {"note_type": "decision"}
    assert MCP_ALLOWED_METADATA_KEYS == {"client_id", "note_type"}

    with pytest.raises(ValueError):
        MCPTextIngestRequest(title=" ", content="content", category_ids=[1])

    with pytest.raises(ValueError):
        MCPTextIngestRequest(title="notes", content=" ", category_ids=[1])

    with pytest.raises(ValueError):
        MCPTextIngestRequest(title="notes", content="content", category_ids=[])

    with pytest.raises(ValueError):
        MCPTextIngestRequest(title="notes", content="content", category_ids=[1, 1])

    with pytest.raises(ValueError, match="Unsupported metadata keys"):
        MCPTextIngestRequest(
            title="notes",
            content="content",
            category_ids=[1],
            metadata={"unsafe": "value"},
        )


@pytest.mark.asyncio
async def test_search_knowledge_returns_citation_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_kwargs: dict[str, object] = {}

    async def fake_search_backend_knowledge(**_: object) -> list[KnowledgeChunkRead]:
        captured_kwargs.update(_)
        return [
            KnowledgeChunkRead(
                id=10,
                source_id="33333333-3333-4333-8333-333333333333",
                source_title="runbook.md",
                source_type="upload",
                uri="upload:runbook.md",
                categories=[{"id": 2, "name": "docs"}],
                location={
                    "chunk_index": 1,
                    "page": None,
                    "section": "Setup",
                    "start_char": 20,
                    "end_char": 60,
                },
                content="result content",
                score=0.92,
                metadata={"note_type": "decision"},
            )
        ]

    class FakeSessionLocal:
        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *_: object) -> None:
            return None

    monkeypatch.setattr("mcp_server.tools.knowledge.SessionLocal", FakeSessionLocal)
    monkeypatch.setattr(
        "mcp_server.tools.knowledge.search_backend_knowledge",
        fake_search_backend_knowledge,
    )
    monkeypatch.setattr("mcp_server.tools.knowledge.build_embedding_client", lambda: object())

    results = await search_knowledge("find", limit=1, category_ids=[2], min_score=0.55)

    assert captured_kwargs["min_score"] == 0.55
    assert captured_kwargs["include_match_reasons"] is False
    assert results[0].source_id == "33333333-3333-4333-8333-333333333333"
    assert results[0].source_title == "runbook.md"
    assert results[0].location.section == "Setup"
    assert results[0].metadata == {"note_type": "decision"}
    assert results[0].match_reasons is None


@pytest.mark.asyncio
async def test_search_knowledge_can_return_match_reasons(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_kwargs: dict[str, object] = {}

    async def fake_search_backend_knowledge(**kwargs: object) -> list[KnowledgeChunkRead]:
        captured_kwargs.update(kwargs)
        return [
            KnowledgeChunkRead(
                id=10,
                source_id="33333333-3333-4333-8333-333333333333",
                source_title="runbook.md",
                source_type="upload",
                uri="upload:runbook.md",
                categories=[{"id": 2, "name": "docs"}],
                location={
                    "chunk_index": 1,
                    "page": None,
                    "section": "Setup",
                    "start_char": 20,
                    "end_char": 60,
                },
                content="ERR_CONN_RESET",
                score=0.92,
                metadata={},
                match_reasons=["vector", "text"],
            )
        ]

    class FakeSessionLocal:
        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *_: object) -> None:
            return None

    monkeypatch.setattr("mcp_server.tools.knowledge.SessionLocal", FakeSessionLocal)
    monkeypatch.setattr(
        "mcp_server.tools.knowledge.search_backend_knowledge",
        fake_search_backend_knowledge,
    )
    monkeypatch.setattr("mcp_server.tools.knowledge.build_embedding_client", lambda: object())

    results = await search_knowledge("ERR_CONN_RESET", include_match_reasons=True)

    assert captured_kwargs["include_match_reasons"] is True
    assert results[0].match_reasons == ["vector", "text"]


@pytest.mark.asyncio
async def test_search_knowledge_rejects_invalid_min_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSessionLocal:
        async def __aenter__(self) -> object:
            raise AssertionError("session should not open for invalid min_score")

        async def __aexit__(self, *_: object) -> None:
            return None

    monkeypatch.setattr("mcp_server.tools.knowledge.SessionLocal", FakeSessionLocal)

    with pytest.raises(ValidationError):
        await search_knowledge("find", min_score=1.01)


@pytest.mark.asyncio
async def test_registered_search_tool_forwards_min_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from mcp_server import server

    captured_kwargs: dict[str, object] = {}

    async def fake_search_knowledge(**kwargs: object) -> list[KnowledgeChunkRead]:
        captured_kwargs.update(kwargs)
        return []

    monkeypatch.setattr(server, "search_knowledge", fake_search_knowledge)

    results = await server.search(
        query="find",
        limit=3,
        category_ids=[2],
        min_score=0.6,
    )

    assert results == []
    assert captured_kwargs == {
        "query": "find",
        "limit": 3,
        "category_ids": [2],
        "min_score": 0.6,
        "include_match_reasons": False,
    }


@pytest.mark.asyncio
async def test_ingest_mcp_text_creates_mcp_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authorize(monkeypatch, ["knowledge:read", "knowledge:write"])

    async def fake_ingest_plain_text(**kwargs: object) -> tuple[object, int]:
        assert kwargs["title"] == "Architecture note"
        assert kwargs["content"] == "Keep MCP tools thin."
        assert kwargs["category_ids"] == [2, 3]
        assert kwargs["source_type"] == "mcp"
        assert kwargs["metadata"] == {"note_type": "decision"}
        return (
            SimpleNamespace(
                public_id="11111111-1111-4111-8111-111111111111",
                title="Architecture note",
                categories=[
                    SimpleNamespace(id=2, name="docs"),
                    SimpleNamespace(id=3, name="ops"),
                ],
            ),
            2,
        )

    monkeypatch.setattr("mcp_server.tools.knowledge.ingest_plain_text", fake_ingest_plain_text)

    result = await ingest_mcp_text(
        title="Architecture note",
        content="Keep MCP tools thin.",
        category_ids=[2, 3],
        metadata={"note_type": "decision"},
    )

    assert result.source_id == "11111111-1111-4111-8111-111111111111"
    assert result.title == "Architecture note"
    assert [category.name for category in result.categories] == ["docs", "ops"]
    assert result.chunks_created == 2


@pytest.mark.asyncio
async def test_ingest_mcp_text_denies_read_only_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authorize(monkeypatch, ["knowledge:read"])
    called = False

    async def fake_ingest_plain_text(**_: object) -> tuple[object, int]:
        nonlocal called
        called = True
        return SimpleNamespace(id=1, title="notes", categories=[]), 1

    monkeypatch.setattr("mcp_server.tools.knowledge.ingest_plain_text", fake_ingest_plain_text)

    with pytest.raises(MCPAuthorizationError, match="knowledge:write"):
        await ingest_mcp_text(
            title="notes",
            content="content",
            category_ids=[1],
        )

    assert called is False


@pytest.mark.asyncio
async def test_ingest_mcp_text_maps_category_and_empty_content_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authorize(monkeypatch, ["knowledge:write"])

    async def missing_category(**_: object) -> tuple[object, int]:
        raise CategoryNotFoundError("Category 99 does not exist.")

    monkeypatch.setattr("mcp_server.tools.knowledge.ingest_plain_text", missing_category)

    with pytest.raises(MCPIngestionError, match="Category 99 does not exist"):
        await ingest_mcp_text(title="notes", content="content", category_ids=[99])

    async def empty_content(**_: object) -> tuple[object, int]:
        raise EmptyDocumentError("Text content does not contain readable text.")

    monkeypatch.setattr("mcp_server.tools.knowledge.ingest_plain_text", empty_content)

    with pytest.raises(MCPIngestionError, match="readable text"):
        await ingest_mcp_text(title="notes", content="content", category_ids=[1])


@pytest.mark.asyncio
async def test_ingest_mcp_text_maps_embedding_failure_without_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authorize(monkeypatch, ["knowledge:write"])

    async def embedding_failure(**_: object) -> tuple[object, int]:
        raise EmbeddingError("Embedding provider returned HTTP 500.")

    monkeypatch.setattr("mcp_server.tools.knowledge.ingest_plain_text", embedding_failure)

    with pytest.raises(MCPIngestionError, match="Embedding provider failure"):
        await ingest_mcp_text(title="notes", content="content", category_ids=[1])


@pytest.mark.asyncio
async def test_get_knowledge_source_returns_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_source_detail(_: object, source_id: str) -> dict[str, object]:
        assert source_id == "22222222-2222-4222-8222-222222222222"
        return {
            "source_id": source_id,
            "title": "notes",
            "categories": [{"id": 1, "name": "docs"}],
            "source_type": "text",
            "uri": "text:notes",
            "content_hash": "abc123",
            "content": "stored content",
        }

    monkeypatch.setattr("mcp_server.tools.knowledge.get_source_detail", fake_get_source_detail)

    result = await get_knowledge_source("22222222-2222-4222-8222-222222222222")

    assert result.source_id == "22222222-2222-4222-8222-222222222222"
    assert result.content == "stored content"
    assert result.categories[0].name == "docs"


@pytest.mark.asyncio
async def test_get_knowledge_source_maps_missing_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_source_detail(_: object, __: str) -> dict[str, object]:
        from backend.app.services.sources import SourceNotFoundError

        raise SourceNotFoundError("Source does not exist.")

    monkeypatch.setattr("mcp_server.tools.knowledge.get_source_detail", fake_get_source_detail)

    with pytest.raises(MCPSourceNotFoundError, match="Source does not exist"):
        await get_knowledge_source("22222222-2222-4222-8222-222222222222")
