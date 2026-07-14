# Tasks: Categorias Muitos-Para-Muitos

**Input**: Design documents from `/specs/002-categorias-muitos-para-muitos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Phase 1: Spec Kit Artifacts

- [X] T001 Create spec, plan, research, data model, contract, quickstart and tasks files.

## Phase 2: Persistence Foundation

- [X] T002 Update SQLAlchemy models for `Category.created_at`, source/category many-to-many relationships and association table.
- [X] T003 Update idempotent database initialization to migrate legacy `category_id` values into `document_source_categories` and drop the legacy column.

## Phase 3: Backend Services

- [X] T004 Update schemas to expose `category_ids` inputs and `categories` outputs.
- [X] T005 Implement category normalization, create, update, delete and multi-fetch validation services.
- [X] T006 Update ingestion to require multiple categories, use category-independent URIs and refresh associations on recadastro.
- [X] T007 Update source listing and search repositories to return categories and filter with ANY semantics without duplicate chunks.

## Phase 4: API and MCP

- [X] T008 Update FastAPI routes for new category CRUD, ingestion, search and answer contracts.
- [X] T009 Update MCP models/tools/server signatures for `category_ids` and source categories.

## Phase 5: Tests and Documentation

- [X] T010 Update service tests for schema validation, ingestion associations, category management and search filtering.
- [X] T011 Update API integration tests for new contracts and status-code mapping.
- [X] T012 Update README and `doc/API.md` to remove singular `category_id` and document category CRUD.

## Phase 6: Validation

- [X] T013 Run pytest and fix regressions.
