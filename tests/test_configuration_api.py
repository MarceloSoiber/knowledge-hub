from __future__ import annotations

from typing import Any

import httpx
import pytest

from backend.app.core.auth import require_auth_token
from backend.app.main import create_app


async def no_auth() -> None:
    return None


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> Any:
    async def noop_init_db() -> None:
        return None

    monkeypatch.setattr("backend.app.main.init_db", noop_init_db)
    test_app = create_app()
    test_app.dependency_overrides[require_auth_token] = no_auth
    yield test_app
    test_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_ai_configuration_never_returns_api_key(
    app: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_configuration(_: object) -> dict[str, object]:
        return {
            "llm_provider": "local",
            "local_llm_base_url": "http://127.0.0.1:1234",
            "local_llm_model": "gpt-oss-20b",
            "api_llm_base_url": "https://api.openai.com/v1",
            "api_llm_model": "gpt-4.1-mini",
            "api_key_configured": True,
            "embedding_model": "text-embedding-nomic-embed-text-v1.5",
            "vector_dim": 768,
            "origins": {"llm_provider": "portal"},
        }

    monkeypatch.setattr(
        "backend.app.api.routes.configuration.get_effective_ai_configuration", fake_configuration
    )
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/configuration/ai")

    assert response.status_code == 200
    assert response.json()["api_key_configured"] is True
    assert "api_key" not in response.json()


@pytest.mark.asyncio
async def test_update_ai_configuration_rejects_vector_dimension_change(
    app: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from backend.app.services.config import VectorDimensionChangeRequired

    async def reject_dimension(_: object, __: object) -> object:
        raise VectorDimensionChangeRequired("VECTOR_DIM requires a pgvector migration")

    monkeypatch.setattr(
        "backend.app.api.routes.configuration.update_ai_configuration", reject_dimension
    )
    payload = {
        "llm_provider": "local",
        "local_llm_base_url": "http://127.0.0.1:1234",
        "local_llm_model": "gpt-oss-20b",
        "api_llm_base_url": "https://api.openai.com/v1",
        "api_llm_model": "gpt-4.1-mini",
        "embedding_model": "text-embedding-nomic-embed-text-v1.5",
        "vector_dim": 1024,
    }
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put("/api/v1/configuration/ai", json=payload)

    assert response.status_code == 409
    assert "VECTOR_DIM" in response.json()["detail"]
