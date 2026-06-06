from ..schemas.knowledge import KnowledgeChunkRead


async def search_knowledge(query: str, limit: int = 5) -> list[KnowledgeChunkRead]:
    _ = query
    return []


async def list_sources() -> list[dict[str, str | int]]:
    return []