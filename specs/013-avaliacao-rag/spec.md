# Feature Specification: Avaliacao do RAG

**Feature Branch**: `013-avaliacao-rag`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "com base no plano plan/12-avaliacao-rag.md planeje a implementacao"

## User Scenarios & Testing

### User Story 1 - Executar baseline reproduzivel (Priority: P1)

Como mantenedor do knowledge hub, quero executar uma avaliacao versionada contra a implementacao atual de recuperacao e resposta, para ter uma linha de base objetiva antes de alterar chunking, embeddings, threshold ou busca.

**Why this priority**: O plano exige impedir regressao. Sem baseline reproduzivel, qualquer mudanca de RAG fica baseada em impressao manual.

**Independent Test**: Rodar o runner com um dataset pequeno versionado, congelar a configuracao avaliada e gerar um relatorio JSON/Markdown contendo metricas de recuperacao, resposta, recusas e latencia.

**Acceptance Scenarios**:

1. **Given** um dataset versionado com perguntas conhecidas e sem resposta, **When** o mantenedor executa o runner em modo baseline, **Then** o sistema grava um relatorio com versao do dataset, configuracao, metricas agregadas e resultados por caso.
2. **Given** a mesma revisao de codigo, dataset e configuracao, **When** o runner e executado novamente, **Then** os identificadores esperados, metricas e decisao de aceite sao reproduziveis salvo variacao de latencia.

---

### User Story 2 - Comparar candidato contra baseline (Priority: P2)

Como mantenedor, quero comparar uma configuracao candidata contra um baseline aprovado, para decidir se busca hibrida, thresholds, HNSW, chunking ou modelos novos podem entrar sem reduzir qualidade.

**Why this priority**: A avaliacao precisa funcionar como gate para mudancas de recuperacao, nao apenas como relatorio informativo.

**Independent Test**: Rodar o runner em modo comparacao apontando para um baseline salvo e verificar que o relatorio destaca deltas, metricas abaixo do minimo e decisao aprovado/reprovado.

**Acceptance Scenarios**:

1. **Given** um baseline salvo e uma configuracao candidata, **When** a comparacao executa, **Then** o relatorio mostra diferencas de Recall@K, MRR, resposta correta, recusa correta, citacoes sustentadas e latencia.
2. **Given** que qualquer metrica critica fica abaixo do limite minimo configurado, **When** a comparacao termina, **Then** a decisao final e reprovada e lista os casos que causaram a falha.

---

### User Story 3 - Auditar respostas, recusas e citacoes (Priority: P3)

Como revisora de qualidade, quero ver quais respostas foram sustentadas pelas fontes, quais citacoes estao corretas e quando o sistema recusou perguntas sem contexto, para revisar regressao qualitativa sem abrir logs brutos.

**Why this priority**: O RAG pode recuperar bons chunks e ainda responder mal; a avaliacao deve cobrir resposta e citacao, nao apenas ranking.

**Independent Test**: Rodar casos com resposta esperada, pontos essenciais, fontes esperadas e perguntas sem resposta; confirmar que o relatorio marca acertos, faltas, citacoes incorretas e recusas corretas.

**Acceptance Scenarios**:

1. **Given** um caso com pontos essenciais esperados, **When** a resposta gerada contem os pontos exigidos e usa fontes recuperadas, **Then** o caso e marcado como resposta sustentada.
2. **Given** uma pergunta deliberadamente sem resposta, **When** nenhum contexto suficiente e encontrado ou o LLM recusa, **Then** o caso conta como recusa correta.
3. **Given** uma resposta com citacao a chunk nao recuperado ou fonte errada, **When** o avaliador processa o caso, **Then** a citacao e marcada como incorreta mesmo que a resposta textual pareca plausivel.

### Edge Cases

- Dataset vazio ou malformado deve falhar antes de chamar embeddings/LLM.
- Casos sem resposta nao podem ter `expected_chunks` obrigatorios.
- Chunks esperados podem mudar de id apos reingestao; o dataset deve permitir referencias estaveis por `source_public_id`, `chunk_index` e/ou metadados.
- LLM nao deterministico pode variar redacao; a avaliacao deve aceitar pontos essenciais e recusas padronizadas em vez de exigir igualdade literal completa.
- Falha de provider de embeddings ou LLM deve ser registrada como erro de execucao, nao como resposta incorreta silenciosa.
- Latencia deve ser reportada separadamente para embedding da query, recuperacao e resposta.

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a separate evaluation runner outside the normal unit-test suite.
- **FR-002**: System MUST load a versioned dataset containing query, expected sources/chunks, expected category/project, expected answer or essential points, unanswered cases and case type metadata.
- **FR-003**: System MUST record the evaluated configuration, including retrieval limit, threshold, hybrid settings, embedding identity, LLM model/provider and dataset version.
- **FR-004**: System MUST calculate Recall@K and Mean Reciprocal Rank for retrieval.
- **FR-005**: System MUST calculate known-answer correctness using expected answer points.
- **FR-006**: System MUST calculate correct-refusal rate for unanswered questions.
- **FR-007**: System MUST validate citation correctness and whether answers are supported by retrieved sources.
- **FR-008**: System MUST measure latency for query embedding, search/retrieval and answer generation separately.
- **FR-009**: System MUST produce a machine-readable JSON report and a human-readable summary suitable for review.
- **FR-010**: System MUST compare a candidate report against a baseline and apply configurable minimum thresholds.
- **FR-011**: System MUST keep API/MCP search and answer contracts unchanged for this feature.
- **FR-012**: System MUST include fixture tests for metric calculations, dataset validation and pass/fail decision logic.

### Key Entities

- **Evaluation Dataset**: Versioned collection of cases and global defaults used by the runner.
- **Evaluation Case**: One question with expected retrieval, answer/refusal expectations, filters and metadata.
- **Evaluation Run Configuration**: Captured runtime/configuration identity for reproducibility.
- **Evaluation Result**: Per-case retrieval, answer, citation, refusal, latency and error outcome.
- **Evaluation Report**: Aggregated metrics, baseline/candidate comparison and final gate decision.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A baseline report can be generated from a committed example dataset with no API contract changes.
- **SC-002**: The runner reports Recall@K, MRR, answer correctness, refusal correctness, citation correctness and latency buckets.
- **SC-003**: A candidate run is rejected when any configured critical threshold is missed.
- **SC-004**: Unanswered questions are mandatory in the example dataset and represented in aggregate refusal metrics.
- **SC-005**: Metric and decision logic are covered by pytest without requiring external LLM/provider calls.

## Assumptions

- The first implementation is backend/operator tooling only; no frontend screen is required.
- The runner can use mocked/stubbed answer evaluation in tests and real providers in manual runs.
- Dataset references prefer stable public source ids and chunk metadata over database integer ids.
- Reports are file artifacts under `reports/` or a caller-provided path, not persisted in PostgreSQL for the MVP.
- Existing search and answer services remain the behavior under evaluation.
