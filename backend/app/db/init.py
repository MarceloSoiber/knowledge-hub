from sqlalchemy import text

from .base import Base
from .models import AppConfig, Category, DocumentSource, KnowledgeChunk  # noqa: F401
from .session import engine


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text("ALTER TABLE document_sources DROP CONSTRAINT IF EXISTS document_sources_uri_key")
        )
        await connection.execute(
            text("ALTER TABLE document_sources ADD COLUMN IF NOT EXISTS public_id VARCHAR(36)")
        )
        await connection.execute(
            text("UPDATE document_sources SET public_id = gen_random_uuid()::text WHERE public_id IS NULL")
        )
        await connection.execute(
            text("ALTER TABLE document_sources ALTER COLUMN public_id SET NOT NULL")
        )
        await connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_document_sources_public_id "
                "ON document_sources (public_id)"
            )
        )
        await connection.execute(
            text("ALTER TABLE document_sources ADD COLUMN IF NOT EXISTS content_text TEXT")
        )
        await connection.execute(
            text(
                "UPDATE document_sources AS source "
                "SET content_text = COALESCE(chunk_payload.content, '') "
                "FROM ("
                "SELECT source_id, string_agg(content, E'\\n\\n' ORDER BY id) AS content "
                "FROM knowledge_chunks GROUP BY source_id"
                ") AS chunk_payload "
                "WHERE source.id = chunk_payload.source_id "
                "AND source.content_text IS NULL"
            )
        )
        await connection.execute(
            text("UPDATE document_sources SET content_text = '' WHERE content_text IS NULL")
        )
        await connection.execute(
            text("ALTER TABLE document_sources ALTER COLUMN content_text SET NOT NULL")
        )
        await connection.execute(
            text("ALTER TABLE document_sources ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64)")
        )
        await connection.execute(
            text(
                "UPDATE document_sources "
                "SET content_hash = encode(digest(content_text, 'sha256'), 'hex') "
                "WHERE content_hash IS NULL"
            )
        )
        await connection.execute(
            text("ALTER TABLE document_sources ALTER COLUMN content_hash SET NOT NULL")
        )
        await connection.execute(
            text("DROP INDEX IF EXISTS uq_document_sources_content_hash")
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_document_sources_content_hash "
                "ON document_sources (content_hash)"
            )
        )
        await connection.execute(
            text(
                "ALTER TABLE document_sources "
                "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()"
            )
        )
        await connection.execute(
            text("UPDATE document_sources SET updated_at = created_at WHERE updated_at IS NULL")
        )
        await connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_lower_name "
                "ON categories (lower(name))"
            )
        )
        await connection.execute(
            text(
                "DO $$ "
                "BEGIN "
                "IF EXISTS ("
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = current_schema() "
                "AND table_name = 'document_sources' AND column_name = 'category'"
                ") THEN "
                "ALTER TABLE document_sources ADD COLUMN IF NOT EXISTS category_id INTEGER; "
                "END IF; "
                "END $$"
            )
        )
        await connection.execute(
            text(
                "DO $$ "
                "BEGIN "
                "IF EXISTS ("
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = current_schema() "
                "AND table_name = 'document_sources' AND column_name = 'category'"
                ") THEN "
                "INSERT INTO categories (name) "
                "SELECT DISTINCT lower(btrim(category)) FROM document_sources "
                "WHERE category IS NOT NULL AND btrim(category) <> '' "
                "ON CONFLICT DO NOTHING; "
                "UPDATE document_sources AS source "
                "SET category_id = category.id "
                "FROM categories AS category "
                "WHERE source.category_id IS NULL "
                "AND lower(btrim(source.category)) = category.name; "
                "END IF; "
                "END $$"
            )
        )
        await connection.execute(
            text(
                "INSERT INTO categories (name) VALUES ('uncategorized') "
                "ON CONFLICT DO NOTHING"
            )
        )
        await connection.execute(
            text(
                "DO $$ "
                "BEGIN "
                "IF EXISTS ("
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = current_schema() "
                "AND table_name = 'document_sources' AND column_name = 'category_id'"
                ") THEN "
                "UPDATE document_sources SET category_id = ("
                "SELECT id FROM categories WHERE name = 'uncategorized'"
                ") WHERE category_id IS NULL; "
                "INSERT INTO document_source_categories (document_source_id, category_id) "
                "SELECT id, category_id FROM document_sources "
                "WHERE category_id IS NOT NULL "
                "ON CONFLICT DO NOTHING; "
                "END IF; "
                "END $$"
            )
        )
        await connection.execute(
            text("ALTER TABLE document_sources DROP COLUMN IF EXISTS category_id")
        )
        await connection.execute(
            text("ALTER TABLE document_sources DROP COLUMN IF EXISTS category")
        )
        await connection.execute(
            text(
                "DO $$ "
                "BEGIN "
                "IF EXISTS ("
                "SELECT 1 FROM pg_attribute "
                "WHERE attrelid = 'knowledge_chunks'::regclass "
                "AND attname = 'embedding' "
                "AND atttypmod <> 768"
                ") THEN "
                "ALTER TABLE knowledge_chunks ALTER COLUMN embedding TYPE vector(768); "
                "END IF; "
                "END $$"
            )
        )
