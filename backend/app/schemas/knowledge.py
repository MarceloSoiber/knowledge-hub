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


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TagWrite(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectWrite(BaseModel):
    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
    ]
    description: Annotated[
        str,
        StringConstraints(strip_whitespace=True, max_length=2000),
    ] | None = None


class ProjectPatch(BaseModel):
    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
    ] | None = None
    description: Annotated[
        str,
        StringConstraints(strip_whitespace=True, max_length=2000),
    ] | None = None

    @model_validator(mode="after")
    def require_any_field(self) -> "ProjectPatch":
        if self.name is None and self.description is None:
            raise ValueError("At least one project field must be provided.")
        return self


class KnowledgeSourceRead(BaseModel):
    source_id: str
    title: str
    categories: list[CategoryRead]
    tags: list[TagRead] = Field(default_factory=list)
    projects: list[ProjectRead] = Field(default_factory=list)
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
    tag_ids: list[int] | None = None
    project_ids: list[int] | None = None
    content: NonEmptyStr | None = None

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_category_ids(value)

    @field_validator("tag_ids")
    @classmethod
    def validate_tag_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_source_patch_tag_ids(value)

    @field_validator("project_ids")
    @classmethod
    def validate_project_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_source_patch_project_ids(value)

    @model_validator(mode="after")
    def require_any_field(self) -> "KnowledgeSourcePatchRequest":
        if (
            self.title is None
            and self.category_ids is None
            and self.tag_ids is None
            and self.project_ids is None
            and self.content is None
        ):
            raise ValueError("At least one source field must be provided.")
        return self


class KnowledgeChunkLocation(BaseModel):
    chunk_index: int
    page: int | None = None
    section: str | None = None
    start_char: int
    end_char: int


class KnowledgeEmbeddingRead(BaseModel):
    status: str
    provider: str | None = None
    model: str | None = None
    dimension: int | None = None
    version: str | None = None
    embedded_at: datetime | None = None


class KnowledgeChunkRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    source_id: str
    source_title: str
    source_type: str
    uri: str
    categories: list[CategoryRead]
    tags: list[TagRead] = Field(default_factory=list)
    projects: list[ProjectRead] = Field(default_factory=list)
    location: KnowledgeChunkLocation
    content: str
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchRequest(BaseModel):
    query: NonEmptyStr
    limit: int = Field(default=5, ge=1, le=50)
    category_ids: list[int] | None = Field(default=None)
    tag_ids: list[int] | None = Field(default=None)
    project_ids: list[int] | None = Field(default=None)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    include_match_reasons: bool = Field(default=False)

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_category_ids(value)

    @field_validator("tag_ids")
    @classmethod
    def validate_tag_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_tag_ids(value)

    @field_validator("project_ids")
    @classmethod
    def validate_project_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_project_ids(value)


class KnowledgeSearchResponse(BaseModel):
    query: str
    limit: int
    results: list[KnowledgeChunkRead]


class KnowledgeUploadResponse(BaseModel):
    source_id: str
    title: str
    categories: list[CategoryRead]
    tags: list[TagRead] = Field(default_factory=list)
    projects: list[ProjectRead] = Field(default_factory=list)
    chunks_created: int


class KnowledgeUploadRequest(BaseModel):
    category_ids: list[int]
    tag_ids: list[int] | None = None
    project_ids: list[int] | None = None

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, value: list[int]) -> list[int]:
        return validate_required_category_ids(value)

    @field_validator("tag_ids")
    @classmethod
    def validate_tag_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_tag_ids(value)

    @field_validator("project_ids")
    @classmethod
    def validate_project_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_project_ids(value)

    @classmethod
    async def as_form(
        cls,
        category_ids: Annotated[list[int], Form(...)],
        tag_ids: Annotated[list[int] | None, Form()] = None,
        project_ids: Annotated[list[int] | None, Form()] = None,
    ) -> "KnowledgeUploadRequest":
        return cls(category_ids=category_ids, tag_ids=tag_ids, project_ids=project_ids)


class KnowledgeTextIngestRequest(BaseModel):
    title: TitleStr
    category_ids: list[int]
    tag_ids: list[int] | None = None
    project_ids: list[int] | None = None
    content: NonEmptyStr

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, value: list[int]) -> list[int]:
        return validate_required_category_ids(value)

    @field_validator("tag_ids")
    @classmethod
    def validate_tag_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_tag_ids(value)

    @field_validator("project_ids")
    @classmethod
    def validate_project_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_project_ids(value)


class KnowledgeAnswerRequest(BaseModel):
    query: NonEmptyStr
    limit: int = Field(default=5, ge=1, le=20)
    category_ids: list[int] | None = Field(default=None)
    tag_ids: list[int] | None = Field(default=None)
    project_ids: list[int] | None = Field(default=None)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    include_match_reasons: bool = Field(default=False)

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_category_ids(value)

    @field_validator("tag_ids")
    @classmethod
    def validate_tag_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_tag_ids(value)

    @field_validator("project_ids")
    @classmethod
    def validate_project_ids(cls, value: list[int] | None) -> list[int] | None:
        return validate_optional_project_ids(value)


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


def validate_optional_tag_ids(value: list[int] | None) -> list[int] | None:
    if value is None:
        return None
    if not value:
        raise ValueError("Tag id filter must not be empty.")
    return validate_tag_id_list(value)


def validate_source_patch_tag_ids(value: list[int] | None) -> list[int] | None:
    if value is None:
        return None
    return validate_tag_id_list(value)


def validate_optional_project_ids(value: list[int] | None) -> list[int] | None:
    if value is None:
        return None
    if not value:
        raise ValueError("Project id filter must not be empty.")
    return validate_project_id_list(value)


def validate_source_patch_project_ids(value: list[int] | None) -> list[int] | None:
    if value is None:
        return None
    return validate_project_id_list(value)


def validate_category_id_list(value: list[int]) -> list[int]:
    if any(category_id < 1 for category_id in value):
        raise ValueError("Category ids must be greater than zero.")
    if len(set(value)) != len(value):
        raise ValueError("Category ids must not contain duplicates.")
    return value


def validate_tag_id_list(value: list[int]) -> list[int]:
    if any(tag_id < 1 for tag_id in value):
        raise ValueError("Tag ids must be greater than zero.")
    if len(set(value)) != len(value):
        raise ValueError("Tag ids must not contain duplicates.")
    return value


def validate_project_id_list(value: list[int]) -> list[int]:
    if any(project_id < 1 for project_id in value):
        raise ValueError("Project ids must be greater than zero.")
    if len(set(value)) != len(value):
        raise ValueError("Project ids must not contain duplicates.")
    return value
