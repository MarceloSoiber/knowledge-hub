from __future__ import annotations

from typing import Annotated
from typing import Any

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    field_validator,
)

from backend.app.db.session import SessionLocal
from backend.app.schemas.knowledge import validate_optional_project_ids
from backend.app.schemas.knowledge import validate_required_category_ids
from backend.app.schemas.knowledge import validate_optional_tag_ids
from backend.app.services.categories import CategoryNotFoundError, list_categories
from backend.app.services.documents.extractors import EmptyDocumentError
from backend.app.services.embeddings import (
    EmbeddingConfigurationError,
    EmbeddingError,
    build_embedding_client,
)
from backend.app.services.ingestion import KnowledgeIngestionError, ingest_plain_text
from backend.app.services.projects import ProjectNotFoundError, list_project_sources, list_projects
from backend.app.services.search import list_sources
from backend.app.services.search import search_knowledge as search_backend_knowledge
from backend.app.services.sources import SourceNotFoundError, get_source_detail
from backend.app.services.tags import TagNotFoundError, autocomplete_tags, list_tags

MCP_ALLOWED_METADATA_KEYS = {"client_id", "note_type"}
MCP_WRITE_SCOPE = "knowledge:write"

TitleStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
ContentStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
MinScore = Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)]
min_score_adapter = TypeAdapter(MinScore | None)


class KnowledgeHit(BaseModel):
    id: int = Field(description="ID do chunk encontrado")
    source_id: str = Field(description="UUID publico da origem do chunk")
    source_title: str = Field(description="Titulo da origem")
    source_type: str = Field(description="Tipo da origem")
    uri: str = Field(description="URI publica ou sanitizada da origem")
    categories: list["KnowledgeCategory"] = Field(description="Categorias da origem")
    tags: list["KnowledgeTag"] = Field(default_factory=list, description="Tags da origem")
    projects: list["KnowledgeProject"] = Field(default_factory=list, description="Projetos da origem")
    location: "KnowledgeChunkLocation" = Field(description="Localizacao citavel do chunk")
    content: str = Field(description="Conteúdo encontrado")
    score: float | None = Field(default=None, description="Score de relevância")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadados publicos")
    match_reasons: list[str] | None = Field(
        default=None,
        description="Motivos opcionais do match quando diagnostico e solicitado",
    )


class KnowledgeCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class KnowledgeTag(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class KnowledgeProject(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    status: str


class KnowledgeChunkLocation(BaseModel):
    chunk_index: int
    page: int | None = None
    section: str | None = None
    start_char: int
    end_char: int


class KnowledgeSource(BaseModel):
    source_id: str
    title: str
    categories: list[KnowledgeCategory]
    tags: list[KnowledgeTag] = Field(default_factory=list)
    projects: list[KnowledgeProject] = Field(default_factory=list)
    source_type: str
    uri: str
    content_hash: str


class KnowledgeSourceDetail(KnowledgeSource):
    content: str


class MCPTextIngestRequest(BaseModel):
    title: TitleStr = Field(description="Titulo da nota confirmada pelo usuario")
    content: ContentStr = Field(description="Conteudo textual confirmado para persistencia")
    category_ids: list[int] = Field(description="IDs das categorias existentes")
    tag_ids: list[int] | None = Field(default=None, description="IDs das tags existentes")
    project_ids: list[int] | None = Field(default=None, description="IDs dos projetos existentes")
    metadata: dict[str, str] | None = Field(
        default=None,
        description="Metadados opcionais permitidos: client_id, note_type",
    )

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

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
        unsupported_keys = sorted(set(value) - MCP_ALLOWED_METADATA_KEYS)
        if unsupported_keys:
            raise ValueError(
                "Unsupported metadata keys: " + ", ".join(unsupported_keys)
            )
        return {key: metadata_value.strip() for key, metadata_value in value.items()}


class MCPTextIngestResult(BaseModel):
    source_id: str
    title: str
    categories: list[KnowledgeCategory]
    tags: list[KnowledgeTag] = Field(default_factory=list)
    projects: list[KnowledgeProject] = Field(default_factory=list)
    chunks_created: int


class MCPAuthorizationError(PermissionError):
    pass


class MCPIngestionError(ValueError):
    pass


class MCPSourceNotFoundError(LookupError):
    pass


def require_mcp_scope(scope: str, access_token: AccessToken | None = None) -> None:
    token = access_token or get_access_token()
    if token is None or scope not in token.scopes:
        raise MCPAuthorizationError(f"MCP tool requires scope '{scope}'.")


async def search_knowledge(
    query: str,
    limit: int = 5,
    category_ids: list[int] | None = None,
    tag_ids: list[int] | None = None,
    project_ids: list[int] | None = None,
    min_score: MinScore | None = None,
    include_match_reasons: bool = False,
) -> list[KnowledgeHit]:
    validated_min_score = min_score_adapter.validate_python(min_score)
    validated_tag_ids = validate_optional_tag_ids(tag_ids)
    validated_project_ids = validate_optional_project_ids(project_ids)
    async with SessionLocal() as session:
        results = await search_backend_knowledge(
            session=session,
            query=query,
            limit=limit,
            category_ids=category_ids,
            tag_ids=validated_tag_ids,
            project_ids=validated_project_ids,
            min_score=validated_min_score,
            include_match_reasons=include_match_reasons,
            embedding_client=build_embedding_client(),
        )
    return [KnowledgeHit(**result.model_dump()) for result in results]


async def get_knowledge_sources() -> list[KnowledgeSource]:
    async with SessionLocal() as session:
        sources = await list_sources(session)
    return [KnowledgeSource(**source) for source in sources]


async def get_knowledge_source(source_id: str) -> KnowledgeSourceDetail:
    try:
        async with SessionLocal() as session:
            source = await get_source_detail(session, source_id)
    except SourceNotFoundError as exc:
        raise MCPSourceNotFoundError(str(exc)) from exc
    return KnowledgeSourceDetail(**source)


async def get_knowledge_categories() -> list[KnowledgeCategory]:
    async with SessionLocal() as session:
        categories = await list_categories(session)
    return [KnowledgeCategory(**category) for category in categories]


async def get_knowledge_tags() -> list[KnowledgeTag]:
    async with SessionLocal() as session:
        tags = await list_tags(session)
    return [KnowledgeTag(**tag) for tag in tags]


async def get_knowledge_projects(status: str | None = None) -> list[KnowledgeProject]:
    async with SessionLocal() as session:
        projects = await list_projects(session, status=status)
    return [KnowledgeProject(**project) for project in projects]


async def get_knowledge_project_sources(project_id: int) -> list[KnowledgeSource]:
    async with SessionLocal() as session:
        sources = await list_project_sources(session, project_id)
    return [KnowledgeSource(**source) for source in sources]


async def autocomplete_knowledge_tags(query: str, limit: int = 10) -> list[KnowledgeTag]:
    async with SessionLocal() as session:
        tags = await autocomplete_tags(session, query, limit)
    return [KnowledgeTag(**tag) for tag in tags]


async def ingest_mcp_text(
    title: str,
    content: str,
    category_ids: list[int],
    tag_ids: list[int] | None = None,
    project_ids: list[int] | None = None,
    metadata: dict[str, str] | None = None,
) -> MCPTextIngestResult:
    require_mcp_scope(MCP_WRITE_SCOPE)

    try:
        payload = MCPTextIngestRequest(
            title=title,
            content=content,
            category_ids=category_ids,
            tag_ids=tag_ids,
            project_ids=project_ids,
            metadata=metadata,
        )
    except ValidationError as exc:
        raise MCPIngestionError(str(exc)) from exc

    try:
        async with SessionLocal() as session:
            source, chunks_created = await ingest_plain_text(
                session=session,
                title=payload.title,
                content=payload.content,
                category_ids=payload.category_ids,
                tag_ids=payload.tag_ids,
                project_ids=payload.project_ids,
                embedding_client=build_embedding_client(),
                source_type="mcp",
                metadata=payload.metadata,
            )
    except (CategoryNotFoundError, TagNotFoundError, ProjectNotFoundError) as exc:
        raise MCPIngestionError(str(exc)) from exc
    except (EmptyDocumentError, KnowledgeIngestionError) as exc:
        raise MCPIngestionError(str(exc)) from exc
    except EmbeddingConfigurationError as exc:
        raise MCPIngestionError(f"Embedding configuration unavailable: {exc}") from exc
    except EmbeddingError as exc:
        raise MCPIngestionError(f"Embedding provider failure: {exc}") from exc

    return MCPTextIngestResult(
        source_id=source.public_id,
        title=source.title,
        categories=source.categories,
        tags=getattr(source, "tags", []),
        projects=getattr(source, "projects", []),
        chunks_created=chunks_created,
    )


def get_workspace_overview() -> dict[str, str]:
    return {
        "frontend": "Vite + React",
        "backend": "FastAPI",
        "database": "PostgreSQL + pgvector",
        "mcp": "FastMCP streamable-http",
        "llm": "local ou API via settings",
    }
