# Implementation Plan: Projetos

**Branch**: `009-projetos` | **Date**: 2026-07-20 | **Spec**: `specs/009-projetos/spec.md`

**Input**: Feature specification from `/specs/009-projetos/spec.md`

## Summary

Add projects as an optional work-context dimension for knowledge sources. Introduce `projects` and `document_source_projects`, expose project lifecycle operations, allow ingestion/source patch to associate projects by id, list sources for a project, and support `project_ids` filters in search, answer and MCP. Categories and tags remain subject/classification dimensions; projects narrow context without duplicating documents or chunks.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, SQLAlchemy async, Pydantic v2, FastMCP, PostgreSQL + pgvector

**Storage**: PostgreSQL with pgvector; add relational `projects` and `document_source_projects` tables with unique/indexed project names and association indexes.

**Testing**: `.venv/bin/python -m pytest`

**Target Platform**: Linux web service with MCP server.

**Project Type**: Backend API + MCP tool integration.

**Performance Goals**: Preserve typical search under 500ms; project CRUD/listing and project source list under 1 second for representative local data.

**Constraints**: Keep routes thin; business rules in `backend/app/services/projects.py`; persistence helpers in `backend/app/repositories/projects.py`; update `doc/API.md`; do not regenerate embeddings for project-only source changes.

**Scale/Scope**: Existing `/api/v1/knowledge/*` API, MCP knowledge tools, source listing/detail, text/upload ingestion, source patch, search and answer. No mandatory frontend change.

## Constitution Check

- Code Quality: Pass. Project rules belong in service/repository modules; API/MCP only validate and forward.
- Testing Standards: Pass. Unit and integration tests cover project lifecycle, association, filtering and MCP contracts.
- Performance: Pass with gate. Project filters use indexed many-to-many association predicates before candidate limits.
- Documentation: Pass. API documentation and Spec Kit contract must distinguish categories/tags from projects.

## Project Structure

### Documentation (this feature)

```text
specs/009-projetos/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- knowledge-projects.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/app/
|-- api/routes/
|   `-- knowledge.py
|-- db/
|   |-- init.py
|   `-- models.py
|-- repositories/
|   |-- chunks.py
|   |-- projects.py
|   `-- sources.py
|-- schemas/
|   `-- knowledge.py
`-- services/
    |-- ingestion.py
    |-- projects.py
    |-- search.py
    `-- sources.py

mcp_server/
|-- server.py
`-- tools/knowledge.py

tests/
|-- test_knowledge_api_integration.py
|-- test_knowledge_service.py
`-- test_mcp_knowledge.py

doc/API.md
```

**Structure Decision**: Reuse the knowledge route and MCP module because projects are another knowledge dimension, not a separate bounded context. Add project-specific service/repository modules to keep lifecycle/status rules out of routes.

## Implementation Details

### Database and Lifecycle

- Add `Project` SQLAlchemy model with:
  - `id`
  - `name`
  - `normalized_name`
  - `description`
  - `status`
  - `created_at`
  - `updated_at`
- Add `document_source_projects` association table:
  - `document_source_id` FK with `ON DELETE CASCADE`.
  - `project_id` FK.
  - composite primary key.
- Add unique index on `projects.normalized_name`.
- Add indexes on `document_source_projects.project_id` and optionally `(project_id, document_source_id)`.
- Use statuses `active` and `archived` for MVP. Archive/reactivate updates `status`; no source/chunk deletion occurs.
- Implement idempotent schema setup in `backend/app/db/init.py`, consistent with existing category/tag init style.

### Service and Repository Design

- Add `backend/app/repositories/projects.py`:
  - `get_project`
  - `get_project_by_normalized_name`
  - `list_projects`
  - `list_projects_by_ids`
  - `list_sources_for_project`
- Add `backend/app/services/projects.py`:
  - `ProjectNotFoundError`
  - `ProjectConflictError`
  - `ProjectStatusError` if invalid transitions need explicit errors.
  - `normalize_project_name`
  - `get_projects(session, project_ids)`
  - `create_project`, `update_project`, `archive_project`, `reactivate_project`.
- Keep delete out of MVP unless a safe no-association delete is explicitly chosen during implementation.
- Preserve request order in `get_projects()` and report the first missing id, matching categories/tags.

