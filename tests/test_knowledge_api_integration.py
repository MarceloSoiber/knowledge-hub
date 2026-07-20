from __future__ import annotations

from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from backend.app.api.dependencies import get_answer_client, get_embedding_client
from backend.app.core.auth import require_auth_token
from backend.app.db.session import get_session
from backend.app.main import create_app
from backend.app.services.categories import (
    CategoryConflictError,
    CategoryInUseError,
    CategoryNotFoundError,
)
from backend.app.services.projects import (
    ProjectConflictError,
    ProjectNotFoundError,
    ProjectStatusError,
)
from backend.app.services.tags import TagConflictError, TagInUseError, TagNotFoundError
from backend.app.services.ingestion import DuplicateSourceContentError
from backend.app.services.rag import LLMConfigurationError
from backend.app.services.sources import SourceDeleteConfirmationError, SourceNotFoundError


class FakeSession:
    pass


async def no_auth() -> None:
    return None


async def fake_embedding_client() -> object:
    return object()


async def fake_answer_client() -> object:
    return object()


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> Any:
    async def noop_init_db() -> None:
        return None

    async def override_session() -> AsyncIterator[FakeSession]:
        yield FakeSession()

    monkeypatch.setattr("backend.app.main.init_db", noop_init_db)

    test_app = create_app()
    test_app.dependency_overrides[get_session] = override_session
    yield test_app
    test_app.dependency_overrides.clear()


@pytest.fixture
def transport(app: Any) -> httpx.ASGITransport:
    return httpx.ASGITransport(app=app)


