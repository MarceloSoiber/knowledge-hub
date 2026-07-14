# Tasks: Ingestao de Texto pelo MCP

**Input**: Design documents from `/specs/003-ingestao-texto-mcp/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Phase 1: Authorization Research Gate

- [X] T001 Inspect FastMCP support for per-tool scope requirements in the installed `mcp>=1.12.0` package.
- [X] T002 Decide and document the enforcement path in `specs/003-ingestao-texto-mcp/research.md`: per-tool guard, separate write server or disabled-by-default write config.

## Phase 2: Tests First

- [X] T003 [P] Add MCP schema validation tests for title, content, `category_ids` and metadata in `tests/test_mcp_knowledge.py`.
- [X] T004 [P] Add successful MCP text ingestion test proving source, categories and chunk count in `tests/test_mcp_knowledge.py`.
- [X] T005 [P] Add tests for category-not-found and empty-content failures with no persisted data in `tests/test_mcp_knowledge.py`.
- [X] T006 [P] Add embedding failure rollback test for MCP ingestion in `tests/test_mcp_knowledge.py`.
- [X] T007 Add read-only authorization denial test proving `ingest_text` cannot persist with only `knowledge:read`.

## Phase 3: MCP Contracts and Tool Models

- [X] T008 Add `MCPTextIngestRequest` and `MCPTextIngestResult` Pydantic models in `mcp_server/tools/knowledge.py`.
- [X] T009 Add allowlisted metadata validation in `mcp_server/tools/knowledge.py`.
- [X] T010 Ensure category response models are declared before models that reference them in `mcp_server/tools/knowledge.py`.

## Phase 4: Backend Reuse and Origin

- [X] T011 Add the minimum backend service support needed for MCP source origin `mcp` in `backend/app/services/ingestion.py`.
- [X] T012 Preserve existing API `/knowledge/texts` behavior as `source_type="text"` in `backend/app/api/routes/knowledge.py`.
- [X] T013 Implement MCP ingestion helper in `mcp_server/tools/knowledge.py` using `SessionLocal`, `build_embedding_client` and backend ingestion service.
- [X] T014 Map category, validation, empty-content and embedding exceptions to useful MCP-facing errors in `mcp_server/tools/knowledge.py`.

## Phase 5: MCP Registration and Authorization

- [X] T015 Register `ingest_text` in `mcp_server/server.py` with catalog instructions requiring explicit user confirmation.
- [X] T016 Enforce `knowledge:write` before `ingest_text` runs according to the Phase 1 decision.
- [X] T017 Keep `search`, `sources`, `categories` and `workspace_overview` compatible with read-only clients.
- [X] T018 Add settings or deployment documentation for disabling/enabling MCP write capability if a split or gated setup is required.

## Phase 6: Documentation

- [X] T019 Update README MCP tool catalog with `ingest_text`, required scope and confirmation guidance.
- [X] T020 Update `doc/API.md` or MCP documentation section with request/response examples and error cases.
- [X] T021 Cross-reference Plano 03 for recadastro/source identity policy so this feature does not overdefine lifecycle behavior.

## Phase 7: Validation

- [X] T022 Run `.venv/bin/python -m pytest tests/test_mcp_knowledge.py tests/test_knowledge_service.py`.
- [X] T023 Run `.venv/bin/python -m pytest` if the focused suite passes and the local database/test environment is available.
- [X] T024 Verify MCP catalog manually or through tests to confirm `ingest_text` appears only when write enforcement is safe.

## Dependencies & Execution Order

- Phase 1 blocks exposing the tool.
- Phase 2 should be written before implementation tasks.
- Phase 3 and Phase 4 can proceed after the authorization decision, but `T013` depends on `T008` and `T011`.
- Phase 5 depends on the tool helper and authorization decision.
- Phase 6 can run in parallel with late implementation once the final enforcement path is known.

## MVP First

1. Complete T001-T002.
2. Complete T004, T007, T008, T011, T013, T015 and T016.
3. Validate a write-scoped successful ingestion and read-only denial.
4. Add remaining error-path tests and documentation before considering the feature complete.