### API Contract

- Add Pydantic schemas:
  - `ProjectRead`
  - `ProjectWrite`
  - `ProjectPatch`
  - reusable project id validators.
- Extend source/chunk responses with `projects: list[ProjectRead]`.
- Extend ingestion and source patch:
  - optional `project_ids`.
  - source patch `project_ids: []` clears project associations.
- Add endpoints:
  - `GET /knowledge/projects`
  - `POST /knowledge/projects`
  - `PATCH /knowledge/projects/{project_id}`
  - `POST /knowledge/projects/{project_id}/archive`
  - `POST /knowledge/projects/{project_id}/reactivate`
  - `GET /knowledge/projects/{project_id}/sources`
- Decide in implementation whether list defaults to active-only or all statuses. Recommended: include all by default with optional `status` filter so archived projects remain discoverable.
- Error mapping:
  - missing project -> `404`.
  - duplicate normalized name -> `409`.
  - invalid status/filter -> `422`.

### Ingestion and Source Patch

- Extend `ingest_plain_text()` and `ingest_uploaded_file()` with optional `project_ids`.
- Validate project ids before content extraction/embedding generation where feasible.
- Persist project associations on `DocumentSource`.
- Extend `update_source()` so project-only changes do not rebuild chunks or call embeddings.
- If content changes and project ids are also supplied, update associations and regenerated chunks in one transaction.
- Return projects in upload/text ingest responses and source detail/list responses.

### Search, Answer and MCP

- Extend `search_knowledge()` and `answer_knowledge()` with `project_ids: list[int] | None`.
- Validate project ids before embedding generation and before repository queries.
- Extend vector and text candidate queries in `backend/app/repositories/chunks.py`:
  - project filter uses `exists()` over `document_source_projects`.
  - apply project/category/tag filters before candidate limits.
  - combine dimensions with AND and values within each dimension with ANY.
- Keep general knowledge visible when no `project_ids` filter is provided.
- Exclude unassociated general sources when `project_ids` is provided unless a future "include general knowledge" option is explicitly added.
- Extend MCP:
  - source/hit/read models include projects.
  - `search` accepts `project_ids`.
  - `ingest_text` accepts `project_ids`.
  - `projects()` lists projects.
  - optional `project_sources(project_id)` helper if useful for clients.

### Documentation and Observability

- Update `doc/API.md` with project endpoints, source/chunk response fields and search/answer/MCP request fields.
- Add contract docs in `specs/009-projetos/contracts/knowledge-projects.md`.
- Log project filter counts where search already logs candidate counts; do not log arbitrary project names by default.

## Data Model / API Implications

- Database gains `projects` and `document_source_projects`.
- Source and chunk responses gain `projects: list[ProjectRead]`.
- Search and answer requests gain optional `project_ids`.
- Ingestion and source patch requests gain optional project association fields.
- MCP source/hit models gain projects and MCP search/ingest accepts project ids.
- API docs must clearly state:
  - category = broad controlled subject.
  - tag = granular reusable marker.
  - project = work context.

## Test Strategy

- Unit test project normalization, duplicate names, missing-id validation and archive/reactivate behavior.
- Service tests for creating sources with multiple projects and updating only projects without embedding calls.
- Repository/service tests for project-filtered search, project+category/tag combinations and no duplicate chunk ids.
- API integration tests for project CRUD, archive/reactivate, project source listing, ingestion/patch contracts and search/answer filters.
- MCP tests for project fields in source/search responses, `project_ids` forwarding and project listing tool.
- Documentation quickstart smoke test with project endpoints.

## Risk Notes

- Project scope can be confused with category. Documentation and field names must make project a work context, not a subject taxonomy.
- Archived project semantics affect agents. Recommended behavior: archived projects remain filterable by explicit id but are visibly marked `archived`.
- General knowledge behavior under project filters may be debated. MVP should exclude general sources when a project filter is present, preserving strict context for AI.
- Project-only patch must avoid embedding calls just like tag-only/category-only metadata updates.
- Additional many-to-many filters can slow search if joins are not indexed. Use `exists()` predicates and indexes before candidate limits.

## Complexity Tracking

No constitution violations identified.
