from __future__ import annotations

from types import SimpleNamespace

import pytest
from mcp.server.auth.provider import AccessToken

from backend.app.services.categories import CategoryNotFoundError
from backend.app.services.documents.extractors import EmptyDocumentError
from backend.app.services.embeddings import EmbeddingError
from mcp_server.tools.knowledge import (
    MCP_ALLOWED_METADATA_KEYS,
    MCPAuthorizationError,
    MCPIngestionError,
    MCPTextIngestRequest,
    ingest_mcp_text,
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
                id=42,
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

    assert result.source_id == 42
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
