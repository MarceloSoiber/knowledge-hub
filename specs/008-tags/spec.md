# Feature Specification: Tags

**Feature Branch**: `008-tags`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Com base no `plan/07-tags.md`, montar o planejamento para implementacao."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Classificar documentos com tags livres (Priority: P1)

Um usuario associa uma ou mais tags especificas a uma fonte de conhecimento para complementar as categorias amplas sem multiplicar a taxonomia controlada.

**Why this priority**: E o valor central da feature: permitir classificacao granular e reutilizavel sem transformar categorias em uma lista dificil de administrar.

**Independent Test**: Criar ou ingerir uma fonte com tags como `python` e `postgres`, listar a fonte e confirmar que as tags aparecem sem duplicidade.

**Acceptance Scenarios**:

1. **Given** uma ingestao de texto com tags `Python` e ` postgres `, **When** a fonte e persistida, **Then** ela retorna tags normalizadas e associadas ao documento.
2. **Given** duas fontes usando a tag `rag`, **When** a segunda fonte e criada, **Then** o sistema reutiliza a tag existente em vez de criar duplicata.
3. **Given** uma fonte existente com embeddings gerados, **When** apenas suas tags sao alteradas, **Then** a alteracao nao reprocessa chunks nem embeddings.

---

### User Story 2 - Encontrar e gerenciar tags existentes (Priority: P2)

Um usuario lista, cria, renomeia, exclui e usa autocomplete de tags para manter marcadores consistentes durante ingestao e organizacao.

**Why this priority**: Tags livres ficam ruidosas sem descoberta e regras de normalizacao claras.

**Independent Test**: Criar tags com variacoes de caixa, espacos e acentos; buscar por prefixo; renomear; tentar excluir tag em uso.

**Acceptance Scenarios**:

1. **Given** tags `postgres`, `python` e `rag`, **When** autocomplete recebe prefixo `po`, **Then** retorna `postgres` ordenada por nome ou relevancia definida.
2. **Given** uma tag associada a uma fonte, **When** exclusao e solicitada, **Then** a API retorna `409 Conflict`.
3. **Given** uma tentativa de renomear `imposto` para `Imposto`, **When** a tag equivalente ja existe, **Then** o sistema evita duplicidade pela chave normalizada.

---

### User Story 3 - Filtrar busca por tags combinadas com categorias (Priority: P3)

Um usuario filtra busca, resposta e listagem por tags, combinando marcadores especificos com categorias amplas sem duplicar chunks.

**Why this priority**: Tags so entregam recuperacao pratica quando participam dos mesmos fluxos de busca e RAG que categorias.

**Independent Test**: Ingerir fontes com tags e categorias sobrepostas, buscar com filtros de categoria e tag, e confirmar que cada chunk aparece uma vez.

**Acceptance Scenarios**:

1. **Given** uma fonte na categoria `software` com tags `python` e `postgres`, **When** a busca filtra por `tag_ids=[python, postgres]`, **Then** os chunks da fonte aparecem uma unica vez com semantica ANY.
2. **Given** filtro por categoria `software` e tag `imposto`, **When** nenhuma fonte atende as duas dimensoes, **Then** a busca retorna lista vazia sem erro.
3. **Given** necessidade real de intersecao de tags, **When** o cliente envia modo ALL, **Then** somente fontes associadas a todas as tags solicitadas participam da busca.

### Edge Cases

- Tags repetidas na mesma requisicao nao devem criar associacoes duplicadas.
- Tags equivalentes ignorando acentos, caixa e espacos devem colidir pela mesma chave normalizada.
- Tag vazia, apenas espacos ou acima do limite aceito deve falhar em validacao.
- Tag inexistente em filtros por id deve retornar `404`.
- Filtro `tag_ids=[]` deve falhar; ausencia de filtro continua significando "todas as tags".
- Alterar apenas tags de uma fonte nao deve alterar `content_hash`, chunks ou embeddings.
- Busca com categorias e tags deve aplicar ambas as dimensoes sem duplicar chunks.
- Exclusao de tag em uso deve retornar `409`; exclusao de tag sem uso deve ser idempotente apenas se o contrato definir isso explicitamente.
- O modo ALL so deve ser implementado se houver caso real confirmado; caso contrario, documentar como fora do MVP.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add a reusable Tag entity distinct from Category.
- **FR-002**: System MUST maintain many-to-many associations between document sources and tags.
- **FR-003**: System MUST normalize tag keys using trim, lowercase and accent-insensitive comparison.
- **FR-004**: System MUST prevent duplicate tags by normalized key.
- **FR-005**: System MUST allow document ingestion and source patch operations to associate existing tags by id and optionally create/reuse tags by name when the API contract chooses name-based input.
- **FR-006**: System MUST expose tags on source and chunk read models alongside categories.
- **FR-007**: System MUST provide tag create, update, delete, list and autocomplete endpoints.
- **FR-008**: System MUST reject deletion of tags associated with any source.
- **FR-009**: System MUST allow search and answer filters by tag ids using ANY semantics for the MVP.
- **FR-010**: System MUST combine category filters and tag filters as separate AND dimensions.
- **FR-011**: System MUST avoid duplicate chunks when a source matches multiple requested tags.
- **FR-012**: System MUST not regenerate embeddings when only source tags change.
- **FR-013**: System MUST update MCP tools/models where ingestion, source reads, search and answer expose or accept tags.
- **FR-014**: System MUST update `doc/API.md` when API request or response behavior changes.
- **FR-015**: System MUST keep tag implementation postponable unless real usage shows categories do not solve the classification need well.

### Key Entities *(include if feature involves data)*

- **Tag**: A reusable, normalized marker for specific subjects such as `python`, `postgres`, `imposto` or `rag`.
- **DocumentSource**: Existing persisted source that may have zero or more tags in addition to one or more categories.
- **DocumentSourceTag**: Association between a source and a tag.
- **TagFilter**: Request-level filter over tag ids, initially with ANY semantics and optional future ALL semantics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Creating or associating duplicate tag names differing only by case, whitespace or accents produces one persisted tag.
- **SC-002**: Updating only tags on an existing source leaves the chunk count and embeddings unchanged.
- **SC-003**: Search and answer filters can combine category ids and tag ids without duplicate chunk ids.
- **SC-004**: Autocomplete returns matching tags in under 1 second for representative local datasets.
- **SC-005**: API, MCP and documentation consistently distinguish categories from tags.
- **SC-006**: The feature is accepted only after at least one real classification case is identified where multiple categories are less appropriate than tags.

## Assumptions

- Categories remain mandatory for ingestion; tags are optional metadata in the first implementation.
- The first implementation accepts tag ids in stable API/MCP contracts; name-based upsert can be added for ergonomics if it does not blur validation.
- Tag display names may be the normalized key in v1; preserving a separate original label is optional.
- The current idempotent database initialization approach remains the schema-change mechanism.
- Frontend changes are optional unless an existing UI already exposes source editing or advanced search filters.
