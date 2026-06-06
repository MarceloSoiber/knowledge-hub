from fastapi import APIRouter

from ...schemas.knowledge import KnowledgeSearchRequest, KnowledgeSearchResponse
from ...services.knowledge import list_sources, search_knowledge

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/search", response_model=KnowledgeSearchResponse)
async def knowledge_search(payload: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
    results = await search_knowledge(payload.query, payload.limit)
    return KnowledgeSearchResponse(query=payload.query, limit=payload.limit, results=results)


@router.get("/sources")
async def knowledge_sources() -> list[dict[str, str | int]]:
    return await list_sources()