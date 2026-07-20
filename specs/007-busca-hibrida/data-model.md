# Data Model: Busca Hibrida

## KnowledgeChunk Changes

Existing table: `knowledge_chunks`

| Field | Type | Source | Rules |
| --- | --- | --- | --- |
| `search_vector` | `tsvector` | derived from `content` | NOT user editable; backfilled for existing chunks; indexed with GIN |

Existing fields reused:

| Field | Purpose |
| --- | --- |
| `id` | Deduplication key across vector and text candidates |
| `source_id` | Join to `document_sources` for citation metadata and category filtering |
| `content` | Text indexed by full-text search |
| `embedding` | Existing vector retrieval path |
| `metadata_json` | Existing citation location and public metadata |

## HybridSearchCandidate

Internal service object, not persisted.

| Field | Type | Rules |
| --- | --- | --- |
| `chunk` | `KnowledgeChunkRead` | Built through the existing repository mapper |
| `chunk_id` | `int` | Deduplication key |
| `vector_rank` | `int | None` | 1-based rank from vector candidate list |
| `text_rank` | `int | None` | 1-based rank from text candidate list |
| `vector_score` | `float | None` | Existing cosine-derived similarity score |
| `text_score` | `float | None` | PostgreSQL text rank for diagnostics/tie-breaks only |
| `rrf_score` | `float` | Internal rank-fusion score |
| `match_reasons` | `list[str]` | Contains `vector`, `text`, or both |

## Public Response Compatibility

Default `KnowledgeChunkRead` remains:

| Field | Behavior |
| --- | --- |
| `score` | Existing vector similarity when candidate has vector match; text-only behavior must be documented before release |
| `metadata` | Existing public metadata only |
| `location` | Existing citation location |

Optional diagnostics may add:

| Field | Type | Rule |
| --- | --- | --- |
| `match_reasons` | `list[str]` | Present only when explicitly requested; values are stable strings such as `vector` and `text` |

## Relationships

- `KnowledgeChunk.search_vector` is derived from `KnowledgeChunk.content`.
- Candidate retrieval joins `KnowledgeChunk -> DocumentSource -> categories` exactly as the current vector search does.
- Category filters apply through `document_source_categories` before vector/text candidate limits.
