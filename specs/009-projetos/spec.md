# Feature Specification: Projetos

**Feature Branch**: `009-projetos`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Com base no plano `plan/08-projetos.md`, planejar a implementacao."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agrupar fontes por contexto de projeto (Priority: P1)

Um usuario cria projetos e associa fontes existentes ou novas a um ou mais projetos para reutilizar conhecimento compartilhado sem duplicar documentos.

**Why this priority**: Este e o objetivo principal: projeto representa contexto de trabalho, enquanto categorias e tags continuam representando assunto/classificacao.

**Independent Test**: Criar dois projetos, associar a mesma fonte aos dois, listar fontes de cada projeto e confirmar que a fonte aparece em ambos com o mesmo `source_id`.

**Acceptance Scenarios**:

1. **Given** uma fonte existente e dois projetos ativos, **When** a fonte e associada aos dois projetos, **Then** a fonte aparece nas listagens dos dois projetos sem duplicar chunks.
2. **Given** uma ingestao de texto com `project_ids`, **When** a fonte e persistida, **Then** ela retorna os projetos associados junto com categorias e tags.
3. **Given** uma fonte sem projeto, **When** a fonte e listada ou buscada sem filtro de projeto, **Then** ela continua disponivel como conhecimento geral.

---

### User Story 2 - Gerenciar ciclo de vida de projetos (Priority: P2)

Um usuario cria, lista, renomeia, descreve, arquiva e reativa projetos sem excluir o conhecimento associado.

**Why this priority**: Projetos precisam de governanca minima para serem confiaveis em workflows de agentes e consultas contextualizadas.

**Independent Test**: Criar projeto, atualizar nome/descricao/status, arquivar e confirmar que fontes/chunks associados permanecem intactos.

**Acceptance Scenarios**:

1. **Given** um projeto ativo com fontes associadas, **When** o projeto e arquivado, **Then** as fontes e chunks permanecem no banco.
2. **Given** um projeto arquivado, **When** a listagem padrao de projetos e chamada, **Then** o contrato define claramente se ele aparece ou se precisa de filtro por status.
3. **Given** tentativa de criar projeto com nome duplicado, **When** o nome normalizado ja existe, **Then** a API retorna `409 Conflict`.

---

### User Story 3 - Restringir busca e IA ao projeto atual (Priority: P3)

Um usuario ou agente consulta conhecimento com `project_ids` para limitar resultados ao contexto de trabalho atual, combinando projeto com categoria e tag quando necessario.

**Why this priority**: Este e o criterio de aceite principal para IA: a consulta deve poder ficar restrita ao projeto em foco.

**Independent Test**: Ingerir fontes em projetos diferentes, executar busca e answer com `project_ids`, e confirmar que apenas chunks dos projetos informados participam do resultado/contexto.

**Acceptance Scenarios**:

1. **Given** duas fontes parecidas em projetos diferentes, **When** a busca usa `project_ids=[A]`, **Then** somente chunks associados ao projeto A aparecem.
2. **Given** filtros por projeto e categoria, **When** ambos sao enviados, **Then** a fonte deve satisfazer as duas dimensoes para aparecer.
3. **Given** projeto inexistente no filtro, **When** search, answer, ingestao ou patch e chamado, **Then** a operacao falha sem gravacao parcial.

### Edge Cases

- Projeto e opcional; fontes sem projeto continuam validas e buscaveis quando nao ha filtro `project_ids`.
- A mesma fonte pode pertencer a varios projetos sem duplicar `document_sources` ou `knowledge_chunks`.
- `project_ids=[]` deve ser invalido em filtros; ausencia do campo significa "todos os projetos e conhecimento geral".
- Em patch de fonte, lista vazia de `project_ids` deve limpar associacoes de projeto se a feature escolher permitir isso.
- Arquivar projeto nao deve excluir fontes, chunks, categorias, tags ou associacoes historicas.
- Projetos arquivados devem ter semantica definida para filtros: permitir filtro explicito por id, mas evitar retorno em autocomplete/listagem padrao se o contrato escolher isso.
- Nome duplicado ignorando caixa/espacos deve retornar `409`.
- Projeto inexistente em qualquer associacao ou filtro deve retornar `404` antes de embedding/LLM ou escrita parcial.
- Busca combinada por projetos, categorias e tags nao deve duplicar chunks quando uma fonte satisfaz varias associacoes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add a Project entity with `id`, `name`, `description`, `status`, `created_at` and `updated_at`.
- **FR-002**: System MUST maintain a many-to-many relationship between document sources and projects.
- **FR-003**: System MUST keep project association optional for sources.
- **FR-004**: System MUST allow a source to be associated with multiple projects without duplicating source content or chunks.
- **FR-005**: System MUST provide project create, read/list, update, archive/reactivate and delete-or-safe-remove behavior according to the chosen lifecycle contract.
- **FR-006**: System MUST define project statuses at least for `active` and `archived`.
- **FR-007**: System MUST allow ingestion and source patch flows to set project associations by `project_ids`.
- **FR-008**: System MUST expose projects on source and chunk read models.
- **FR-009**: System MUST provide an endpoint to list sources for a project.
- **FR-010**: System MUST allow search and answer filters by `project_ids`.
- **FR-011**: System MUST combine project, category and tag filters as separate AND dimensions.
- **FR-012**: System MUST use ANY semantics within the `project_ids` list for MVP.
- **FR-013**: System MUST reject missing project ids before writing data or calling embedding/LLM providers.
- **FR-014**: System MUST keep archived projects from deleting knowledge or associations.
- **FR-015**: System MUST update MCP tools/models so agents can list projects, ingest into projects and search within projects.
- **FR-016**: System MUST update `doc/API.md` when API behavior changes.

### Key Entities *(include if feature involves data)*

- **Project**: Context of work with normalized unique name, optional description and lifecycle status.
- **DocumentSource**: Existing source that can belong to zero or more projects.
- **DocumentSourceProject**: Association between a source and a project.
- **ProjectFilter**: Request-level filter over project ids, initially with ANY semantics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: One source can be associated with two projects and keeps one `source_id` and one set of chunks.
- **SC-002**: Search/answer with `project_ids` returns only chunks whose source is associated with at least one requested project.
- **SC-003**: Search/answer combining `project_ids`, `category_ids` and `tag_ids` returns no duplicate chunk ids.
- **SC-004**: Archiving a project leaves associated sources and chunks queryable without project filter.
- **SC-005**: API and MCP clients can discover projects and pass project filters using stable ids.
- **SC-006**: Automated tests cover missing project rejection without partial writes.

## Assumptions

- Project names are normalized with trim and lowercase, matching category simplicity unless research chooses accent-insensitive keys.
- Project deletion is out of MVP; archive/reactivate is the lifecycle operation to avoid accidental knowledge loss.
- `project_ids` is ID-based in API and MCP, mirroring categories and tags.
- Source patch with `project_ids: []` clears project associations because projects are optional.
- Frontend changes are optional unless the existing UI already exposes source editing or advanced search controls.
