# Tasks: Organização do acervo no frontend

**Input**: Artefatos em `specs/019-organizacao-frontend/`

## Phase 1: Core

- [x] T001 Adicionar payloads e métodos CRUD de categorias, tags e projetos em `frontend/src/app/core/knowledge.types.ts` e `knowledge-api.service.ts`.
- [x] T002 Cobrir os novos contratos HTTP em `frontend/src/app/core/knowledge-api.service.spec.ts`.
- [x] T003 Criar catálogo reativo e seus testes em `frontend/src/app/core/metadata-catalog.service.ts` e `.spec.ts`.

## Phase 2: US1 — Categorias e tags (P1)

- [x] T004 [US1] Criar rota, navegação e página Organização em `frontend/src/app/app.routes.ts`, layout e `features/organization/`.
- [x] T005 [US1] Implementar CRUD e confirmação para categorias/tags, incluindo conflito de item em uso.
- [x] T006 [US1] Evoluir `shared/metadata-selector/` com autocomplete acessível de tags e integrar Ingestão/detalhe.
- [ ] T007 [US1] Cobrir CRUD, conflitos e autocomplete com testes de componente.

## Phase 3: US2 — Projetos (P1)

- [x] T008 [US2] Implementar criação, edição, filtro de status, arquivamento e reativação de projetos.
- [ ] T009 [US2] Testar transições de status e atualização do catálogo ativo.

## Phase 4: US3 — Fontes do projeto (P2)

- [x] T010 [US3] Implementar `/organizacao/projetos/:projectId/fontes` e navegação para detalhe de fonte.
- [ ] T011 [US3] Testar carregamento, vazio, erro/retry e links das fontes.

## Phase 5: Verificação

- [ ] T012 Executar `npm run typecheck`, `npm test -- --watch=false` e `npm run build` em `frontend/`.
