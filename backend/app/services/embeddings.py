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


def openai_base_url(base_url: str) -> str:
    clean_base_url = base_url.rstrip("/")
    if clean_base_url.endswith("/v1"):
        return clean_base_url
    return f"{clean_base_url}/v1"


class OpenAIEmbeddingClient(EmbeddingClient):
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if self.settings.llm_provider == "local":
            base_url = self.settings.local_llm_base_url
            headers = {}
        else:
            base_url = self.settings.api_llm_base_url
            headers = {"Authorization": f"Bearer {self.settings.api_key}"}

        if self.settings.llm_provider != "local" and not self.settings.api_key:
            raise EmbeddingConfigurationError("API_KEY is required to generate embeddings.")

        url = f"{openai_base_url(base_url)}/embeddings"
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
