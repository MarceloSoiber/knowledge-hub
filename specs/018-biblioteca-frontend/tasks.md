# Tasks: Biblioteca e manutenção de fontes

**Input**: Artefatos em `specs/018-biblioteca-frontend/`

## Phase 1: Fundação

- [x] T001 Adicionar `KnowledgeSourcePatchRequest`, `updateSource` e `deleteSource` tipados em `frontend/src/app/core/knowledge.types.ts` e `frontend/src/app/core/knowledge-api.service.ts`.
- [x] T002 Cobrir PATCH e DELETE com `HttpTestingController` em `frontend/src/app/core/knowledge-api.service.spec.ts`.
- [x] T003 Registrar `/biblioteca` e a navegação autenticada em `frontend/src/app/app.routes.ts` e `frontend/src/app/layout/authenticated-layout.component.html`.

## Phase 2: US1 — Consultar o acervo (P1)

- [x] T004 [US1] Criar a página de Biblioteca e seus estados em `frontend/src/app/features/library/`.
- [x] T005 [US1] Implementar busca normalizada e filtros locais cumulativos por associações.
- [x] T006 [US1] Cobrir carregamento, filtro e estados de lista em `frontend/src/app/features/library/library-page.component.spec.ts`.

## Phase 3: US2 — Editar uma fonte (P2)

- [x] T007 [US2] Evoluir `frontend/src/app/features/source-detail/` para exibir detalhe completo e editar PATCH mínimo.
- [x] T008 [US2] Exibir aviso de reprocessamento quando o conteúdo mudar e preservar rascunho em erros.
- [ ] T009 [US2] Cobrir carregamento, PATCH, aviso e erros no spec do detalhe.

## Phase 4: US3 — Excluir uma fonte (P3)

- [x] T010 [US3] Integrar `ConfirmDialogComponent` à exclusão e navegar à Biblioteca após `204`.
- [ ] T011 [US3] Cobrir cancelar/Escape, confirmação e falhas de exclusão no spec do detalhe.

## Phase 5: Verificação

- [ ] T012 Executar `npm run typecheck`, `npm test -- --watch=false` e `npm run build` em `frontend/`.
