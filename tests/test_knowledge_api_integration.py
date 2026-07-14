from __future__ import annotations

from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.app.core.auth import require_auth_token
from backend.app.db.session import get_session
from backend.app.main import create_app
from backend.app.services.knowledge import CategoryNotFoundError
from backend.app.services.rag import LLMConfigurationError


class FakeSession:
    pass


@pytest.fixture
def app_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[tuple[TestClient, Any]]:
    async def noop_init_db() -> None:
        return None

    async def override_session() -> AsyncIterator[FakeSession]:
        yield FakeSession()

    monkeypatch.setattr("backend.app.main.init_db", noop_init_db)

    app = create_app()
    app.dependency_overrides[get_session] = override_session

    with TestClient(app) as client:
        yield client, app

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_knowledge_categories_requires_bearer_token(
    app_client: tuple[TestClient, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = app_client

    async def fake_get_auth_token(_: object) -> str:
        return "secret-token"

    async def fake_list_categories(_: object) -> list[dict[str, object]]:
        return [{"id": 1, "name": "docs"}]

    monkeypatch.setattr("backend.app.core.auth.get_auth_token", fake_get_auth_token)
    monkeypatch.setattr("backend.app.api.routes.knowledge.list_categories", fake_list_categories)

    unauthorized = client.get("/api/v1/knowledge/categories")
    assert unauthorized.status_code == 401

    forbidden = client.get(
        "/api/v1/knowledge/categories",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert forbidden.status_code == 401

    invalid_scheme = client.get(
        "/api/v1/knowledge/categories",
        headers={"Authorization": "Basic secret-token"},
    )
    assert invalid_scheme.status_code == 401

    authorized = client.get(
        "/api/v1/knowledge/categories",
        headers={"Authorization": "Bearer secret-token"},
    )
    assert authorized.status_code == 200
    assert authorized.json() == [{"id": 1, "name": "docs"}]


def test_categories_response_contract(
    app_client: tuple[TestClient, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, app = app_client

    async def fake_list_categories(_: object) -> list[dict[str, object]]:
        return [
            {"id": 1, "name": "engineering"},
            {"id": 2, "name": "finance"},
        ]

    app.dependency_overrides[require_auth_token] = lambda: None
    monkeypatch.setattr("backend.app.api.routes.knowledge.list_categories", fake_list_categories)

    response = client.get("/api/v1/knowledge/categories")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "engineering"},
        {"id": 2, "name": "finance"},
    ]


def test_search_response_contract(
    app_client: tuple[TestClient, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, app = app_client

    async def fake_search(**_: object) -> list[dict[str, object]]:
        return [
            {
                "id": 10,
                "source_id": 3,
                "content": "result content",
                "score": 0.92,
            }
        ]

    app.dependency_overrides[require_auth_token] = lambda: None
    monkeypatch.setattr("backend.app.api.routes.knowledge.build_embedding_client", lambda: object())
    monkeypatch.setattr("backend.app.api.routes.knowledge.search_knowledge", fake_search)

    response = client.post(
        "/api/v1/knowledge/search",
        json={"query": "find this", "limit": 5},
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


def test_upload_maps_category_not_found_to_404(
    app_client: tuple[TestClient, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, app = app_client

    async def fake_ingest(**_: object) -> tuple[object, int]:
        raise CategoryNotFoundError("Category 99 does not exist.")

    app.dependency_overrides[require_auth_token] = lambda: None
    monkeypatch.setattr("backend.app.api.routes.knowledge.build_embedding_client", lambda: object())
    monkeypatch.setattr("backend.app.api.routes.knowledge.ingest_uploaded_file", fake_ingest)

    response = client.post(
        "/api/v1/knowledge/uploads",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
        data={"category_id": "99"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category 99 does not exist."}


def test_answer_maps_llm_config_error_to_503(
    app_client: tuple[TestClient, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, app = app_client

    async def fake_answer(**_: object) -> tuple[str, list[dict[str, object]]]:
        raise LLMConfigurationError("Missing API key")

    app.dependency_overrides[require_auth_token] = lambda: None
    monkeypatch.setattr("backend.app.api.routes.knowledge.build_embedding_client", lambda: object())
    monkeypatch.setattr("backend.app.api.routes.knowledge.build_answer_client", lambda: object())
    monkeypatch.setattr("backend.app.api.routes.knowledge.answer_knowledge", fake_answer)

    response = client.post(
        "/api/v1/knowledge/answer",
        json={"query": "summarize", "limit": 5},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Missing API key"}


def test_text_ingestion_response_contract(
    app_client: tuple[TestClient, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, app = app_client

    async def fake_ingest_text(**_: object) -> tuple[object, int]:
        return (
            SimpleNamespace(id=12, title="meeting-notes", category_id=2),
            3,
        )

    app.dependency_overrides[require_auth_token] = lambda: None
    monkeypatch.setattr("backend.app.api.routes.knowledge.build_embedding_client", lambda: object())
    monkeypatch.setattr("backend.app.api.routes.knowledge.ingest_plain_text", fake_ingest_text)

    response = client.post(
        "/api/v1/knowledge/texts",
        json={
            "title": "meeting-notes",
            "category_id": 2,
            "content": "first line\\nsecond line",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "source_id": 12,
        "title": "meeting-notes",
        "category_id": 2,
        "chunks_created": 3,
    }


def test_sources_response_contract(
    app_client: tuple[TestClient, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, app = app_client

    async def fake_list_sources(_: object) -> list[dict[str, object]]:
        return [
            {
                "id": 1,
                "title": "onboarding-guide",
                "category_id": 4,
                "source_type": "upload",
                "uri": "upload:docs:onboarding-guide.pdf",
            }
        ]

    app.dependency_overrides[require_auth_token] = lambda: None
    monkeypatch.setattr("backend.app.api.routes.knowledge.list_sources", fake_list_sources)

    response = client.get("/api/v1/knowledge/sources")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "title": "onboarding-guide",
            "category_id": 4,
            "source_type": "upload",
            "uri": "upload:docs:onboarding-guide.pdf",
        }
    ]
