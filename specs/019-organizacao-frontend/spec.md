# Feature Specification: Organização do acervo no frontend

**Feature Branch**: `019-organizacao-frontend`  
**Created**: 2026-07-27  
**Status**: Draft  
**Input**: Plano `plan/frontend/06-organizacao.md`

## User Scenarios & Testing

### User Story 1 - Manter categorias e tags (Priority: P1)

Uma pessoa autenticada administra categorias e tags, e as tags podem ser encontradas por autocomplete nos formulários que as usam.

**Why this priority**: Categorias e tags classificam o acervo e são pré-requisito para ingestão, busca e biblioteca.

**Independent Test**: Criar, renomear e excluir uma categoria ou tag sem uso; tentar excluir uma em uso e verificar que ela continua disponível com explicação acionável.

**Acceptance Scenarios**:

1. **Given** a tela Organização, **When** a pessoa cria ou edita categoria/tag válida, **Then** a lista e os seletores de metadados abertos refletem o item normalizado sem recarregar a aplicação.
2. **Given** uma categoria/tag usada por fonte, **When** a pessoa confirma sua exclusão, **Then** a interface explica o conflito e preserva o item.
3. **Given** um formulário que seleciona tags, **When** a pessoa digita uma consulta, **Then** recebe sugestões normalizadas do autocomplete e pode selecionar múltiplas tags sem duplicação.

---

### User Story 2 - Gerir ciclo de vida de projetos (Priority: P1)

Uma pessoa cria e edita projetos, alterna a listagem entre ativos e arquivados e arquiva ou reativa cada projeto de modo explícito.

**Why this priority**: Projetos agrupam fontes e o status evita que agrupamentos encerrados apareçam como opções ativas.

**Independent Test**: Criar um projeto, editá-lo, arquivá-lo, confirmar que sai da visão de ativos e reativá-lo na visão de arquivados.

**Acceptance Scenarios**:

1. **Given** a visão de projetos ativos, **When** a pessoa arquiva um projeto, **Then** ele deixa essa lista e fica disponível no filtro de arquivados.
2. **Given** a visão de arquivados, **When** a pessoa reativa um projeto, **Then** ele volta a ativo e os seletores de projeto se atualizam.
3. **Given** nome duplicado ou dados inválidos, **When** a criação/edição termina com erro, **Then** o rascunho permanece e a pessoa recebe instrução segura.

---

### User Story 3 - Consultar fontes de um projeto (Priority: P2)

Uma pessoa abre um projeto e acessa as fontes vinculadas a ele, podendo navegar ao detalhe canônico de cada fonte.

**Why this priority**: O agrupamento só é útil se permitir verificar seu conteúdo sem perder o contexto.

**Independent Test**: Abrir um projeto com fontes associadas e navegar de um item para `/sources/:sourceId`; um projeto sem fontes mostra estado vazio.

**Acceptance Scenarios**:

1. **Given** um projeto listado, **When** a pessoa abre suas fontes, **Then** vê título, tipo e metadados de cada fonte retornada pela API.
2. **Given** nenhuma fonte vinculada, **When** a pessoa abre o projeto, **Then** vê um estado vazio distinto de erro.

### Edge Cases

- Listas vazias, falha de carregamento, item removido em outra sessão e falhas 404/409/422 têm estados recuperáveis, sem sucesso enganoso.
- A exclusão de categoria/tag só é enviada após diálogo de confirmação; `409` nunca remove o item localmente.
- Consultas de autocomplete vazias não chamam a API; respostas antigas não podem substituir sugestões de uma consulta mais recente.
- Um projeto arquivado não é opção de associação ativa, mas continua visível na gestão, no filtro explícito de arquivados e nos metadados de fontes históricas.

## Requirements

### Functional Requirements

- **FR-001**: O sistema DEVE disponibilizar uma rota privada de Organização com áreas navegáveis para categorias, tags e projetos.
- **FR-002**: A interface DEVE listar, criar, editar e excluir categorias e tags pelos endpoints publicados, com confirmação antes de exclusão.
- **FR-003**: A interface DEVE tratar `409` de exclusão de categoria/tag como conflito de item em uso, mantendo-o na lista e explicando que suas fontes precisam ser reclassificadas antes.
- **FR-004**: Os formulários que consomem tags DEVEM oferecer autocomplete por `GET /tags/autocomplete`, seleção múltipla e IDs únicos; a gestão de tags continua acessível sem depender de uma busca.
- **FR-005**: A interface DEVE listar projetos por status, criar e editar seus campos publicados, arquivar ativos e reativar arquivados.
- **FR-006**: Projeto arquivado NÃO DEVE aparecer como opção ativa de associação; a UI DEVE preservar sua identificação em fontes que já o referenciam.
- **FR-007**: A interface DEVE carregar e apresentar as fontes de um projeto pelo endpoint publicado e navegar ao detalhe existente por UUID público.
- **FR-008**: Mudanças bem-sucedidas em categorias, tags e projetos DEVEM atualizar o catálogo compartilhado e seletores/filtros já montados, sem recarga completa da aplicação.
- **FR-009**: A interface DEVE bloquear reenvio durante mutações, preservar rascunhos em falhas e apresentar mensagens locais seguras para `400/404/409/422/502/503`; não pode renderizar detalhes remotos como HTML.
- **FR-010**: Listas, formulários, autocomplete e diálogos DEVEM ser operáveis por teclado, anunciados apropriadamente e responsivos a partir de 320 px.

### Key Entities

- **Catálogo de metadados**: estado cliente compartilhado de categorias, tags e projetos, atualizado por respostas canônicas da API.
- **Rascunho de classificação**: nome de categoria/tag em criação ou edição, sem persistência até o envio válido.
- **Rascunho de projeto**: nome e descrição editáveis, com status retornado apenas pelo servidor.
- **Sugestão de tag**: tag retornada para uma consulta normalizada, descartável e distinta do catálogo completo.
- **Fonte de projeto**: `KnowledgeSource` associado ao projeto e linkado por `source_id` público.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Testes demonstram que CRUD bem-sucedido atualiza a lista e o catálogo compartilhado sem navegação ou reload completo.
- **SC-002**: Testes demonstram que exclusões canceladas não enviam DELETE e que respostas `409` preservam item e associação visível.
- **SC-003**: Testes demonstram que arquivar remove o projeto do catálogo ativo e reativar o devolve, sem perder fontes vinculadas.
- **SC-004**: Testes demonstram autocomplete com consulta, seleção sem duplicatas e descarte de resposta obsoleta.

## Assumptions

- Os endpoints existentes são a fonte de verdade; não haverá mudança em FastAPI, banco, MCP, autenticação nem `doc/API.md`.
- A descrição de projeto é opcional, e apenas nome/descrição são editáveis; status muda exclusivamente pelas ações de arquivo/reativação.
- A quantidade de classificações é apropriada para catálogo em memória; autocomplete complementa a seleção de tags e não introduz paginação.

## Out of Scope

- Exclusão de projetos, fusão de classificações, edição em lote de fontes, histórico/auditoria, permissões por projeto e importação/exportação.
- Alteração de classificações dentro desta tela de fontes; essa manutenção pertence ao detalhe/ingestão existentes.
- Mudança de semântica de filtros do backend ou de contratos REST.
