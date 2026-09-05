from backend.app.services.documents.chunker import (
    chunk_text_with_locations,
    detect_document_sections,
)
from backend.app.services.documents.extractors import extract_pdf_native_document
from backend.app.services.documents.normalizer import normalize_pdf_pages


def test_pdf_normalization_removes_only_repeated_margin_paragraphs() -> None:
    pages = [
        "Público\n\nCapítulo 1\n\nConteúdo de IA\n\nMarca do curso",
        "Público\n\nCapítulo 2\n\nConteúdo de RAG\n\nMarca do curso",
        "Público\n\nCapítulo 3\n\nConteúdo de LLM\n\nMarca do curso",
    ]

    normalized = normalize_pdf_pages(pages)

    assert all("Público" not in page for page in normalized)
    assert all("Marca do curso" not in page for page in normalized)
    assert "Conteúdo de RAG" in normalized[1]


def test_pdf_normalization_keeps_one_off_body_text() -> None:
    pages = [
        "Público\n\nCapítulo 1\n\nO público alvo são programadores.",
        "Público\n\nCapítulo 2\n\nConteúdo de RAG",
        "Público\n\nCapítulo 3\n\nConteúdo de LLM",
    ]

    normalized = normalize_pdf_pages(pages)

    assert "O público alvo são programadores." in normalized[0]


def test_native_pdf_extraction_preserves_page_spans_after_margin_cleanup() -> None:
    class Page:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self, extraction_mode: str | None = None) -> str:
            return self.text

    class Reader:
        pages = [
            Page("Público\n\nCapítulo 1\n\nConteúdo de IA"),
            Page("Público\n\nCapítulo 2\n\nConteúdo de RAG"),
            Page("Público\n\nCapítulo 3\n\nConteúdo de LLM"),
        ]

    text, page_spans = extract_pdf_native_document(Reader())

    assert "Público" not in text
    assert [span.page for span in page_spans] == [1, 2, 3]
    assert text[page_spans[1].start_char:page_spans[1].end_char].startswith("Capítulo 2")


def test_document_sections_and_chunks_do_not_cross_chapter_boundary() -> None:
    text = (
        "Capítulo 1: IA\n\n"
        + ("ALPHA_MARKER " * 12)
        + "\n\nCapítulo 2: RAG\n\n"
        + ("BETA_MARKER " * 12)
    )
    sections = detect_document_sections(text)
    chunks = chunk_text_with_locations(text, chunk_size=100, overlap=20, section_spans=sections)

    assert [section.section for section in sections] == ["Capítulo 1: IA", "Capítulo 2: RAG"]
    assert all(
        not ("ALPHA_MARKER" in chunk.content and "BETA_MARKER" in chunk.content)
        for chunk in chunks
    )
    assert {chunk.location.section for chunk in chunks} == {"Capítulo 1: IA", "Capítulo 2: RAG"}
