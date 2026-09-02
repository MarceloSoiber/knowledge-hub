from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_session
from ..services.embeddings import EmbeddingClient, build_embedding_client
from ..services.rag import AnswerClient, build_answer_client
from ..services.config import resolve_ai_settings


async def get_embedding_client(
    session: AsyncSession = Depends(get_session),
) -> EmbeddingClient:
    return build_embedding_client(await resolve_ai_settings(session))


async def get_answer_client(
    session: AsyncSession = Depends(get_session),
) -> AnswerClient:
    return build_answer_client(await resolve_ai_settings(session))
