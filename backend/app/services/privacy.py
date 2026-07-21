from __future__ import annotations

import unicodedata
from collections.abc import Iterable

from ..schemas.knowledge import KnowledgeChunkRead


class SensitiveContentExternalProviderError(RuntimeError):
    """Raised before sensitive retrieved content is sent to an external provider."""


def normalize_category_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return " ".join(without_accents.casefold().split())


def has_sensitive_category(
    sources: Iterable[KnowledgeChunkRead], sensitive_category_names: Iterable[str]
) -> bool:
    sensitive_names = {
        normalize_category_name(name) for name in sensitive_category_names if name.strip()
    }
    if not sensitive_names:
        return False
    return any(
        normalize_category_name(category.name) in sensitive_names
        for source in sources
        for category in source.categories
    )


def assert_provider_can_receive_sources(
    *,
    provider: str,
    sources: Iterable[KnowledgeChunkRead],
    sensitive_category_names: Iterable[str],
    allow_external_sensitive_content: bool,
) -> None:
    if (
        provider.strip().lower() == "api"
        and not allow_external_sensitive_content
        and has_sensitive_category(sources, sensitive_category_names)
    ):
        raise SensitiveContentExternalProviderError(
            "Sensitive retrieved content cannot be sent to an external provider. "
            "Use a local provider or narrow the query to non-sensitive content."
        )
