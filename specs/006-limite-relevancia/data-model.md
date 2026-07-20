# Data Model: Limite Minimo de Relevancia

## ResolvedSearchThreshold

Operational value, not persisted.

| Field | Type | Source | Validation |
|-------|------|--------|------------|
| `value` | `float` | request `min_score` or `Settings.search_min_score` | `0.0 <= value <= 1.0` |
| `source` | `"request" | "settings"` | service resolution | derived |

## SearchResultScore

Existing value on `KnowledgeChunkRead`.

| Field | Type | Notes |
|-------|------|-------|
| `score` | `float | None` | Computed as `1 - cosine_distance`; used for ranking/filtering, not a probability. |

## SearchTelemetryEvent

Structured log event, not persisted.

| Field | Type | Notes |
|-------|------|-------|
| `threshold` | `float` | Effective threshold used for the request. |
| `threshold_source` | `str` | `request` or `settings`. |
| `raw_count` | `int` | Number of candidates returned before filtering. |
| `filtered_count` | `int` | Number of candidates returned after filtering. |
| `min_score` | `float | None` | Minimum valid raw score, when any. |
| `max_score` | `float | None` | Maximum valid raw score, when any. |

## Persistence

No database changes. Existing `KnowledgeChunk` embeddings and returned `KnowledgeChunkRead.score` are sufficient.
