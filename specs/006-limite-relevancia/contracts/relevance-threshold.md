# Contract: Relevance Threshold

## API Search

`POST /api/v1/knowledge/search`

### Request

```json
{
  "query": "Como configuro o MCP?",
  "limit": 5,
  "category_ids": [2],
  "min_score": 0.35
}
```

- `min_score` is optional.
- When omitted, the server uses `SEARCH_MIN_SCORE`.
- Valid range: `0.0` through `1.0`.
- Invalid values return FastAPI/Pydantic validation errors.

### Response

Response shape is unchanged. `results` may contain fewer than `limit` items or be empty.

```json
{
  "query": "Como configuro o MCP?",
  "limit": 5,
  "results": []
}
```

## API Answer

`POST /api/v1/knowledge/answer`

### Request

```json
{
  "query": "Como configuro o MCP?",
  "limit": 5,
  "category_ids": [2],
  "min_score": 0.35
}
```

`min_score` follows the same rules as API search.

### Response

Response shape is unchanged. When no sources pass the threshold, `sources` is empty and the answer should declare that the information was not found.

## MCP Search Tool

`search_knowledge(query: str, limit: int = 5, category_ids: list[int] | None = None, min_score: float | None = None)`

- `min_score` is optional and validated in the same range as the API.
- Results use the existing `KnowledgeHit` contract.
- The registered FastMCP `search` tool exposes the same `min_score` argument and forwards it to the backend search service.

## Configuration

`SEARCH_MIN_SCORE=0.35`

The default is intentionally conservative and should be calibrated per domain and after embedding model changes. Treat the score as a similarity ranking signal, not as a probability.
