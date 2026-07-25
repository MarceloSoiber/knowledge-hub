# Tasks: Busca Inteligente no Frontend

**Input**: Design documents from `/specs/015-busca-inteligente-frontend/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md` and `contracts/frontend-search.md`.

**Dependency**: A Fase 01 de `plan/frontend/01-fundacao.md` deve estar concluída antes de T003: Router, guard, `KnowledgeApiService`, tipos de domínio e componentes compartilhados são bloqueadores.

## Phase 1: Validate Foundation and Shared Contracts

**Purpose**: Garantir os pré-requisitos sem duplicar infraestrutura prevista na fundação.

- [x] T001 Implementar a infraestrutura mínima da Fase 01 em `frontend/src/app/app.routes.ts`, `frontend/src/app/core/auth.guard.ts` e `frontend/src/app/layout/` para disponibilizar rotas protegidas e shell autenticado.
- [x] T002 [P] Criar em `frontend/src/app/shared/models/knowledge.models.ts` os tipos públicos `SearchRequest`, `SearchResponse`, `KnowledgeSearchResult`, `Location`, `Category`, `Tag` e `Project`, incluindo `score: number | null` e `match_reasons?: ('vector' | 'text')[]`.
- [x] T003 Implementar em `frontend/src/app/core/knowledge-api.service.ts` os métodos tipados para `categories()`, `tags()`, `autocompleteTags(query, limit)`, `projects()`, `search(request)` e `source(sourceId)`, conforme `specs/015-busca-inteligente-frontend/contracts/frontend-search.md`.
- [ ] T004 [P] Criar ou completar testes de contrato do cliente em `frontend/src/app/core/knowledge-api.service.spec.ts` para serialização da busca, campos opcionais, score nulo e motivos opcionais.

**Checkpoint**: A feature possui contratos tipados e uma única camada de acesso aos cinco endpoints.

---

## Phase 2: User Story 1 - Encontrar trechos relevantes (Priority: P1) 🎯 MVP

**Goal**: Permitir a busca simples autenticada, mostrar resultados citáveis e navegar por `source_id` público.

**Independent Test**: Pesquisar um termo conhecido em uma API stubada ou ambiente com dados e abrir o link de uma fonte retornada.

### Tests for User Story 1

- [ ] T005 [P] [US1] Criar `frontend/src/app/features/search/search-page.component.spec.ts` cobrindo consulta válida, consulta em branco, loading, resposta com resultados e estado vazio.
- [ ] T006 [P] [US1] Criar `frontend/src/app/features/search/search-result-list.component.spec.ts` cobrindo título, trecho, localização, chips, score nulo e link baseado em `sourceId`.

### Implementation for User Story 1

- [x] T007 [US1] Registrar em `frontend/src/app/app.routes.ts` as rotas autenticadas `search` e `sources/:sourceId` usando o guard e o shell.
- [x] T008 [US1] Criar `frontend/src/app/features/search/search-page.component.*` com formulário de consulta e limite, estado local e submissão pelo `KnowledgeApiService`.
- [x] T009 [US1] Implementar em `frontend/src/app/features/search/search-page.component.*` a renderização segura de resultados, localização condicional, metadados e link acessível por UUID público; criar `frontend/src/app/features/source-detail/source-detail.component.*` para abrir a fonte.
- [x] T010 [US1] Implementar na página estados semânticos de loading, vazio e erro com `aria-live` e `role="alert"`.

**Checkpoint**: Uma pessoa autenticada pesquisa, entende os resultados e aciona o detalhe de uma fonte.

---

## Phase 3: User Story 2 - Refinar a busca com metadados (Priority: P2)

**Goal**: Aplicar e remover filtros sem perder a consulta.

**Independent Test**: Selecionar categoria, tag e projeto, verificar o request, remover cada chip e manter o texto de busca.

### Tests for User Story 2

- [ ] T011 [P] [US2] Estender `frontend/src/app/features/search/search-page.component.spec.ts` para validar payload com categoria/tag/projeto, limite e score mínimo, além da remoção individual de filtros.
- [ ] T012 [P] [US2] Criar `frontend/src/app/features/search/search-filters.component.spec.ts` para autocomplete com debounce, seleção pelo teclado e ausência de criação de tag.

