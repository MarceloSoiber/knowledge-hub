from pydantic import BaseModel, Field


class KnowledgeHit(BaseModel):
    title: str = Field(description="Título do item encontrado")
    summary: str = Field(description="Resumo curto do item")
    source: str = Field(description="Origem do item")
    score: float = Field(description="Score de relevância")


async def search_knowledge(query: str, limit: int = 5) -> list[KnowledgeHit]:
    _ = query
    return [] if limit > 0 else []


def get_workspace_overview() -> dict[str, str]:
    return {
        "frontend": "Vite + React",
        "backend": "FastAPI",
        "database": "PostgreSQL + pgvector",
        "mcp": "FastMCP stdio",
        "llm": "local ou API via settings",
    }