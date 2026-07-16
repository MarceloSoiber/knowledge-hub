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
from backend.app.services.rag import LLMConfigurationError


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
    async def fake_search(**_: object) -> list[dict[str, object]]:
        return [
            {
                "id": 10,
                "source_id": 3,
                "content": "result content",
                "score": 0.92,
            }
        ]

    app.dependency_overrides[require_auth_token] = no_auth
    app.dependency_overrides[get_embedding_client] = fake_embedding_client
    monkeypatch.setattr("backend.app.api.routes.knowledge.search_knowledge", fake_search)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "find this", "limit": 5, "category_ids": [2, 3]},
        )

    assert response.status_code == 200
    assert response.json() == {
        "query": "find this",
        "limit": 5,
        "results": [
            {
                "id": 10,
                "source_id": 3,
                "content": "result content",
                "score": 0.92,
            }
        ],
    }


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
                id=12,
                title="meeting-notes",
                categories=[SimpleNamespace(id=2, name="docs"), SimpleNamespace(id=3, name="ops")],
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
                "content": "first line\nsecond line",
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "source_id": 12,
        "title": "meeting-notes",
        "categories": [{"id": 2, "name": "docs"}, {"id": 3, "name": "ops"}],
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
        return (
            SimpleNamespace(
                id=13,
                title="market-notes",
                categories=[SimpleNamespace(id=1, name="financeiro")],
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
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "source_id": 13,
        "title": "market-notes",
        "categories": [{"id": 1, "name": "financeiro"}],
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
                "id": 1,
                "title": "onboarding-guide",
                "categories": [{"id": 4, "name": "docs"}],
                "source_type": "upload",
                "uri": "upload:onboarding-guide.pdf",
            }
        ]

    app.dependency_overrides[require_auth_token] = no_auth
    monkeypatch.setattr("backend.app.api.routes.knowledge.list_sources", fake_list_sources)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/knowledge/sources")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "title": "onboarding-guide",
            "categories": [{"id": 4, "name": "docs"}],
            "source_type": "upload",
            "uri": "upload:onboarding-guide.pdf",
        }
    ]


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
