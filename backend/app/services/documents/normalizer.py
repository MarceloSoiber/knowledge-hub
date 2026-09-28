from __future__ import annotations

import re

PDF_PAGE_COUNTER_PATTERN = re.compile(r"^\s*\d+\s*/\s*\d+\s*$")
PDF_GENERATOR_FOOTER_PATTERN = re.compile(
    r"^\s*powered\s+by\s+tcpdf(?:\s*\([^)]*\))?\s*$",
    re.IGNORECASE,
)
PDF_MARGIN_CANDIDATE_MAX_LENGTH = 120
PDF_REPEATED_MARGIN_MIN_PAGES = 3


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def normalize_pdf_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)

    paragraphs = re.split(r"\n{2,}", text)
    normalized: list[str] = []
    for paragraph in paragraphs:
        lines = [
            " ".join(line.split())
            for line in paragraph.splitlines()
            if not PDF_PAGE_COUNTER_PATTERN.fullmatch(line)
            and not PDF_GENERATOR_FOOTER_PATTERN.fullmatch(line)
        ]
        paragraph_text = " ".join(line for line in lines if line)
        if paragraph_text:
            normalized.append(paragraph_text)
    return "\n\n".join(normalized)


def normalize_pdf_pages(pages: list[str]) -> list[str]:
    """Normalize PDF pages and remove repeated margin-only boilerplate.

    A term is removed only when it appears at a page margin on at least three
    distinct pages. This deliberately avoids a global stop-word list: a word
    such as "Público" remains intact when it is part of the document body.
    """
    normalized_pages = [normalize_pdf_text(page) for page in pages]
    repeated_margins = find_repeated_page_margins(normalized_pages)
    return [remove_repeated_page_margins(page, repeated_margins) for page in normalized_pages]


def find_repeated_page_margins(pages: list[str]) -> set[str]:
    occurrences: dict[str, set[int]] = {}
    for page_index, page in enumerate(pages):
        paragraphs = pdf_paragraphs(page)
        for paragraph in page_margin_paragraphs(paragraphs):
            occurrences.setdefault(paragraph.casefold(), set()).add(page_index)
    return {
        paragraph
        for paragraph, page_indexes in occurrences.items()
        if len(page_indexes) >= PDF_REPEATED_MARGIN_MIN_PAGES
    }


def remove_repeated_page_margins(page: str, repeated_margins: set[str]) -> str:
    if not repeated_margins:
        return page
    return "\n\n".join(
        paragraph
        for paragraph in pdf_paragraphs(page)
        if paragraph.casefold() not in repeated_margins
    )


def pdf_paragraphs(page: str) -> list[str]:
    return [paragraph.strip() for paragraph in page.split("\n\n") if paragraph.strip()]


def page_margin_paragraphs(paragraphs: list[str]) -> list[str]:
    if not paragraphs:
        return []
    margin = paragraphs[:2] + paragraphs[-2:]
    return [
        paragraph
        for paragraph in margin
        if len(paragraph) <= PDF_MARGIN_CANDIDATE_MAX_LENGTH
    ]
