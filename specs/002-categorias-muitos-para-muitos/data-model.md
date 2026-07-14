# Data Model: Categorias Muitos-Para-Muitos

## Category

- `id`: integer primary key.
- `name`: required normalized string, max 100 chars, unique case-insensitively.
- `created_at`: timezone-aware creation timestamp.
- Relationships: many document sources through `document_source_categories`.

## DocumentSource

- `id`, `title`, `source_type`, `uri`, `created_at`: existing source fields.
- Relationships: many categories through `document_source_categories`; many chunks through `knowledge_chunks`.
- Validation: a source must have at least one category at ingestion time.

## DocumentSourceCategory

- `document_source_id`: foreign key to `document_sources.id`, cascade on source delete.
- `category_id`: foreign key to `categories.id`.
- Primary key: (`document_source_id`, `category_id`).
- Deleting a category in use is refused by service/API before database delete.

## Migration Rules

- Create association table if missing.
- Copy each existing `document_sources.category_id` value into the association table.
- Ensure uncategorized fallback exists for any legacy row without a category.
- Drop legacy `document_sources.category_id` after association data exists.
- Re-running initialization must not duplicate associations or fail.