### Implementation for User Story 2

- [x] T013 [US2] Implementar em `frontend/src/app/features/search/search-page.component.*` os seletores de categorias e projetos, reutilizando os tipos de domínio.
- [x] T014 [US2] Implementar autocomplete RxJS de tags com debounce, cancelamento da requisição anterior, limite 10 e seleção por botões operáveis pelo teclado.
- [x] T015 [US2] Implementar chips removíveis individualmente e propagar `category_ids`, `tag_ids`, `project_ids`, `limit` e `min_score` validados ao formulário da página de busca.
- [x] T016 [US2] Carregar metadados, preservar consulta/filtros após resposta ou erro e enviar somente campos válidos ao serviço.

**Checkpoint**: Todos os filtros opcionalmente refinam a mesma busca e podem ser removidos sem reiniciar o trabalho da pessoa.

---

## Phase 4: User Story 3 - Entender estados e diagnósticos da busca (Priority: P3)

**Goal**: Oferecer erros seguros e o diagnóstico opcional de motivos de correspondência.

**Independent Test**: Simular `422`, `404`, `502`, `503`, resposta vazia e resposta com motivos; confirmar mensagem e comportamento esperado.

### Tests for User Story 3

- [ ] T017 [P] [US3] Estender `frontend/src/app/features/search/search-page.component.spec.ts` com erros `422`, `404`, `502` e `503`, preservação do formulário e mensagens sem detalhe cru de API.
- [ ] T018 [P] [US3] Estender `frontend/src/app/features/search/search-result-list.component.spec.ts` para o toggle de motivos, resultado sem `matchReasons` e `score: null`.

### Implementation for User Story 3

- [x] T019 [US3] Implementar em `frontend/src/app/features/search/search-page.component.ts` o mapeamento seguro de falhas por status, recarregamento de metadados para `404` e nova tentativa para `502`/`503`.
- [x] T020 [US3] Adicionar à página o controle acessível de diagnóstico, enviando `include_match_reasons=true` somente quando ativado.
- [x] T021 [US3] Exibir em `frontend/src/app/features/search/search-page.component.*` os motivos `vector` e `text` quando presentes, mantendo a tela neutra quando não houver motivos.

**Checkpoint**: Estados críticos são compreensíveis, preservam o trabalho do usuário e não expõem dados sensíveis.

---

## Phase 5: Polish and Verification

**Purpose**: Validar integração, responsividade e qualidade da entrega.

- [ ] T022 [P] Revisar `frontend/src/app/features/search/*.html` e `*.css` para foco visível, contraste, navegação por teclado, ARIA e viewport mínimo de 320 px.
- [ ] T023 [P] Atualizar `specs/015-busca-inteligente-frontend/quickstart.md` caso nomes reais de rotas, comandos de testes ou componentes entregues pela Fase 01 divirjam do planejamento.
- [ ] T024 Executar a suíte frontend configurada, `npm run typecheck` e `npm run build` em `frontend/`; registrar falhas bloqueadoras antes de concluir a fase.
- [ ] T025 Executar o roteiro manual de `specs/015-busca-inteligente-frontend/quickstart.md` contra a API, incluindo busca, filtros, diagnóstico, erros, teclado e mobile.

## Dependencies and Execution Order

- T001 é bloqueadora. T002 e T004 podem ocorrer em paralelo, mas T003 depende dos tipos necessários.
- US1 começa após T003; T005 e T006 podem ser preparados em paralelo antes da implementação T007–T010.
- US2 depende de US1 porque compõe o formulário e a página já existentes.
- US3 depende de US1; pode ser realizada após T010 em paralelo com partes de US2 que não alterem os mesmos arquivos, mas a execução sequencial evita conflitos em `search-page.component.*`.
- T022 e T023 podem ocorrer após os componentes existirem; T024 e T025 fecham a entrega.

## Implementation Strategy

1. Concluir a fundação e os contratos compartilhados.
2. Entregar US1 e validar a busca simples como MVP.
3. Adicionar US2 para refinamento por metadados.
4. Adicionar US3 para resiliência e diagnóstico.
5. Executar gates automatizados e validação manual antes de abrir revisão.
