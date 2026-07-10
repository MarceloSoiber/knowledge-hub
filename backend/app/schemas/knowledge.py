from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, Field, StringConstraints


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
CategoryStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]
TitleStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]


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
    query: NonEmptyStr
    limit: int = Field(default=5, ge=1, le=50)
    category: CategoryStr | None = None


class KnowledgeSearchResponse(BaseModel):
    query: str
    limit: int
    results: list[KnowledgeChunkRead]


class KnowledgeUploadResponse(BaseModel):
    source_id: int
    title: str
    category: str
    chunks_created: int


class KnowledgeUploadRequest(BaseModel):
    category: CategoryStr

    @classmethod
    def as_form(cls, category: Annotated[str, Form(...)]) -> "KnowledgeUploadRequest":
        return cls(category=category)


class KnowledgeTextIngestRequest(BaseModel):
    title: TitleStr
    category: CategoryStr
    content: NonEmptyStr


class KnowledgeAnswerRequest(BaseModel):
    query: NonEmptyStr
    limit: int = Field(default=5, ge=1, le=20)
    category: CategoryStr | None = None


class KnowledgeAnswerResponse(BaseModel):
    query: str
    answer: str
    sources: list[KnowledgeChunkRead]
