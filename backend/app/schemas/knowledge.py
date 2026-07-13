from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, Field, StringConstraints


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
TitleStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]


class CategoryRead(BaseModel):
    id: int
    name: str


class KnowledgeSourceRead(BaseModel):
    id: int
    title: str
    category_id: int
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
    category_id: int | None = Field(default=None, ge=1)


class KnowledgeSearchResponse(BaseModel):
    query: str
    limit: int
    results: list[KnowledgeChunkRead]


class KnowledgeUploadResponse(BaseModel):
    source_id: int
    title: str
    category_id: int
    chunks_created: int


class KnowledgeUploadRequest(BaseModel):
    category_id: int = Field(ge=1)

    @classmethod
    def as_form(cls, category_id: Annotated[int, Form(...)]) -> "KnowledgeUploadRequest":
        return cls(category_id=category_id)


class KnowledgeTextIngestRequest(BaseModel):
    title: TitleStr
    category_id: int = Field(ge=1)
    content: NonEmptyStr


class KnowledgeAnswerRequest(BaseModel):
    query: NonEmptyStr
    limit: int = Field(default=5, ge=1, le=20)
    category_id: int | None = Field(default=None, ge=1)


class KnowledgeAnswerResponse(BaseModel):
    query: str
    answer: str
    sources: list[KnowledgeChunkRead]
