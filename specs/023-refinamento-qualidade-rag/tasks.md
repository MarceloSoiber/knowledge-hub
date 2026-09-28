# Tasks: Refinamento da Qualidade de Indexação e Recuperação RAG

**Input**: [spec.md](spec.md) e [plan.md](plan.md)

**Dependencies**: Reconciliar as specs `006-limite-relevancia`, `007-busca-hibrida`, `011-reindexacao-backup` e `013-avaliacao-rag` antes de qualquer mudança de comportamento.

## Phase 1: Baseline e preparação

- [x] T001 Inventariar implementação versus specs 006, 007, 011 e 013 em `specs/023-refinamento-qualidade-rag/implementation-status.md` e marcar decisões/débitos sem duplicar contratos.
- [x] T002 [P] Criar dataset de avaliação sanitizado em `evaluation/fundamentos-ia-rag.example.json` com perguntas de domínio, paráfrases e perguntas sem resposta, usando referências estáveis de fonte/chunk.
- [ ] T003 [US3] Executar e armazenar baseline com o runner de `backend/app/cli/evaluate_rag.py` (ou implementar o runner conforme spec 013 caso ainda não exista).
- [ ] T004 [US3] Definir critérios de aceite de Recall@K, MRR, recusa correta e latência em `evaluation/thresholds.*` com justificativa baseada no baseline.

**Checkpoint**: baseline revisado; nenhuma alteração na base ativa.

## Phase 2: User Story 1 — Conteúdo limpo e chunks pertinentes (P1)

**Goal**: reduzir ruído de PDF e tornar chunks estruturalmente coerentes.

- [x] T005 [P] [US1] Criar fixtures sintéticos de PDF/texto com cabeçalho/rodapé repetido, títulos de módulo/capítulo e hifenização em `tests/test_document_quality.py`.
- [x] T006 [P] [US1] Escrever testes de normalização e preservação de página em `tests/test_document_quality.py`.
- [x] T007 [US1] Implementar detecção explicável de cabeçalho/rodapé repetido em `backend/app/services/documents/normalizer.py`.
- [x] T008 [US1] Integrar limpeza por página em `backend/app/services/documents/extractors.py`, preservando `PageSpan` correto após a transformação.
- [x] T009 [P] [US1] Escrever testes de fronteiras de seção e chunking em `tests/test_document_quality.py`.
- [x] T010 [US1] Estender detecção de seções para títulos de PDF em `backend/app/services/documents/chunker.py` e propagar seção para `metadata_json` em `backend/app/services/ingestion.py`.
- [x] T011 [US1] Ajustar a estratégia de chunking para respeitar seção/parágrafo, tamanho-alvo e overlap, mantendo localizações citáveis.
- [ ] T012 [US1] Rodar avaliação search-only contra corpus candidato e revisar manualmente os top-3 das cinco perguntas de domínio.

**Checkpoint**: não há ruído repetitivo no fixture; perguntas de domínio atingem o critério de top-3.

## Phase 3: User Story 2 — Ausência segura e recuperação explicável (P2)

**Goal**: impedir que chunks de IA sejam usados como evidência para perguntas sem cobertura.

- [x] T013 [US2] Revisar o estado de `SEARCH_MIN_SCORE`, `min_score` em API/MCP e vazio seguro contra `specs/006-limite-relevancia/spec.md`.
- [ ] T014 [P] [US2] Cobrir threshold, score não finito, lista vazia e resposta de ausência em `tests/test_knowledge_service.py`, `tests/test_knowledge_api_integration.py` e `tests/test_mcp_knowledge.py`.
- [ ] T015 [US2] Implementar os itens pendentes da spec 006 em `backend/app/services/search.py`, `backend/app/services/rag.py`, schemas/rotas e ferramentas MCP correspondentes.
- [ ] T016 [US2] Calibrar thresholds candidatos contra dataset, incluindo a pergunta de férias/reembolso, e registrar a decisão em `doc/OPERATIONS.md`.
- [x] T017 [US2] Revisar o estado da spec 007: recuperação textual + vetorial, fusão RRF, deduplicação e `match_reasons` opt-in já estão em `backend/app/repositories/chunks.py` e `backend/app/services/search.py`.
- [ ] T018 [US2] Executar avaliação de perguntas exatas, paráfrases e fora de escopo; manter a mudança somente se preservar casos semânticos e reduzir falsos positivos.
- [x] T029 [US2] Preservar, em `backend/app/services/search.py`, resultado híbrido abaixo do threshold somente quando a frase distintiva consultada ocorrer literalmente no chunk; cobrir o caso `ollama pull` e uma correspondência textual parcial em `tests/test_knowledge_service.py`.

**Checkpoint**: perguntas sem resposta não retornam evidência; perguntas válidas continuam recuperáveis.

## Phase 4: User Story 3 — Avaliação, reindexação e rollout (P3)

**Goal**: aplicar somente a configuração vencedora de maneira recuperável.

- [x] T019 [US3] Revisar runner, relatório e comparação descritos em `specs/013-avaliacao-rag/`; já implementados em `backend/app/services/evaluation.py` e `backend/app/cli/evaluate_rag.py`.
- [x] T020 [US3] Revisar dry-run, reindexação idempotente e retomada descritos em `specs/011-reindexacao-backup/`; já implementados em `backend/app/services/reindex.py` e `backend/app/cli/reindex.py`.
- [ ] T021 [US3] Executar dry-run filtrado para `Fundamentos de IA e LLMs para Programadores.pdf`; registrar contagens, dimensão, versão e riscos sem expor conteúdo integral.
- [ ] T022 [US3] Reindexar a fonte candidata preservando batch anterior e suas relações de categoria, tags e projeto.
- [ ] T023 [US3] Comparar relatório candidato versus baseline e obter aceite explícito antes de ativar/reutilizar a configuração refinada.
- [ ] T024 [US3] Documentar rollout, monitoramento e rollback em `doc/OPERATIONS.md`.

## Phase 5: Verificação final

- [ ] T025 Executar `.venv/bin/python -m pytest` para a suíte alterada e os testes de avaliação/reindexação.
- [ ] T026 Executar lint nos arquivos Python alterados e validar `git diff --check`.
- [ ] T027 Atualizar `doc/API.md` somente se a implementação expuser ou alterar contratos públicos de busca/diagnóstico.
- [ ] T028 Anexar ao PR o relatório baseline/candidato, os casos regressivos revisados e a decisão de aceite.

## Execution Order

`T001–T004` bloqueiam todas as mudanças de qualidade. `T005–T012` e `T013–T018` podem avançar em paralelo após o baseline, mas ambos precisam concluir antes de `T019–T024`. Reindexação e rollout só começam após avaliação aprovada.
