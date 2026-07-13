from pydantic import BaseModel, Field

from backend.app.db.session import SessionLocal
from backend.app.services.embeddings import build_embedding_client
from backend.app.services.knowledge import list_categories, list_sources
from backend.app.services.knowledge import search_knowledge as search_backend_knowledge


class KnowledgeHit(BaseModel):
    id: int = Field(description="ID do chunk encontrado")
    source_id: int = Field(description="ID da origem do chunk")
    content: str = Field(description="Conteúdo encontrado")
    score: float | None = Field(default=None, description="Score de relevância")


class KnowledgeSource(BaseModel):
    id: int
    title: str
    category_id: int
    source_type: str
    uri: str


class KnowledgeCategory(BaseModel):
    id: int
    name: str


async def search_knowledge(
    query: str,
    limit: int = 5,
    category_id: int | None = None,
) -> list[KnowledgeHit]:
    async with SessionLocal() as session:
        results = await search_backend_knowledge(
            session=session,
            query=query,
            limit=limit,
            category_id=category_id,
            embedding_client=build_embedding_client(),
        )
    return [KnowledgeHit(**result.model_dump()) for result in results]


async def get_knowledge_sources() -> list[KnowledgeSource]:
    async with SessionLocal() as session:
        sources = await list_sources(session)
    return [KnowledgeSource(**source) for source in sources]


async def get_knowledge_categories() -> list[KnowledgeCategory]:
    async with SessionLocal() as session:
        categories = await list_categories(session)
    return [KnowledgeCategory(**category) for category in categories]


def get_workspace_overview() -> dict[str, str]:
    return {
        "frontend": "Vite + React",
        "backend": "FastAPI",
        "database": "PostgreSQL + pgvector",
        "mcp": "FastMCP streamable-http",
        "llm": "local ou API via settings",
    }
