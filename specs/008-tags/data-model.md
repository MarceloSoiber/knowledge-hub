# Data Model: Tags

## Tag

New table: `tags`

| Field | Type | Rules |
| --- | --- | --- |
| `id` | integer | Primary key |
| `name` | string(100) | Public tag label for v1; normalized, non-empty |
| `normalized_name` | string(100) | Unique lookup key; trim/lowercase/accent-insensitive |
| `created_at` | timestamptz | Server default `now()` |

Indexes/constraints:

- Unique constraint on `normalized_name`.
- Optional prefix lookup index for autocomplete if needed after testing.

## DocumentSourceTag

New association table: `document_source_tags`

| Field | Type | Rules |
| --- | --- | --- |
| `document_source_id` | integer | FK to `document_sources.id`, cascade on source delete |
| `tag_id` | integer | FK to `tags.id` |

Constraints:

- Composite primary key `(document_source_id, tag_id)`.
- Index on `tag_id` for reverse lookup and in-use checks.

## DocumentSource Changes

Existing table: `document_sources`

| Field/Relationship | Behavior |
| --- | --- |
| `tags` | Many-to-many relationship through `document_source_tags`; optional |
| `categories` | Existing controlled broad classification; remains mandatory for ingestion |
| `content_hash` | Unchanged when only tags change |
| `chunks` | Not regenerated when only tags change |

## KnowledgeChunk Read Model Changes

Persisted `knowledge_chunks` table does not need a tag column.

Public read payload gains:

| Field | Type | Rule |
| --- | --- | --- |
| `tags` | `list[TagRead]` | Derived from chunk source, sorted by name |

## Request Models

| Model | New Field | Rule |
| --- | --- | --- |
| `KnowledgeTextIngestRequest` | `tag_ids: list[int] | None` | Optional; no duplicates; ids must exist |
| `KnowledgeUploadRequest` | `tag_ids: list[int] | None` | Optional repeated multipart field |
| `KnowledgeSourcePatchRequest` | `tag_ids: list[int] | None` | Optional; empty list clears tags if explicitly allowed by implementation |
| `KnowledgeSearchRequest` | `tag_ids: list[int] | None` | Optional filter; empty list invalid |
| `KnowledgeAnswerRequest` | `tag_ids: list[int] | None` | Optional filter; empty list invalid |

## Relationships

- One `Tag` can be associated with many `DocumentSource` records.
- One `DocumentSource` can have many tags and must keep one or more categories.
- Search joins `KnowledgeChunk -> DocumentSource -> document_source_tags` only when tag filters or tag serialization require it.
- Category and tag filters combine by requiring a source to satisfy both filter dimensions when both are present.
