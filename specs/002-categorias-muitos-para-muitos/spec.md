# Feature Specification: Categorias Muitos-Para-Muitos

**Feature Branch**: `002-categorias-muitos-para-muitos`

**Created**: 2026-07-14

**Status**: Draft

**Input**: User description: "Permitir que documentos tenham varias categorias, gerir categorias e substituir category_id singular por category_ids."

## User Scenarios & Testing

### User Story 1 - Ingerir Documento Com Varias Categorias (Priority: P1)

Um usuario cadastra arquivo ou texto atribuindo uma ou mais categorias ao documento para que o conteudo possa ser encontrado por qualquer uma delas.

**Why this priority**: E o comportamento principal da melhoria e desbloqueia classificacao mais flexivel.

**Independent Test**: Cadastrar um texto com duas categorias e confirmar que a fonte retorna ambas.

**Acceptance Scenarios**:

1. **Given** duas categorias existentes, **When** um texto e cadastrado com `category_ids` contendo as duas, **Then** a fonte e persistida com as duas associacoes.
2. **Given** uma fonte ja cadastrada, **When** ela e recadastrada com outra lista de categorias, **Then** os chunks sao substituidos e as associacoes refletem a nova lista.

---

### User Story 2 - Gerir Categorias (Priority: P2)

Um usuario cria, renomeia, lista e exclui categorias para manter a taxonomia do hub.

**Why this priority**: A ingestao multi-categoria depende de categorias confiaveis e gerenciaveis.

**Independent Test**: Criar categoria, renomear, listar e tentar excluir uma categoria em uso.

**Acceptance Scenarios**:

1. **Given** um nome novo com espacos e maiusculas, **When** a categoria e criada, **Then** o nome e salvo normalizado.
2. **Given** uma categoria associada a documento, **When** exclusao e solicitada, **Then** a API retorna `409 Conflict`.

---

### User Story 3 - Buscar Por Multiplas Categorias (Priority: P3)

Um usuario filtra busca e resposta por uma ou mais categorias, aceitando resultados que pertencam a qualquer uma delas.

**Why this priority**: Mantem a experiencia de recuperacao compativel com a nova classificacao.

**Independent Test**: Buscar com duas categorias e confirmar que chunks de uma fonte associada as duas aparecem uma unica vez.

**Acceptance Scenarios**:

1. **Given** uma fonte em duas categorias, **When** a busca filtra pelas duas, **Then** os chunks dessa fonte nao sao duplicados.
2. **Given** nenhuma categoria no filtro, **When** a busca roda, **Then** todas as fontes elegiveis continuam participando.

### Edge Cases

- Lista de categorias vazia em cadastro deve falhar.
- IDs repetidos em cadastro, busca ou answer devem falhar.
- Categoria inexistente em cadastro deve retornar `404`.
- Categoria inexistente em filtro de busca/answer deve retornar `404`.
- Nome de categoria duplicado ignorando maiusculas/minusculas deve retornar `409`.

## Requirements

### Functional Requirements

- **FR-001**: System MUST replace singular document category assignment with many-to-many document-category associations.
- **FR-002**: System MUST require at least one category when ingesting upload or text content.
- **FR-003**: System MUST accept `category_ids` lists for text ingestion, search and answer payloads.
- **FR-004**: System MUST accept repeated multipart `category_ids` fields for upload ingestion.
- **FR-005**: System MUST return source categories as `categories` objects with `id` and `name`.
- **FR-006**: System MUST provide category create, update and delete endpoints while preserving the existing list endpoint.
- **FR-007**: System MUST reject category deletion when the category is associated with any source.
- **FR-008**: System MUST filter search and answer by ANY category semantics without duplicate chunks.
- **FR-009**: System MUST stop exposing `category_id` in API, MCP and documentation contracts.

### Key Entities

- **Category**: A normalized classification label with unique name.
- **DocumentSource**: A file or text source with chunks and one or more categories.
- **DocumentSourceCategory**: Association between a source and a category.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Existing documents keep their category after migration.
- **SC-002**: Multi-category ingestion, search filtering and source listing pass automated tests.
- **SC-003**: API docs and MCP docs contain no singular `category_id` contract.
- **SC-004**: Running the database initialization more than once does not fail or duplicate associations.

## Assumptions

- No backward compatibility for singular `category_id` is required.
- Category names are normalized with trim and lowercase.
- The current lightweight database initialization remains the migration mechanism.
- The frontend is informational and does not require behavior changes for this feature.