@pytest.mark.asyncio
async def test_knowledge_categories_requires_bearer_token(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_auth_token(_: object) -> str:
        return "secret-token"

    async def fake_list_categories(_: object) -> list[dict[str, object]]:
        return [{"id": 1, "name": "docs"}]

    monkeypatch.setattr("backend.app.core.auth.get_auth_token", fake_get_auth_token)
    monkeypatch.setattr("backend.app.api.routes.knowledge.list_categories", fake_list_categories)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        unauthorized = await client.get("/api/v1/knowledge/categories")
        forbidden = await client.get(
            "/api/v1/knowledge/categories",
            headers={"Authorization": "Bearer wrong-token"},
        )
        invalid_scheme = await client.get(
            "/api/v1/knowledge/categories",
            headers={"Authorization": "Basic secret-token"},
        )
        authorized = await client.get(
            "/api/v1/knowledge/categories",
            headers={"Authorization": "Bearer secret-token"},
        )

    assert unauthorized.status_code == 401
    assert forbidden.status_code == 401
    assert invalid_scheme.status_code == 401
    assert authorized.status_code == 200
    assert authorized.json() == [{"id": 1, "name": "docs"}]


@pytest.mark.asyncio
async def test_knowledge_categories_rejects_when_auth_token_is_unconfigured(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_auth_token(_: object) -> str:
        return ""

    monkeypatch.setattr("backend.app.core.auth.get_auth_token", fake_get_auth_token)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/knowledge/categories",
            headers={"Authorization": "Bearer any-token"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing bearer token."}


@pytest.mark.asyncio
async def test_categories_response_contract(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_list_categories(_: object) -> list[dict[str, object]]:
        return [
            {"id": 1, "name": "engineering"},
            {"id": 2, "name": "finance"},
        ]

    app.dependency_overrides[require_auth_token] = no_auth
    monkeypatch.setattr("backend.app.api.routes.knowledge.list_categories", fake_list_categories)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/knowledge/categories")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "engineering"},
        {"id": 2, "name": "finance"},
    ]


@pytest.mark.asyncio
async def test_search_response_contract(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_kwargs: dict[str, object] = {}

    async def fake_search(**_: object) -> list[dict[str, object]]:
        captured_kwargs.update(_)
        return [
            {
                "id": 10,
                "source_id": "33333333-3333-4333-8333-333333333333",
                "source_title": "runbook.md",
                "source_type": "upload",
                "uri": "upload:runbook.md",
                "categories": [{"id": 2, "name": "docs"}],
                "tags": [{"id": 7, "name": "postgres"}],
                "projects": [
                    {
                        "id": 9,
                        "name": "hub",
                        "description": None,
                        "status": "active",
                        "created_at": None,
                        "updated_at": None,
                    }
                ],
                "location": {
                    "chunk_index": 1,
                    "page": None,
                    "section": "Setup",
                    "start_char": 20,
                    "end_char": 60,
                },
                "content": "result content",
                "score": 0.92,
                "metadata": {"note_type": "decision"},
            }
        ]

    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    monkeypatch.setattr("backend.app.api.routes.knowledge.search_knowledge", fake_search)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/knowledge/search",
            json={
                "query": "find this",
                "limit": 5,
                "category_ids": [2, 3],
                "tag_ids": [7],
                "project_ids": [9],
                "min_score": 0.42,
            },
        )

    assert response.status_code == 200
    assert captured_kwargs["min_score"] == 0.42
    assert captured_kwargs["tag_ids"] == [7]
    assert captured_kwargs["project_ids"] == [9]
    assert captured_kwargs["include_match_reasons"] is False
    assert response.json() == {
        "query": "find this",
        "limit": 5,
        "results": [
            {
                "id": 10,
                "source_id": "33333333-3333-4333-8333-333333333333",
                "source_title": "runbook.md",
                "source_type": "upload",
                "uri": "upload:runbook.md",
                "categories": [{"id": 2, "name": "docs"}],
                "tags": [{"id": 7, "name": "postgres"}],
                "projects": [
                    {
                        "id": 9,
                        "name": "hub",
                        "description": None,
                        "status": "active",
                        "created_at": None,
                        "updated_at": None,
                    }
                ],
                "location": {
                    "chunk_index": 1,
                    "page": None,
                    "section": "Setup",
                    "start_char": 20,
                    "end_char": 60,
                },
                "content": "result content",
                "score": 0.92,
                "metadata": {"note_type": "decision"},
            }
        ],
    }


@pytest.mark.asyncio
async def test_search_response_includes_match_reasons_when_requested(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_kwargs: dict[str, object] = {}

    async def fake_search(**kwargs: object) -> list[dict[str, object]]:
        captured_kwargs.update(kwargs)
        return [
            {
                "id": 10,
                "source_id": "33333333-3333-4333-8333-333333333333",
                "source_title": "runbook.md",
                "source_type": "upload",
            "uri": "upload:runbook.md",
            "categories": [{"id": 2, "name": "docs"}],
            "tags": [{"id": 7, "name": "postgres"}],
                "location": {
                    "chunk_index": 1,
                    "page": None,
                    "section": "Setup",
                    "start_char": 20,
                    "end_char": 60,
                },
                "content": "ERR_CONN_RESET",
                "score": 0.92,
                "metadata": {},
                "match_reasons": ["vector", "text"],
            }
        ]

    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    monkeypatch.setattr("backend.app.api.routes.knowledge.search_knowledge", fake_search)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/knowledge/search",
            json={
                "query": "ERR_CONN_RESET",
                "limit": 5,
                "include_match_reasons": True,
            },
        )

    assert response.status_code == 200
    assert captured_kwargs["include_match_reasons"] is True
    assert response.json()["results"][0]["match_reasons"] == ["vector", "text"]


@pytest.mark.asyncio
async def test_search_response_allows_empty_results(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_search(**_: object) -> list[dict[str, object]]:
        return []

    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    monkeypatch.setattr("backend.app.api.routes.knowledge.search_knowledge", fake_search)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "unknown", "limit": 5, "min_score": 0.8},
        )

    assert response.status_code == 200
    assert response.json() == {"query": "unknown", "limit": 5, "results": []}


@pytest.mark.asyncio
async def test_search_rejects_invalid_min_score(
    app: Any,
    transport: httpx.ASGITransport,
) -> None:
    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        too_low = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "find", "min_score": -0.01},
        )
        too_high = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "find", "min_score": 1.01},
        )

    assert too_low.status_code == 422
    assert too_high.status_code == 422


