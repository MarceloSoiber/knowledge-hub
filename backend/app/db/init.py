from sqlalchemy import text

from .base import Base
from .models import AppConfig, DocumentSource, KnowledgeChunk  # noqa: F401
from .session import engine


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text(
                "ALTER TABLE document_sources "
                "ADD COLUMN IF NOT EXISTS category VARCHAR(100) "
                "NOT NULL DEFAULT 'uncategorized'"
            )
        )
        await connection.execute(
            text("ALTER TABLE knowledge_chunks ALTER COLUMN embedding TYPE vector(768)")
        )
