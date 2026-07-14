from __future__ import annotations


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


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


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap.")

    chunks: list[str] = []
    start = 0
    while start < len(text):
        max_end = min(start + chunk_size, len(text))
        end = find_chunk_end(text, start, max_end, chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = find_chunk_start(text, max(end - overlap, 0))
    return chunks
