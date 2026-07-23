# Feature Specification: Ciclo de Vida dos Documentos

**Feature Branch**: `004-ciclo-vida-documentos`

**Created**: 2026-07-16

**Status**: Draft

**Input**: Plano 03 — Ciclo de vida dos documentos

## User Scenarios & Testing

### User Story 1 - Administrar Fonte Individual (Priority: P1)

Um usuario consulta uma fonte especifica por identificador publico estavel para ver titulo, categorias, origem, hash, timestamps e conteudo canonico.

**Why this priority**: Atualizacao e exclusao seguras dependem de uma identidade que nao seja titulo, categoria ou URI.

**Independent Test**: Buscar uma fonte existente por UUID e confirmar o contrato completo; buscar UUID inexistente retorna 404.

**Acceptance Scenarios**:

1. **Given** uma fonte persistida, **When** `GET /sources/{source_id}` recebe seu UUID, **Then** a resposta contem metadados, categorias, hash e conteudo.
2. **Given** uma fonte inexistente, **When** o detalhe e solicitado, **Then** a API retorna `404 Not Found`.

---

### User Story 2 - Atualizar Metadados Sem Reindexar (Priority: P2)

Um usuario altera titulo e categorias de uma fonte sem recriar embeddings quando o conteudo nao mudou.

**Why this priority**: Metadados devem ser baratos de corrigir e nao devem chamar provedores externos desnecessariamente.

**Independent Test**: Aplicar `PATCH` apenas com titulo/categorias e verificar que chunks permanecem e o cliente de embeddings nao e chamado.

**Acceptance Scenarios**:

1. **Given** uma fonte existente, **When** `PATCH` altera apenas titulo e categorias, **Then** a fonte e atualizada sem reprocessar chunks.
2. **Given** categorias inexistentes, **When** `PATCH` e chamado, **Then** a API retorna `404` e nada e alterado.

---

### User Story 3 - Atualizar ou Excluir Conteudo (Priority: P3)

Um usuario substitui o conteudo de uma fonte ou exclui definitivamente a fonte quando confirma explicitamente a operacao.

**Why this priority**: O hub precisa corrigir documentos obsoletos sem limpeza total, preservando consistencia transacional.

**Independent Test**: Alterar conteudo recria chunks/embeddings atomicamente; excluir com confirmacao remove fonte, chunks e associacoes.

**Acceptance Scenarios**:

1. **Given** uma fonte existente, **When** `PATCH` envia novo conteudo, **Then** hash, texto canonico, chunks e embeddings sao substituidos em uma transacao.
2. **Given** falha no provedor de embeddings, **When** conteudo e atualizado, **Then** nenhuma atualizacao parcial permanece.
3. **Given** uma fonte existente, **When** `DELETE /sources/{source_id}?confirm=true` e chamado, **Then** a fonte e removida definitivamente.

### Edge Cases

- Dois documentos com mesmo titulo e conteudo diferente devem coexistir.
- Conteudo identico a outra fonte ativa deve retornar `409 Conflict`.
- Exclusao sem `confirm=true` deve retornar `400 Bad Request`.
- UUID malformado deve falhar por validacao da API.

## Requirements

### Functional Requirements

- **FR-001**: System MUST expose a stable public UUID for each document source.
- **FR-002**: System MUST stop replacing sources implicitly by title, category or URI during ingestion.
- **FR-003**: System MUST store canonical normalized source content and SHA-256 content hash.
- **FR-004**: System MUST reject duplicate canonical content with `409 Conflict`.
- **FR-005**: Users MUST be able to retrieve, patch and delete a source by public UUID.
- **FR-006**: System MUST regenerate chunks and embeddings only when canonical content changes.
- **FR-007**: System MUST delete source chunks and category associations when a source is deleted.
- **FR-008**: MCP MUST expose read-only detailed source lookup by UUID and no destructive source tools.
- **FR-009**: API documentation MUST describe UUID identity, duplicate policy and definitive deletion.

### Key Entities

- **DocumentSource**: Persisted knowledge source with internal integer ID, public UUID, title, source type, URI, canonical content, content hash, timestamps and categories.
- **KnowledgeChunk**: Searchable chunk attached to a document source and replaced when source content changes.
- **DocumentSourceCategory**: Association removed by cascade when a source is deleted.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Automated tests prove equal titles do not overwrite different documents.
- **SC-002**: Automated tests prove metadata-only updates do not call embeddings.
- **SC-003**: Automated tests prove content update rollback/no partial writes on embedding failure.
- **SC-004**: API and MCP contracts expose UUID source IDs for source management.

## Assumptions

- Public UUID is the source identifier for source list, detail, ingestion responses and MCP source tools.
- Existing chunk search can continue exposing internal integer `source_id` for compatibility.
- `content_text` stores canonical normalized text, not original upload bytes.
- Deletion is definitive and assumes an external/manual backup process.
