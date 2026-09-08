# Feature Specification: Refinamento da Qualidade de Indexação e Recuperação RAG

**Feature Branch**: `023-refinamento-qualidade-rag`

**Created**: 2026-09-04

**Status**: Draft

**Input**: Validação do PDF "Fundamentos de IA e LLMs para Programadores" indexado no Knowledge Hub.

## User Scenarios & Testing

### User Story 1 - Recuperar contexto limpo e pertinente (Priority: P1)

Como usuária da base, quero que perguntas sobre o material retornem trechos do capítulo pertinente, sem cabeçalhos repetidos, texto quebrado ou abertura genérica do curso ocupando as primeiras posições.

**Why this priority**: A validação mostrou recuperação conceitualmente correta, mas também ruído recorrente (`Público`) e um trecho promocional acima da explicação técnica para a pergunta sobre IA, ML e Deep Learning.

**Independent Test**: Indexar um PDF de amostra com cabeçalho/rodapé repetido e títulos de módulo/capítulo, buscar por cinco conceitos conhecidos e confirmar que os trechos esperados ficam entre os três primeiros sem o cabeçalho repetido.

**Acceptance Scenarios**:

1. **Given** um PDF cujo cabeçalho ou rodapé se repete em muitas páginas, **When** ele é ingerido, **Then** esse ruído não aparece nos chunks nem influencia a recuperação.
2. **Given** um documento com títulos de módulo e capítulo, **When** ele é dividido em chunks, **Then** cada chunk preserva a seção correspondente e não mistura conteúdo de capítulos não relacionados quando houver uma fronteira adequada.
3. **Given** perguntas conhecidas sobre IA, RAG, embeddings, Transformer e Ollama, **When** a busca é executada, **Then** o resultado esperado aparece nos três primeiros resultados e contém conteúdo técnico pertinente.

---

### User Story 2 - Declarar ausência de conhecimento (Priority: P2)

Como usuária, quero que uma pergunta fora do escopo indexado não receba trechos aleatórios como se fossem evidência.

**Why this priority**: A pergunta sobre férias e reembolso retornou chunks de IA com scores entre 0,68 e 0,72, embora a base não possua esse assunto.

**Independent Test**: Executar perguntas deliberadamente fora do corpus e confirmar que a busca retorna lista vazia, e que a resposta RAG declara ausência de contexto em vez de inferir uma resposta.

**Acceptance Scenarios**:

1. **Given** uma pergunta sem cobertura documental, **When** nenhum candidato atingir o critério calibrado de relevância, **Then** a busca retorna vazia.
2. **Given** uma pergunta com termos exatos ou uma paráfrase válida, **When** a recuperação é refinada, **Then** o filtro de ausência não descarta o chunk correto.
3. **Given** um resultado retornado ao cliente, **When** o diagnóstico é solicitado, **Then** é possível identificar os sinais de recuperação que justificaram sua posição, sem expor conteúdo adicional desnecessário.

---

### User Story 3 - Evoluir a qualidade sem regressão (Priority: P3)

Como mantenedor, quero comparar o corpus atual com uma versão refinada antes de reindexá-lo em produção, para aprovar mudanças por evidência e poder voltar atrás se houver regressão.

**Why this priority**: Limpeza, novo chunking, threshold e busca híbrida alteram os embeddings e rankings; sem baseline, a decisão seria subjetiva.

**Independent Test**: Rodar o conjunto versionado de consultas contra baseline e candidato, incluindo perguntas sem resposta, e produzir um relatório comparável com métricas e casos regressivos.

**Acceptance Scenarios**:

1. **Given** um conjunto de avaliação versionado, **When** o baseline atual é executado, **Then** o relatório registra Recall@K, MRR, taxa de recusa correta, latência e a configuração usada.
2. **Given** a versão refinada do corpus, **When** ela é comparada ao baseline, **Then** a mudança só é aceita se atender aos thresholds definidos e não reduzir os casos críticos conhecidos.
3. **Given** uma reindexação aprovada, **When** ela falha ou é interrompida, **Then** é possível retomá-la ou manter a versão ativa anterior sem perder a fonte nem suas relações.

### Edge Cases

