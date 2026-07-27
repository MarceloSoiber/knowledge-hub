# Tasks: Dashboard inicial do acervo

**Input**: Design documents from `/specs/020-dashboard-frontend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/frontend-dashboard.md`

**Tests**: Required by the feature specification and implementation plan.

## Phase 1: Setup

- [x] T001 Confirmar em `frontend/src/app/core/knowledge-api.service.ts` que os quatro GETs e tipos necessários já existem, sem mudança de contrato.
- [x] T002 Criar esta lista em `specs/020-dashboard-frontend/tasks.md` e registrar a estratégia de validação em `quickstart.md`.

---

## Phase 2: Foundational

- [x] T003 Criar os helpers puros e o estado independente por coleção em `frontend/src/app/features/home/home.component.ts`.
- [x] T004 Criar testes de estado, métricas e ordenação em `frontend/src/app/features/home/home.component.spec.ts`.

**Checkpoint**: a fundação permite consumir cada endpoint e derivar o resumo sem depender de uma barreira global.

---

## Phase 3: User Story 1 - Entender o acervo ao entrar (Priority: P1)

**Goal**: Exibir métricas confiáveis e as fontes recentes, com falha e retry isolados.

**Independent Test**: Popular respostas dos quatro endpoints e verificar cinco métricas, recentes ordenadas, dados vazios e erro parcial.

- [x] T005 [US1] Implementar carregamento independente e retry por coleção em `frontend/src/app/features/home/home.component.ts`.
- [x] T006 [US1] Implementar cartões de métricas, recentes e estados locais em `frontend/src/app/features/home/home.component.html`.
- [x] T007 [US1] Implementar grade responsiva e estados visuais em `frontend/src/app/features/home/home.component.css`.
- [x] T008 [US1] Cobrir carregamento, métricas, ordenação/fallback, vazio e falha/retry em `frontend/src/app/features/home/home.component.spec.ts`.

---

## Phase 4: User Story 2 - Começar uma ação de valor (Priority: P1)

**Goal**: Disponibilizar atalhos sempre navegáveis para os três fluxos de valor.

**Independent Test**: Renderizar o Dashboard em carregamento/erro e confirmar os links para Busca, Pergunte e Ingestão.

- [x] T009 [US2] Adicionar atalhos semânticos e links de fontes em `frontend/src/app/features/home/home.component.html`.
- [x] T010 [US2] Cobrir links e disponibilidade durante erro/carregamento em `frontend/src/app/features/home/home.component.spec.ts`.

---

## Phase 5: User Story 3 - Ser orientado em uma base vazia (Priority: P2)

**Goal**: Distinguir base vazia de falha e orientar a primeira ingestão.

**Independent Test**: Retornar `[]` para fontes e metadados e verificar cartões com zero e CTA funcional.

- [x] T011 [US3] Integrar `EmptyStateComponent` e CTA para `/ingestao` em `frontend/src/app/features/home/home.component.html`.
- [x] T012 [US3] Cobrir CTA e cartões vazios em `frontend/src/app/features/home/home.component.spec.ts`.

---

## Phase 6: Verification

- [x] T013 Executar `npm run typecheck` em `frontend/`.
- [ ] T014 Executar `npm test -- --watch=false` em `frontend/`.
- [ ] T015 Executar `npm run build` em `frontend/`.
- [x] T016 Revisar aderência de `spec.md`, `plan.md`, `tasks.md` e implementação; registrar tarefas concluídas.

## Dependencies & Execution Order

- T003–T004 antecedem T005–T012.
- T005–T008 entregam o MVP de resumo do acervo.
- T009–T010 e T011–T012 dependem da estrutura do template de T006, mas não alteram contratos HTTP.
- T013–T016 dependem da implementação completa.
