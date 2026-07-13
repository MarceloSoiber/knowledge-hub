from sqlalchemy import text

from .base import Base
from .models import AppConfig, Category, DocumentSource, KnowledgeChunk  # noqa: F401
from .session import engine


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text(
                "ALTER TABLE document_sources "
                "ADD COLUMN IF NOT EXISTS category_id INTEGER"
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
                "SELECT DISTINCT category FROM document_sources "
                "WHERE category IS NOT NULL AND btrim(category) <> '' "
                "ON CONFLICT (name) DO NOTHING; "
                "UPDATE document_sources AS source "
                "SET category_id = category.id "
                "FROM categories AS category "
                "WHERE source.category_id IS NULL AND source.category = category.name; "
                "END IF; "
                "END $$"
            )
        )
        await connection.execute(
            text(
                "INSERT INTO categories (name) VALUES ('uncategorized') "
                "ON CONFLICT (name) DO NOTHING"
            )
        )
        await connection.execute(
            text(
                "UPDATE document_sources SET category_id = ("
                "SELECT id FROM categories WHERE name = 'uncategorized'"
                ") WHERE category_id IS NULL"
            )
        )
        await connection.execute(
            text("ALTER TABLE document_sources ALTER COLUMN category_id SET NOT NULL")
        )
        await connection.execute(
            text(
                "DO $$ "
                "BEGIN "
                "IF NOT EXISTS ("
                "SELECT 1 FROM pg_constraint "
                "WHERE conrelid = 'document_sources'::regclass "
                "AND confrelid = 'categories'::regclass AND contype = 'f'"
                ") THEN "
                "ALTER TABLE document_sources ADD CONSTRAINT fk_document_sources_category_id "
                "FOREIGN KEY (category_id) REFERENCES categories(id); "
                "END IF; "
                "END $$"
            )
        )
        await connection.execute(
            text("ALTER TABLE document_sources DROP COLUMN IF EXISTS category")
        )
        await connection.execute(
            text("ALTER TABLE knowledge_chunks ALTER COLUMN embedding TYPE vector(768)")
        )
