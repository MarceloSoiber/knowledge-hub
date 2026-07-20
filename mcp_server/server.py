import logging

from mcp.server.fastmcp import FastMCP

from backend.app.core.auth import is_valid_token
from backend.app.core.settings import get_settings
from backend.app.db.session import SessionLocal
from backend.app.services.config import get_auth_token

from .tools.knowledge import (
    KnowledgeHit,
    KnowledgeCategory,
    KnowledgeSource,
    MinScore,
    MCPTextIngestResult,
    KnowledgeSourceDetail,
    get_knowledge_categories,
    get_knowledge_source,
    get_knowledge_sources,
    get_workspace_overview,
    ingest_mcp_text,
    search_knowledge,
)


logger = logging.getLogger(__name__)


def build_token_verifier():
    from mcp.server.auth.provider import AccessToken

    class StaticTokenVerifier:
        async def verify_token(self, token: str) -> AccessToken | None:
            try:
                async with SessionLocal() as session:
                    expected_token = await get_auth_token(session)
            except Exception:
                logger.exception("Failed to validate MCP bearer token.")
                return None
            if not expected_token or not is_valid_token(token, expected_token):
                return None
            return AccessToken(
                token=token,
                client_id="knowledge-hub-mcp-client",
                scopes=build_mcp_scopes(),
            )

    return StaticTokenVerifier()


def build_mcp_scopes() -> list[str]:
    scopes = ["knowledge:read"]
    if get_settings().mcp_write_enabled:
        scopes.append("knowledge:write")
    return scopes


def build_auth_settings():
    settings = get_settings()

    from mcp.server.auth.settings import AuthSettings

    return AuthSettings(
        issuer_url=settings.mcp_public_url,
        # VS Code treats the protected-resource metadata as an OAuth flow and
        # prompts for client registration. This server uses a static Bearer
        # token instead, so keep bearer validation without advertising OAuth.
        resource_server_url=None,
        required_scopes=["knowledge:read"],
    )


settings = get_settings()

mcp = FastMCP(
    "knowledge-hub-mcp",
    instructions="Ferramentas MCP para consultar e ampliar o Knowledge Hub.",
    host=settings.mcp_host,
    port=settings.mcp_port,
    streamable_http_path=settings.mcp_path,
    auth=build_auth_settings(),
    token_verifier=build_token_verifier(),
)


@mcp.tool()
def health() -> dict[str, str]:
    return {"status": "ok", "service": "knowledge-hub-mcp"}


@mcp.tool()
async def search(
    query: str,
    limit: int = 5,
    category_ids: list[int] | None = None,
    min_score: MinScore | None = None,
) -> list[KnowledgeHit]:
    return await search_knowledge(
        query=query,
        limit=limit,
        category_ids=category_ids,
        min_score=min_score,
    )


@mcp.tool()
async def sources() -> list[KnowledgeSource]:
    return await get_knowledge_sources()


@mcp.tool(description="Consulta uma fonte detalhada por UUID publico.")
async def source(source_id: str) -> KnowledgeSourceDetail:
    return await get_knowledge_source(source_id)


@mcp.tool()
async def categories() -> list[KnowledgeCategory]:
    return await get_knowledge_categories()


@mcp.tool(
    description=(
        "Persiste uma nota textual no Knowledge Hub somente depois de confirmacao "
        "explicita do usuario. Nao use para arquivar conversas automaticamente. "
        "Use categories() antes para escolher category_ids validos. Requer "
        "escopo knowledge:write."
    )
)
async def ingest_text(
    title: str,
    content: str,
    category_ids: list[int],
    metadata: dict[str, str] | None = None,
) -> MCPTextIngestResult:
    return await ingest_mcp_text(
        title=title,
        content=content,
        category_ids=category_ids,
        metadata=metadata,
    )


@mcp.resource("config://workspace-overview")
def workspace_overview() -> dict[str, str]:
    return get_workspace_overview()


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
