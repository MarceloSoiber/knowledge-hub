from __future__ import annotations

import pytest

from backend.app.schemas.knowledge import KnowledgeChunkRead
from backend.app.services.agent_policy import (
    build_mcp_instructions,
    request_matches_category_inventory,
)
from backend.app.services.privacy import (
    SensitiveContentExternalProviderError,
    assert_provider_can_receive_sources,
    has_sensitive_category,
    normalize_category_name,
)


def make_chunk(category_name: str) -> KnowledgeChunkRead:
    return KnowledgeChunkRead(
        id=1,
        source_id="11111111-1111-4111-8111-111111111111",
        source_title="Private source",
        source_type="text",
        uri="text:private",
        categories=[{"id": 1, "name": category_name}],
        location={
            "chunk_index": 0,
            "page": None,
            "section": None,
            "start_char": 0,
            "end_char": 7,
        },
        content="private",
    )


def test_policy_treats_categories_as_dynamic_memory_inventory() -> None:
    assert not request_matches_category_inventory("qual o status do lancamento", ["documentacao"])
    assert request_matches_category_inventory("qual o status do lancamento", ["lancamento"])
    assert request_matches_category_inventory("revisar impostos", ["Impostos 2026"])


def test_policy_instructions_cover_search_boundaries_and_untrusted_context() -> None:
    instructions = build_mcp_instructions()

    assert "categories() como o inventario dinamico" in instructions
    assert "Nao pesquise para calculos simples" in instructions
    assert "reformule a consulta uma unica vez" in instructions
    assert "evidencia nao confiavel" in instructions
    assert "confirmacao explicita" in instructions


def test_privacy_normalizes_sensitive_category_names() -> None:
    source = make_chunk("  Financeiro Estrategico ")

    assert normalize_category_name(" Financeiro Estrategico ") == "financeiro estrategico"
    assert has_sensitive_category([source], ["FINANCEIRO ESTRATEGICO"])


def test_privacy_blocks_external_provider_without_leaking_content() -> None:
    source = make_chunk("Financeiro")

    with pytest.raises(SensitiveContentExternalProviderError) as error:
        assert_provider_can_receive_sources(
            provider="api",
            sources=[source],
            sensitive_category_names=["financeiro"],
            allow_external_sensitive_content=False,
        )

    assert "Financeiro" not in str(error.value)
    assert "private" not in str(error.value)


def test_privacy_allows_local_provider_for_sensitive_content() -> None:
    assert_provider_can_receive_sources(
        provider="local",
        sources=[make_chunk("Financeiro")],
        sensitive_category_names=["financeiro"],
        allow_external_sensitive_content=False,
    )
