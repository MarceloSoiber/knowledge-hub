# Tasks: Metadados e Citacoes na Busca

**Input**: Design documents from `/specs/005-metadados-citacoes/`

**Prerequisites**: plan.md, spec.md

## Phase 1: Spec Kit Artifacts

- [x] T001 Create `specs/005-metadados-citacoes/spec.md`
- [x] T002 Create `specs/005-metadados-citacoes/plan.md`
- [x] T003 Create `specs/005-metadados-citacoes/tasks.md`
- [x] T004 Create API/MCP contract notes in `specs/005-metadados-citacoes/contracts/search-citations.md`

## Phase 2: Metadata Foundation

- [x] T005 Change `KnowledgeChunk.metadata_json` to JSONB in `backend/app/db/models.py`
- [x] T006 Add idempotent metadata JSONB migration in `backend/app/db/init.py`
- [x] T007 Add structured chunk location support in `backend/app/services/documents/chunker.py`
- [x] T008 Preserve PDF page spans in `backend/app/services/documents/extractors.py`

## Phase 3: Search Result Contract

- [x] T009 Expand `KnowledgeChunkRead` in `backend/app/schemas/knowledge.py`
- [x] T010 Store structured metadata during ingestion in `backend/app/services/ingestion.py`
- [x] T011 Store structured metadata during content updates in `backend/app/services/sources.py`
- [x] T012 Build enriched search hits in `backend/app/repositories/chunks.py`
- [x] T013 Update RAG context formatting in `backend/app/services/rag.py`
- [x] T014 Update MCP search hit schema in `mcp_server/tools/knowledge.py`

## Phase 4: Tests and Docs

- [x] T015 Update service tests for chunk location, public UUID source IDs and metadata allowlist
- [x] T016 Update API integration tests for enriched `/search` and `/answer` contracts
- [x] T017 Update MCP tests for enriched search hits
- [x] T018 Update `doc/API.md`
- [x] T019 Run `.venv/bin/python -m pytest`
