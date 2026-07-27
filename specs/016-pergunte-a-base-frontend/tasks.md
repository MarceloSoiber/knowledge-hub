# Tasks: Pergunte à Base no Frontend

**Input**: Design documents from `/specs/016-pergunte-a-base-frontend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/frontend-answer.md`

## Phase 1: Setup

- [x] T001 Create the Angular feature folder and register protected route in `frontend/src/app/features/ask/` and `frontend/src/app/app.routes.ts`.

## Phase 2: Foundational

- [x] T002 Define typed local request/history/view state and safe API error mapping in `frontend/src/app/features/ask/ask-page.component.ts`.
- [x] T003 Confirm and reuse `KnowledgeApiService.answer()` and `KnowledgeAnswer*` contracts in `frontend/src/app/core/knowledge-api.service.ts` and `frontend/src/app/core/knowledge.types.ts`; do not change the API contract.

## Phase 3: User Story 1 - Fazer uma pergunta fundamentada (Priority: P1)

**Goal**: Send a valid question and display its textual RAG answer with navigable source cards.

**Independent Test**: Mock a successful answer response and confirm text, source metadata and `/sources/:sourceId` link render.

- [x] T004 [P] [US1] Add component tests for success response, source rendering and route link in `frontend/src/app/features/ask/ask-page.component.spec.ts`.
- [x] T005 [US1] Implement question submission, loading guard, answer rendering and source-card navigation in `frontend/src/app/features/ask/ask-page.component.ts` and `.html`.
- [x] T006 [US1] Add responsive, semantic source-card and answer styles in `frontend/src/app/features/ask/ask-page.component.css`.

## Phase 4: User Story 2 - Restringir o contexto da resposta (Priority: P2)

**Goal**: Filter answer context by metadata, limit and minimum score without changing the question.

**Independent Test**: Select each metadata type and assert the serialized `/answer` request; remove a chip and assert other form fields remain.

- [x] T007 [P] [US2] Add component tests for request serialization, validation and independent chip removal in `frontend/src/app/features/ask/ask-page.component.spec.ts`.
- [x] T008 [US2] Implement metadata loading, tag autocomplete, filter chips and local limit/score validation in `frontend/src/app/features/ask/ask-page.component.ts` and `.html`.

## Phase 5: User Story 3 - Recuperar-se de falhas e reutilizar a resposta (Priority: P3)

**Goal**: Preserve the form on expected failures and allow accessible copying of response/references.

**Independent Test**: Simulate no sources and expected error statuses, then test clipboard success and failure feedback.

- [x] T009 [P] [US3] Add component tests for no-source state, safe error messages, history reset semantics and clipboard feedback in `frontend/src/app/features/ask/ask-page.component.spec.ts`.
- [x] T010 [US3] Implement status-specific recovery, no-source messaging, in-memory history and clipboard actions in `frontend/src/app/features/ask/ask-page.component.ts` and `.html`.

## Phase 6: Polish & Verification

- [x] T011 [P] Update accessible labels, focus states and mobile layout in `frontend/src/app/features/ask/ask-page.component.html` and `.css`.
- [ ] T012 Run `npm run typecheck`, `npm run build` and relevant frontend tests from `frontend/` (typecheck passed; build and tests blocked by Node 22.22.1, while Angular CLI requires >=22.22.3).

## Dependencies & Execution Order

- T001–T003 block the feature implementation.
- T004–T006 deliver the independently usable MVP.
- T007–T008 build on the shared form from US1.
- T009–T010 build on the successful answer state from US1.
- T011–T012 run after all feature work.

## Implementation Strategy

Implement the route and P1 question/answer path first; then reuse the existing search filter pattern for P2 and add failure/copy/history behavior for P3. Keep all feature state local, never persist result text or tokens, and use the existing typed API client.
