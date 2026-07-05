from pydantic import BaseModel, Field


class KnowledgeSourceRead(BaseModel):
    id: int
    title: str
    category: str
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
    category: str | None = Field(default=None, min_length=1, max_length=100)


class KnowledgeSearchResponse(BaseModel):
    query: str
    limit: int
    results: list[KnowledgeChunkRead]


class KnowledgeUploadResponse(BaseModel):
    source_id: int
    title: str
    category: str
    chunks_created: int


class KnowledgeAnswerRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)
    category: str | None = Field(default=None, min_length=1, max_length=100)


class KnowledgeAnswerResponse(BaseModel):
    query: str
    answer: str
    sources: list[KnowledgeChunkRead]
