from __future__ import annotations

import re

PDF_PAGE_COUNTER_PATTERN = re.compile(r"^\s*\d+\s*/\s*\d+\s*$")
PDF_GENERATOR_FOOTER_PATTERN = re.compile(
    r"^\s*powered\s+by\s+tcpdf(?:\s*\([^)]*\))?\s*$",
    re.IGNORECASE,
)


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
