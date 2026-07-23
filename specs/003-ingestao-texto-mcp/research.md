# Research: Ingestao de Texto pelo MCP

## Decision: Reuse `ingest_plain_text` as the default ingestion path

**Rationale**: The API already validates categories, normalizes text, chunks content, generates embeddings, replaces existing text sources and commits in one service path. Reusing it avoids divergent MCP behavior.

**Alternatives considered**: Implement chunking and embeddings directly in `mcp_server/tools/knowledge.py`, rejected because it duplicates backend rules and increases rollback risk.

## Decision: Introduce MCP-specific schemas in the MCP layer

**Rationale**: The MCP tool needs descriptions and optional metadata behavior that differ from the REST payload, while still sharing response shapes with backend read models.

**Alternatives considered**: Reuse `KnowledgeTextIngestRequest` directly, accepted as a fallback but less expressive for tool catalog descriptions and future MCP metadata.

## Decision: Treat write authorization as a release gate

**Rationale**: The current MCP token verifier returns only `knowledge:read`. `ingest_text` must not ship enabled unless `knowledge:write` is enforced before persistence.

**Alternatives considered**: Rely on instructions alone, rejected because model instructions cannot enforce security.

## Decision: Enforce write scope in the tool handler and keep write scope disabled by default

**Rationale**: FastMCP 1.12 exposes token scopes through the auth context, but the `@mcp.tool()` decorator does not accept per-tool `required_scopes`. The implementation therefore checks `knowledge:write` inside `ingest_mcp_text` before any validation or persistence. The token verifier grants `knowledge:write` only when `MCP_WRITE_ENABLED=true`, so existing deployments stay read-only by default.

**Alternatives considered**: Add the tool globally and trust clients to honor scopes, rejected because clients vary and tests would not prove server-side enforcement. Split into a separate write server, rejected for now because handler-level enforcement is available and testable.

## Decision: Keep optional metadata allowlisted

**Rationale**: The feature asks for optional permitted metadata, not arbitrary schema-less persistence. An allowlist supports client attribution without turning metadata into an unbounded contract.

**Alternatives considered**: Store arbitrary JSON from agents, rejected because it invites sensitive data leakage and undocumented coupling.
