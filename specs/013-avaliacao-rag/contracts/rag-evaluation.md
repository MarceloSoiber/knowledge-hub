# Contract: RAG Evaluation Runner

## CLI

### `rag-eval baseline`

Runs the dataset against the current implementation and writes a baseline report.

```bash
rag-eval baseline \
  --dataset evaluation/rag-dataset.example.json \
  --thresholds evaluation/thresholds.example.json \
  --output reports/rag-baseline.json
```

Required:

- `--dataset`: JSON dataset path.
- `--output`: report path.

Optional:

- `--thresholds`: threshold config path.
- `--search-only`: skip answer generation and answer/citation grading.
- `--limit`: override retrieval limit.
- `--min-score`: override search threshold.

### `rag-eval candidate`

Runs the dataset against a candidate implementation/configuration.

```bash
rag-eval candidate \
  --dataset evaluation/rag-dataset.example.json \
  --thresholds evaluation/thresholds.example.json \
  --output reports/rag-candidate.json
```

### `rag-eval compare`

Compares two saved reports and applies thresholds.

```bash
rag-eval compare \
  --baseline reports/rag-baseline.json \
  --candidate reports/rag-candidate.json \
  --thresholds evaluation/thresholds.example.json \
  --output reports/rag-comparison.json
```

Exit behavior:

- Exit code `0` when the candidate passes all critical thresholds.
- Exit code `1` when the candidate fails any critical threshold.
- Exit code `2` for invalid input, missing files or malformed reports.

### `rag-eval summarize`

Prints a compact review summary for one report.

```bash
rag-eval summarize --report reports/rag-candidate.json
```

## Dataset JSON Shape

```json
{
  "dataset_version": "rag-eval-v1",
  "description": "Small non-sensitive RAG evaluation dataset",
  "defaults": {
    "limit": 5,
    "min_score": 0.35
  },
  "cases": [
    {
      "id": "known-answer-001",
      "kind": "known_answer",
      "question": "Which runbook command creates the HNSW index?",
      "expected_chunks": [
        {
          "source_public_id": "00000000-0000-0000-0000-000000000000",
          "chunk_index": 3,
          "snippet": "knowledge-hnsw create"
        }
      ],
      "expected_answer_points": ["knowledge-hnsw create"],
      "expected_refusal": false
    },
    {
      "id": "unanswered-001",
      "kind": "unanswered",
      "question": "What is the private payroll number of the project owner?",
      "expected_refusal": true
    }
  ]
}
```

## Report JSON Shape

```json
{
  "report_version": "1",
  "created_at": "2026-07-21T00:00:00Z",
  "run_config": {
    "dataset_version": "rag-eval-v1",
    "dataset_hash": "sha256:...",
    "git_revision": "abc123",
    "retrieval_limit": 5,
    "min_score": 0.35,
    "embedding_model": "text-embedding-...",
    "embedding_version": "default",
    "llm_model": "gpt-...",
    "mode": "baseline"
  },
  "metrics": {
    "recall_at_k": 1.0,
    "mrr": 1.0,
    "answer_correct_rate": 1.0,
    "refusal_correct_rate": 1.0,
    "citation_correct_rate": 1.0,
    "search_latency_p95_ms": 120.0
  },
  "decision": "passed",
  "failures": [],
  "case_results": []
}
```
