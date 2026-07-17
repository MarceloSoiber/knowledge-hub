# Feature Specification: Metadados e Citacoes na Busca

**Feature Branch**: `005-metadados-citacoes`

**Created**: 2026-07-17

**Status**: Draft

**Input**: Plano 04 - Metadados e citacoes na busca

## User Scenarios & Testing

### User Story 1 - Resultado Rastreavel (Priority: P1)

Um usuario executa uma busca semantica e recebe, em cada resultado, a origem publica, titulo, categorias, URI sanitizada, conteudo, score e localizacao do trecho.

**Why this priority**: Resultados sem origem citavel nao permitem auditoria nem uso confiavel por agentes.

**Independent Test**: Executar `/search` e confirmar que cada item aponta para um UUID publico de fonte e uma localizacao.

**Acceptance Scenarios**:

1. **Given** uma fonte indexada, **When** uma busca retorna um chunk, **Then** o resultado contem UUID publico, titulo, URI, categorias, conteudo, score e localizacao.
2. **Given** uma fonte com multiplas categorias, **When** a busca filtra por categorias, **Then** o resultado nao e duplicado.

---

### User Story 2 - Localizacao para Citacao (Priority: P2)

Um usuario ingere ou atualiza documentos e os chunks preservam indice, offsets e, quando identificavel, pagina de PDF ou secao Markdown/texto.

**Why this priority**: A IA precisa apontar onde encontrou a informacao, nao apenas qual documento foi usado.

**Independent Test**: Ingerir PDF e Markdown de exemplo e verificar metadados de pagina/secao nos chunks resultantes.

**Acceptance Scenarios**:

1. **Given** um PDF com texto nativo, **When** ele e ingerido, **Then** chunks associados preservam numero da pagina.
2. **Given** um Markdown com cabecalhos, **When** ele e ingerido, **Then** chunks preservam a secao predominante.

---

### User Story 3 - Resposta RAG com Fontes Citaveis (Priority: P3)

Um usuario pede uma resposta com LLM e o contexto enviado ao modelo orienta citacoes por titulo e localizacao, usando apenas fontes recuperadas.

**Why this priority**: Respostas sinteticas precisam manter rastreabilidade e evitar citar fontes fora do contexto recuperado.

**Independent Test**: Gerar resposta e inspecionar que as fontes retornadas seguem o mesmo contrato citavel da busca.

**Acceptance Scenarios**:

1. **Given** uma pergunta respondida por `/answer`, **When** fontes sao recuperadas, **Then** a resposta inclui apenas fontes presentes no payload `sources`.

### Edge Cases

- Metadados antigos em texto JSON devem continuar legiveis apos migracao para JSONB.
- Metadados invalidos ou desconhecidos nao devem aparecer como metadados publicos.
- Caminhos locais absolutos ou URIs `file:` devem ser sanitizados antes de sair em API/MCP.
- OCR de PDF pode nao preservar pagina quando o texto por pagina nao estiver disponivel.

## Requirements

### Functional Requirements

- **FR-001**: System MUST expose public UUID source identifiers in search and answer results.
- **FR-002**: System MUST include source title, source type, sanitized URI and categories in each result.
- **FR-003**: System MUST store structured chunk metadata as JSONB.
- **FR-004**: System MUST preserve chunk index and canonical text character offsets for every chunk.
- **FR-005**: System SHOULD preserve PDF page and Markdown section when identifiable.
- **FR-006**: System MUST expose only allowlisted public metadata.
- **FR-007**: MCP search results MUST match the API citation context.
- **FR-008**: API documentation MUST describe the enriched search and answer contracts.

### Key Entities

- **KnowledgeChunk**: Searchable text segment with embedding and structured citation metadata.
- **ChunkLocation**: Public location object with chunk index, optional page, optional section and canonical character offsets.
- **SearchResult**: Public API/MCP representation combining chunk, source metadata, categories, score and location.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every search result contains a public source UUID and location object.
- **SC-002**: PDF ingestion can return page metadata for native-text PDFs.
- **SC-003**: Markdown ingestion can return section metadata for headed content.
- **SC-004**: `/answer` sources use the same enriched result contract as `/search`.

## Assumptions

- Feature `004-ciclo-vida-documentos` is already implemented.
- Search results intentionally stop exposing internal integer source IDs.
- Public metadata allowlist starts with `client_id` and `note_type`.
- No frontend workflow is required for this backend/MCP contract change.
