# Tasks: Experiência visual e usabilidade do frontend

**Input**: Design documents from `/specs/021-experiencia-visual-frontend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/frontend-experience.md`

## Phase 1: Foundation

- [x] T001 Consolidar tokens semânticos, reset, foco, movimento e primitives de página/formulário/cartão em `frontend/src/styles.css`.
- [x] T002 Atualizar os componentes de estado em `frontend/src/app/shared/{loading-state,empty-state,error-state,confirm-dialog,metadata-selector}/` para usar os tokens e manter semântica acessível.

## Phase 2: User Story 1 - Encontrar o próximo passo (P1)

**Goal**: permitir que a pessoa reconheça a área atual e encontre todas as rotas privadas em qualquer viewport.

- [x] T003 [US1] Ajustar `frontend/src/app/layout/authenticated-layout.component.html` com link de salto, agrupamento de navegação e estado semântico da rota atual.
- [x] T004 [US1] Ajustar `frontend/src/app/layout/authenticated-layout.component.css` para sidebar desktop, gaveta mobile, foco e redução de movimento.
- [x] T005 [US1] Adicionar `frontend/src/app/layout/authenticated-layout.component.spec.ts` cobrindo destinos, abrir/fechar por Escape/backdrop e retorno de foco.

## Phase 3: User Story 2 - Compreender e operar cada fluxo (P1)

**Goal**: dar hierarquia consistente a consulta, filtros, cartões, formulários e feedbacks sem alterar comportamentos existentes.

- [x] T006 [US2] Migrar Dashboard em `frontend/src/app/features/home/home.component.{html,css}` para cabeçalho, ações e cartões consistentes.
- [x] T007 [US2] Migrar Busca e Pergunte em `frontend/src/app/features/{search,ask}/*.{html,css}` para destacar consulta, agrupar filtros e padronizar resultados/respostas.
- [x] T008 [US2] Migrar Ingestão e Biblioteca em `frontend/src/app/features/{ingestion,library}/*.{html,css}` para tarefas e feedbacks claros.
- [x] T009 [US2] Migrar Organização e Detalhe em `frontend/src/app/features/{organization,source-detail}/*.{html,css}` para ações, painéis, metadados e risco visualmente coerentes.
- [x] T010 [US2] Atualizar testes de features afetadas em `frontend/src/app/features/**/*.spec.ts` quando a estrutura de acessibilidade ou ações for alterada.

## Phase 4: User Story 3 - Uso responsivo (P2)

**Goal**: preservar leitura e operação em 320 px, tablet e desktop.

- [x] T011 [US3] Revisar breakpoints, overflow e tamanho de controles nos CSS alterados sob `frontend/src/app/`.
- [ ] T012 [US3] Executar o roteiro responsivo e acessível de `specs/021-experiencia-visual-frontend/quickstart.md` em 320 px, 768 px e 1440 px. _(requer validação visual em navegador)_

## Phase 5: Verification

- [x] T013 Executar `npm run typecheck` em `frontend/`.
- [ ] T014 Executar `npm test -- --watch=false` em `frontend/`. _(bloqueado: Node.js 22.22.1; Angular CLI requer 22.22.3+)_
- [ ] T015 Executar `npm run build` em `frontend/`. _(bloqueado: Node.js 22.22.1; Angular CLI requer 22.22.3+)_
- [x] T016 Comparar implementação, `spec.md`, `plan.md`, `tasks.md` e constituição; registrar eventuais lacunas.

## Phase 6: Tema escuro

- [x] T017 Atualizar `spec.md`, `plan.md`, `data-model.md` e `contracts/frontend-experience.md` para incluir a preferência de tema local.
- [x] T018 Implementar `ThemeService` e seus testes em `frontend/src/app/core/theme.service.{ts,spec.ts}`.
- [x] T019 Aplicar tokens de tema escuro em `frontend/src/styles.css` e incluir alternância acessível no layout autenticado.

## Phase 7: Knowledge workspace

- [x] T020 Atualizar `frontend/src/app/layout/authenticated-layout.component.{html,css}` para navegação compacta por ícones SVG, tooltips em mouse/foco e rótulos completos na gaveta mobile.
- [x] T021 Reestruturar `frontend/src/app/features/home/home.component.{html,css}` como área de descoberta: busca principal, ações secundárias, fontes recentes e resumo compacto do acervo.

## Phase 8: Corpos das telas

- [x] T022 Aplicar layout progressivo de filtros e cartões responsivos em `frontend/src/app/features/{search,ask}/`.
- [x] T023 Aplicar grids de conteúdo, formulários e listas com melhor densidade em `frontend/src/app/features/{ingestion,library,organization,source-detail}/`.

## Phase 9: Realinhamento de usabilidade

- [x] T024 Reverter a divisão estrutural de páginas e aplicar fluxo vertical contextual em `frontend/src/app/features/{ingestion,organization,source-detail}/`.
- [x] T025 Reestruturar Biblioteca como barra de busca + filtros progressivos + lista de documentos em `frontend/src/app/features/library/`.
- [x] T026 Reorganizar resultados e citações em listas de leitura em `frontend/src/app/features/{search,ask,home}/`.

## Dependencies & Execution Order

- T001 e T002 são a fundação para T003–T011.
- T003–T005 entregam a primeira fatia verificável de navegação e podem ser testados antes da migração visual das features.
- T006–T009 podem ser aplicados em sequência para reduzir conflitos em `styles.css`; todos dependem da fundação.
- T011–T016 dependem das alterações de interface concluídas.
