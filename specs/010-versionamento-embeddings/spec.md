# Feature Specification: Versionamento de Embeddings

**Feature Branch**: `010-versionamento-embeddings`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "Com base no plano `plan/09-versionamento-embeddings.md`, planejar a implementacao."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rastrear origem de cada embedding (Priority: P1)

Um usuario ou operador inspeciona uma fonte/chunk e consegue saber exatamente qual provider, modelo, dimensao, versao de configuracao e instante produziram o embedding usado.

**Why this priority**: Sem rastreabilidade por embedding, qualquer troca de modelo pode misturar vetores silenciosamente e degradar busca/RAG sem sinal operacional.

**Independent Test**: Ingerir texto com configuracao de embedding conhecida, buscar o chunk criado e confirmar que o retorno ou detalhe interno aponta para um lote com provider, modelo, dimensao, versao, hash do conteudo normalizado e `embedded_at`.

**Acceptance Scenarios**:

1. **Given** uma ingestao nova com `LLM_PROVIDER=local`, `EMBEDDING_MODEL=A` e `VECTOR_DIM=768`, **When** chunks sao persistidos, **Then** cada chunk aponta para um lote de embedding com provider/modelo/dimensao efetivos e timestamp.
2. **Given** dois chunks criados no mesmo fluxo de ingestao, **When** os metadados sao consultados, **Then** ambos podem compartilhar o mesmo lote sem repetir configuracao em todas as linhas.
3. **Given** um chunk antigo sem lote conhecido, **When** a compatibilidade e avaliada, **Then** ele e tratado como `unversioned`/pendente ate reindexacao ou adocao explicita, nunca como compativel por suposicao.

---

### User Story 2 - Evitar mistura em busca e resposta (Priority: P2)

Um usuario troca modelo ou dimensao de embedding e a busca vetorial deixa de misturar chunks gerados por configuracoes diferentes.

**Why this priority**: A busca e o RAG dependem da comparabilidade dos vetores. Misturar modelos diferentes pode produzir rankings aparentemente validos mas semanticamente ruins.

**Independent Test**: Criar chunks em duas versoes de embedding diferentes, executar busca com uma configuracao ativa, e confirmar que a etapa vetorial considera apenas chunks compativeis; chunks incompativeis aparecem como pendentes/reindexaveis, nao como candidatos vetoriais.

**Acceptance Scenarios**:

1. **Given** chunks com `embedding_model=A` e configuracao ativa `embedding_model=B`, **When** search/answer e executado, **Then** esses chunks nao participam da busca vetorial.
2. **Given** a busca hibrida tambem usa full-text, **When** existirem chunks com embedding pendente, **Then** o retorno deve deixar claro quando a correspondencia veio apenas de texto, sem fingir score vetorial.
3. **Given** um projeto/categoria/tag filtrado, **When** a busca aplica filtros e compatibilidade, **Then** ambas as restricoes sao combinadas sem duplicar chunks.

---

### User Story 3 - Identificar pendencias de reindexacao (Priority: P3)

Um operador identifica fontes/chunks que precisam ser reembeddados depois de troca de provider/modelo/dimensao ou alteracao de conteudo.

**Why this priority**: Versionar sem uma fila/visao de pendencias impede recuperar qualidade depois de uma troca planejada.

**Independent Test**: Ingerir conteudo com modelo A, alterar a configuracao efetiva para modelo B, chamar a rotina de avaliacao de pendencias e confirmar que os chunks do modelo A sao marcados como pendentes para B sem recalcular o que ja tem hash compativel.

**Acceptance Scenarios**:

1. **Given** configuracao ativa diferente da usada por chunks existentes, **When** a rotina de compatibilidade roda, **Then** os chunks/fonte sao listados como pendentes de reindexacao.
2. **Given** um chunk cujo hash normalizado ja foi embeddado com a configuracao ativa, **When** a reindexacao e solicitada, **Then** o sistema evita trabalho desnecessario ou reutiliza o embedding compativel quando permitido.
3. **Given** conteudo alterado em uma fonte, **When** chunks sao regenerados, **Then** os novos chunks recebem novo hash e novo lote.

---

### User Story 4 - Bloquear dimensao divergente no startup (Priority: P4)

Um deploy com `VECTOR_DIM` diferente da coluna pgvector falha cedo, com mensagem clara, a menos que uma migracao explicita tenha sido aplicada.

**Why this priority**: Dimensao divergente entre configuracao e tipo `vector(n)` quebra embedding/search de forma perigosa e hoje pode ser mascarada por `ALTER TABLE` automatico.

**Independent Test**: Configurar `VECTOR_DIM=1024` em uma base cuja coluna e `vector(768)` e executar init/startup; o sistema deve falhar antes de servir trafego.

