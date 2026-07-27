# Feature Specification: Pergunte à Base no Frontend

**Feature Branch**: `feature/frontend-pergunte-a-base`  
**Created**: 2026-07-27  
**Status**: Draft  
**Input**: Planejamento `plan/frontend/03-pergunte-a-base.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fazer uma pergunta fundamentada (Priority: P1)

Uma pessoa autenticada escreve uma pergunta em linguagem natural e recebe a resposta produzida a partir da base de conhecimento, acompanhada das fontes usadas.

**Why this priority**: É o fluxo central da fase: obter uma resposta e avaliar em que documentos ela se apoia.

**Independent Test**: Com uma fonte indexada e o endpoint disponível, enviar uma pergunta conhecida e confirmar resposta textual e fontes devolvidas.

**Acceptance Scenarios**:

1. **Given** uma pergunta válida, **When** a pessoa a envia, **Then** a interface chama `POST /api/v1/knowledge/answer` e mostra a resposta recebida como texto.
2. **Given** uma resposta com fontes, **When** a requisição termina, **Then** cada fonte é mostrada como cartão com título, trecho, localização e metadados disponíveis.
3. **Given** fontes retornadas, **When** a pessoa seleciona um cartão por mouse ou teclado, **Then** a aplicação navega ao detalhe usando somente o UUID público `source_id`.

---

### User Story 2 - Restringir o contexto da resposta (Priority: P2)

Uma pessoa aplica filtros por categoria, tag, projeto, limite e score mínimo antes de perguntar, sem que a tela crie ou altere metadados.

**Why this priority**: Em uma base ampla, delimitar o contexto torna a resposta mais relevante e auditável.

**Independent Test**: Selecionar filtros, enviar uma pergunta e verificar que o corpo usa os campos e IDs corretos; remover um filtro e confirmar que a pergunta continua preservada.

**Acceptance Scenarios**:

1. **Given** metadados carregados, **When** a pessoa seleciona categorias, tags e projetos existentes, **Then** seus IDs são enviados como `category_ids`, `tag_ids` e `project_ids`.
2. **Given** uma tag parcialmente digitada, **When** sugestões forem retornadas, **Then** apenas uma tag existente pode ser adicionada ao filtro e o controle é operável por teclado.
3. **Given** filtros aplicados, **When** a pessoa remove um chip, **Then** apenas aquele filtro é removido, preservando a pergunta e os demais valores.

---

### User Story 3 - Recuperar-se de falhas e reutilizar a resposta (Priority: P3)

Uma pessoa entende o carregamento e os erros, pode tentar novamente sem perder a pergunta e copiar a resposta ou as referências exibidas.

**Why this priority**: Respostas RAG dependem de embeddings e LLM; falhas e a necessidade de compartilhar o resultado são parte do uso normal.

**Independent Test**: Simular ausência de fontes, `403`, `422`, `502` e `503`; confirmar mensagem segura, formulário preservado e cópia da resposta/referências em resposta bem-sucedida.

**Acceptance Scenarios**:

1. **Given** uma requisição em andamento, **When** ela ainda não terminou, **Then** a interface indica carregamento e impede novo envio duplicado.
2. **Given** a resposta retornada sem fontes, **When** ela é exibida, **Then** a interface informa claramente que não há fontes para auditar, sem tratar isso como falha da requisição.
3. **Given** uma falha de validação, indisponibilidade ou bloqueio sensível, **When** a API responde, **Then** a interface mostra orientação segura, não exibe detalhes internos e mantém pergunta e filtros para nova tentativa.
4. **Given** uma resposta concluída, **When** a pessoa usa copiar resposta ou copiar referências, **Then** recebe confirmação de sucesso ou falha de cópia sem alterar a resposta exibida.

### Edge Cases

- Pergunta vazia ou composta somente por espaços não dispara chamada HTTP.
- O limite é inteiro de 1 a 20 e `min_score`, quando informado, fica entre 0 e 1; valores inválidos recebem validação local.
- O endpoint pode devolver uma resposta textual com `sources: []`; a resposta continua exibível, mas as referências não podem ser copiadas como se existissem.
- `score` pode ser nulo e `match_reasons` pode não estar presente; a UI não inventa valores.
- Resposta, títulos, trechos, localização e metadados são sempre renderizados como texto, nunca como HTML confiável.
- O histórico existe somente enquanto a aplicação Angular permanece aberta; recarregar a página ou encerrar a sessão o descarta.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A área autenticada MUST disponibilizar uma rota protegida para perguntas à base.
- **FR-002**: A feature MUST usar exclusivamente o `KnowledgeApiService` tipado para listar filtros, autocomplete de tags e chamar `POST /answer`.
- **FR-003**: A feature MUST enviar `query`, `limit`, `category_ids`, `tag_ids`, `project_ids`, `min_score` e `include_match_reasons` somente quando válidos e relevantes ao contrato.
- **FR-004**: A feature MUST validar pergunta não vazia, limite inteiro entre 1 e 20 e score mínimo entre 0 e 1 antes da submissão.
- **FR-005**: A resposta MUST exibir o texto devolvido pela API e as fontes usadas, quando existirem, como cartões acessíveis e clicáveis.
- **FR-006**: Cada fonte MUST navegar ao detalhe em `/sources/:sourceId` (ou rota equivalente da fundação) usando exclusivamente `source_id` público.
- **FR-007**: A seleção de tags MUST usar autocomplete com debounce, cancelamento de resultado obsoleto e operação por teclado; a feature não cria tags.
- **FR-008**: A interface MUST permitir remover individualmente filtros de categoria, tag e projeto, preservando pergunta e demais filtros.
- **FR-009**: A interface MUST distinguir validação local, carregamento, resposta sem fontes, API indisponível/embedding ou LLM indisponível e bloqueio de conteúdo sensível, com feedback semântico e acessível.
- **FR-010**: Em erros `403`, `422`, `502` e `503`, a interface MUST manter os controles preenchidos e não revelar token, cabeçalhos, corpo bruto ou detalhes internos.
- **FR-011**: A feature MUST oferecer cópia independente da resposta e das referências atualmente apresentadas, com confirmação acessível; referências inexistentes não devem ser copiadas como conteúdo válido.
- **FR-012**: O histórico de perguntas e respostas MUST residir somente em memória do componente/sessão e MUST ser descartado ao recarregar ou encerrar a sessão.
- **FR-013**: A implementação MUST cobrir cliente, serialização de requisição, estados de erro/cópia e fluxo principal com testes frontend, mantendo `npm run typecheck` e `npm run build` aprovados.

### Key Entities

- **AnswerQuery**: Estado transitório da pergunta, filtros, limite, score mínimo e preferência de diagnóstico.
- **AnswerResult**: Resposta textual e lista de `KnowledgeChunk` retornadas pelo endpoint, com data de criação somente em memória.
- **AnswerHistoryEntry**: Pergunta enviada e resultado bem-sucedido guardados apenas durante a sessão atual da página.
- **MetadataFilter**: Categoria, tag ou projeto selecionado por ID e nome para compor requisição e chip visível.
- **AnswerViewState**: Estado `idle`, `loading`, sucesso, sucesso sem fontes, erro de validação ou erro de requisição recuperável.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa autenticada consegue enviar uma pergunta, ler a resposta e abrir uma fonte retornada em até quatro interações após acessar a rota.
- **SC-002**: 100% dos campos consumidos de `/answer` permanecem tipados e possuem teste de serialização ou consumo no cliente HTTP.
- **SC-003**: Em viewport de 320 px e usando somente teclado, os controles de pergunta, filtros, chips, cópia e cartões de fonte são utilizáveis.
- **SC-004**: Para `403`, `422`, `502` e `503`, a tela preserva a pergunta e filtros e apresenta uma orientação acionável sem dados sensíveis.
- **SC-005**: Recarregar a página após uma ou mais perguntas não restaura nenhuma entrada do histórico.

## Assumptions

- A fundação do frontend, o guard, o shell autenticado, `KnowledgeApiService`, tipos e componentes compartilhados já estão disponíveis.
- O endpoint existente é `POST /api/v1/knowledge/answer`; não haverá alteração de backend, banco, MCP ou contrato REST nesta fase.
- A rota de detalhe de fonte `/sources/:sourceId` é mantida pela Fase 05 ou pela implementação existente.
- A cópia usa a Clipboard API quando disponível, com alternativa de cópia compatível definida na implementação para contextos sem permissão.
- O histórico mostrado é limitado à vida útil da página/sessão e não é sincronizado entre abas.

## Out of Scope

- Persistência de conversa, histórico em banco/localStorage, favoritos, compartilhamento ou telemetria.
- Streaming de tokens, cancelamento de geração, edição/regeneração da resposta ou conversas multi-turno.
- Alterar prompt, embeddings, ranking, políticas de conteúdo, LLM, contratos REST ou dados do backend.
- Criar, editar, excluir ou arquivar categorias, tags, projetos ou fontes.
- Renderizar Markdown/HTML rico vindo da resposta ou dos documentos.
