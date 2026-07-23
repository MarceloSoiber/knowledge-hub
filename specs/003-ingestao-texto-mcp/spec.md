# Feature Specification: Ingestao de Texto pelo MCP

**Feature Branch**: `003-ingestao-texto-mcp`

**Created**: 2026-07-14

**Status**: Draft

**Input**: User description: "Plano 02 - Ingestao de texto pelo MCP: criar tool `ingest_text` para agentes salvarem notas e conhecimento sem arquivo."

## User Scenarios & Testing

### User Story 1 - Salvar nota confirmada pelo MCP (Priority: P1)

Um agente conectado ao MCP registra uma nota textual no Knowledge Hub somente apos confirmacao explicita do usuario, informando titulo, conteudo e categorias.

**Why this priority**: E o valor principal da melhoria e permite capturar conhecimento sem depender de upload de arquivo.

**Independent Test**: Chamar a tool `ingest_text` com titulo, conteudo e categorias validas, usando credencial de escrita, e confirmar que uma fonte `mcp` e criada com chunks.

**Acceptance Scenarios**:

1. **Given** categorias existentes e credencial com escrita, **When** `ingest_text` recebe titulo, conteudo e `category_ids`, **Then** a fonte e persistida e a resposta contem `source_id`, titulo, categorias e quantidade de chunks.
2. **Given** uma conversa ainda nao confirmada pelo usuario, **When** o agente consulta as instrucoes da tool, **Then** ele encontra orientacao clara para pedir confirmacao antes de persistir qualquer conteudo.

---

### User Story 2 - Bloquear escrita para clientes somente leitura (Priority: P2)

Um cliente MCP com permissao somente leitura continua podendo pesquisar e listar dados, mas nao consegue executar a tool de ingestao.

**Why this priority**: A escrita via agente aumenta o risco operacional; separar leitura e escrita e requisito de seguranca da feature.

**Independent Test**: Usar uma credencial com apenas `knowledge:read` e confirmar que `search`, `sources` e `categories` funcionam, enquanto `ingest_text` falha sem gravar dados.

**Acceptance Scenarios**:

1. **Given** token MCP com escopo `knowledge:read`, **When** o cliente executa `ingest_text`, **Then** a execucao e negada antes da persistencia.
2. **Given** token MCP com escopos `knowledge:read` e `knowledge:write`, **When** o cliente executa `ingest_text`, **Then** a tool pode persistir seguindo as validacoes de ingestao.

---

### User Story 3 - Reportar erros de ingestao de forma acionavel (Priority: P3)

Um agente recebe mensagens de erro curtas e uteis quando a ingestao falha, permitindo corrigir categoria, conteudo ou configuracao de embeddings.

**Why this priority**: Erros MCP mal traduzidos dificultam automacao e podem fazer o agente repetir chamadas inseguras.

**Independent Test**: Simular categoria inexistente, conteudo vazio e falha de embedding; cada caso retorna erro legivel e nao deixa fonte/chunks parciais.

**Acceptance Scenarios**:

1. **Given** `category_ids` com ID inexistente, **When** `ingest_text` e chamada, **Then** a resposta informa categoria ausente e nada e gravado.
2. **Given** falha no provedor de embeddings, **When** `ingest_text` e chamada, **Then** a transacao e revertida e o agente recebe mensagem de indisponibilidade/falha de embedding.

### Edge Cases

- `title` vazio ou apenas espacos deve falhar antes de chamar embeddings.
- `content` vazio, apenas espacos ou sem texto legivel deve falhar sem gravar dados.
- `category_ids` vazio, com IDs repetidos ou IDs menores que 1 deve falhar por validacao.
- Categoria inexistente deve falhar sem criar fonte nem chunks.
- Falha de embedding deve provocar rollback completo.
- Recadastro com mesmo titulo segue a politica de identidade de texto existente ate o Plano 03 redefinir ciclo de vida.
- Tool nao deve incentivar salvamento automatico de conversas completas.

## Requirements

### Functional Requirements

- **FR-001**: System MUST expose an MCP tool named `ingest_text` for text-only knowledge ingestion.
- **FR-002**: `ingest_text` MUST accept `title`, `content`, `category_ids` and optional allowlisted metadata.
- **FR-003**: System MUST reuse the backend text ingestion service instead of duplicating chunking, category validation, embedding, source replacement or transaction rules in the MCP layer.
- **FR-004**: The MCP response MUST include `source_id`, `title`, `categories` and `chunks_created`.
- **FR-005**: System MUST record MCP-created sources with source type/origin `mcp` when this can be done without breaking API text ingestion semantics.
- **FR-006**: System MUST separate read and write authorization for MCP, requiring `knowledge:write` for `ingest_text`.
- **FR-007**: System MUST keep read tools available to `knowledge:read` clients.
- **FR-008**: System MUST keep `ingest_text` disabled or isolated if the installed FastMCP version cannot enforce per-tool write authorization safely.
- **FR-009**: Tool instructions MUST require explicit user confirmation before saving content.
- **FR-010**: Tool instructions MUST avoid telling agents to persist conversations automatically.
- **FR-011**: System MUST map validation, missing category, empty content and embedding failures to useful MCP errors.
- **FR-012**: System MUST document the MCP write capability, required scope, confirmation expectation and failure modes.

### Key Entities

- **MCP Text Ingestion Request**: Tool input containing title, content, category IDs and optional safe metadata.
- **MCP Text Ingestion Result**: Tool output summarizing the created or replaced source and chunks.
- **MCP Access Scope**: Authorization capability distinguishing `knowledge:read` from `knowledge:write`.
- **DocumentSource**: Persisted knowledge source created from MCP text content.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A valid `ingest_text` call with write scope creates a source and at least one chunk in automated tests.
- **SC-002**: A read-only MCP client cannot execute `ingest_text` and no database rows are created.
- **SC-003**: Empty content, invalid categories and embedding failures each have automated tests proving rollback/no partial writes.
- **SC-004**: MCP documentation/catalog describes `ingest_text` and states that user confirmation is required before persistence.
- **SC-005**: Existing read-only MCP tools keep their current behavior.

## Assumptions

- The multi-category contract from `specs/002-categorias-muitos-para-muitos/` is already implemented.
- The first implementation may use a separate write-capable MCP server/configuration if per-tool FastMCP scopes are not reliable.
- Optional metadata is limited to a small allowlist and does not become an arbitrary JSON persistence contract in this feature.
- Frontend changes are out of scope unless needed to document status of MCP write capability.