**Acceptance Scenarios**:

1. **Given** coluna `knowledge_chunks.embedding` em `vector(768)` e `VECTOR_DIM=1024`, **When** `init_db()` roda, **Then** ele falha com erro orientando migracao explicita.
2. **Given** coluna e configuracao ambas em 768, **When** `init_db()` roda, **Then** o startup segue normalmente.
3. **Given** uma migracao explicita para nova dimensao foi aplicada, **When** `VECTOR_DIM` corresponde a nova coluna, **Then** o sistema aceita novos embeddings.

### Edge Cases

- Chunks antigos sem metadados de embedding nao podem ser marcados como compativeis automaticamente.
- Duas configuracoes com mesmo modelo mas dimensao diferente sao incompativeis.
- Duas configuracoes com mesmo provider/modelo/dimensao mas `embedding_version` diferente devem ser tratadas conforme decisao de compatibilidade: recomendado considerar versao parte da identidade.
- Provider local e provider API externa podem usar o mesmo nome de modelo; provider faz parte da chave.
- Search full-text pode retornar chunks sem embedding compativel, mas `match_reasons`/score devem diferenciar texto de vetor.
- Uma falha no embedding provider nao deve criar lote concluido nem chunks parcialmente versionados.
- Reindexacao deve ser idempotente para o mesmo hash normalizado e mesma configuracao.
- Alterar apenas metadados de fonte, categorias, tags ou projetos nao deve marcar embeddings como pendentes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST persist the effective embedding provider, model, dimension, version/revision and timestamp for every newly generated embedding.
- **FR-002**: System MUST persist a normalized content hash for each embedded chunk.
- **FR-003**: System MUST associate each embedded chunk with an embedding batch/configuration record instead of relying only on global settings.
- **FR-004**: System MUST expose enough internal/read-model data to answer which embedding configuration produced any chunk.
- **FR-005**: System MUST validate active embedding compatibility before vector search and answer retrieval.
- **FR-006**: System MUST exclude incompatible or unversioned chunks from vector similarity search.
- **FR-007**: System MUST not silently treat legacy chunks without embedding metadata as compatible.
- **FR-008**: System MUST identify chunks/sources pending reindexation when the active embedding configuration changes.
- **FR-009**: System MUST avoid redundant embedding work when normalized content hash and active embedding configuration already have a valid embedding.
- **FR-010**: System MUST fail startup when configured `VECTOR_DIM` differs from the database vector column dimension unless an explicit migration changed the column.
- **FR-011**: System MUST keep metadata-only source changes from invalidating embeddings.
- **FR-012**: System MUST preserve existing category/tag/project filtering semantics while adding embedding compatibility filters.
- **FR-013**: System MUST update API/MCP/read contracts when embedding metadata or reindex status becomes user-visible.
- **FR-014**: System MUST update `doc/API.md` for any public API behavior changes.

### Key Entities *(include if feature involves data)*

- **EmbeddingBatch**: One effective embedding configuration and indexing run, including provider, model, dimension, version, status, timestamps and counters.
- **KnowledgeChunk**: Existing chunk with embedding vector, normalized content hash, embedding status and optional batch relationship.
- **EmbeddingCompatibility**: Runtime decision comparing active settings with stored batch metadata.
- **ReindexCandidate**: Source/chunk view describing why an item needs embedding regeneration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every newly ingested chunk, an operator can identify provider, model, dimension, version and `embedded_at`.
- **SC-002**: Search/answer never use vectors whose stored provider/model/dimension/version differ from the active embedding configuration.
- **SC-003**: Legacy unversioned chunks are reported as pending or unversioned rather than silently mixed into vector search.
- **SC-004**: Changing `EMBEDDING_MODEL` marks existing chunks as pending for the new configuration before they can participate in vector search for that configuration.
- **SC-005**: Reindexing unchanged normalized chunk text with the same configuration avoids an unnecessary embedding provider call where a reusable embedding already exists.
- **SC-006**: Startup with mismatched `VECTOR_DIM` and pgvector column dimension fails with an actionable error.

## Assumptions

- `embedding_version` defaults to a deterministic setting such as `EMBEDDING_VERSION` or a derived configuration fingerprint when not supplied.
- Backfilling exact metadata for old embeddings is impossible unless an operator explicitly declares the legacy configuration; default behavior is to mark them unversioned/pending.
- Vector search strictness is required; full-text search can remain available for unversioned chunks if responses distinguish match reasons.
- Reindex execution can be implemented as a service/CLI/API flow after the metadata and compatibility foundation exists.
- No frontend change is required for MVP unless public reindex status endpoints are added and the existing UI needs to display them.
