# Tasks: Ciclo de Vida dos Documentos

**Input**: `specs/004-ciclo-vida-documentos/spec.md`, `plan.md`

## Phase 1: Spec and Storage Foundation

- [X] T001 Create Spec Kit feature artifacts for `004-ciclo-vida-documentos`.
- [X] T002 Add public UUID, content hash, canonical content and updated timestamp fields to `DocumentSource`.
- [X] T003 Update idempotent database initialization for new source fields, hash backfill and non-unique URI.

## Phase 2: Backend Lifecycle Services

- [X] T004 Add source repository helpers for public UUID, content hash, detail listing and deletion.
- [X] T005 Update ingestion to create new sources and reject duplicate content hash.
- [X] T006 Add transactional source detail, metadata patch, content patch and delete service.

## Phase 3: API and MCP Contracts

- [X] T007 Update Pydantic schemas for UUID source responses and patch payloads.
- [X] T008 Add `GET`, `PATCH` and `DELETE` source routes with status mapping.
- [X] T009 Add MCP read-only source detail lookup by UUID.

## Phase 4: Tests and Documentation

- [X] T010 Update service tests for duplicate detection, same-title coexistence and patch behavior.
- [X] T011 Update API integration tests for lifecycle endpoints and response contracts.
- [X] T012 Update MCP tests for source detail lookup.
- [X] T013 Update `doc/API.md` and feature contract notes.
- [X] T014 Run `.venv/bin/python -m pytest` and fix regressions.
