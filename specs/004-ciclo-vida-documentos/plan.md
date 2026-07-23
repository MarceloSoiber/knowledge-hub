# Implementation Plan: Ciclo de Vida dos Documentos

**Branch**: `004-ciclo-vida-documentos` | **Date**: 2026-07-16 | **Spec**: `specs/004-ciclo-vida-documentos/spec.md`

## Summary

Add stable public UUID lifecycle management for document sources. Ingestion creates new sources unless canonical content is duplicated, detail/update/delete operate by UUID, metadata-only patches avoid embedding calls, and content patches replace chunks atomically.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: FastAPI, SQLAlchemy async, Pydantic v2, FastMCP, pgvector

**Storage**: PostgreSQL with pgvector; `init_db()` performs idempotent schema updates.

**Testing**: `.venv/bin/python -m pytest`

**Target Platform**: Linux web service with MCP server.

**Performance Goals**: Search remains within existing 500ms target; metadata-only updates avoid embedding provider calls.

**Constraints**: Keep routes thin, backend business logic in services, update `doc/API.md` for API changes.

**Scale/Scope**: Source lifecycle for existing knowledge documents; no soft delete and no automated backup implementation.

## Constitution Check

- Code Quality: Pass. Business logic moves to `backend/app/services/sources.py`; routes stay thin.
- Testing Standards: Pass. Unit and API integration tests cover lifecycle and duplicate behavior.
- Performance: Pass. Embeddings are regenerated only for changed content.
- Documentation: Pass. API docs and Spec Kit contracts are updated.

## Project Structure

```text
backend/app/
├── api/routes/knowledge.py
├── db/init.py
├── db/models.py
├── repositories/sources.py
├── schemas/knowledge.py
└── services/
    ├── ingestion.py
    └── sources.py

mcp_server/
├── server.py
└── tools/knowledge.py

tests/
├── test_knowledge_api_integration.py
├── test_knowledge_service.py
└── test_mcp_knowledge.py
```

**Structure Decision**: Use the existing FastAPI backend, repository helpers and MCP tool module; no frontend changes.

## Risk Notes

- Dropping uniqueness from `document_sources.uri` is required so same-title/different-content sources can coexist.
- Existing sources receive best-effort `content_text` from concatenated chunks during init; exact original upload bytes are not recoverable.
