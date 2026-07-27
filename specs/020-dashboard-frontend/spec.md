# Feature Specification: Dashboard inicial do acervo

**Feature Branch**: `020-dashboard-frontend`  
**Created**: 2026-07-27  
**Status**: Draft  
**Input**: Plano `plan/frontend/07-dashboard.md`

## User Scenarios & Testing

### User Story 1 - Entender o acervo ao entrar (Priority: P1)

Uma pessoa autenticada abre o início e vê contagens confiáveis de fontes, categorias, tags e projetos ativos e arquivados, além das fontes mais recentes.

**Why this priority**: A visão inicial orienta rapidamente o uso do produto e torna visível se já há material disponível para buscar ou consultar.

**Independent Test**: Com coleções retornadas pelos quatro endpoints, abrir `/inicio` e conferir que cada cartão corresponde aos seus dados e que as fontes recentes estão em ordem decrescente de data no cliente.

**Acceptance Scenarios**:

1. **Given** um acervo com fontes e metadados, **When** a pessoa abre o Dashboard, **Then** vê cartões com as contagens de fontes, categorias, tags, projetos ativos e projetos arquivados.
2. **Given** fontes com datas distintas, **When** a lista de recentes é exibida, **Then** ela é ordenada localmente da mais recente para a mais antiga e cada item permite abrir seu detalhe.
3. **Given** uma das coleções secundárias falha ou ainda está carregando, **When** a pessoa navega pelo Dashboard, **Then** os dados já disponíveis e a navegação continuam utilizáveis, com estado recuperável apenas na área afetada.

---

### User Story 2 - Começar uma ação de valor (Priority: P1)

Uma pessoa usa atalhos claros para buscar no acervo, perguntar à base ou iniciar uma ingestão.

**Why this priority**: O Dashboard deve reduzir a distância entre o estado do acervo e os fluxos mais valiosos já entregues.

**Independent Test**: Abrir o início e ativar cada atalho por mouse e teclado, confirmando as rotas privadas corretas.

**Acceptance Scenarios**:

1. **Given** o Dashboard carregado, **When** a pessoa escolhe Busca, Pergunte à base ou Ingestão, **Then** navega para `/busca`, `/perguntar` ou `/ingestao`, respectivamente.
2. **Given** qualquer estado de carregamento ou erro parcial, **When** a pessoa usa um atalho, **Then** a navegação não é bloqueada.

---

### User Story 3 - Ser orientado em uma base vazia (Priority: P2)

Uma pessoa que ainda não ingeriu fontes recebe uma mensagem explícita e um caminho direto para a primeira ingestão, sem cartões incompletos ou números incorretos.

**Why this priority**: Uma base vazia é o primeiro estado provável e precisa orientar a ação seguinte, não parecer erro.

**Independent Test**: Retornar listas vazias dos endpoints e confirmar zero nos cartões, estado vazio acessível e link funcional para Ingestão.

**Acceptance Scenarios**:

1. **Given** `GET /sources` retorna lista vazia, **When** a pessoa abre o Dashboard, **Then** vê uma chamada para a primeira ingestão e não vê uma lista recente vazia sem explicação.
2. **Given** metadados também estão vazios, **When** os cartões terminam de carregar, **Then** cada contagem é exibida como zero, sem placeholder quebrado.

### Edge Cases

- Datas ausentes ou inválidas não podem tornar a ordenação instável; tais fontes ficam após as fontes com data válida, com desempate determinístico por título e `source_id`.
- Uma falha em fontes não deve fabricar a contagem zero nem ocultar os cartões de metadados que carregaram corretamente; cada área oferece retry próprio.
- Respostas vazias são sucesso, não erro; fontes recentes só aparecem quando há fontes.
- Títulos e URIs retornados pela API são renderizados como texto, nunca como HTML.

## Requirements

### Functional Requirements

- **FR-001**: O sistema DEVE substituir a página inicial provisória por um Dashboard privado em `/inicio`.
- **FR-002**: O Dashboard DEVE carregar `GET /knowledge/sources`, `GET /knowledge/categories`, `GET /knowledge/tags` e `GET /knowledge/projects` usando os contratos existentes no cliente.
- **FR-003**: O Dashboard DEVE mostrar contagens que correspondam exatamente às coleções carregadas: fontes, categorias, tags, projetos com `status=active` e projetos com `status=archived`.
- **FR-004**: O Dashboard DEVE derivar no cliente uma lista de fontes recentes a partir de `created_at`, com fallback definido para datas ausentes/inválidas e sem exigir nova ordenação da API.
- **FR-005**: O Dashboard DEVE oferecer atalhos semanticamente rotulados para Busca, Pergunte à base e Ingestão, sem depender da conclusão das requisições.
- **FR-006**: Se não houver fontes, o Dashboard DEVE apresentar estado vazio com chamada para `/ingestao`; contagens de coleções vazias devem mostrar `0`.
- **FR-007**: O Dashboard DEVE isolar carregamento, erro e retry por grupo de dados para que uma falha secundária não bloqueie a página nem descarte dados válidos já mostrados.
- **FR-008**: A interface DEVE ser responsiva a partir de 320 px, navegável por teclado, usar HTML semântico, links reais e anúncios acessíveis para carregamento/erro sem expor detalhes remotos.
- **FR-009**: A implementação NÃO DEVE alterar FastAPI, banco, MCP, autenticação, contratos HTTP publicados ou `doc/API.md`.

### Key Entities

- **Resumo do Dashboard**: estado cliente derivado das listas canônicas de fontes e metadados, sem persistência própria.
- **Cartão de métrica**: apresentação de uma contagem e seu estado individual de carregamento/erro.
- **Fonte recente**: `KnowledgeSource` existente, ordenada localmente para destaque no Dashboard.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Testes demonstram que os cinco cartões refletem corretamente coleções vazias, preenchidas e projetos de ambos os estados.
- **SC-002**: Testes demonstram ordenação determinística de fontes recentes, incluindo datas nulas/inválidas.
- **SC-003**: Testes demonstram que erro e retry de uma coleção não impedem os atalhos nem a renderização dos demais dados.
- **SC-004**: Testes demonstram que uma base vazia orienta à Ingestão e não contém cartões quebrados.

## Assumptions

- As respostas existentes de fontes e metadados são pequenas o bastante para o carregamento inicial atual; paginação e agregados server-side estão fora do escopo.
- “Recente” significa maior `created_at`; `updated_at` é usado somente como fallback de ordenação quando `created_at` estiver ausente ou inválido.
- A lista inicial exibirá no máximo cinco fontes recentes para manter o Dashboard resumido, com acesso à Biblioteca para o acervo completo.

## Out of Scope

- Novos endpoints agregados, paginação, filtros no Dashboard, gráficos, métricas históricas, persistência de preferências e atualização em tempo real.
- Alterar fluxos de Busca, Pergunte à base, Ingestão, Biblioteca ou Organização além de seus links já existentes.
