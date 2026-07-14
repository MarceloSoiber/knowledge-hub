"""Compatibility facade for knowledge services.

New code should import from the focused service modules directly.
"""

from .categories import CategoryNotFoundError, get_category, list_categories
from .documents.chunker import chunk_text, find_chunk_end, find_chunk_start
from .documents.extractors import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    build_pdf_reader,
    extract_pdf_page_text,
    extract_text,
    validate_upload,
)
from .documents.normalizer import normalize_pdf_text, normalize_text
from .ingestion import KnowledgeIngestionError, ingest_plain_text, ingest_text_source
from .ingestion import ingest_uploaded_file
from .search import answer_knowledge, list_sources, search_knowledge

__all__ = [
    "CategoryNotFoundError",
    "EmptyDocumentError",
    "FileTooLargeError",
    "KnowledgeIngestionError",
    "UnsupportedFileTypeError",
    "answer_knowledge",
    "build_pdf_reader",
    "chunk_text",
    "extract_pdf_page_text",
    "extract_text",
    "find_chunk_end",
    "find_chunk_start",
    "get_category",
    "ingest_plain_text",
    "ingest_text_source",
    "ingest_uploaded_file",
    "list_categories",
    "list_sources",
    "normalize_pdf_text",
    "normalize_text",
    "search_knowledge",
    "validate_upload",
]
