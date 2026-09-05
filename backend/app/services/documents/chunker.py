from __future__ import annotations

from dataclasses import dataclass
import re


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
DOCUMENT_SECTION_PATTERN = re.compile(
    r"^(?:(?:m[oó]dulo|module)\s+\d+\b.*|(?:cap[ií]tulo|chapter)\s+\d+\b.*)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TextSpan:
    start_char: int
    end_char: int


@dataclass(frozen=True)
class PageSpan(TextSpan):
    page: int


@dataclass(frozen=True)
class SectionSpan(TextSpan):
    section: str


@dataclass(frozen=True)
class ChunkLocation:
    chunk_index: int
    start_char: int
    end_char: int
    page: int | None = None
    section: str | None = None


@dataclass(frozen=True)
class TextChunk:
    content: str
    location: ChunkLocation


def find_chunk_end(text: str, start: int, max_end: int, chunk_size: int) -> int:
    if max_end == len(text):
        return max_end

    min_end = start + max(chunk_size // 2, 1)
    for separator in ("\n\n", "\n", ". ", "; ", ", ", " "):
        boundary = text.rfind(separator, min_end, max_end)
        if boundary != -1:
            return boundary + len(separator)
    return max_end


def find_chunk_start(text: str, start: int) -> int:
    while start < len(text) and text[start].isspace():
        start += 1
    return start


def chunk_text_with_locations(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    page_spans: list[PageSpan] | None = None,
    section_spans: list[SectionSpan] | None = None,
) -> list[TextChunk]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap.")

    chunks: list[TextChunk] = []
    start = 0
    while start < len(text):
        section_end = section_end_for_offset(start, section_spans or [], len(text))
        max_end = min(start + chunk_size, section_end)
        end = find_chunk_end(text, start, max_end, chunk_size)
        chunk_start, chunk_end = trim_span(text, start, end)
        chunk = text[chunk_start:chunk_end]
        if chunk:
            location = ChunkLocation(
                chunk_index=len(chunks),
                start_char=chunk_start,
                end_char=chunk_end,
                page=find_overlapping_page(chunk_start, chunk_end, page_spans or []),
                section=find_overlapping_section(chunk_start, chunk_end, section_spans or []),
            )
            chunks.append(TextChunk(content=chunk, location=location))
        if end == len(text):
            break
        # An overlap cannot re-enter a finished section, otherwise a short
        # section would repeatedly produce the same final chunk.
        next_start = end if end == section_end else max(end - overlap, 0)
        start = find_chunk_start(text, next_start)
    return chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    return [
        chunk.content
        for chunk in chunk_text_with_locations(text, chunk_size=chunk_size, overlap=overlap)
    ]


def trim_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def find_overlapping_page(start: int, end: int, page_spans: list[PageSpan]) -> int | None:
    best_page: int | None = None
    best_overlap = 0
    for span in page_spans:
        overlap = max(0, min(end, span.end_char) - max(start, span.start_char))
        if overlap > best_overlap:
            best_overlap = overlap
            best_page = span.page
    return best_page


def find_overlapping_section(
    start: int,
    end: int,
    section_spans: list[SectionSpan],
) -> str | None:
    best_section: str | None = None
    best_overlap = 0
    for span in section_spans:
        overlap = max(0, min(end, span.end_char) - max(start, span.start_char))
        if overlap > best_overlap:
            best_overlap = overlap
            best_section = span.section
    return best_section


def detect_markdown_sections(text: str) -> list[SectionSpan]:
    return build_section_spans(text, markdown_headings(text))


def detect_document_sections(text: str) -> list[SectionSpan]:
    headings = markdown_headings(text)
    headings.extend(pdf_headings(text))
    headings.sort(key=lambda item: item[0])
    return build_section_spans(text, deduplicate_headings(headings))


def markdown_headings(text: str) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                headings.append((offset, title))
        offset += len(line)
    return headings


def pdf_headings(text: str) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    offset = 0
    for paragraph in text.split("\n\n"):
        title = paragraph.strip()
        if DOCUMENT_SECTION_PATTERN.fullmatch(title):
            headings.append((offset, title))
        offset += len(paragraph) + 2
    return headings


def deduplicate_headings(headings: list[tuple[int, str]]) -> list[tuple[int, str]]:
    deduplicated: list[tuple[int, str]] = []
    seen_offsets: set[int] = set()
    for offset, title in headings:
        if offset not in seen_offsets:
            deduplicated.append((offset, title))
            seen_offsets.add(offset)
    return deduplicated


def build_section_spans(text: str, headings: list[tuple[int, str]]) -> list[SectionSpan]:
    sections: list[SectionSpan] = []
    for index, (start, title) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(text)
        sections.append(SectionSpan(start_char=start, end_char=end, section=title))
    return sections


def section_end_for_offset(offset: int, sections: list[SectionSpan], default_end: int) -> int:
    for section in sections:
        if section.start_char <= offset < section.end_char:
            return section.end_char
    return default_end
