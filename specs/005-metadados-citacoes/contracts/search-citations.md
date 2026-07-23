# Search and Answer Citation Contract

`POST /api/v1/knowledge/search` and `POST /api/v1/knowledge/answer` keep their request payloads unchanged.

Each returned chunk result MUST include:

```json
{
  "id": 30,
  "source_id": "33333333-3333-4333-8333-333333333333",
  "source_title": "onboarding-guide.pdf",
  "source_type": "upload",
  "uri": "upload:onboarding-guide.pdf",
  "categories": [{"id": 4, "name": "docs"}],
  "location": {
    "chunk_index": 2,
    "page": 5,
    "section": "Instalacao",
    "start_char": 1200,
    "end_char": 1840
  },
  "content": "Trecho encontrado...",
  "score": 0.87,
  "metadata": {}
}
```

`source_id` is the public UUID for the source. Internal integer source IDs MUST NOT be exposed in search or answer results.

`metadata` MUST contain only allowlisted public keys.