- Um termo repetido pode ser conteúdo legítimo; a limpeza deve remover apenas padrões de cabeçalho/rodapé comprovadamente repetitivos, nunca palavras por uma lista fixa.
- PDFs escaneados, páginas vazias e OCR de baixa qualidade devem continuar no fluxo de extração atual e registrar diagnóstico sanitizado quando a qualidade for insuficiente.
- Títulos de capítulo no meio de um parágrafo não podem causar corte arbitrário ou perda de localização de página.
- Scores de similaridade não são probabilidades e devem ser calibrados por dataset/modelo de embedding.
- Perguntas fora da base podem compartilhar vocabulário com o corpus; apenas threshold fixo não é garantia suficiente e a avaliação deve cobrir esses casos adversariais.
- Reindexação não pode duplicar fontes, chunks, tags, categorias ou vínculos de projeto.

## Requirements

### Functional Requirements

- **FR-001**: System MUST normalizar texto de PDF antes de calcular o hash, criar chunks e embeddings, preservando texto legível e localização por página.
- **FR-002**: System MUST detectar e remover somente cabeçalhos/rodapés repetitivos validados por frequência e posição de página.
- **FR-003**: System MUST usar títulos estruturais de documentos para orientar chunking e registrar seção/página em cada chunk recuperável.
- **FR-004**: System MUST manter o texto original preservado ou uma trilha de proveniência suficiente para reindexação e auditoria.
- **FR-005**: System MUST manter um dataset de avaliação com perguntas conhecidas e sem resposta, incluindo os casos observados nesta validação.
- **FR-006**: System MUST aplicar uma política de ausência de evidência consistente em API, resposta RAG e MCP, com threshold calibrado e comportamento seguro de lista vazia.
- **FR-007**: System MUST avaliar busca híbrida/reranking como evolução controlada da busca vetorial, sem substituir a recuperação semântica sem comparação de métricas.
- **FR-008**: System MUST permitir reindexação segura, idempotente e reversível do corpus refinado após a aprovação do candidato.
- **FR-009**: System MUST documentar o procedimento operacional de avaliação, reindexação e rollback, sem registrar tokens ou conteúdo completo em logs.
- **FR-010**: System MUST preservar um resultado abaixo do threshold vetorial quando a consulta distintiva ocorrer literalmente no chunk e a busca textual também o tiver recuperado; correspondências textuais parciais continuam sujeitas ao threshold normal.

### Key Entities

- **Perfil de limpeza de PDF**: Regras explicáveis de normalização e remoção de padrões repetitivos aplicadas antes da indexação.
- **Chunk com proveniência**: Trecho indexado com conteúdo limpo, seção, página, posição e identidade da configuração de embedding.
- **Caso de avaliação RAG**: Pergunta versionada com expectativa de recuperação, ausência ou resposta sustentada.
- **Baseline/Candidato de recuperação**: Relatórios comparáveis usados para aprovar ou reprovar uma mudança de qualidade.
- **Execução de reindexação**: Processo rastreável que aplica a configuração aprovada às fontes sem duplicação.

## Success Criteria

### Measurable Outcomes

- **SC-001**: O conjunto inicial de cinco perguntas de domínio retorna o trecho esperado no top 3 em pelo menos 90% dos casos.
- **SC-002**: Todas as perguntas sem resposta do conjunto inicial retornam lista vazia ou recusa fundamentada; nenhuma deve encaminhar chunks como evidência para a resposta.
- **SC-003**: O texto de teste não contém ocorrências de cabeçalho/rodapé repetitivo nos chunks, exceto quando o termo fizer parte do conteúdo do capítulo.
- **SC-004**: A versão candidata iguala ou melhora Recall@K e MRR do baseline e não piora a taxa de recusa correta.
- **SC-005**: A recuperação típica continua dentro de 500 ms no corpus de referência, conforme a constituição do projeto.

## Assumptions

- O PDF validado permanece uma fonte de referência para o dataset inicial, sem que seu conteúdo integral seja versionado no repositório.
- As especificações existentes `006-limite-relevancia`, `007-busca-hibrida`, `011-reindexacao-backup` e `013-avaliacao-rag` serão reutilizadas e reconciliadas, não duplicadas.
- A primeira entrega é operacional/backend; interface para configurar critérios avançados fica fora do escopo até que a calibração seja validada.
- A aprovação de um threshold inicial ocorrerá por dados de avaliação, e não por interpretação de scores isolados.
