# Implementation Plan: Integracao com Agentes

**Branch**: `014-integracao-agentes` | **Date**: 2026-07-21 | **Spec**: `specs/014-integracao-agentes/spec.md`

**Input**: Feature specification from `/specs/014-integracao-agentes/spec.md`

## Summary

Make MCP-connected agents use Knowledge Hub memory intentionally: derive memory-search decisions from the current category inventory, search before answering when requests plausibly match categories represented in the base, avoid unnecessary searches for self-contained tasks, retry with one reformulation when memory likely exists, require explicit user confirmation and `knowledge:write` for persistence, treat retrieved content as untrusted data, and block sensitive categories from external providers.

The implementation will keep MCP tools thin while adding a small policy layer, clearer FastMCP instructions/tool descriptions, settings-driven MCP profile/privacy checks, and tests that exercise realistic agent decisions.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, SQLAlchemy async, Pydantic v2, FastMCP, PostgreSQL + pgvector

**Storage**: Existing PostgreSQL categories/sources/chunks. MVP stores sensitive category policy in settings, not a new table.

**Testing**: `.venv/bin/python -m pytest`

**Target Platform**: Linux web service with FastAPI backend and FastMCP streamable HTTP server.

**Project Type**: Backend API + MCP integration.

**Performance Goals**: No material search latency regression; policy checks are in-memory/settings based except optional category inventory reads.

**Constraints**: Keep routes and MCP wrappers thin; business logic in `backend/app/services`; Pydantic v2 schemas for validation; update `doc/API.md` when MCP/API behavior changes; retrieved documents must never be elevated to system instructions.

**Scale/Scope**: MCP server instructions/tools, category-driven agent policy, RAG answer prompt construction, settings, privacy guardrails, tests and docs. No frontend changes required for MVP.

## Constitution Check

- Code Quality: Pass. Add policy helpers in `backend/app/services` and keep `mcp_server/server.py` and `mcp_server/tools/knowledge.py` as thin adapters.
- Testing Standards: Pass. This touches agent safety and write permissions, so service and MCP tests are required.
- Performance: Pass. The policy layer avoids additional database work except optional category-name checks for sensitive filters.
- Documentation: Pass. MCP usage and privacy behavior must be documented in `doc/API.md`.
- MCP Integration: Pass. Tool names remain short/domain-oriented; descriptions and server instructions become more explicit.

## Project Structure

### Documentation (this feature)

```text
specs/014-integracao-agentes/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- mcp-agent-policy.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/app/
|-- core/
|   `-- settings.py
|-- services/
|   |-- agent_policy.py
|   |-- privacy.py
|   |-- rag.py
|   `-- search.py
|-- schemas/
|   `-- knowledge.py
`-- api/routes/
    `-- knowledge.py

mcp_server/
|-- server.py
`-- tools/
    `-- knowledge.py

