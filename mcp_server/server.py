from mcp.server.fastmcp import FastMCP

from backend.app.core.auth import is_valid_token
from backend.app.core.settings import get_settings
from backend.app.db.session import SessionLocal
from backend.app.services.config import get_auth_token

from .tools.knowledge import (
    KnowledgeHit,
    KnowledgeCategory,
    KnowledgeSource,
    get_knowledge_categories,
    get_knowledge_sources,
    get_workspace_overview,
    search_knowledge,
)


def build_token_verifier():
    from mcp.server.auth.provider import AccessToken

    class StaticTokenVerifier:
        async def verify_token(self, token: str) -> AccessToken | None:
            async with SessionLocal() as session:
                expected_token = await get_auth_token(session)
                if not expected_token or not is_valid_token(token, expected_token):
                    return None
            return AccessToken(
                token=token,
                client_id="knowledge-hub-mcp-client",
                scopes=["knowledge:read"],
            )

    return StaticTokenVerifier()


def build_auth_settings():
    settings = get_settings()

    from mcp.server.auth.settings import AuthSettings

    return AuthSettings(
        issuer_url=settings.mcp_public_url,
        resource_server_url=settings.mcp_public_url,
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
    category_id: int | None = None,
) -> list[KnowledgeHit]:
    return await search_knowledge(query=query, limit=limit, category_id=category_id)


@mcp.tool()
async def sources() -> list[KnowledgeSource]:
    return await get_knowledge_sources()


@mcp.tool()
async def categories() -> list[KnowledgeCategory]:
    return await get_knowledge_categories()


@mcp.resource("config://workspace-overview")
def workspace_overview() -> dict[str, str]:
    return get_workspace_overview()


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
