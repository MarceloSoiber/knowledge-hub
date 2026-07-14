# Implementation Plan: Ingestao de Texto pelo MCP

**Branch**: `003-ingestao-texto-mcp` | **Date**: 2026-07-14 | **Spec**: `specs/003-ingestao-texto-mcp/spec.md`

**Input**: Feature specification from `/specs/003-ingestao-texto-mcp/spec.md`

## Summary

Add a write-capable MCP tool, `ingest_text`, that lets agents persist confirmed text notes through the same backend ingestion path used by the API. The implementation must introduce MCP-specific request/response schemas, enforce `knowledge:write` separately from existing read tools, preserve transaction rollback behavior, and update MCP documentation so agents ask for user confirmation before saving.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastMCP (`mcp>=1.12.0`), FastAPI backend services, SQLAlchemy async, Pydantic v2, PostgreSQL + pgvector

**Storage**: Existing PostgreSQL tables for sources, chunks, categories and pgvector embeddings

**Testing**: pytest via `.venv/bin/python -m pytest`

**Target Platform**: Docker/local Linux MCP server using Streamable HTTP

**Project Type**: Backend service + MCP server

**Performance Goals**: Ingestion uses existing chunking and embedding path; read tool latency must not regress. Search remains within the constitution's typical 500ms target.

**Constraints**: MCP layer stays thin; business rules remain in `backend/app/services`. Do not expose write access if FastMCP cannot enforce it safely. Tool instructions must avoid automatic conversation capture.

**Scale/Scope**: One new text-ingestion MCP tool, authorization changes for MCP, tests and documentation. No file upload over MCP in this feature.

## Constitution Check

- Clean architecture: Pass. `mcp_server/tools/knowledge.py` delegates ingestion to `backend/app/services/ingestion.py` or a small service wrapper.
- Testing: Pass. Service and MCP authorization/error mapping tests cover write path and rollback-sensitive failures.
- Documentation: Pass. README and/or `doc/API.md` document MCP catalog, scopes and confirmation expectations.
- Performance: Pass. No new search query path; ingestion follows existing embedding flow.
- Type safety: Pass. Pydantic v2 models define MCP input/output contracts.

## Project Structure

### Documentation (this feature)

```text
specs/003-ingestao-texto-mcp/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── mcp-ingest-text.md
└── tasks.md
```

### Source Code

```text
backend/app/
├── core/auth.py
├── core/settings.py
├── schemas/knowledge.py
└── services/ingestion.py

mcp_server/
├── server.py
└── tools/knowledge.py

tests/
├── test_knowledge_service.py
└── test_mcp_knowledge.py

doc/
└── API.md

README.md
```

**Structure Decision**: Use the existing MCP server and backend service boundaries. Add MCP-focused tests under `tests/` instead of creating a new test package.

## Improvement Plan

### Phase 0 - Validate authorization capability

- Inspect the installed FastMCP API for per-tool scope metadata or middleware hooks.
- Decide between one-server per-tool enforcement and a safer split-server/write-disabled configuration.
- Add configuration names for enabling MCP write capability only after the enforcement path is known.

### Phase 1 - Define MCP contracts

- Add MCP Pydantic input/output models for `ingest_text`, including `title`, `content`, `category_ids` and allowlisted metadata.
- Reuse category output shape from existing MCP source/category models.
- Write tool instructions that state persistence requires explicit user confirmation.

### Phase 2 - Reuse ingestion safely

- Call the backend ingestion path from the MCP tool rather than duplicating chunking/embedding/category behavior.
- If `source_type="mcp"` requires backend service changes, introduce a narrow parameter or wrapper while preserving API `/texts` behavior as `source_type="text"`.
- Preserve commit/rollback behavior on validation and embedding failures.

### Phase 3 - Enforce write scope

- Keep existing read tools under `knowledge:read`.
- Require `knowledge:write` before `ingest_text` can run.
- If only global scopes are supported, either expose `ingest_text` from a separate write server or keep it disabled by default with clear documentation.

### Phase 4 - Error mapping and observability

- Translate `CategoryNotFoundError`, `EmptyDocumentError`, validation errors and embedding failures into useful MCP-facing messages.
- Include source ID and chunk count in success responses.
- Record MCP origin/client when available without storing secrets.

### Phase 5 - Tests and docs

- Add tests for successful ingestion, invalid categories, empty content, embedding rollback and read-only authorization denial.
- Update README and `doc/API.md` for MCP tool catalog, scopes and confirmation guidance.
- Run the focused pytest suite, then the broader suite if the environment is available.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Potential separate MCP write server | Needed only if FastMCP cannot enforce per-tool `knowledge:write` safely | A single globally write-scoped server would expose existing read tools with broader credentials than necessary |
