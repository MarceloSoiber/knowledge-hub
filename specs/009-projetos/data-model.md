# Data Model: Projetos

## Project

New table: `projects`

| Field | Type | Rules |
| --- | --- | --- |
| `id` | integer | Primary key |
| `name` | string(150) | Public name, normalized for v1 |
| `normalized_name` | string(150) | Unique lookup key |
| `description` | text/null | Optional human description |
| `status` | string(32) | `active` or `archived` |
| `created_at` | timestamptz | Server default `now()` |
| `updated_at` | timestamptz | Server default `now()`, updated on changes |

Indexes/constraints:

- Unique constraint or unique index on `normalized_name`.
- Optional index on `status` if status-filtered listing needs it.

## DocumentSourceProject

New association table: `document_source_projects`

| Field | Type | Rules |
| --- | --- | --- |
| `document_source_id` | integer | FK to `document_sources.id`, cascade on source delete |
| `project_id` | integer | FK to `projects.id` |

Constraints:

- Composite primary key `(document_source_id, project_id)`.
- Index on `project_id` for project source listing and filters.

## DocumentSource Changes

Existing table: `document_sources`

| Field/Relationship | Behavior |
| --- | --- |
| `projects` | Many-to-many relationship through `document_source_projects`; optional |
| `categories` | Existing controlled broad classification; remains mandatory for ingestion |
| `tags` | Existing granular markers; optional |
| `content_hash` | Unchanged when only projects change |
| `chunks` | Not regenerated when only projects change |

## KnowledgeChunk Read Model Changes

Persisted `knowledge_chunks` table does not need a project column.

Public read payload gains:

| Field | Type | Rule |
| --- | --- | --- |
| `projects` | `list[ProjectRead]` | Derived from chunk source, sorted by name |

## Request Models

| Model | New Field | Rule |
| --- | --- | --- |
| `KnowledgeTextIngestRequest` | `project_ids: list[int] | None` | Optional; no duplicates; ids must exist |
| `KnowledgeUploadRequest` | `project_ids: list[int] | None` | Optional repeated multipart field |
| `KnowledgeSourcePatchRequest` | `project_ids: list[int] | None` | Optional; empty list clears projects |
| `KnowledgeSearchRequest` | `project_ids: list[int] | None` | Optional filter; empty list invalid |
| `KnowledgeAnswerRequest` | `project_ids: list[int] | None` | Optional filter; empty list invalid |

## Relationships

- One `Project` can be associated with many `DocumentSource` records.
- One `DocumentSource` can have many projects, many tags and one or more categories.
- Search joins `KnowledgeChunk -> DocumentSource -> document_source_projects` only when project filters or project serialization require it.
- Project, category and tag filters combine by requiring a source to satisfy every provided filter dimension.
