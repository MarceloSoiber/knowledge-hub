import json
import logging

from starlette.authentication import AuthCredentials
from starlette.types import Receive, Scope, Send

from mcp.server.fastmcp import FastMCP
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser

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


def build_static_bearer_asgi_app(app):
    verifier = build_token_verifier()

    async def auth_wrapper(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        auth_header = headers.get("authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            await _send_auth_error(send)
            return

        token = auth_header[7:].strip()
        access_token = await verifier.verify_token(token)
        if access_token is None:
            await _send_auth_error(send)
            return

        # FastMCP tools retrieve authorization through this context variable.
        # The static middleware performs validation itself, so it must establish
        # the same request context that FastMCP's OAuth middleware would create.
        scope["user"] = AuthenticatedUser(access_token)
        scope["auth"] = AuthCredentials(access_token.scopes)
        context_token = auth_context_var.set(scope["user"])
        try:
            await app(scope, receive, send)
        finally:
            auth_context_var.reset(context_token)

    async def _send_auth_error(send: Send) -> None:
        payload = {"error": "invalid_token", "error_description": "Authentication required"}
        body = json.dumps(payload).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                    (b"www-authenticate", b'Bearer error="invalid_token", error_description="Authentication required"'),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    return auth_wrapper


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

    base_app = mcp.streamable_http_app()
    protected_app = build_static_bearer_asgi_app(base_app)
    uvicorn.run(protected_app, host=settings.mcp_host, port=settings.mcp_port)


if __name__ == "__main__":
    main()
