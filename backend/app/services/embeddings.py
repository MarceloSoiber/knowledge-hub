from __future__ import annotations

import httpx

from ..core.settings import Settings, get_settings


class EmbeddingError(RuntimeError):
    pass


class EmbeddingConfigurationError(EmbeddingError):
    pass


class EmbeddingClient:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class OpenAIEmbeddingClient(EmbeddingClient):
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if not self.settings.api_key:
            raise EmbeddingConfigurationError("API_KEY is required to generate embeddings.")

        url = f"{self.settings.api_llm_base_url.rstrip('/')}/embeddings"
        headers = {"Authorization": f"Bearer {self.settings.api_key}"}
        payload = {"model": self.settings.embedding_model, "input": texts}

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code >= 400:
            raise EmbeddingError(f"Embedding provider returned HTTP {response.status_code}.")

        data = response.json()
        vectors = [
            item["embedding"] for item in sorted(data["data"], key=lambda item: item["index"])
        ]
        expected_dim = self.settings.vector_dim
        for vector in vectors:
            if len(vector) != expected_dim:
                raise EmbeddingError(
                    f"Embedding dimension mismatch: expected {expected_dim}, got {len(vector)}."
                )

        return vectors


def build_embedding_client(settings: Settings | None = None) -> EmbeddingClient:
    return OpenAIEmbeddingClient(settings)
