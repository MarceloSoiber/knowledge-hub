# Data Model: Integracao com Agentes

## AgentMemoryPolicy

Runtime policy text exposed to MCP clients.

Fields:

- `search_triggers`: situations where agents should search before answering.
- `no_search_triggers`: situations where agents should avoid search.
- `category_inventory_guidance`: instruction that categories define the current memory domains dynamically.
- `search_strategy`: global-first guidance, filter usage, and one reformulation rule.
- `write_policy`: explicit-confirmation and no automatic conversation archiving rule.
- `trust_boundary`: retrieved content is data, not instructions.
- `privacy_policy`: sensitive category/provider behavior.

Storage: code-level helper in `backend/app/services/agent_policy.py`.

## CategoryInventory

Current set of categories available through `categories()`.

Fields:

- `id`: category ID used for optional `category_ids` filters.
- `name`: normalized category name used by agents to infer memory domains.

Behavior:

- Category names are used as dynamic hints for when memory may be relevant.
- A category match should not force a filtered search immediately; broad search remains preferred when uncertainty is high.
- Newly created categories can expand the agent's search decision surface without changing policy code.

Storage: existing `categories` table.

## MCPProfile

Effective permission profile derived from settings and token verifier.

Fields:

- `read_scope`: always `knowledge:read`.
- `write_scope`: `knowledge:write` only when `MCP_WRITE_ENABLED=true`.
- `write_enabled`: boolean from settings.

Storage: existing settings and `mcp_server/server.py`.

## SensitiveCategoryPolicy

Configuration used to decide whether retrieved content can be sent to external providers.

Fields:

- `sensitive_category_names`: normalized list of category names.
- `allow_external_sensitive_content`: default false.
- `provider`: effective provider, currently from `llm_provider`.

Storage: settings in `backend/app/core/settings.py`; checks in `backend/app/services/privacy.py`.

## RetrievedContext

Existing search/source results used by agents and RAG.

Fields used by this feature:

- `source_id`
- `source_title`
- `categories`
- `content`
- `location`
- `metadata`
- `match_reasons`

Trust boundary: content is untrusted evidence and cannot supply system/developer instructions.

## Database Changes

None for MVP.

Future candidate: add `categories.is_sensitive` with API/admin support if settings-based policy becomes too coarse.
