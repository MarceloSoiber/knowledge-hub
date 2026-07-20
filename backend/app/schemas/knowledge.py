from datetime import datetime
from typing import Annotated, Any

from fastapi import Form
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
TitleStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CategoryWrite(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class KnowledgeSourceRead(BaseModel):
    source_id: str
    title: str
    categories: list[CategoryRead]
    source_type: str
    uri: str
    content_hash: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KnowledgeSourceDetail(KnowledgeSourceRead):
    content: str


class KnowledgeSourcePatchRequest(BaseModel):
    title: TitleStr | None = None
    category_ids: list[int] | None = None
    content: NonEmptyStr | None = None

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_category_ids(value)

    @model_validator(mode="after")
    def require_any_field(self) -> "KnowledgeSourcePatchRequest":
        if self.title is None and self.category_ids is None and self.content is None:
            raise ValueError("At least one source field must be provided.")
        return self


class KnowledgeChunkLocation(BaseModel):
    chunk_index: int
    page: int | None = None
    section: str | None = None
    start_char: int
    end_char: int


class KnowledgeChunkRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    source_id: str
    source_title: str
    source_type: str
    uri: str
    categories: list[CategoryRead]
    location: KnowledgeChunkLocation
    content: str
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchRequest(BaseModel):
    query: NonEmptyStr
    limit: int = Field(default=5, ge=1, le=50)
    category_ids: list[int] | None = Field(default=None)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    include_match_reasons: bool = Field(default=False)

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_category_ids(value)


class KnowledgeSearchResponse(BaseModel):
    query: str
    limit: int
    results: list[KnowledgeChunkRead]


class KnowledgeUploadResponse(BaseModel):
    source_id: str
    title: str
    categories: list[CategoryRead]
    chunks_created: int


class KnowledgeUploadRequest(BaseModel):
    category_ids: list[int]

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, value: list[int]) -> list[int]:
        return validate_required_category_ids(value)

    @classmethod
    async def as_form(
        cls, category_ids: Annotated[list[int], Form(...)]
    ) -> "KnowledgeUploadRequest":
        return cls(category_ids=category_ids)


class KnowledgeTextIngestRequest(BaseModel):
    title: TitleStr
    category_ids: list[int]
    content: NonEmptyStr

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, value: list[int]) -> list[int]:
        return validate_required_category_ids(value)


class KnowledgeAnswerRequest(BaseModel):
    query: NonEmptyStr
    limit: int = Field(default=5, ge=1, le=20)
    category_ids: list[int] | None = Field(default=None)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    include_match_reasons: bool = Field(default=False)

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_category_ids(value)


class KnowledgeAnswerResponse(BaseModel):
    query: str
    answer: str
    sources: list[KnowledgeChunkRead]


def validate_required_category_ids(value: list[int]) -> list[int]:
    if not value:
        raise ValueError("At least one category id is required.")
    return validate_category_id_list(value)


def validate_optional_category_ids(value: list[int] | None) -> list[int] | None:
    if value is None:
        return None
    if not value:
        raise ValueError("Category id filter must not be empty.")
    return validate_category_id_list(value)


def validate_category_id_list(value: list[int]) -> list[int]:
    if any(category_id < 1 for category_id in value):
        raise ValueError("Category ids must be greater than zero.")
    if len(set(value)) != len(value):
        raise ValueError("Category ids must not contain duplicates.")
    return value
