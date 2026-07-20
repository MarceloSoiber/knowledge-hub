# Feature Specification: Busca Hibrida

**Feature Branch**: `007-busca-hibrida`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Com base no plano `plan/06-busca-hibrida.md`, montar o planejamento para o ajuste."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recuperar termos exatos e identificadores (Priority: P1)

Um usuario busca por codigos, tickers, numeros, nomes proprios ou mensagens de erro e recebe os chunks que contem esses termos mesmo quando a similaridade vetorial isolada nao os ranqueia bem.

**Why this priority**: Este e o principal ganho da busca hibrida: cobrir lacunas conhecidas da busca apenas semantica para termos exatos.

**Independent Test**: Ingerir documentos com identificadores exatos e executar buscas por esses tokens, confirmando que os chunks corretos aparecem nos primeiros resultados.

**Acceptance Scenarios**:

1. **Given** uma fonte com o termo `ERR_CONN_RESET`, **When** a busca usa `ERR_CONN_RESET`, **Then** o chunk contendo o termo aparece sem depender apenas do embedding.
2. **Given** uma fonte com ticker ou codigo curto, **When** a busca usa esse identificador, **Then** o resultado retorna a fonte correta com score e citacao existentes.
3. **Given** o mesmo chunk encontrado pela busca vetorial e textual, **When** os rankings sao combinados, **Then** o chunk aparece apenas uma vez no resultado final.

---

### User Story 2 - Preservar recuperacao semantica (Priority: P2)

Um usuario faz uma pergunta parafraseada sem compartilhar palavras importantes com o documento e continua recebendo os resultados semanticos relevantes.

**Why this priority**: A busca hibrida nao pode regredir o comportamento que a busca vetorial ja resolve bem.

**Independent Test**: Executar casos parafraseados conhecidos e confirmar que a busca hibrida iguala ou supera a busca vetorial anterior no conjunto de avaliacao.

**Acceptance Scenarios**:

1. **Given** uma pergunta semanticamente equivalente mas com vocabulario diferente, **When** a busca hibrida e executada, **Then** o chunk esperado permanece nos resultados.
2. **Given** candidatos vetoriais e textuais com escalas de score diferentes, **When** o ranking final e calculado, **Then** a fusao usa posicoes relativas em vez de somar scores diretamente.

---

### User Story 3 - Diagnosticar por que um resultado apareceu (Priority: P3)

Um operador habilita diagnostico de busca e ve se cada resultado veio por similaridade vetorial, match textual ou ambos.

**Why this priority**: Diagnostico acelera calibracao e comparacao com o Plano 12, mas nao e necessario para o MVP de recuperacao.

**Independent Test**: Executar a mesma query com diagnostico habilitado e confirmar que cada resultado informa os sinais que contribuíram para o ranking sem expor dados sensiveis adicionais.

**Acceptance Scenarios**:

1. **Given** uma query com diagnostico habilitado, **When** um chunk aparece nos dois caminhos, **Then** o resultado indica match vetorial e textual.
2. **Given** uma query sem diagnostico, **When** a busca retorna resultados, **Then** o contrato padrao permanece enxuto e compativel com clientes existentes.

### Edge Cases

- Termos curtos, codigos com pontuacao, tickers e numeros devem ser preservados pela configuracao textual escolhida.
- Query vazia ou apenas espacos continua rejeitada pela validacao existente.
- Categoria inexistente continua retornando erro antes de executar a busca.
- Filtros de categorias devem ser aplicados antes do limite final e antes da fusao dos candidatos.
- Chunks sem embedding nao participam do caminho vetorial, mas podem participar do caminho textual se estiverem indexados.
- Resultados duplicados entre busca vetorial e textual devem ser fundidos por `chunk.id`.
- Quando nao houver match textual, a busca deve se comportar como a busca vetorial filtrada atual.
- Quando o indice textual ainda nao estiver preenchido em dados antigos, a inicializacao/migracao deve reconstruir o vetor textual.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain a full-text searchable representation for each knowledge chunk.
- **FR-002**: System MUST create a PostgreSQL GIN index for the full-text search representation.
- **FR-003**: System MUST choose and document the text search configuration, including behavior for Portuguese content and code-like tokens.
- **FR-004**: System MUST execute vector and textual candidate retrieval as independent query paths.
- **FR-005**: System MUST apply category filters before candidate limits and before final ranking.
- **FR-006**: System MUST combine candidate rankings with Reciprocal Rank Fusion or equivalent rank-based fusion, not direct score addition across incomparable scales.
- **FR-007**: System MUST deduplicate chunks returned by both retrieval paths.
- **FR-008**: System MUST keep the existing search, answer and MCP result contract compatible by default.
- **FR-009**: System MUST optionally expose match reasons for diagnostics when explicitly requested by API or MCP clients.
- **FR-010**: System MUST keep existing `min_score` behavior meaningful for vector similarity while defining how hybrid scores are filtered or reported.
- **FR-011**: System MUST update API documentation when request or response fields change.
- **FR-012**: System MUST include automated tests for exact identifiers, semantic paraphrases, deduplication and filtered search.
- **FR-013**: System MUST compare hybrid retrieval with the previous vector-only behavior using the Plano 12 evaluation dataset before release acceptance.

### Key Entities *(include if feature involves data)*

- **KnowledgeChunk**: Searchable text segment with existing embedding, citation metadata and new full-text search vector.
- **HybridSearchCandidate**: Internal candidate representation containing chunk id, retrieval mode, rank, optional vector score and optional text rank.
- **HybridSearchResult**: Existing public chunk result enriched internally with fused ranking information and optional diagnostic match reasons.
- **SearchDiagnostics**: Optional response metadata that explains whether a result matched vector, text or both.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Exact identifier queries from the Plano 12 dataset return the expected chunk in the top 5.
- **SC-002**: Semantic paraphrase queries from the Plano 12 dataset equal or exceed vector-only Recall@K and Mean Reciprocal Rank.
- **SC-003**: Hybrid search returns no duplicate chunk ids when the same chunk matches both retrieval paths.
- **SC-004**: Typical search latency remains within the constitution target of 500ms for representative local datasets.
- **SC-005**: PostgreSQL execution plans use the GIN index for text search and the pgvector path for vector candidates when applicable.

## Assumptions

- The feature starts after `006-limite-relevancia` and keeps its request-level `min_score` support.
- PostgreSQL is the production persistence target and supports generated `tsvector` or idempotent column maintenance in `init_db()`.
- The first implementation uses PostgreSQL `simple` text search configuration unless tests prove `portuguese` improves Portuguese content without damaging code-like tokens.
- API and MCP diagnostics are opt-in to avoid breaking existing clients and to avoid noisy default responses.
- The frontend does not need a new workflow unless an existing search screen already has advanced search controls.
