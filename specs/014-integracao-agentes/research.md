# Research: Integracao com Agentes

## Decision 1: Use Categories as the Dynamic Memory Domain Inventory

**Decision**: Base search/no-search guidance on the current category inventory exposed by `categories()`, using examples such as projects, finances and decisions only as illustrative heuristics.

**Rationale**: The Knowledge Hub can receive arbitrary data. A static list of searchable domains would become stale as users create new categories.

**Alternatives considered**:

- Hard-code common domains in policy text: rejected because it hides newly added categories from agent decision-making.
- Always search for every user request: rejected because the feature explicitly avoids unnecessary searches for self-contained tasks.

## Decision 2: Use Runtime MCP Instructions as the Primary Agent Policy Surface

**Decision**: Centralize the agent behavior policy in a backend helper and inject it into `FastMCP(..., instructions=...)`.

**Rationale**: MCP clients see server instructions before tool selection. Keeping the text generated from code makes it testable and prevents drift between server behavior and docs.

**Alternatives considered**:

- Only update `doc/API.md`: rejected because connected agents may not read the docs.
- Add a new `policy()` tool: useful later, but weaker as a default because agents must choose to call it.

## Decision 3: Keep Tool Names Stable

**Decision**: Preserve current tool names (`search`, `sources`, `source`, `categories`, `tags`, `projects`, `project_sources`, `tag_autocomplete`, `ingest_text`) and improve descriptions/parameter docs.

**Rationale**: Existing clients and tests already target these names. The issue is not naming incompatibility; it is missing or incomplete usage guidance.

**Alternatives considered**:

- Rename tools to `search_memory` or `save_memory`: rejected for compatibility and because current names are short/domain-oriented per constitution.

## Decision 4: Settings-Based Sensitive Category Policy for MVP

**Decision**: Use normalized category names configured in settings for sensitive-category detection.

**Rationale**: The feature needs privacy enforcement without requiring a schema migration or frontend/admin UI. Category names already exist on search results and sources.

**Alternatives considered**:

- Add `categories.is_sensitive`: stronger long-term model, but expands migration/API/UI scope.
- Store policy in document metadata: inconsistent because category-level policy is easier for operators and agents to reason about.

## Decision 5: One Search Reformulation

**Decision**: Policy should permit exactly one reformulation when the first search fails and the request still appears memory-dependent.

**Rationale**: This balances recall with avoiding excessive tool calls.

**Alternatives considered**:

- Unlimited retries: rejected because it can waste time and create noisy agent loops.
- No retry: rejected because failed keyword choice should not immediately imply absent memory.

## Decision 6: Retrieved Context Is Untrusted Evidence

**Decision**: RAG prompt construction must explicitly tell the model that retrieved excerpts are untrusted evidence and cannot override system/developer/user instructions.

**Rationale**: Stored content may be external, stale or malicious. This is a core safety boundary for agent integrations.

**Alternatives considered**:

- Strip suspicious strings from retrieved content: rejected because it can remove useful evidence and is brittle.
- Rely on model behavior without explicit prompt boundary: rejected because prompt injection should be handled intentionally.
