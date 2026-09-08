# Status de implementação — Refinamento da Qualidade RAG

**Atualizado**: 2026-09-08

## Entregue no código

| Capacidade | Estado | Evidência |
|---|---|---|
| Limite de relevância e ausência segura | Entregue | `backend/app/services/search.py`, API e MCP aceitam `min_score`; a lista pode ficar vazia. |
| Busca híbrida e diagnóstico | Entregue | Busca FTS + vetorial com RRF, deduplicação e `match_reasons` opt-in. |
| Runner de avaliação | Entregue | `rag-eval`, schemas, métricas, relatórios e comparador. |
| Reindexação de embeddings | Entregue | `reindex-embeddings` com dry-run, filtros, retomada e contadores. |
| Limpeza de PDF por margens repetitivas | Entregue | `normalize_pdf_pages()` remove apenas marcadores repetidos em margens de três ou mais páginas. |
| Seções e fronteiras de chunk | Entregue | Módulos/capítulos de PDF são detectados e chunks não atravessam a seção. |
| Dataset deste corpus | Entregue | `evaluation/fundamentos-ia-rag.example.json`. |

## Pendente de operação no ambiente alvo

1. Copiar os arquivos `evaluation/fundamentos-ia-*.example.json` para arquivos locais sem o sufixo `.example`.
2. Executar baseline da fonte atualmente indexada e registrar o relatório fora do Git.
3. Implantar a versão que contém a limpeza de PDF.
4. Enviar novamente o PDF original como fonte candidata. **Não use apenas `reindex-embeddings`**: esse comando refaz vetores dos chunks existentes e não reextrai o PDF.
5. Executar candidato, comparar com baseline e revisar os casos regressivos.
6. Somente após aceite, excluir/arquivar a fonte antiga para não haver resultados duplicados.

## Decisão de calibração

O score observado em pergunta fora de escopo foi aproximadamente 0,69–0,72. Ele não é probabilidade nem threshold universal. O dataset começa sem `min_score` global para registrar o baseline; o valor padrão só deve ser alterado após a comparação de relatórios.