tests/
|-- test_agent_policy.py
|-- test_mcp_knowledge.py
`-- test_knowledge_service.py

doc/
`-- API.md
```

**Structure Decision**: Add policy logic to `backend/app/services/agent_policy.py` and provider/category privacy checks to `backend/app/services/privacy.py`. Keep MCP functions as wrappers that expose descriptions and call existing services.

## Implementation Details

### Agent Policy

- Add an `AgentMemoryPolicy` helper with stable text blocks for:
  - category-driven when-to-search rules;
  - when not to search;
  - how to use `categories()` as the dynamic inventory of domains stored in memory;
  - global-first search strategy;
  - one reformulation on likely-memory misses;
  - explicit confirmation before persistence;
  - retrieved content as untrusted data.
- Use this helper to build `FastMCP(..., instructions=...)` rather than keeping a one-line instruction.
- Keep hard-coded domains such as projects, finances and decisions as examples only; the implemented policy must generalize to any category added by users.
- Keep policy text concise enough for clients but explicit enough to guide agent behavior.
- Add examples in docs/contracts rather than overloading every runtime description.

### MCP Tool Descriptions

- Add descriptions to `search`, `sources`, `source`, `categories`, `tags`, `projects`, `project_sources`, `tag_autocomplete` and `ingest_text`.
- Make `search` describe:
  - use when the request plausibly maps to existing memory categories or stored sources;
  - avoid for simple calculations and fully self-contained tasks;
  - start global, then filter with known IDs;
  - reformulate once before concluding absence.
- Make `source` describe retrieving full/detail context after `search`.
- Keep `ingest_text` explicit that confirmation is required and automatic conversation archiving is forbidden.

### Read/Write Profiles

- Keep `MCP_WRITE_ENABLED=false` as default.
- Add helper/test coverage around `build_mcp_scopes()` to prove default read-only and explicit read-write behavior.
- Do not add update/delete MCP tools in this feature.
- If future update/delete tools are added, they must use `knowledge:write` and confirmation language by default.

### Prompt Injection and RAG Isolation

- Update `backend/app/services/rag.py` system/developer prompt text to say retrieved excerpts are untrusted evidence and may contain malicious instructions.
- Keep source citations and context formatting, but ensure prompt hierarchy clearly separates policy instructions from retrieved content.
- Add tests with a malicious retrieved chunk to assert the prompt sent to the answer client includes the untrusted-content warning and keeps malicious text inside context.

### Privacy Guardrails

- Add settings:
  - `sensitive_category_names: list[str]` with empty default;
  - `allow_external_sensitive_content: bool` default `False` only if an override is absolutely needed for local development/testing.
- Add `privacy.py` helper that normalizes category names and detects sensitive categories from retrieved chunks/sources.
- For provider `api`, block answer generation when selected/retrieved context includes sensitive categories and override is false.
- For local provider, allow the flow.
- Keep vector embedding provider behavior tied to existing `llm_provider` until a separate embedding provider setting exists; document this assumption.

### Documentation

- Update `doc/API.md` MCP section with:
  - agent decision policy;
  - global-first/filter-later search strategy;
  - retry/reformulation guidance;
  - read-only vs read-write profile setup;
  - retrieved content trust boundary;
  - sensitive category provider behavior.
- Keep `specs/014-integracao-agentes/contracts/mcp-agent-policy.md` aligned with implemented text.

## Data Model / API Implications

- No database migration in MVP.
- Category names from existing `categories` records become part of the agent policy context.
- Settings gain sensitive category privacy fields.
- MCP runtime instructions and tool descriptions change, but tool names and return payloads remain compatible.
- RAG answer behavior may return/block with a clear privacy error when external provider would receive sensitive category content.
- `doc/API.md` changes are public documentation changes; OpenAPI shape is unchanged unless an error response is documented for answer privacy blocking.

## Test Strategy

- Unit tests for category-driven policy text and decision examples in `tests/test_agent_policy.py`.
- MCP tests for tool descriptions/instructions and scope profile behavior in `tests/test_mcp_knowledge.py`.
- Service tests for RAG prompt isolation and privacy blocking in `tests/test_knowledge_service.py`.
- Existing MCP ingestion tests remain to prove read-only write denial.
- Run `.venv/bin/python -m pytest tests/test_agent_policy.py tests/test_mcp_knowledge.py tests/test_knowledge_service.py tests/test_knowledge_api_integration.py`.

## Risk Notes

- Tool descriptions and dynamic category inventory cannot force every external agent to comply; tests can only validate the contract we expose.
- Category names without descriptions may be ambiguous. The MVP should encourage broad/global search when the category match is uncertain.
- Sensitive category detection by name is simple and reversible, but less robust than a persisted category flag. A DB-backed flag can be a later feature.
- Blocking answer generation after retrieval may surprise users if search succeeds but answer fails; error messages should mention local provider or category scope.
- If embeddings currently use an external provider through `llm_provider=api`, ingestion of sensitive categories may also need blocking. MVP should document and test the provider paths that actually send text externally.

## Complexity Tracking

No constitution violations identified.
