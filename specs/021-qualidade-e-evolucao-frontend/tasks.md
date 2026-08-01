# Tasks: Qualidade, segurança e evolução do frontend

**Input**: Design documents from `/specs/021-qualidade-e-evolucao-frontend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/frontend-quality.md`

**Tests**: Required by the specification.

## Phase 1: Foundation and session boundary

- [x] T001 Create core specs for `AuthService`, `authGuard`, `authInterceptor`, and `unauthorizedInterceptor` under `frontend/src/app/core/`.
- [x] T002 Expand `frontend/src/app/core/api-error.spec.ts` and `knowledge-api.service.spec.ts` for safe error mapping and published HTTP reads.
- [x] T003 Extract and test safe return URL behavior in `frontend/src/app/features/login/`.

## Phase 2: Critical-flow component coverage

- [x] T004 Add component coverage for Login and confirmation dialog behavior in `frontend/src/app/features/login/` and `frontend/src/app/shared/confirm-dialog/`.
- [x] T005 Extend tests for component loading, empty/error/success, validation and destructive-operation confirmation in critical features where gaps remain.
- [x] T006 Keep the quality matrix and quickstart aligned with executable tests in `specs/021-qualidade-e-evolucao-frontend/`.

## Phase 3: Verification

- [x] T007 Run `npm run typecheck` in `frontend/`.
- [x] T008 Run `npm test -- --watch=false` in `frontend/` with a supported Node version.
- [x] T009 Run `npm run build` in `frontend/` with a supported Node version.
- [x] T010 Review spec, plan, tasks and implementation; record remaining manual checks or environment blockers.

## Manual delivery check still required

- [ ] Execute the desktop/mobile, keyboard and screen-reader flow in `quickstart.md` against a configured backend. This requires an interactive browser and test credentials; it was not automated in this implementation.
