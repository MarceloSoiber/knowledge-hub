# Implementation Plan: Refinamento da Qualidade de Indexação e Recuperação RAG

**Branch**: `023-refinamento-qualidade-rag` | **Date**: 2026-09-04 | **Spec**: [spec.md](spec.md)

## Summary

Melhorar a qualidade do PDF já validado por meio de limpeza explicável de extração, chunking orientado por seção, avaliação reproduzível de recuperação, política calibrada de ausência de evidência e reindexação segura. O trabalho consolida planos existentes em uma sequência operacional, sem reinserir a fonte nem alterar a base antes de existir baseline e decisão de aceite.

## Evidence and Scope

Observações da validação que motivam o plano:

- Fonte indexada: `Fundamentos de IA e LLMs para Programadores.pdf`, 105 páginas, categoria Desenvolvimento de Software, tag IA e projeto Engenharia de Software em IA Aplicada.
- Consultas de domínio retornaram conteúdo tecnicamente pertinente para IA/ML/DL, RAG, embeddings, Transformer e Ollama.
- A extração contém ruído recorrente de página (`Público`), cabeçalhos e algumas palavras partidas.
- A consulta fora de escopo sobre férias/reembolso retornou chunks de IA com scores de aproximadamente 0,69–0,72.
- Uma consulta sobre IA/ML/DL trouxe primeiro um trecho genérico de apresentação antes da explicação conceitual.

## Technical Context

**Language/Version**: Python 3.13; TypeScript/Angular somente se uma visualização operacional for aprovada posteriormente.

**Primary Dependencies**: FastAPI, SQLAlchemy async, PostgreSQL/pgvector, Pydantic v2, FastMCP, pytest.

**Storage**: `document_sources`, `knowledge_chunks`, `embedding_batches`, `reindex_runs` e `reindex_items`; datasets e relatórios de avaliação em arquivos versionados.

**Testing**: `.venv/bin/python -m pytest`; execução manual do runner RAG contra ambiente controlado.

**Target Platform**: Backend Linux e CLI operacional; não exige mudança imediata de API ou frontend.

**Performance Goals**: Busca típica abaixo de 500 ms; registrar separadamente latência de embedding de consulta, recuperação e geração.

**Constraints**: Não registrar tokens ou texto completo em logs; não reindexar produção antes de baseline/candidato aprovados; preservar origem, seção e página para citação.

## Constitution Check

- **Qualidade e arquitetura**: aprovado. A limpeza fica em `services/documents`, a orquestração em `services`, e rotas/MCP permanecem finos.
- **Testes**: aprovado com gate. Transformação de PDF, chunking, ranking, ausência e reindexação devem ter testes determinísticos; provider real fica fora dos unit tests.
- **Performance**: aprovado com gate. Medir baseline antes/depois e não aceitar regressão acima do alvo.
- **UX**: aprovado. A primeira fase produz relatórios e comportamento seguro; controles de usuário só entram após calibração.
- **Dados**: aprovado com gate. A mudança de normalização altera hash/chunks; usar reindexação versionada e rollback, nunca atualização destrutiva manual.

## Delivery Sequence

### Phase 0 — Consolidar baseline e critérios de aceite

1. Reconciliar o estado implementado com as specs `006`, `007`, `011` e `013`; registrar o que já existe, o que ainda está Draft e quais contratos precisam permanecer compatíveis.
2. Criar um dataset privado/versionado de avaliação com, no mínimo:
   - cinco perguntas de domínio usadas na validação;
   - quatro paráfrases;
   - três perguntas fora do escopo, incluindo férias/reembolso;
   - referências estáveis por `source_public_id`, `chunk_index`, página/seção e pontos essenciais.
3. Executar baseline de busca vetorial atual, salvar relatório e definir thresholds de aceite por métrica, não por um único score.

**Gate**: Nenhuma limpeza, alteração de chunking ou threshold global é aplicada antes de o baseline ser revisado.

### Phase 1 — Qualidade da extração e chunking

1. Auditar `normalize_pdf_text()` e o chunker contra PDFs com cabeçalhos/rodapés repetidos e títulos estruturais.
2. Introduzir perfil de limpeza por documento PDF:
   - detectar linhas repetidas em páginas distintas e posições de cabeçalho/rodapé;
   - remover apenas padrões que excedam a frequência configurada;
   - normalizar hifenização/quebras de linha sem unir palavras legítimas;
   - manter contagem de remoções e proveniência sanitizada para auditoria.
