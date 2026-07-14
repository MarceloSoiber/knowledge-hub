from __future__ import annotations

from typing import Annotated

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
)

from backend.app.db.session import SessionLocal
from backend.app.schemas.knowledge import validate_required_category_ids
from backend.app.services.categories import CategoryNotFoundError, list_categories
from backend.app.services.documents.extractors import EmptyDocumentError
from backend.app.services.embeddings import (
    EmbeddingConfigurationError,
    EmbeddingError,
    build_embedding_client,
)
from backend.app.services.ingestion import KnowledgeIngestionError, ingest_plain_text
from backend.app.services.search import list_sources
from backend.app.services.search import search_knowledge as search_backend_knowledge

MCP_ALLOWED_METADATA_KEYS = {"client_id", "note_type"}
MCP_WRITE_SCOPE = "knowledge:write"

TitleStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
ContentStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class KnowledgeHit(BaseModel):
    id: int = Field(description="ID do chunk encontrado")
    source_id: int = Field(description="ID da origem do chunk")
    content: str = Field(description="Conteúdo encontrado")
    score: float | None = Field(default=None, description="Score de relevância")


class KnowledgeCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class KnowledgeSource(BaseModel):
    id: int
    title: str
    categories: list[KnowledgeCategory]
    source_type: str
    uri: str


class MCPTextIngestRequest(BaseModel):
    title: TitleStr = Field(description="Titulo da nota confirmada pelo usuario")
    content: ContentStr = Field(description="Conteudo textual confirmado para persistencia")
    category_ids: list[int] = Field(description="IDs das categorias existentes")
    metadata: dict[str, str] | None = Field(
        default=None,
        description="Metadados opcionais permitidos: client_id, note_type",
    )

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, value: list[int]) -> list[int]:
        return validate_required_category_ids(value)

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
    source_id: int
    title: str
    categories: list[KnowledgeCategory]
    chunks_created: int


class MCPAuthorizationError(PermissionError):
    pass


class MCPIngestionError(ValueError):
    pass


def require_mcp_scope(scope: str, access_token: AccessToken | None = None) -> None:
    token = access_token or get_access_token()
    if token is None or scope not in token.scopes:
        raise MCPAuthorizationError(f"MCP tool requires scope '{scope}'.")


async def search_knowledge(
    query: str,
    limit: int = 5,
    category_ids: list[int] | None = None,
) -> list[KnowledgeHit]:
    async with SessionLocal() as session:
        results = await search_backend_knowledge(
            session=session,
            query=query,
            limit=limit,
            category_ids=category_ids,
            embedding_client=build_embedding_client(),
        )
    return [KnowledgeHit(**result.model_dump()) for result in results]


async def get_knowledge_sources() -> list[KnowledgeSource]:
    async with SessionLocal() as session:
        sources = await list_sources(session)
    return [KnowledgeSource(**source) for source in sources]


async def get_knowledge_categories() -> list[KnowledgeCategory]:
    async with SessionLocal() as session:
        categories = await list_categories(session)
    return [KnowledgeCategory(**category) for category in categories]


async def ingest_mcp_text(
    title: str,
    content: str,
    category_ids: list[int],
    metadata: dict[str, str] | None = None,
) -> MCPTextIngestResult:
    require_mcp_scope(MCP_WRITE_SCOPE)

    try:
        payload = MCPTextIngestRequest(
            title=title,
            content=content,
            category_ids=category_ids,
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
                embedding_client=build_embedding_client(),
                source_type="mcp",
                metadata=payload.metadata,
            )
    except CategoryNotFoundError as exc:
        raise MCPIngestionError(str(exc)) from exc
    except (EmptyDocumentError, KnowledgeIngestionError) as exc:
        raise MCPIngestionError(str(exc)) from exc
    except EmbeddingConfigurationError as exc:
        raise MCPIngestionError(f"Embedding configuration unavailable: {exc}") from exc
    except EmbeddingError as exc:
        raise MCPIngestionError(f"Embedding provider failure: {exc}") from exc

    return MCPTextIngestResult(
        source_id=source.id,
        title=source.title,
        categories=source.categories,
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
