import json
import logging

from starlette.middleware import Middleware
from starlette.types import Receive, Scope, Send

from mcp.server.fastmcp import FastMCP

from backend.app.core.auth import is_valid_token
from backend.app.core.settings import get_settings
from backend.app.db.session import SessionLocal
from backend.app.services.agent_policy import (
    CATEGORIES_DESCRIPTION,
    INGEST_TEXT_DESCRIPTION,
    PROJECTS_DESCRIPTION,
    PROJECT_SOURCES_DESCRIPTION,
    SEARCH_DESCRIPTION,
    SOURCE_DESCRIPTION,
    SOURCES_DESCRIPTION,
    TAGS_DESCRIPTION,
    TAG_AUTOCOMPLETE_DESCRIPTION,
    build_mcp_instructions,
)
from backend.app.services.config import get_auth_token

from .tools.knowledge import (
    KnowledgeHit,
    KnowledgeCategory,
    KnowledgeProject,
    KnowledgeTag,
    KnowledgeSource,
    MinScore,
    MCPTextIngestResult,
    KnowledgeSourceDetail,
    get_knowledge_categories,
    get_knowledge_project_sources,
    get_knowledge_projects,
    get_knowledge_source,
    get_knowledge_sources,
    get_knowledge_tags,
    get_workspace_overview,
    autocomplete_knowledge_tags,
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
            except Exception:  # pylint: disable=broad-exception-caught
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
    """Keep static bearer-token deployments out of OAuth metadata mode.

    VS Code interprets OAuth-protected resource metadata as a sign that the MCP
    server expects an interactive OAuth client registration flow. This project
    intentionally uses a fixed bearer token instead, so we advertise no OAuth
    metadata and enforce the static token via ASGI middleware.
    """
    return None


class StaticBearerAuthMiddleware:
    def __init__(self, app, token_verifier):
        self.app = app
        self.token_verifier = token_verifier

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        auth_header = next(
            (
                value.decode("latin-1")
                for key, value in scope.get("headers", [])
                if key.lower() == b"authorization"
            ),
            None,
        )
        if not auth_header or not auth_header.lower().startswith("bearer "):
            await self._send_auth_error(send, "invalid_token", "Authentication required")
            return

        token = auth_header[7:].strip()
        if not await self.token_verifier.verify_token(token):
            await self._send_auth_error(send, "invalid_token", "Authentication required")
            return

        await self.app(scope, receive, send)

    async def _send_auth_error(self, send: Send, error: str, description: str) -> None:
        payload = {"error": error, "error_description": description}
        body = json.dumps(payload).encode()
        header = 'Bearer error="invalid_token", error_description="Authentication required"'
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                    (b"www-authenticate", header.encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


settings = get_settings()

mcp = FastMCP(
    "knowledge-hub",
    instructions=build_mcp_instructions(),
    host=settings.mcp_host,
    port=settings.mcp_port,
    streamable_http_path=settings.mcp_path,
)


@mcp.tool()
def health() -> dict[str, str]:
    return {"status": "ok", "service": "knowledge-hub"}


@mcp.tool(description=SEARCH_DESCRIPTION)
async def search(
    query: str,
    limit: int = 5,
    category_ids: list[int] | None = None,
    tag_ids: list[int] | None = None,
    project_ids: list[int] | None = None,
    min_score: MinScore | None = None,
    include_match_reasons: bool = False,
) -> list[KnowledgeHit]:
    return await search_knowledge(
        query=query,
        limit=limit,
        category_ids=category_ids,
        tag_ids=tag_ids,
        project_ids=project_ids,
        min_score=min_score,
        include_match_reasons=include_match_reasons,
    )


@mcp.tool(description=SOURCES_DESCRIPTION)
async def sources() -> list[KnowledgeSource]:
    return await get_knowledge_sources()


@mcp.tool(description=SOURCE_DESCRIPTION)
async def source(source_id: str) -> KnowledgeSourceDetail:
    return await get_knowledge_source(source_id)


@mcp.tool(description=CATEGORIES_DESCRIPTION)
async def categories() -> list[KnowledgeCategory]:
    return await get_knowledge_categories()


@mcp.tool(description=TAGS_DESCRIPTION)
async def tags() -> list[KnowledgeTag]:
    return await get_knowledge_tags()


@mcp.tool(description=PROJECTS_DESCRIPTION)
async def projects(status: str | None = None) -> list[KnowledgeProject]:
    return await get_knowledge_projects(status)


@mcp.tool(description=PROJECT_SOURCES_DESCRIPTION)
async def project_sources(project_id: int) -> list[KnowledgeSource]:
    return await get_knowledge_project_sources(project_id)


@mcp.tool(description=TAG_AUTOCOMPLETE_DESCRIPTION)
async def tag_autocomplete(query: str, limit: int = 10) -> list[KnowledgeTag]:
    return await autocomplete_knowledge_tags(query, limit)


@mcp.tool(description=INGEST_TEXT_DESCRIPTION)
async def ingest_text(
    title: str,
    content: str,
    category_ids: list[int],
    tag_ids: list[int] | None = None,
    project_ids: list[int] | None = None,
    metadata: dict[str, str] | None = None,
) -> MCPTextIngestResult:
    return await ingest_mcp_text(
        title=title,
        content=content,
        category_ids=category_ids,
        tag_ids=tag_ids,
        project_ids=project_ids,
        metadata=metadata,
    )


@mcp.resource("config://workspace-overview")
def workspace_overview() -> dict[str, str]:
    return get_workspace_overview()


def main() -> None:
    import uvicorn

    app = mcp.streamable_http_app()
    app.add_middleware(Middleware(StaticBearerAuthMiddleware, token_verifier=build_token_verifier()))
    uvicorn.run(app, host=settings.mcp_host, port=settings.mcp_port)


if __name__ == "__main__":
    main()