3. Extrair seções de PDF por títulos como `Módulo` e `Capítulo`, propagando-as para `SectionSpan` e metadados do chunk.
4. Ajustar chunking para privilegiar fronteiras de seção/parágrafo e tamanho-alvo em tokens/caracteres, com sobreposição moderada, em vez de corte puramente posicional.
5. Criar testes de regressão usando um fixture sintético que reproduza `Público`, cabeçalhos e palavras partidas, sem versionar o PDF do usuário.

**Affected files**: `backend/app/services/documents/normalizer.py`, `chunker.py`, `extractors.py`, `ingestion.py`, `tests/test_document_*` e, se necessário, schema/proveniência de chunks.

### Phase 2 — Recuperação segura e explicável

1. Concluir/revisar `006-limite-relevancia`: threshold global e override validado em API, resposta RAG e MCP; em caso de vazio, a resposta deve declarar ausência.
2. Calibrar valores candidatos no dataset. O score observado de 0,69–0,72 fora de escopo é um sinal de partida, não um threshold universal.
3. Concluir/revisar `007-busca-hibrida`: GIN/FTS para termos exatos, busca vetorial para paráfrases e Reciprocal Rank Fusion para união de rankings.
4. Expor `match_reasons` somente em diagnóstico operacional e confirmar que categoria/projeto/filtros são aplicados antes da fusão.

**Gate**: Nenhuma configuração passa a padrão sem superar baseline em Recall@K/MRR e melhorar ou preservar recusas corretas.

### Phase 3 — Reindexação controlada e rollout

1. Concluir/revisar `011-reindexacao-backup` para produzir dry-run, contagens por fonte, reprocessamento idempotente, falhas isoladas e rollback documentado.
2. Executar reindexação candidata somente para a fonte Fundamentos de IA e LLMs, preservando a versão anterior até o aceite.
3. Executar o dataset contra o candidato, comparar com baseline e revisar manualmente os top-3 dos casos críticos.
4. Após aceite, ativar o conjunto refinado, monitorar telemetria sem queries sensíveis e manter plano de reversão para o batch anterior.

## Data Model / API Implications

- Preservar `DocumentSource.content_text` como texto normalizado usado para a versão ativa e manter identidade/hash de normalização explícitos para que uma mudança não pareça duplicata acidental.
- Os metadados de `KnowledgeChunk` devem continuar contendo `chunk_index`, página, seção e posições. Se seção de PDF passar a ser detectada, preencher o campo sem quebrar consumidores existentes.
- `SEARCH_MIN_SCORE` e `min_score` seguem a spec 006; não criar segunda configuração concorrente.
- A busca híbrida segue a spec 007 e mantém contratos API/MCP compatíveis por padrão.
- Não há mudança pública obrigatória nesta iniciativa além dos campos diagnósticos já planejados como opt-in.

## Test Strategy

- Unit tests: detecção de cabeçalho/rodapé, normalização de hifenização, seção de PDF, fronteiras/overlap de chunks e preservação de página.
- Service/repository tests: threshold, vazio seguro, fusão/deduplicação híbrida, filtros e motivos diagnósticos.
- Evaluation tests: validação do dataset, Recall@K, MRR, recusa correta, comparação baseline/candidato e decisão de aceite.
- Reindex tests: dry-run, idempotência, recuperação após falha e preservação de relações.
- Manual acceptance: executar o dataset no ambiente alvo, inspecionar resultados para as perguntas de domínio e fora de escopo, e medir latência.

## Risk Notes

- Limpeza agressiva pode remover conteúdo legítimo; a heurística precisa ser baseada em repetição por página e coberta por fixtures adversariais.
- Trocar normalização/chunking muda hashes e embeddings; a operação deve passar pelo fluxo de reindexação, não por SQL manual.
- Threshold alto pode ocultar conteúdo válido; baixo mantém falsos positivos. A calibração é iterativa e dependente do modelo de embedding.
- Busca híbrida adiciona custo e complexidade; só deve ser ativada após a medição mostrar ganho real nos casos de código/termos exatos sem regressão de paráfrases.
- A coleção ainda é pequena; as métricas iniciais são sinal de qualidade, não garantia estatística. O dataset deve crescer a cada fonte relevante.

## Complexity Tracking

Não há violação da constituição. Esta iniciativa coordena quatro capacidades já especificadas para impedir que mudanças de ingestão e recuperação sejam feitas isoladamente ou sem avaliação.
