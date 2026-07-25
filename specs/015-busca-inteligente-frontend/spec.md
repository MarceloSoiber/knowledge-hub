# Feature Specification: Busca Inteligente no Frontend

**Feature Branch**: `feature/frontend-busca-inteligente`

**Created**: 2026-07-25

**Status**: Draft

**Input**: Planejamento `plan/frontend/02-busca.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Encontrar trechos relevantes (Priority: P1)

Uma pessoa autenticada informa uma consulta e recebe trechos relevantes, com dados suficientes para entender a origem e abrir a fonte correspondente.

**Why this priority**: É o fluxo central da entrega e produz valor mesmo sem filtros avançados.

**Independent Test**: Com ao menos uma fonte indexada, pesquisar um termo conhecido e confirmar que a tela mostra os resultados e que o link abre o detalhe da fonte.

**Acceptance Scenarios**:

1. **Given** uma pessoa autenticada e uma consulta não vazia, **When** ela executa a busca, **Then** a interface chama `POST /api/v1/knowledge/search` e apresenta cada resultado com título, trecho, score quando disponível, localização e metadados públicos.
2. **Given** uma lista de resultados, **When** a pessoa seleciona a fonte de um resultado por mouse ou teclado, **Then** a aplicação navega para o detalhe da fonte usando seu `source_id` público.
3. **Given** uma consulta vazia ou composta apenas de espaços, **When** a pessoa tenta pesquisar, **Then** a chamada não é enviada e a interface solicita uma consulta válida.

---

### User Story 2 - Refinar a busca com metadados (Priority: P2)

Uma pessoa restringe a consulta por categorias, tags, projetos, limite e score mínimo, podendo remover qualquer filtro sem apagar o texto consultado.

**Why this priority**: Filtros reduzem ruído em acervos maiores, mas a busca simples permanece útil como MVP.

**Independent Test**: Carregar metadados, aplicar ao menos um filtro de cada tipo, buscar e confirmar o corpo da requisição; remover cada chip e confirmar que o texto da consulta continua preservado.

**Acceptance Scenarios**:

1. **Given** os metadados disponíveis, **When** a pessoa seleciona categorias, tags ou projetos, **Then** os IDs selecionados são enviados respectivamente como `category_ids`, `tag_ids` e `project_ids`.
2. **Given** uma tag parcialmente digitada, **When** a pessoa aguarda a sugestão, **Then** a interface consulta o autocomplete de tags, permite selecioná-la por teclado e não cria tags novas.
3. **Given** filtros aplicados, **When** a pessoa remove um chip, **Then** somente aquele filtro é removido e a consulta permanece intacta.

---

### User Story 3 - Entender estados e diagnósticos da busca (Priority: P3)

Uma pessoa recebe feedback claro durante a busca, quando não há resultados ou ocorre uma falha, e pode revelar os motivos de correspondência quando a API os retornar.

**Why this priority**: Esses estados tornam a busca confiável e acionável sem bloquear o fluxo essencial de pesquisa.

**Independent Test**: Simular resposta vazia, erro de validação, indisponibilidade de embeddings e resposta com `match_reasons`, confirmando mensagens seguras e a alternância de diagnóstico.

**Acceptance Scenarios**:

1. **Given** uma busca em andamento, **When** a requisição ainda não terminou, **Then** os controles comunicam o carregamento e evitam submissões duplicadas.
2. **Given** uma resposta sem resultados, **When** a busca termina, **Then** a interface informa que nada foi encontrado e mantém consulta e filtros para refinamento.
3. **Given** erro `422`, `404`, `502` ou `503`, **When** a API responde, **Then** a interface mostra uma orientação adequada sem expor token, cabeçalhos, conteúdo sensível ou detalhes internos.
4. **Given** resultados com `match_reasons`, **When** a pessoa ativa a visualização de motivos, **Then** os motivos são exibidos como informação diagnóstica acessível; se não existirem, o controle não induz erro.

### Edge Cases

- Uma resposta de busca textual pode ter `score: null`; a interface mostra que não há score vetorial em vez de inventar `0`.
- IDs inválidos ou recursos removidos retornados pela API não descartam a consulta digitada nem os filtros ainda válidos.
- Projetos arquivados são apresentados conforme retornados pela API; esta fase não os altera nem deduz permissões.
- A tag digitada que não possui sugestão não vira filtro até que uma tag existente seja selecionada.
- Conteúdo do trecho e metadados são renderizados como texto, nunca como HTML confiável.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A área autenticada MUST disponibilizar uma rota de busca protegida pelo guard da fundação.
- **FR-002**: A tela MUST obter categorias, tags e projetos pelo cliente HTTP tipado centralizado, sem duplicar chamadas de API em componentes.
- **FR-003**: A busca MUST enviar `query`, `limit`, `category_ids`, `tag_ids`, `project_ids`, `min_score` e `include_match_reasons` apenas quando seus valores forem válidos e relevantes.
- **FR-004**: A tela MUST validar localmente consulta não vazia, limite entre 1 e 50 e score mínimo entre 0 e 1 antes da submissão.
- **FR-005**: Cada resultado MUST apresentar título da fonte, trecho, localização disponível, categorias, tags, projetos e score vetorial quando retornado.
- **FR-006**: Cada resultado MUST permitir navegação acessível ao detalhe em `/sources/:sourceId` ou na rota equivalente definida pela fundação, usando somente o UUID público `source_id`.
- **FR-007**: A seleção de tags MUST usar `GET /api/v1/knowledge/tags/autocomplete` com debounce e ser operável por teclado.
- **FR-008**: A interface MUST permitir remover individualmente filtros de categoria, tag e projeto, preservando consulta e demais filtros.
- **FR-009**: A interface MUST comunicar estados de validação, carregamento, vazio e erro com elementos semânticos, foco visível e anúncios ARIA apropriados.
- **FR-010**: Para falhas de embeddings/API, a interface MUST apresentar uma ação segura de recuperação (por exemplo, tentar novamente ou revisar a consulta) sem revelar token ou dados internos.
- **FR-011**: A alternância de motivos MUST pedir `include_match_reasons=true` em buscas futuras e somente exibir os motivos retornados pela API.
- **FR-012**: A implementação MUST cobrir o cliente, formulário e estados críticos com testes frontend e manter `npm run typecheck` e `npm run build` aprovados.

### Key Entities

- **SearchQuery**: Estado transitório da consulta, limite, score mínimo, filtros e preferência de diagnóstico.
- **MetadataFilter**: Categoria, tag ou projeto selecionado por ID e nome para compor a requisição e o chip visível.
- **KnowledgeSearchResult**: Chunk retornado pela API, com fonte pública, conteúdo, score opcional, localização, metadados e motivos opcionais.
- **SearchViewState**: Estado de validação, carregamento, sucesso vazio, sucesso com resultados ou erro recuperável da tela.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa autenticada consegue executar uma busca simples e abrir uma fonte retornada em até três interações após acessar a rota.
- **SC-002**: 100% dos campos do contrato de busca consumidos pelo frontend permanecem tipados e são validados por testes do cliente HTTP.
- **SC-003**: Em viewport de 320 px e com navegação exclusivamente por teclado, os controles de busca, filtros, chips, resultados e link de fonte continuam acessíveis.
- **SC-004**: Para respostas vazias e erros esperados (`422`, `404`, `502`, `503`), a interface mantém a consulta e oferece uma mensagem acionável sem dados sensíveis.

## Assumptions

- A Fase 01 será concluída antes desta entrega e fornecerá Router, guard, shell autenticado, `KnowledgeApiService`, tipos de domínio e componentes compartilhados.
- Os endpoints descritos em `doc/API.md` continuam disponíveis sob `/api/v1/knowledge` e não exigem alteração de backend.
- A rota de detalhe da fonte será entregue pela Fase 05; até então, o link pode apontar para a rota reservada pela fundação e a integração será validada quando o detalhe existir.
- O navegador mantém somente o estado da busca durante a navegação da tela; persistência em URL, histórico e favoritos estão fora do escopo.
- A primeira versão usa o limite padrão da API como valor inicial e não cria ou edita metadados.

## Out of Scope

- Alterar contratos REST, ranking, embeddings, filtros ou regras de negócio do backend.
- Criar, editar, excluir ou arquivar categorias, tags, projetos e fontes.
- Paginação, ordenação manual, destaque de termos, histórico de buscas ou salvamento de filtros.
- Exibir conteúdo de fonte completo na tela de busca.
