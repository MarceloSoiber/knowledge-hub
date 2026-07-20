# Feature Specification: Limite Minimo de Relevancia

**Feature Branch**: `006-limite-relevancia`

**Created**: 2026-07-17

**Status**: Draft

**Input**: Plano 05 - Limite minimo de relevancia

## User Scenarios & Testing

### User Story 1 - Filtrar Resultados Fracos (Priority: P1)

Um usuario executa uma busca semantica e recebe apenas chunks cujo score atinge o limite minimo configurado ou solicitado de forma valida.

**Why this priority**: Sem esse filtro, perguntas fora da base podem retornar trechos semanticamente fracos como se fossem conhecimento confiavel.

**Independent Test**: Executar a busca com resultados simulados acima e abaixo do limite e confirmar que apenas os resultados aprovados aparecem.

**Acceptance Scenarios**:

1. **Given** chunks com scores acima e abaixo do limite, **When** a busca e executada, **Then** apenas chunks com score maior ou igual ao limite sao retornados.
2. **Given** uma busca com categorias validas, **When** o filtro de relevancia remove parte dos resultados, **Then** o contrato de resposta permanece o mesmo e a lista final respeita o limite solicitado.

---

### User Story 2 - Ausencia Explicita de Informacao (Priority: P2)

Um usuario pergunta algo fora da base e recebe lista vazia na busca; ao pedir uma resposta RAG, o LLM e orientado a declarar que nao encontrou a informacao.

**Why this priority**: O comportamento seguro para conhecimento ausente e admitir ausencia, nao sintetizar resposta a partir de contexto fraco.

**Independent Test**: Simular uma pergunta cujo melhor score fica abaixo do limite e validar `/search` com `results=[]` e `/answer` sem fontes recuperadas.

**Acceptance Scenarios**:

1. **Given** nenhum resultado acima do limite, **When** `/api/v1/knowledge/search` e chamado, **Then** a resposta contem `results` vazio.
2. **Given** nenhum resultado acima do limite, **When** `/api/v1/knowledge/answer` e chamado, **Then** o LLM recebe contexto vazio e deve responder que nao encontrou a informacao.

---

### User Story 3 - Calibracao Controlada (Priority: P3)

Um operador calibra a busca alterando `SEARCH_MIN_SCORE` ou enviando um override valido em API/MCP sem aceitar valores fora de faixa.

**Why this priority**: O limiar precisa ser ajustavel por dominio e por modelo de embeddings, mas ajustes inseguros nao devem entrar silenciosamente.

**Independent Test**: Enviar valores validos e invalidos de `min_score` e confirmar validacao, filtragem e documentacao do valor padrao.

**Acceptance Scenarios**:

1. **Given** `SEARCH_MIN_SCORE` configurado, **When** uma busca nao informa `min_score`, **Then** o limite global e usado.
2. **Given** `min_score` dentro da faixa permitida, **When** a busca e chamada por API ou MCP, **Then** o override e aplicado somente naquela requisicao.
3. **Given** `min_score` fora da faixa permitida, **When** a busca e chamada por API ou MCP, **Then** a requisicao e rejeitada por validacao.

### Edge Cases

- Scores `None`, `NaN` ou nao numericos nao devem aprovar resultados.
- Score exatamente igual ao limite deve aprovar o resultado.
- Limite solicitado maior que 1 ou menor que 0 deve ser rejeitado.
- Logs podem registrar score, limite resolvido, quantidade bruta e quantidade filtrada, mas nao devem registrar a pergunta por padrao.
- `1 - distancia` deve ser tratado como score de ordenacao/calibracao, nao como probabilidade.

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a global `SEARCH_MIN_SCORE` setting with documented default value.
- **FR-002**: System MUST filter semantic search results after cosine similarity score calculation.
- **FR-003**: System MUST apply the same relevance filtering to API search, API answer and MCP search flows.
- **FR-004**: System MUST return an empty result list when no chunk reaches the resolved relevance threshold.
- **FR-005**: System MUST allow a request-scoped `min_score` override for API and MCP search within validated bounds.
- **FR-006**: System MUST reject invalid `min_score` values before executing search.
- **FR-007**: System MUST keep sensitive user questions out of score logs by default.
- **FR-008**: System MUST document the default score, its conservative rationale and recalibration guidance.

### Key Entities

- **ResolvedSearchThreshold**: Effective minimum relevance score for a request, resolved from request override or global settings.
- **SearchResultScore**: Existing search result score computed from cosine distance and used only for ranking/filtering.
- **SearchTelemetryEvent**: Non-sensitive operational log containing threshold, raw result count, filtered result count and score range.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Results with score below the effective threshold are absent from API and MCP search responses.
- **SC-002**: A question outside the indexed knowledge base does not receive arbitrary chunks when all scores are below threshold.
- **SC-003**: Invalid `min_score` values are rejected by API/MCP validation.
- **SC-004**: Documentation states the default threshold and explains that scores require domain/model calibration.

## Assumptions

- Feature `005-metadados-citacoes` is already implemented and search results expose `score`.
- The initial default threshold is conservative and may be recalibrated with domain-specific question sets.
- No new database table is required for this feature.
- Frontend changes are limited to including an optional threshold control only if the current UI exposes advanced search options.
