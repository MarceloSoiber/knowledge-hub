from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from .chunker import PageSpan
from .normalizer import normalize_pdf_text, normalize_text


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
PDF_OCR_DPI = 200
PDF_OCR_LANGUAGES = "por+eng"
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    page_spans: list[PageSpan]
    document_type: str


class DocumentExtractionError(ValueError):
    pass


class UnsupportedFileTypeError(DocumentExtractionError):
    pass


class FileTooLargeError(DocumentExtractionError):
    pass


class EmptyDocumentError(DocumentExtractionError):
    pass


def build_pdf_reader(stream: io.BytesIO):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise DocumentExtractionError("pypdf is required to extract text from PDF files.") from exc

    return PdfReader(stream)


def extract_pdf_page_text(page: object) -> str:
    extract_text_method = getattr(page, "extract_text")
    try:
        return extract_text_method(extraction_mode="layout") or ""
    except TypeError:
        return extract_text_method() or ""


def build_pdf_ocr_images(content: bytes) -> list[object]:
    try:
        from pdf2image import convert_from_bytes
    except ImportError as exc:
        raise DocumentExtractionError("pdf2image is required to OCR scanned PDF files.") from exc

    return convert_from_bytes(content, dpi=PDF_OCR_DPI)


def extract_pdf_image_text(image: object) -> str:
    try:
        import pytesseract
    except ImportError as exc:
        raise DocumentExtractionError("pytesseract is required to OCR scanned PDF files.") from exc

    return pytesseract.image_to_string(image, lang=PDF_OCR_LANGUAGES) or ""


def extract_pdf_ocr_text(content: bytes) -> str:
    try:
        images = build_pdf_ocr_images(content)
        text = "\n\n".join(extract_pdf_image_text(image) for image in images)
    except DocumentExtractionError:
        raise
    except Exception as exc:
        raise DocumentExtractionError(f"PDF OCR failed: {exc}") from exc

    return normalize_pdf_text(text)


def validate_upload(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError("Only .txt, .md and .pdf files are supported.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise FileTooLargeError("Uploaded file is larger than 10MB.")
    return extension


def extract_text(filename: str, content: bytes) -> str:
    return extract_document(filename, content).text


def extract_document(filename: str, content: bytes) -> ExtractedDocument:
    extension = validate_upload(filename, content)

    if extension in {".txt", ".md"}:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentExtractionError("File must be encoded as UTF-8.") from exc
        text = normalize_text(text)
        page_spans: list[PageSpan] = []
    else:
        reader = build_pdf_reader(io.BytesIO(content))
        text, page_spans = extract_pdf_native_document(reader)
        if not text:
            text = extract_pdf_ocr_text(content)
            page_spans = []

    if not text:
        raise EmptyDocumentError("Uploaded document does not contain readable text.")
    return ExtractedDocument(text=text, page_spans=page_spans, document_type=extension.lstrip("."))


def extract_pdf_native_document(reader: object) -> tuple[str, list[PageSpan]]:
    parts: list[str] = []
    spans: list[PageSpan] = []
    cursor = 0
    pages = getattr(reader, "pages")
    for index, page in enumerate(pages, start=1):
        page_text = normalize_pdf_text(extract_pdf_page_text(page))
        if not page_text:
            continue
        if parts:
            parts.append("\n\n")
            cursor += 2
        start = cursor
        parts.append(page_text)
        cursor += len(page_text)
        spans.append(PageSpan(page=index, start_char=start, end_char=cursor))
    return "".join(parts), spans
