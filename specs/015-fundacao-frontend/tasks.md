# Tasks: Fundação do Frontend

**Input**: `spec.md` and `plan.md` in `/specs/015-fundacao-frontend/`

## Phase 1: Setup

- [x] T001 Criar a estrutura `core`, `layout`, `shared` e `features` em `frontend/src/app/`.
- [x] T002 Configurar Router e o comando de testes Angular em `frontend/angular.json` e `frontend/package.json`.

## Phase 2: Foundational

- [x] T003 Criar contratos de domínio e normalização de erros em `frontend/src/app/core/knowledge.types.ts` e `frontend/src/app/core/api-error.ts`.
- [x] T004 Criar `KnowledgeApiService` tipado em `frontend/src/app/core/knowledge-api.service.ts`.
- [x] T005 Atualizar `AuthService`, criar `auth.guard.ts` e `unauthorized.interceptor.ts` em `frontend/src/app/core/`.
- [x] T006 Registrar Router e interceptors em `frontend/src/app/app.config.ts` e definir rotas em `frontend/src/app/app.routes.ts`.

## Phase 3: User Story 1 - Acessar a área autenticada (P1)

**Goal**: Login separado, rota privada `/inicio`, layout com navegação e logout.

- [x] T007 [US1] Extrair login para `frontend/src/app/features/login/`.
- [x] T008 [US1] Criar `AuthenticatedLayoutComponent` em `frontend/src/app/layout/`.
- [x] T009 [US1] Criar página inicial em `frontend/src/app/features/home/` e tornar `AppComponent` um host de rota.

## Phase 4: User Story 2 - Encerrar sessão inválida (P1)

**Goal**: Proteger rotas e reagir globalmente a 401 sem expor token.

- [ ] T010 [US2] Validar restauração de sessão, guard e redirecionamento 401 por testes e fluxo manual.

## Phase 5: User Story 3 - Estados reutilizáveis acessíveis (P2)

**Goal**: Componentes compartilhados para feedback, confirmação e metadados.

- [x] T011 [P] [US3] Criar loading, erro e estado vazio em `frontend/src/app/shared/`.
- [x] T012 [P] [US3] Criar diálogo de confirmação acessível em `frontend/src/app/shared/confirm-dialog/`.
- [x] T013 [US3] Criar seletor de metadados em `frontend/src/app/shared/metadata-selector/`.
- [x] T014 [US3] Consolidar tokens visuais, foco e responsividade em `frontend/src/styles.css`.

## Phase 6: Verification

- [ ] T015 Criar testes unitários de core e shared com `HttpTestingController` em `frontend/src/app/**/*.spec.ts`.
- [ ] T016 Executar `npm run typecheck`, testes frontend e `npm run build` em `frontend/`.

## Dependencies & Execution Order

- T001–T006 bloqueiam as histórias de usuário.
- T007–T009 entregam o primeiro fluxo navegável; T010 o protege contra sessão inválida.
- T011–T014 podem avançar após T003 e são reutilizáveis pelas próximas fases.
- T015–T016 encerram a entrega após todos os componentes estarem integrados.

## Verification Note

`npm run typecheck` passou em 2026-07-24. `npm test` e `npm run build` não puderam iniciar porque o ambiente usa Node.js 22.22.1 e o Angular CLI 22 requer ao menos 22.22.3. T010, T015 e T016 permanecem abertos até que o ambiente compatível execute a cobertura completa.
