from __future__ import annotations

import httpx

from ..core.settings import Settings, get_settings
from ..schemas.knowledge import KnowledgeChunkRead


class LLMError(RuntimeError):
    pass


class LLMConfigurationError(LLMError):
    pass


class AnswerClient:
    async def answer(self, query: str, sources: list[KnowledgeChunkRead]) -> str:
        raise NotImplementedError


def openai_base_url(base_url: str) -> str:
    clean_base_url = base_url.rstrip("/")
    if clean_base_url.endswith("/v1"):
        return clean_base_url
    return f"{clean_base_url}/v1"


class OpenAICompatibleAnswerClient(AnswerClient):
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def answer(self, query: str, sources: list[KnowledgeChunkRead]) -> str:
        if self.settings.llm_provider == "api" and not self.settings.api_key:
            raise LLMConfigurationError("API_KEY is required to generate answers with API LLM.")

        if self.settings.llm_provider == "api":
            base_url = self.settings.api_llm_base_url
            model = self.settings.api_llm_model
            headers = {"Authorization": f"Bearer {self.settings.api_key}"}
        else:
            base_url = self.settings.local_llm_base_url
            model = self.settings.local_llm_model
            headers = {}

        context = "\n\n".join(
            f"[source_id={source.source_id}; chunk_id={source.id}]\n{source.content}"
            for source in sources
        )
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Responda usando apenas o contexto fornecido. "
                        "Se o contexto nao contiver a resposta, "
                        "diga que nao encontrou essa informacao."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Contexto:\n{context}\n\nPergunta:\n{query}",
                },
            ],
            "temperature": 0.2,
        }

        url = f"{openai_base_url(base_url)}/chat/completions"
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code >= 400:
            raise LLMError(f"LLM provider returned HTTP {response.status_code}.")

        data = response.json()
        return data["choices"][0]["message"]["content"]


def build_answer_client(settings: Settings | None = None) -> AnswerClient:
    return OpenAICompatibleAnswerClient(settings)