@pytest.mark.asyncio
async def test_answer_response_contract_includes_citation_sources(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_kwargs: dict[str, object] = {}
    source = {
        "id": 10,
        "source_id": "33333333-3333-4333-8333-333333333333",
        "source_title": "runbook.md",
        "source_type": "upload",
        "uri": "upload:runbook.md",
        "categories": [{"id": 2, "name": "docs"}],
        "tags": [{"id": 7, "name": "postgres"}],
        "projects": [
            {
                "id": 9,
                "name": "hub",
                "description": None,
                "status": "active",
                "created_at": None,
                "updated_at": None,
            }
        ],
        "location": {
            "chunk_index": 1,
            "page": None,
            "section": "Setup",
            "start_char": 20,
            "end_char": 60,
        },
        "content": "result content",
        "score": 0.92,
        "metadata": {},
    }

    async def fake_answer(**_: object) -> tuple[str, list[dict[str, object]]]:
        captured_kwargs.update(_)
        return "answer with citation", [source]

    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    app.dependency_overrides[get_answer_client] = fake_answer_client
    monkeypatch.setattr("backend.app.api.routes.knowledge.answer_knowledge", fake_answer)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/knowledge/answer",
            json={
                "query": "summarize",
                "limit": 5,
                "tag_ids": [7],
                "project_ids": [9],
                "min_score": 0.45,
            },
        )

    assert response.status_code == 200
    assert captured_kwargs["min_score"] == 0.45
    assert captured_kwargs["tag_ids"] == [7]
    assert captured_kwargs["project_ids"] == [9]
    assert response.json() == {
        "query": "summarize",
        "answer": "answer with citation",
        "sources": [source],
    }


@pytest.mark.asyncio
async def test_answer_rejects_invalid_min_score(
    app: Any,
    transport: httpx.ASGITransport,
) -> None:
    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    app.dependency_overrides[get_answer_client] = fake_answer_client

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/knowledge/answer",
            json={"query": "summarize", "min_score": 1.01},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_maps_unknown_category_to_404(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_search(**_: object) -> list[dict[str, object]]:
        raise CategoryNotFoundError("Category 99 does not exist.")

    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    monkeypatch.setattr("backend.app.api.routes.knowledge.search_knowledge", fake_search)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "find this", "category_ids": [99]},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category 99 does not exist."}


