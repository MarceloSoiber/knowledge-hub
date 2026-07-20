# Contract: Hybrid Search

## API Search

`POST /api/v1/knowledge/search`

Existing request fields remain supported:

```json
{
  "query": "ERR_CONN_RESET",
  "limit": 5,
  "category_ids": [1],
  "min_score": 0.35
}
```

Optional diagnostic request field, if implemented:

```json
{
  "query": "ERR_CONN_RESET",
  "limit": 5,
  "include_match_reasons": true
}
```

Default response remains compatible:

```json
{
  "query": "ERR_CONN_RESET",
  "limit": 5,
  "results": [
    {
      "id": 10,
      "source_id": "4d2eb6ec-64ff-4c72-8fb7-08fb5c6f33ab",
      "source_title": "Logs de rede",
      "source_type": "text",
      "uri": "text:Logs de rede",
      "categories": [{"id": 1, "name": "infra"}],
      "location": {
        "chunk_index": 0,
        "page": null,
        "section": null,
        "start_char": 0,
        "end_char": 120
      },
      "content": "Falha observada: ERR_CONN_RESET ao chamar o gateway.",
      "score": 0.71,
      "metadata": {}
    }
  ]
}
```

Diagnostic response may include `match_reasons` per result:

```json
{
  "id": 10,
  "match_reasons": ["vector", "text"]
}
```

## API Answer

`POST /api/v1/knowledge/answer`

- Uses the same hybrid retrieval path as `/search`.
- Existing request fields remain supported.
- If `include_match_reasons` is added, sources may include the same optional diagnostics as search results.

## MCP Search

Tool signature remains compatible:

```python
search_knowledge(
    query: str,
    limit: int = 5,
    category_ids: list[int] | None = None,
    min_score: float | None = None,
) -> list[KnowledgeHit]
```

Optional diagnostic parameter, if implemented:

```python
include_match_reasons: bool = False
```

## Ranking Semantics

- Final ordering is hybrid and rank-fused.
- Public `score` remains a vector similarity signal when present.
- RRF score is internal by default and MUST NOT be documented as probability.
- Results MUST NOT contain duplicate chunk ids.
