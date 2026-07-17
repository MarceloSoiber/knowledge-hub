# Implementation Plan: Metadados e Citacoes na Busca

**Branch**: `005-metadados-citacoes` | **Date**: 2026-07-17 | **Spec**: `specs/005-metadados-citacoes/spec.md`

## Summary

Enrich semantic search and answer results with citation-ready source metadata and chunk location. Store chunk metadata as JSONB, preserve page/section/offsets during ingestion, and expose the same public contract through FastAPI and MCP.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: FastAPI, SQLAlchemy async, Pydantic v2, FastMCP, pgvector

**Storage**: PostgreSQL with pgvector; `init_db()` performs idempotent schema updates.

**Testing**: `.venv/bin/python -m pytest`

**Target Platform**: Linux web service with MCP server.

**Performance Goals**: Search remains within the existing 500ms target for typical queries.

**Constraints**: Keep routes thin, backend business logic in services/repositories, update `doc/API.md`.

**Scale/Scope**: Enriched result contract for existing knowledge search; no new frontend workflow.

## Constitution Check

- Code Quality: Pass. Metadata and chunking logic stays in services/repositories; routes remain thin.
- Testing Standards: Pass. Unit, API and MCP tests cover public contract and metadata behavior.
- Performance: Pass. Search adds joins already needed for source/category citation context.
- Documentation: Pass. API docs and Spec Kit contracts are updated.

## Project Structure

```text
backend/app/
├── db/init.py
├── db/models.py
├── repositories/chunks.py
├── schemas/knowledge.py
└── services/
    ├── documents/chunker.py
    ├── documents/extractors.py
    ├── ingestion.py
    ├── rag.py
    └── sources.py

mcp_server/tools/knowledge.py

tests/
├── test_knowledge_api_integration.py
├── test_knowledge_service.py
└── test_mcp_knowledge.py
```

**Structure Decision**: Use existing backend, repository and MCP modules. No frontend changes.

## Risk Notes

- Changing `source_id` in search hits from internal integer to public UUID is an intentional public contract change.
- Existing invalid textual metadata is converted to empty JSON during best-effort migration.
- OCR-only PDFs may not retain page metadata until OCR is split by page.
