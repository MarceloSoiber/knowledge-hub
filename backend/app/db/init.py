from sqlalchemy import text

from .base import Base
from .models import (  # noqa: F401
    AppConfig,
    Category,
    DocumentSource,
    EmbeddingBatch,
    KnowledgeChunk,
    Project,
    Tag,
)
from .session import engine
from ..core.settings import get_settings
from ..services.embedding_versions import assert_pgvector_dimension


# pylint: disable=too-many-statements
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
            text(
                "UPDATE document_sources "
                "SET public_id = gen_random_uuid()::text "
                "WHERE public_id IS NULL"
            )
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
                "ALTER TABLE tags ADD COLUMN IF NOT EXISTS normalized_name VARCHAR(100)"
            )
        )
        await connection.execute(
            text(
                "UPDATE tags SET normalized_name = lower(btrim(name)) "
                "WHERE normalized_name IS NULL"
            )
        )
        await connection.execute(
            text("ALTER TABLE tags ALTER COLUMN normalized_name SET NOT NULL")
        )
        await connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_tags_normalized_name "
                "ON tags (normalized_name)"
            )
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_document_source_tags_tag_id "
                "ON document_source_tags (tag_id)"
            )
        )
        await connection.execute(
            text(
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS normalized_name VARCHAR(150)"
            )
        )
        await connection.execute(
            text(
                "UPDATE projects SET normalized_name = lower(btrim(name)) "
                "WHERE normalized_name IS NULL"
            )
        )
        await connection.execute(
            text("ALTER TABLE projects ALTER COLUMN normalized_name SET NOT NULL")
        )
        await connection.execute(
            text(
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS description TEXT"
            )
        )
        await connection.execute(
            text(
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'active'"
            )
        )
        await connection.execute(
            text("UPDATE projects SET status = 'active' WHERE status IS NULL")
        )
        await connection.execute(
            text("ALTER TABLE projects ALTER COLUMN status SET NOT NULL")
        )
        await connection.execute(
            text(
                "ALTER TABLE projects "
                "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()"
            )
        )
        await connection.execute(
            text("UPDATE projects SET updated_at = created_at WHERE updated_at IS NULL")
        )
        await connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_projects_normalized_name "
                "ON projects (normalized_name)"
            )
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_projects_status "
                "ON projects (status)"
            )
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_document_source_projects_project_id "
                "ON document_source_projects (project_id)"
            )
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_embedding_batches_config_hash "
                "ON embedding_batches (config_hash)"
            )
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_embedding_batches_identity "
                "ON embedding_batches (provider, model, dimension, version)"
            )
        )
        await connection.execute(
            text(
                "ALTER TABLE knowledge_chunks "
                "ADD COLUMN IF NOT EXISTS embedding_batch_id INTEGER"
            )
        )
        await connection.execute(
            text(
                "DO $$ "
                "BEGIN "
                "IF NOT EXISTS ("
                "SELECT 1 "
                "FROM pg_constraint constraint_row "
                "JOIN pg_class source_table ON source_table.oid = constraint_row.conrelid "
                "JOIN pg_class target_table ON target_table.oid = constraint_row.confrelid "
                "WHERE constraint_row.contype = 'f' "
                "AND source_table.relname = 'knowledge_chunks' "
                "AND target_table.relname = 'embedding_batches' "
                ") THEN "
                "ALTER TABLE knowledge_chunks "
                "ADD CONSTRAINT fk_knowledge_chunks_embedding_batch_id "
                "FOREIGN KEY (embedding_batch_id) REFERENCES embedding_batches(id); "
                "END IF; "
                "END $$"
            )
        )
        await connection.execute(
            text(
                "ALTER TABLE knowledge_chunks "
                "ADD COLUMN IF NOT EXISTS embedding_content_hash VARCHAR(64)"
            )
        )
        await connection.execute(
            text(
                "ALTER TABLE knowledge_chunks "
                "ADD COLUMN IF NOT EXISTS embedding_status VARCHAR(32)"
            )
        )
        await connection.execute(
            text(
                "UPDATE knowledge_chunks "
                "SET embedding_status = CASE "
                "WHEN embedding IS NULL THEN 'pending' "
                "ELSE 'unversioned' "
                "END "
                "WHERE embedding_status IS NULL"
            )
        )
        await connection.execute(
            text("ALTER TABLE knowledge_chunks ALTER COLUMN embedding_status SET NOT NULL")
        )
        await connection.execute(
            text(
                "ALTER TABLE knowledge_chunks "
                "ADD COLUMN IF NOT EXISTS embedded_at TIMESTAMP WITH TIME ZONE"
            )
        )
        await connection.execute(
            text("ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS embedding_error TEXT")
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding_batch_id "
                "ON knowledge_chunks (embedding_batch_id)"
            )
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding_status_batch "
                "ON knowledge_chunks (embedding_status, embedding_batch_id)"
            )
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding_hash_batch "
                "ON knowledge_chunks (embedding_content_hash, embedding_batch_id)"
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
                "ALTER TABLE knowledge_chunks "
                "ADD COLUMN IF NOT EXISTS search_vector tsvector "
                "GENERATED ALWAYS AS (to_tsvector('simple'::regconfig, content)) STORED"
            )
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_search_vector "
                "ON knowledge_chunks USING GIN (search_vector)"
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
                "CREATE OR REPLACE FUNCTION try_parse_jsonb(value text) "
                "RETURNS jsonb AS $$ "
                "BEGIN "
                "RETURN value::jsonb; "
                "EXCEPTION WHEN others THEN "
                "RETURN '{}'::jsonb; "
                "END; "
                "$$ LANGUAGE plpgsql IMMUTABLE"
            )
        )
        await connection.execute(
            text(
                "DO $$ "
                "BEGIN "
                "IF EXISTS ("
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = current_schema() "
                "AND table_name = 'knowledge_chunks' "
                "AND column_name = 'metadata_json' "
                "AND data_type <> 'jsonb'"
                ") THEN "
                "ALTER TABLE knowledge_chunks "
                "ALTER COLUMN metadata_json TYPE jsonb "
                "USING CASE "
                "WHEN metadata_json IS NULL THEN NULL "
                "ELSE try_parse_jsonb(metadata_json) "
                "END; "
                "END IF; "
                "END $$"
            )
        )
        await connection.execute(text("DROP FUNCTION IF EXISTS try_parse_jsonb(text)"))
        await assert_pgvector_dimension(connection, get_settings().vector_dim)
