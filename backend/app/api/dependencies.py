from __future__ import annotations

from ..services.embeddings import EmbeddingClient, build_embedding_client
from ..services.rag import AnswerClient, build_answer_client


def get_embedding_client() -> EmbeddingClient:
    return build_embedding_client()


def get_answer_client() -> AnswerClient:
    return build_answer_client()
