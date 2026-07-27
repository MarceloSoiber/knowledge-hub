# Tasks: Ingestão de Conhecimento no Frontend

**Input**: Design documents from `/specs/017-ingestao-frontend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/frontend-ingestion.md`

## Phase 1: Setup and route

- [x] T001 Register protected `/ingestao` route in `frontend/src/app/app.routes.ts`.
- [x] T002 Add the Ingestão navigation item in `frontend/src/app/layout/authenticated-layout.component.html`.
- [x] T003 Create the standalone feature files under `frontend/src/app/features/ingestion/`.

## Phase 2: Foundation

- [x] T004 Load categories, tags and projects with `KnowledgeApiService`; expose loading, error and retry states in `ingestion-page.component.ts`.
- [x] T005 Reuse `MetadataSelectorComponent`, `LoadingStateComponent` and `ErrorStateComponent` without duplicating HTTP or metadata mutation logic.

## Phase 3: User Story 1 — Ingerir um arquivo (P1)

**Goal**: Submit a valid file with metadata and open the created source.

- [x] T006 [US1] Add unit tests for `FormData` serialization and successful/invalid file submission in `frontend/src/app/features/ingestion/ingestion-page.component.spec.ts`.
- [x] T007 [US1] Implement file selection, accepted-extension/10 MB/category validation and accessible errors in the ingestion feature files.
- [x] T008 [US1] Call `KnowledgeApiService.upload`, render success with source link and clear only the completed file draft.

## Phase 4: User Story 2 — Adicionar texto (P1)

**Goal**: Submit valid text with metadata and retain data on failure.

- [x] T009 [US2] Add tests for JSON serialization, required title/content/categories and successful text submission in `frontend/src/app/features/ingestion/ingestion-page.component.spec.ts`.
- [x] T010 [US2] Implement text form, local validation and `KnowledgeApiService.ingestText` request with omitted empty optional arrays.
- [x] T011 [US2] Render the successful text result and clear only the completed text draft.

## Phase 5: User Story 3 — Processamento e recuperação (P2)

**Goal**: Prevent duplicate submits and recover safely from conflicts and service errors.

- [x] T012 [US3] Add tests for pending requests, `409` with/without UUID and error-message mapping in `frontend/src/app/features/ingestion/ingestion-page.component.spec.ts`.
- [x] T013 [US3] Implement per-tab indeterminate processing state and duplicate-submit guards.
- [x] T014 [US3] Implement safe HTTP-error mapping, structured duplicate link and metadata reload action while retaining drafts.

## Phase 6: Verification

- [ ] T015 Run `npm run typecheck`, `npm test -- --watch=false` and `npm run build` in `frontend/` (typecheck passed; test/build blocked by Node.js v22.22.1, while Angular CLI requires v22.22.3+).
- [x] T016 Review the implementation against `spec.md`, `plan.md` and accessibility/manual scenarios in `quickstart.md`.

## Dependencies

- T001–T005 block the feature UI.
- T006–T008 and T009–T011 depend on T001–T005 and can then be implemented independently.
- T012–T014 depend on both submit flows because they normalize shared states.
- T015–T016 depend on all prior tasks.
