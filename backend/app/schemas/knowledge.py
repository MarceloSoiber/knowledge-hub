from pydantic import BaseModel, Field


class KnowledgeSourceRead(BaseModel):
    id: int
    title: str
    source_type: str
    uri: str


class KnowledgeChunkRead(BaseModel):
    id: int
    source_id: int
    content: str
    score: float | None = None


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=50)


class KnowledgeSearchResponse(BaseModel):
    query: str
    limit: int
    results: list[KnowledgeChunkRead]