@pytest.mark.asyncio
async def test_upload_maps_category_not_found_to_404(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_ingest(**_: object) -> tuple[object, int]:
        raise CategoryNotFoundError("Category 99 does not exist.")

    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    monkeypatch.setattr("backend.app.api.routes.knowledge.ingest_uploaded_file", fake_ingest)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/knowledge/uploads",
            files={"file": ("notes.txt", b"hello world", "text/plain")},
            data={"category_ids": "99"},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category 99 does not exist."}


@pytest.mark.asyncio
async def test_answer_maps_llm_config_error_to_503(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_answer(**_: object) -> tuple[str, list[dict[str, object]]]:
        raise LLMConfigurationError("Missing API key")

    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    app.dependency_overrides[get_answer_client] = fake_answer_client
    monkeypatch.setattr("backend.app.api.routes.knowledge.answer_knowledge", fake_answer)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/knowledge/answer",
            json={"query": "summarize", "limit": 5},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "Missing API key"}


@pytest.mark.asyncio
async def test_text_ingestion_response_contract(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_ingest_text(**_: object) -> tuple[object, int]:
        return (
            SimpleNamespace(
                public_id="11111111-1111-4111-8111-111111111111",
                title="meeting-notes",
                categories=[SimpleNamespace(id=2, name="docs"), SimpleNamespace(id=3, name="ops")],
                tags=[SimpleNamespace(id=7, name="postgres")],
                projects=[SimpleNamespace(id=9, name="hub", status="active")],
            ),
            3,
        )

    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    monkeypatch.setattr("backend.app.api.routes.knowledge.ingest_plain_text", fake_ingest_text)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/knowledge/texts",
            json={
                "title": "meeting-notes",
                "category_ids": [2, 3],
                "tag_ids": [7],
                "project_ids": [9],
                "content": "first line\nsecond line",
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "source_id": "11111111-1111-4111-8111-111111111111",
        "title": "meeting-notes",
        "categories": [{"id": 2, "name": "docs"}, {"id": 3, "name": "ops"}],
        "tags": [{"id": 7, "name": "postgres"}],
        "projects": [{"id": 9, "name": "hub", "description": None, "status": "active", "created_at": None, "updated_at": None}],
        "chunks_created": 3,
    }


@pytest.mark.asyncio
async def test_text_ingestion_accepts_form_data(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_ingest_text(**kwargs: object) -> tuple[object, int]:
        assert kwargs["title"] == "market-notes"
        assert kwargs["content"] == "ações e dividendos"
        assert kwargs["category_ids"] == [1]
        assert kwargs["tag_ids"] == [8]
        assert kwargs["project_ids"] == [9]
        return (
            SimpleNamespace(
                public_id="22222222-2222-4222-8222-222222222222",
                title="market-notes",
                categories=[SimpleNamespace(id=1, name="financeiro")],
                tags=[SimpleNamespace(id=8, name="imposto")],
                projects=[SimpleNamespace(id=9, name="hub", status="active")],
            ),
            1,
        )

    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    monkeypatch.setattr("backend.app.api.routes.knowledge.ingest_plain_text", fake_ingest_text)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/knowledge/texts",
            data={
                "title": "market-notes",
                "content": "ações e dividendos",
                "category_ids": "1",
                "tag_ids": "8",
                "project_ids": "9",
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "source_id": "22222222-2222-4222-8222-222222222222",
        "title": "market-notes",
        "categories": [{"id": 1, "name": "financeiro"}],
        "tags": [{"id": 8, "name": "imposto"}],
        "projects": [{"id": 9, "name": "hub", "description": None, "status": "active", "created_at": None, "updated_at": None}],
        "chunks_created": 1,
    }


@pytest.mark.asyncio
async def test_sources_response_contract(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_list_sources(_: object) -> list[dict[str, object]]:
        return [
            {
                "source_id": "33333333-3333-4333-8333-333333333333",
                "title": "onboarding-guide",
                "categories": [{"id": 4, "name": "docs"}],
                "tags": [{"id": 5, "name": "python"}],
                "projects": [{"id": 9, "name": "hub", "status": "active"}],
                "source_type": "upload",
                "uri": "upload:onboarding-guide.pdf",
                "content_hash": "abc123",
                "created_at": None,
                "updated_at": None,
            }
        ]

    app.dependency_overrides[require_auth_token] = no_auth
    monkeypatch.setattr("backend.app.api.routes.knowledge.list_sources", fake_list_sources)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/knowledge/sources")

    assert response.status_code == 200
    assert response.json() == [
        {
            "source_id": "33333333-3333-4333-8333-333333333333",
            "title": "onboarding-guide",
            "categories": [{"id": 4, "name": "docs"}],
            "tags": [{"id": 5, "name": "python"}],
            "projects": [{"id": 9, "name": "hub", "description": None, "status": "active", "created_at": None, "updated_at": None}],
            "source_type": "upload",
            "uri": "upload:onboarding-guide.pdf",
            "content_hash": "abc123",
            "created_at": None,
            "updated_at": None,
        }
    ]


@pytest.mark.asyncio
async def test_source_lifecycle_response_contracts(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_id = "44444444-4444-4444-8444-444444444444"
    payload = {
        "source_id": source_id,
        "title": "runbook",
        "categories": [{"id": 4, "name": "docs"}],
        "tags": [{"id": 5, "name": "python"}],
        "projects": [{"id": 9, "name": "hub", "status": "active"}],
        "source_type": "text",
        "uri": "text:runbook",
        "content_hash": "abc123",
        "created_at": None,
        "updated_at": None,
        "content": "hello",
    }

    async def fake_get_source_detail(_: object, requested_source_id: str) -> dict[str, object]:
        assert requested_source_id == source_id
        return payload

    async def fake_update_source(**kwargs: object) -> tuple[dict[str, object], int | None]:
        assert kwargs["source_id"] == source_id
        assert kwargs["title"] == "new title"
        assert kwargs["category_ids"] == [4]
        assert kwargs["tag_ids"] == [5]
        assert kwargs["project_ids"] == [9]
        updated = dict(payload)
        updated["title"] = "new title"
        return updated, None

    async def fake_delete_source(_: object, requested_source_id: str, confirm: bool) -> None:
        assert requested_source_id == source_id
        assert confirm is True

    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    monkeypatch.setattr("backend.app.api.routes.knowledge.get_source_detail", fake_get_source_detail)
    monkeypatch.setattr("backend.app.api.routes.knowledge.update_source", fake_update_source)
    monkeypatch.setattr("backend.app.api.routes.knowledge.delete_source", fake_delete_source)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        detail = await client.get(f"/api/v1/knowledge/sources/{source_id}")
        patched = await client.patch(
            f"/api/v1/knowledge/sources/{source_id}",
            json={"title": "new title", "category_ids": [4], "tag_ids": [5], "project_ids": [9]},
        )
        deleted = await client.delete(f"/api/v1/knowledge/sources/{source_id}?confirm=true")

    assert detail.status_code == 200
    assert detail.json()["projects"][0]["id"] == 9
    assert patched.status_code == 200
    assert patched.json()["title"] == "new title"
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_source_lifecycle_status_mapping(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_id = "55555555-5555-4555-8555-555555555555"

    async def missing_source(_: object, __: str) -> dict[str, object]:
        raise SourceNotFoundError("Source does not exist.")

    async def duplicate_update(**_: object) -> tuple[dict[str, object], int | None]:
        existing = SimpleNamespace(public_id="66666666-6666-4666-8666-666666666666")
        raise DuplicateSourceContentError(existing)  # type: ignore[arg-type]

    async def unconfirmed_delete(_: object, __: str, confirm: bool) -> None:
        assert confirm is False
        raise SourceDeleteConfirmationError("Use confirm=true to delete a source.")

    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    monkeypatch.setattr("backend.app.api.routes.knowledge.get_source_detail", missing_source)
    monkeypatch.setattr("backend.app.api.routes.knowledge.update_source", duplicate_update)
    monkeypatch.setattr("backend.app.api.routes.knowledge.delete_source", unconfirmed_delete)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        missing = await client.get(f"/api/v1/knowledge/sources/{source_id}")
        duplicate = await client.patch(
            f"/api/v1/knowledge/sources/{source_id}",
            json={"content": "duplicate"},
        )
        unconfirmed = await client.delete(f"/api/v1/knowledge/sources/{source_id}")

    assert missing.status_code == 404
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["existing_source_id"] == "66666666-6666-4666-8666-666666666666"
    assert unconfirmed.status_code == 400


@pytest.mark.asyncio
async def test_category_crud_status_mapping(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_create_category(_: object, name: str) -> object:
        return SimpleNamespace(id=9, name=name.strip().lower())

    async def fake_update_category(_: object, category_id: int, name: str) -> object:
        return SimpleNamespace(id=category_id, name=name.strip().lower())

    async def fake_delete_category(_: object, category_id: int) -> None:
        assert category_id == 9

    app.dependency_overrides[require_auth_token] = no_auth
    monkeypatch.setattr("backend.app.api.routes.knowledge.create_category", fake_create_category)
    monkeypatch.setattr("backend.app.api.routes.knowledge.update_category", fake_update_category)
    monkeypatch.setattr("backend.app.api.routes.knowledge.delete_category", fake_delete_category)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post("/api/v1/knowledge/categories", json={"name": " Docs "})
        updated = await client.patch("/api/v1/knowledge/categories/9", json={"name": "Manuals"})
        deleted = await client.delete("/api/v1/knowledge/categories/9")

    assert created.status_code == 201
    assert created.json() == {"id": 9, "name": "docs"}
    assert updated.status_code == 200
    assert updated.json() == {"id": 9, "name": "manuals"}
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_category_conflicts_map_to_409(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_create_category(_: object, __: str) -> object:
        raise CategoryConflictError("Category 'docs' already exists.")

    async def fake_delete_category(_: object, __: int) -> None:
        raise CategoryInUseError("Category 1 is in use.")

    app.dependency_overrides[require_auth_token] = no_auth
    monkeypatch.setattr("backend.app.api.routes.knowledge.create_category", fake_create_category)
    monkeypatch.setattr("backend.app.api.routes.knowledge.delete_category", fake_delete_category)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post("/api/v1/knowledge/categories", json={"name": "docs"})
        delete_response = await client.delete("/api/v1/knowledge/categories/1")

    assert create_response.status_code == 409
    assert delete_response.status_code == 409


@pytest.mark.asyncio
async def test_project_lifecycle_and_sources_contracts(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_payload = {
        "id": 9,
        "name": "hub",
        "description": "contexto",
        "status": "active",
        "created_at": None,
        "updated_at": None,
    }

    async def fake_list_projects(_: object, status: str | None = None) -> list[dict[str, object]]:
        assert status == "active"
        return [project_payload]

    async def fake_create_project(_: object, name: str, description: str | None = None) -> object:
        assert name == "Hub"
        assert description == "contexto"
        return SimpleNamespace(**project_payload)

    async def fake_update_project(
        _: object,
        project_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> object:
        assert project_id == 9
        assert name == "Hub 2"
        assert description == "novo"
        return SimpleNamespace(**{**project_payload, "name": "hub 2", "description": "novo"})

    async def fake_archive_project(_: object, project_id: int) -> object:
        assert project_id == 9
        return SimpleNamespace(**{**project_payload, "status": "archived"})

    async def fake_reactivate_project(_: object, project_id: int) -> object:
        assert project_id == 9
        return SimpleNamespace(**project_payload)

    async def fake_project_sources(_: object, project_id: int) -> list[dict[str, object]]:
        assert project_id == 9
        return [
            {
                "source_id": "33333333-3333-4333-8333-333333333333",
                "title": "notes",
                "categories": [{"id": 1, "name": "docs"}],
                "tags": [],
                "projects": [project_payload],
                "source_type": "text",
                "uri": "text:notes",
                "content_hash": "abc123",
                "created_at": None,
                "updated_at": None,
            }
        ]

    app.dependency_overrides[require_auth_token] = no_auth
    monkeypatch.setattr("backend.app.api.routes.knowledge.list_projects", fake_list_projects)
    monkeypatch.setattr("backend.app.api.routes.knowledge.create_project", fake_create_project)
    monkeypatch.setattr("backend.app.api.routes.knowledge.update_project", fake_update_project)
    monkeypatch.setattr("backend.app.api.routes.knowledge.archive_project", fake_archive_project)
    monkeypatch.setattr("backend.app.api.routes.knowledge.reactivate_project", fake_reactivate_project)
    monkeypatch.setattr("backend.app.api.routes.knowledge.list_project_sources", fake_project_sources)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        listed = await client.get("/api/v1/knowledge/projects?status=active")
        created = await client.post(
            "/api/v1/knowledge/projects",
            json={"name": " Hub ", "description": "contexto"},
        )
        updated = await client.patch(
            "/api/v1/knowledge/projects/9",
            json={"name": "Hub 2", "description": "novo"},
        )
        archived = await client.post("/api/v1/knowledge/projects/9/archive")
        reactivated = await client.post("/api/v1/knowledge/projects/9/reactivate")
        sources = await client.get("/api/v1/knowledge/projects/9/sources")

    assert listed.status_code == 200
    assert listed.json() == [project_payload]
    assert created.status_code == 201
    assert created.json() == project_payload
    assert updated.status_code == 200
    assert updated.json()["name"] == "hub 2"
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    assert reactivated.status_code == 200
    assert sources.status_code == 200
    assert sources.json()[0]["projects"] == [project_payload]


@pytest.mark.asyncio
async def test_project_status_mapping(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def duplicate_project(_: object, __: str, ___: str | None = None) -> object:
        raise ProjectConflictError("Project 'hub' already exists.")

    async def missing_project(_: object, __: int, **___: object) -> object:
        raise ProjectNotFoundError("Project 9 does not exist.")

    async def invalid_status(_: object, status: str | None = None) -> list[dict[str, object]]:
        raise ProjectStatusError(f"Invalid project status: {status}.")

    app.dependency_overrides[require_auth_token] = no_auth
    monkeypatch.setattr("backend.app.api.routes.knowledge.create_project", duplicate_project)
    monkeypatch.setattr("backend.app.api.routes.knowledge.update_project", missing_project)
    monkeypatch.setattr("backend.app.api.routes.knowledge.list_projects", invalid_status)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post("/api/v1/knowledge/projects", json={"name": "hub"})
        update_response = await client.patch("/api/v1/knowledge/projects/9", json={"name": "hub"})
        list_response = await client.get("/api/v1/knowledge/projects?status=bad")

    assert create_response.status_code == 409
    assert update_response.status_code == 404
    assert list_response.status_code == 422


@pytest.mark.asyncio
async def test_tag_crud_and_autocomplete_contracts(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_list_tags(_: object) -> list[dict[str, object]]:
        return [{"id": 9, "name": "postgres"}]

    async def fake_autocomplete_tags(_: object, query: str, limit: int) -> list[dict[str, object]]:
        assert query == "po"
        assert limit == 5
        return [{"id": 9, "name": "postgres"}]

    async def fake_create_tag(_: object, name: str) -> object:
        return SimpleNamespace(id=9, name=name.strip().lower())

    async def fake_update_tag(_: object, tag_id: int, name: str) -> object:
        return SimpleNamespace(id=tag_id, name=name.strip().lower())

    async def fake_delete_tag(_: object, tag_id: int) -> None:
        assert tag_id == 9

    app.dependency_overrides[require_auth_token] = no_auth
    monkeypatch.setattr("backend.app.api.routes.knowledge.list_tags", fake_list_tags)
    monkeypatch.setattr("backend.app.api.routes.knowledge.autocomplete_tags", fake_autocomplete_tags)
    monkeypatch.setattr("backend.app.api.routes.knowledge.create_tag", fake_create_tag)
    monkeypatch.setattr("backend.app.api.routes.knowledge.update_tag", fake_update_tag)
    monkeypatch.setattr("backend.app.api.routes.knowledge.delete_tag", fake_delete_tag)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        listed = await client.get("/api/v1/knowledge/tags")
        completed = await client.get("/api/v1/knowledge/tags/autocomplete?q=po&limit=5")
        created = await client.post("/api/v1/knowledge/tags", json={"name": " Postgres "})
        updated = await client.patch("/api/v1/knowledge/tags/9", json={"name": "RAG"})
        deleted = await client.delete("/api/v1/knowledge/tags/9")

    assert listed.status_code == 200
    assert listed.json() == [{"id": 9, "name": "postgres"}]
    assert completed.status_code == 200
    assert completed.json() == [{"id": 9, "name": "postgres"}]
    assert created.status_code == 201
    assert created.json() == {"id": 9, "name": "postgres"}
    assert updated.status_code == 200
    assert updated.json() == {"id": 9, "name": "rag"}
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_tag_status_mapping(
    app: Any,
    transport: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def duplicate_tag(_: object, __: str) -> object:
        raise TagConflictError("Tag 'postgres' already exists.")

    async def missing_tag(_: object, __: int, ___: str) -> object:
        raise TagNotFoundError("Tag 9 does not exist.")

    async def in_use_tag(_: object, __: int) -> None:
        raise TagInUseError("Tag 9 is in use.")

    app.dependency_overrides[require_auth_token] = no_auth
    monkeypatch.setattr("backend.app.api.routes.knowledge.create_tag", duplicate_tag)
    monkeypatch.setattr("backend.app.api.routes.knowledge.update_tag", missing_tag)
    monkeypatch.setattr("backend.app.api.routes.knowledge.delete_tag", in_use_tag)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post("/api/v1/knowledge/tags", json={"name": "postgres"})
        update_response = await client.patch("/api/v1/knowledge/tags/9", json={"name": "rag"})
        delete_response = await client.delete("/api/v1/knowledge/tags/9")

    assert create_response.status_code == 409
    assert update_response.status_code == 404
    assert delete_response.status_code == 409
