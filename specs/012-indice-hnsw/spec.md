# Feature Specification: Indice Vetorial HNSW

**Feature Branch**: `012-indice-hnsw`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "com base no planejamento plan/11-indice-hnsw.md planeje a implementação"

## User Scenarios & Testing

### User Story 1 - Medir busca vetorial atual (Priority: P1)

Como operador do knowledge hub, quero medir a latencia, plano de execucao e recall da busca vetorial atual antes de criar um indice aproximado, para ter uma linha de base confiavel.

**Why this priority**: O plano HNSW so pode ser aceito se houver ganho mensuravel; sem baseline, os parametros seriam arbitrarios.

**Independent Test**: Rodar o benchmark em uma base com embeddings versionados e registrar latencia, `EXPLAIN (ANALYZE, BUFFERS)` e recall usando busca exata.

**Acceptance Scenarios**:

1. **Given** uma base com chunks embedded e conjunto de avaliacao, **When** o operador executa a medicao baseline, **Then** o sistema registra latencia, plano SQL, total de candidatos e recall exato por consulta.
2. **Given** uma base pequena abaixo do limiar configurado, **When** o operador executa a medicao, **Then** o relatorio recomenda manter busca exata e nao cria HNSW automaticamente.

---

### User Story 2 - Criar e validar indice HNSW (Priority: P2)

Como operador, quero criar o indice HNSW de forma idempotente e validar que a consulta vetorial realmente usa o indice, para reduzir latencia sem trocar silenciosamente a semantica da busca.

**Why this priority**: A criacao do indice e o nucleo da melhoria de performance, mas precisa respeitar pgvector, dimensao ativa, `vector_cosine_ops` e filtros existentes.

**Independent Test**: Criar o indice em banco de desenvolvimento com volume suficiente, executar `ANALYZE`, verificar o plano com `EXPLAIN` e comparar latencia contra baseline.

**Acceptance Scenarios**:

1. **Given** pgvector compativel com HNSW e embeddings com dimensao ativa, **When** o operador aplica a rotina de indice, **Then** o indice `USING hnsw (embedding vector_cosine_ops)` e criado uma unica vez e `ANALYZE knowledge_chunks` e executado.
2. **Given** uma consulta vetorial sem filtros, **When** o operador valida o plano, **Then** o relatorio mostra uso do indice HNSW ou marca a validacao como falha com o plano capturado.
3. **Given** filtros por categoria ou projeto, **When** o operador valida a busca, **Then** os resultados respeitam os filtros e o relatorio indica se o plano ainda usa HNSW.

---

### User Story 3 - Calibrar recall, parametros e rollback (Priority: P3)

Como mantenedor, quero comparar HNSW contra busca exata, ajustar parametros por medicao e documentar rollback, para evitar perda de qualidade ou custo operacional inesperado.

**Why this priority**: HNSW e aproximado; a feature so esta completa quando recall, latencia, memoria, tempo de criacao e rollback estao documentados.

**Independent Test**: Rodar comparacao exata vs HNSW em conjunto de avaliacao, alterar parametros de consulta em sessao controlada e gerar relatorio com decisao de aceite.

**Acceptance Scenarios**:

1. **Given** um conjunto de avaliacao acordado, **When** o comparador roda com HNSW ativo, **Then** ele reporta recall@k, p50/p95 de latencia e diferenca contra busca exata.
2. **Given** perda de recall acima do limite acordado, **When** o operador revisa o relatorio, **Then** a feature nao e aceita e o rollback documentado pode remover o indice.
3. **Given** indice ativo durante insercao/reindexacao, **When** o operador mede throughput, **Then** o relatorio registra impacto de escrita/reindexacao.

### Edge Cases

- Base pequena pode ser mais rapida com busca exata; a rotina deve recomendar nao criar/nao aceitar HNSW quando nao houver ganho.
- Versoes antigas do pgvector podem nao suportar HNSW; a validacao deve detectar e reportar instrucao operacional clara.
- Consultas com filtros seletivos por categorias/projetos podem nao usar HNSW ou podem precisar de estrategia adicional; isso deve ser medido, nao presumido.
- Embeddings nulos, pendentes, unversioned ou de config incompativel nao devem entrar na comparacao vetorial.
- `EXPLAIN ANALYZE` em producao pode ser caro; a documentacao deve orientar uso em replica/dev ou janela controlada.

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide an operator workflow to capture vector-search baseline latency and `EXPLAIN (ANALYZE, BUFFERS)` before HNSW creation.
- **FR-002**: System MUST create the HNSW index idempotently using cosine operator semantics compatible with the active pgvector column.
- **FR-003**: System MUST run `ANALYZE` after index creation before validating query plans.
- **FR-004**: System MUST verify and report whether representative vector queries use the HNSW index.
- **FR-005**: System MUST compare approximate HNSW results against exact vector-search results for recall@k.
- **FR-006**: System MUST validate category and project filters in benchmark and plan-validation scenarios.
- **FR-007**: System MUST measure insertion or reindexation impact with the index active.
- **FR-008**: System MUST document memory cost, index build time, maintenance impact and rollback command.
- **FR-009**: System MUST avoid automatic HNSW creation when the row count is below a configurable/reported minimum threshold.
- **FR-010**: System MUST keep existing API/MCP search behavior unchanged unless a future public diagnostics endpoint is explicitly added.

### Key Entities

- **Vector Index Validation Report**: Operator-facing result containing baseline latency, indexed latency, query plans, recall, row counts, pgvector version, index metadata and acceptance decision.
- **Evaluation Query**: Query text plus expected/exact top-k chunk ids used to compare recall.
- **HNSW Index Metadata**: Index name, operator class, build parameters, creation duration and rollback instruction.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Representative vector search p95 latency improves versus baseline for the agreed corpus size while remaining under the constitution target of 500ms for typical queries.
- **SC-002**: Recall@k loss versus exact search stays within the agreed threshold recorded in the report.
- **SC-003**: At least one unfiltered query and one filtered category/project query are validated with captured `EXPLAIN (ANALYZE, BUFFERS)`.
- **SC-004**: Index build time, memory notes and write/reindex impact are documented before acceptance.
- **SC-005**: Rollback is documented as a concrete `DROP INDEX CONCURRENTLY IF EXISTS ...` or safe equivalent appropriate for the environment.

## Assumptions

- PostgreSQL runs with pgvector and the existing `knowledge_chunks.embedding` column uses cosine-distance search semantics.
- Active embedding dimension/model/operator have already been stabilized by earlier embedding-versioning work.
- Evaluation data may initially be local fixtures plus a documented manual corpus, then evolve with Plano 12.
- HNSW creation is operationally triggered or guarded; it is not forced blindly on every startup for tiny databases.
- No frontend change is required for this feature.
