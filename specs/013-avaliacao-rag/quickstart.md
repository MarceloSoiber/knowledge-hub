# Quickstart: Avaliacao do RAG

## 1. Preparar dataset

Crie ou atualize `evaluation/rag-dataset.example.json` com casos sem dados pessoais sensiveis:

- perguntas com resposta conhecida;
- perguntas com termos exatos;
- perguntas semanticas;
- perguntas deliberadamente sem resposta;
- referencias esperadas por `source_public_id` e `chunk_index` quando possivel.

## 2. Rodar baseline

```bash
rag-eval baseline \
  --dataset evaluation/rag-dataset.example.json \
  --thresholds evaluation/thresholds.example.json \
  --output reports/rag-baseline.json
```

## 3. Rodar candidato

Aplique a mudanca candidata, como novo threshold, busca hibrida, HNSW, chunking ou modelo de embedding, entao rode:

```bash
rag-eval candidate \
  --dataset evaluation/rag-dataset.example.json \
  --thresholds evaluation/thresholds.example.json \
  --output reports/rag-candidate.json
```

## 4. Comparar

```bash
rag-eval compare \
  --baseline reports/rag-baseline.json \
  --candidate reports/rag-candidate.json \
  --thresholds evaluation/thresholds.example.json \
  --output reports/rag-comparison.json
```

Mudancas de recuperacao so devem ser aceitas quando a comparacao passar os limites configurados e os casos regressivos forem revisados.

## 5. Verificar testes

```bash
.venv/bin/python -m pytest tests/test_rag_evaluation_metrics.py tests/test_rag_evaluation_runner.py
```

Os testes devem usar fixtures/mocks e nao depender de chamadas reais a embeddings ou LLM.
