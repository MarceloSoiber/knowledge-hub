# Quickstart: Limite Minimo de Relevancia

## 1. Configure default threshold

Add or update `.env`:

```bash
SEARCH_MIN_SCORE=0.35
```

## 2. Run tests

```bash
.venv/bin/python -m pytest tests/test_knowledge_service.py tests/test_knowledge_api_integration.py tests/test_mcp_knowledge.py
```

## 3. Validate API search

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"pergunta fora da base","limit":5,"min_score":0.35}'
```

Expected behavior: low-score chunks are absent; `results` may be empty.

## 4. Validate answer behavior

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"pergunta fora da base","limit":5,"min_score":0.35}'
```

Expected behavior: when no source passes the threshold, `sources` is empty and the answer declares absence of information.

## 5. Calibration checklist

- Prepare relevant and irrelevant questions for each domain.
- Record only scores and aggregate counts, not sensitive question text.
- Measure false positives and false negatives.
- Recalibrate after changing embedding model or chunking strategy.
