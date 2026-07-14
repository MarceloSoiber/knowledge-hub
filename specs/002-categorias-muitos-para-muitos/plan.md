# Implementation Plan: Categorias Muitos-Para-Muitos

**Branch**: `002-categorias-muitos-para-muitos` | **Date**: 2026-07-14 | **Spec**: `specs/002-categorias-muitos-para-muitos/spec.md`

**Input**: Feature specification from `/specs/002-categorias-muitos-para-muitos/spec.md`

## Summary

Replace the singular `document_sources.category_id` relationship with a many-to-many association, update API/MCP payloads to use `category_ids`, and add category management operations with idempotent migration in `backend/app/db/init.py`.

## Technical Context

**Language/Version**: Python 3.11+, TypeScript for frontend docs only

**Primary Dependencies**: FastAPI, SQLAlchemy async, Pydantic v2, PostgreSQL + pgvector, FastMCP

**Storage**: PostgreSQL with pgvector

**Testing**: pytest via `.venv/bin/python -m pytest`

**Target Platform**: Docker/local Linux web service

**Project Type**: Backend API + MCP server + informational frontend

**Performance Goals**: Preserve vector search response under existing 500ms typical target.

**Constraints**: Routes stay thin; business rules live in services; no singular `category_id` remains in public contract.

**Scale/Scope**: Existing knowledge hub with document sources, chunks, categories and MCP read tools.

## Constitution Check

- Clean architecture: Pass. Routes delegate category, ingestion and search logic to services/repositories.
- Testing: Pass. Unit and integration tests cover migration-sensitive contracts and critical validation.
- Documentation: Pass. `doc/API.md` and README MCP/API sections are updated with the new contract.
- Performance: Pass. Category filtering uses association predicates without duplicate rows.

## Project Structure

### Documentation (this feature)

```text
specs/002-categorias-muitos-para-muitos/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── knowledge-categories.md
└── tasks.md
```

### Source Code

```text
backend/app/
├── api/routes/knowledge.py
├── db/init.py
├── db/models.py
├── repositories/
├── schemas/knowledge.py
└── services/

mcp_server/
├── server.py
└── tools/knowledge.py

tests/
├── test_knowledge_api_integration.py
└── test_knowledge_service.py
```

**Structure Decision**: Use the existing backend and MCP layout; no new package boundary is needed.

## Complexity Tracking

No constitution violations.
