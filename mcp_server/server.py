from mcp.server.fastmcp import FastMCP

from .tools.knowledge import KnowledgeHit, get_workspace_overview, search_knowledge


mcp = FastMCP(
    "knowledge-hub-mcp",
    instructions="Ferramentas MCP para consultar e ampliar o Knowledge Hub.",
)


@mcp.tool()
def health() -> dict[str, str]:
    return {"status": "ok", "service": "knowledge-hub-mcp"}


@mcp.tool()
async def search(query: str, limit: int = 5) -> list[KnowledgeHit]:
    return await search_knowledge(query=query, limit=limit)


@mcp.resource("config://workspace-overview")
def workspace_overview() -> dict[str, str]:
    return get_workspace_overview()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()