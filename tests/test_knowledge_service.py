from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import logging
import math
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from backend.app.cli.config import generate_auth_token, validate_auth_token
from backend.app.core.auth import is_valid_token
from backend.app.core.settings import Settings
from backend.app.db.models import Category, DocumentSource, KnowledgeChunk
from backend.app.repositories.chunks import TextSearchChunk
from backend.app.schemas.knowledge import (
    KnowledgeAnswerRequest,
    KnowledgeChunkRead,
    KnowledgeSearchRequest,
    KnowledgeTextIngestRequest,
    KnowledgeUploadRequest,
)
from backend.app.services.embeddings import (
    EmbeddingConfigurationError,
    OpenAIEmbeddingClient,
)
from backend.app.services.categories import (
    CategoryConflictError,
    CategoryNotFoundError,
    create_category,
    list_categories,
)
from backend.app.services.documents.chunker import chunk_text, chunk_text_with_locations
from backend.app.services.documents.extractors import (
    UnsupportedFileTypeError,
    extract_document,
    extract_text,
)
from backend.app.services.ingestion import ingest_plain_text, ingest_uploaded_file
from backend.app.services.rag import LLMConfigurationError, OpenAICompatibleAnswerClient
from backend.app.services.search import (
    fuse_hybrid_results,
    filter_results_by_score,
    answer_knowledge,
    search_knowledge,
)
from backend.app.services.sources import delete_source, get_source_detail, update_source


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.inputs: list[list[str]] = []

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.inputs.append(texts)
        return [[0.1, 0.2, 0.3] for _ in texts]


class FailingEmbeddingClient:
    def __init__(self) -> None:
        self.inputs: list[list[str]] = []

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.inputs.append(texts)
        raise RuntimeError("embedding failed")


class FakeAnswerClient:
    def __init__(self) -> None:
        self.sources_seen: list[KnowledgeChunkRead] | None = None

    async def answer(self, query: str, sources: list[KnowledgeChunkRead]) -> str:
        self.sources_seen = sources
        return f"answer for {query} with {len(sources)} sources"


@dataclass
class FakeRow:
    KnowledgeChunk: KnowledgeChunk
    DocumentSource: DocumentSource
    distance: float

    def __getitem__(self, index: int) -> object:
        return (self.KnowledgeChunk, self.DocumentSource, self.distance)[index]


class FakeExecuteResult:
    def __init__(self, rows: list[FakeRow]) -> None:
        self._rows = rows

    def all(self) -> list[FakeRow]:
        return self._rows

    def scalars(self) -> "FakeExecuteResult":
        return self

    def __iter__(self):
        return iter(self._rows)


@dataclass
class FakeCategoryRow:
    id: int
    name: str


class FakeSession:
    def __init__(
        self,
        existing_source: DocumentSource | None = None,
        duplicate_source: DocumentSource | None = None,
        source_by_public_id: DocumentSource | None = None,
        categories: list[Category] | None = None,
    ) -> None:
        self.existing_source = existing_source
        self.duplicate_source = duplicate_source
        self.source_by_public_id = source_by_public_id
        self.categories = categories or [Category(id=3, name="docs")]
        self.added: list[object] = []
        self.deleted_old_chunks = False
        self.deleted_source = False
        self.committed = False
        source = DocumentSource(
            id=2,
            public_id="99999999-9999-4999-8999-999999999999",
            title="Stored Source",
            source_type="text",
            uri="text:Stored Source",
            content_text="stored content",
            content_hash=sha256(b"stored content").hexdigest(),
        )
        source.categories = [Category(id=3, name="docs")]
        chunk = KnowledgeChunk(
            id=1,
            source_id=2,
            content="stored content",
            metadata_json={
                "location": {
                    "chunk_index": 0,
                    "start_char": 0,
                    "end_char": 14,
                    "page": None,
                    "section": "Intro",
                },
                "metadata": {"note_type": "decision", "unsafe": "secret"},
            },
        )
        self.rows = [FakeRow(KnowledgeChunk=chunk, DocumentSource=source, distance=0.2)]

    async def scalar(self, statement: object) -> DocumentSource | None:
        statement_text = str(statement)
        if "WHERE document_sources.public_id" in statement_text:
            return self.source_by_public_id
        if "WHERE document_sources.content_hash" in statement_text:
            return self.duplicate_source
        return self.existing_source

    async def get(self, entity: object, entity_id: int) -> Category | None:
        assert entity is Category
        for category in self.categories:
            if category.id == entity_id:
                return category
        return None

    async def execute(self, statement: object) -> FakeExecuteResult:
        statement_text = str(statement)
        if statement.__class__.__name__ == "Delete" and "knowledge_chunks" in statement_text:
            self.deleted_old_chunks = True
        if statement.__class__.__name__ == "Delete" and "document_sources" in statement_text:
            self.deleted_source = True
        if "categories" in str(statement):
            return FakeExecuteResult(self.categories)  # type: ignore[arg-type]
        return FakeExecuteResult(self.rows)

    def add(self, entity: object) -> None:
        if isinstance(entity, DocumentSource) and entity.id is None:
            entity.id = 99
        if isinstance(entity, DocumentSource) and entity.public_id is None:
            entity.public_id = "11111111-1111-4111-8111-111111111111"
        self.added.append(entity)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, entity: object) -> None:
        _ = entity


def test_extract_text_accepts_txt_and_md() -> None:
    assert extract_text("notes.txt", b"hello\n\nworld") == "hello\nworld"
    assert extract_text("notes.md", b"# Title\nbody") == "# Title\nbody"


def test_extract_text_rejects_unsupported_extensions() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        extract_text("notes.docx", b"hello")


def test_extract_text_reads_pdf(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePage:
        def extract_text(self, extraction_mode: str | None = None) -> str:
            assert extraction_mode == "layout"
            return "pdf page"

    class FakePdfReader:
        def __init__(self, stream: object) -> None:
            _ = stream
            self.pages = [FakePage()]

    monkeypatch.setattr("backend.app.services.documents.extractors.build_pdf_reader", FakePdfReader)

    assert extract_text("paper.pdf", b"%PDF") == "pdf page"


def test_extract_text_prefers_pdf_native_text_over_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePage:
        def extract_text(self, extraction_mode: str | None = None) -> str:
            assert extraction_mode == "layout"
            return "native pdf text"

    class FakePdfReader:
        def __init__(self, stream: object) -> None:
            _ = stream
            self.pages = [FakePage()]

    def fail_ocr(_: bytes) -> str:
        raise AssertionError("OCR should not run when native PDF text is available.")

    monkeypatch.setattr("backend.app.services.documents.extractors.build_pdf_reader", FakePdfReader)
    monkeypatch.setattr("backend.app.services.documents.extractors.extract_pdf_ocr_text", fail_ocr)

    assert extract_text("paper.pdf", b"%PDF") == "native pdf text"


def test_extract_text_uses_ocr_when_pdf_native_text_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakePage:
        def extract_text(self, extraction_mode: str | None = None) -> str:
            assert extraction_mode == "layout"
            return "Powered by TCPDF (www.tcpdf.org)"

    class FakePdfReader:
        def __init__(self, stream: object) -> None:
            _ = stream
            self.pages = [FakePage()]

    def fake_ocr(content: bytes) -> str:
        assert content == b"%PDF"
        return "Texto extraido por OCR"

    monkeypatch.setattr("backend.app.services.documents.extractors.build_pdf_reader", FakePdfReader)
    monkeypatch.setattr("backend.app.services.documents.extractors.extract_pdf_ocr_text", fake_ocr)

    assert extract_text("paper.pdf", b"%PDF") == "Texto extraido por OCR"


def test_extract_text_normalizes_pdf_layout(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePage:
        def extract_text(self, extraction_mode: str | None = None) -> str:
            assert extraction_mode == "layout"
            return "Receita de Vendas de Imó-\nveis\nFonte:\xa0TRBL11"

    class FakePdfReader:
        def __init__(self, stream: object) -> None:
            _ = stream
            self.pages = [FakePage()]

    monkeypatch.setattr("backend.app.services.documents.extractors.build_pdf_reader", FakePdfReader)

    assert extract_text("paper.pdf", b"%PDF") == "Receita de Vendas de Imóveis Fonte: TRBL11"


def test_extract_text_removes_pdf_page_counters(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePage:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self, extraction_mode: str | None = None) -> str:
            assert extraction_mode == "layout"
            return self.text

    class FakePdfReader:
        def __init__(self, stream: object) -> None:
            _ = stream
            self.pages = [
                FakePage("1 / 17\n\nResumo do fundo\nReceita recorrente"),
                FakePage("2 / 17\n\nRiscos e oportunidades"),
            ]

    monkeypatch.setattr("backend.app.services.documents.extractors.build_pdf_reader", FakePdfReader)

    assert (
        extract_text("paper.pdf", b"%PDF")
        == "Resumo do fundo Receita recorrente\n\nRiscos e oportunidades"
    )


def test_extract_document_preserves_pdf_page_spans(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePage:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self, extraction_mode: str | None = None) -> str:
            assert extraction_mode == "layout"
            return self.text

    class FakePdfReader:
        def __init__(self, stream: object) -> None:
            _ = stream
            self.pages = [FakePage("Pagina um"), FakePage("Pagina dois")]

    monkeypatch.setattr("backend.app.services.documents.extractors.build_pdf_reader", FakePdfReader)

    document = extract_document("paper.pdf", b"%PDF")

    assert document.text == "Pagina um\n\nPagina dois"
    assert [(span.page, span.start_char, span.end_char) for span in document.page_spans] == [
        (1, 0, 9),
        (2, 11, 22),
    ]


def test_extract_text_removes_pdf_generator_footer(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePage:
        def extract_text(self, extraction_mode: str | None = None) -> str:
            assert extraction_mode == "layout"
            return "Resumo do fundo\n\nPowered by TCPDF (www.tcpdf.org)"

    class FakePdfReader:
        def __init__(self, stream: object) -> None:
            _ = stream
            self.pages = [FakePage()]

    monkeypatch.setattr("backend.app.services.documents.extractors.build_pdf_reader", FakePdfReader)

    assert extract_text("paper.pdf", b"%PDF") == "Resumo do fundo"


def test_chunk_text_uses_overlap() -> None:
    chunks = chunk_text("abcdefghij", chunk_size=6, overlap=2)

    assert chunks == ["abcdef", "efghij"]


def test_chunk_text_prefers_sentence_boundaries() -> None:
    chunks = chunk_text("Primeira frase. Segunda frase. Terceira frase.", chunk_size=32, overlap=0)

    assert chunks == ["Primeira frase. Segunda frase.", "Terceira frase."]


def test_chunk_text_with_locations_tracks_offsets_and_sections() -> None:
    text = "# Intro\nPrimeira frase. Segunda frase.\n\n# Final\nTerceira frase."

    chunks = chunk_text_with_locations(
        text,
        chunk_size=36,
        overlap=0,
        section_spans=[
            SimpleNamespace(start_char=0, end_char=39, section="Intro"),
            SimpleNamespace(start_char=39, end_char=len(text), section="Final"),
        ],  # type: ignore[list-item]
    )

    assert chunks[0].location.chunk_index == 0
    assert chunks[0].location.start_char == 0
    assert chunks[0].location.end_char <= len(text)
    assert chunks[0].location.section == "Intro"


def test_knowledge_schemas_trim_and_reject_blank_values() -> None:
    search = KnowledgeSearchRequest(query="  find me  ", category_ids=[3])
    answer = KnowledgeAnswerRequest(query="  answer me  ")
    upload = KnowledgeUploadRequest(category_ids=[4])
    text = KnowledgeTextIngestRequest(
        title="  Sprint notes  ",
        category_ids=[5],
        content="  decision log  ",
    )

    assert search.query == "find me"
    assert search.category_ids == [3]
    assert answer.query == "answer me"
    assert upload.category_ids == [4]
    assert text.title == "Sprint notes"
    assert text.category_ids == [5]
    assert text.content == "decision log"

    with pytest.raises(ValidationError):
        KnowledgeSearchRequest(query="   ")

    with pytest.raises(ValidationError):
        KnowledgeAnswerRequest(query="   ")

    with pytest.raises(ValidationError):
        KnowledgeUploadRequest(category_ids=[0])

    with pytest.raises(ValidationError):
        KnowledgeUploadRequest(category_ids=[])

    with pytest.raises(ValidationError):
        KnowledgeSearchRequest(query="find", category_ids=[1, 1])

    with pytest.raises(ValidationError):
        KnowledgeTextIngestRequest(title="   ", category_ids=[3], content="text")

    with pytest.raises(ValidationError):
        KnowledgeTextIngestRequest(title="notes", category_ids=[3], content="   ")


def test_knowledge_schemas_reject_invalid_min_score_values() -> None:
    KnowledgeSearchRequest(query="find", min_score=0.0)
    KnowledgeSearchRequest(query="find", min_score=1.0)
    KnowledgeAnswerRequest(query="answer", min_score=0.5)

    for invalid_min_score in (-0.01, 1.01, math.nan, math.inf):
        with pytest.raises(ValidationError):
            KnowledgeSearchRequest(query="find", min_score=invalid_min_score)

        with pytest.raises(ValidationError):
            KnowledgeAnswerRequest(query="answer", min_score=invalid_min_score)


def test_settings_reject_invalid_search_min_score_values() -> None:
    Settings(search_min_score=0.35)

    for invalid_min_score in (-0.01, 1.01, math.nan, math.inf):
        with pytest.raises(ValidationError):
            Settings(search_min_score=invalid_min_score)


def test_token_auth_accepts_matching_bearer_token() -> None:
    assert is_valid_token("secret-token", "secret-token") is True
    assert is_valid_token("wrong-token", "secret-token") is False


def test_token_auth_is_disabled_without_configured_token() -> None:
    assert is_valid_token("", "") is True
    assert is_valid_token("anything", "") is True


def test_auth_token_validation_accepts_generated_token() -> None:
    token = generate_auth_token()

    assert validate_auth_token(token) == token


def test_auth_token_validation_rejects_paste_garbage() -> None:
    with pytest.raises(ValueError):
        validate_auth_token("valid-token" + "\x1b[200~" + "more-text")


@pytest.mark.asyncio
async def test_ingest_uploaded_file_creates_same_title_source_when_content_differs() -> None:
    source = DocumentSource(
        id=7,
        public_id="22222222-2222-4222-8222-222222222222",
        title="old.md",
        source_type="upload",
        uri="upload:notes.md",
        content_text="old content",
        content_hash=sha256(b"old content").hexdigest(),
    )
    session = FakeSession(
        existing_source=source,
        categories=[Category(id=3, name="manuals"), Category(id=4, name="docs")],
    )

    created_source, chunks_created = await ingest_uploaded_file(
        session=session,
        filename="notes.md",
        content=b"new content",
        category_ids=[3, 4],
        embedding_client=FakeEmbeddingClient(),
    )

    assert created_source.id == 99
    assert created_source.title == "notes.md"
    assert [category.id for category in created_source.categories] == [3, 4]
    assert created_source.public_id == "11111111-1111-4111-8111-111111111111"
    assert chunks_created == 1
    assert session.deleted_old_chunks is False
    assert session.committed is True


@pytest.mark.asyncio
async def test_ingest_plain_text_creates_text_source() -> None:
    session = FakeSession()
    embedding_client = FakeEmbeddingClient()

    source, chunks_created = await ingest_plain_text(
        session=session,
        title="  Meeting notes  ",
        content=" Linha um. \n\n Linha dois. ",
        category_ids=[3],
        embedding_client=embedding_client,
    )

    assert source.id == 99
    assert source.title == "Meeting notes"
    assert [category.id for category in source.categories] == [3]
    assert source.source_type == "text"
    assert source.uri == "text:Meeting notes"
    assert source.content_text == "Linha um.\nLinha dois."
    assert source.content_hash == sha256("Linha um.\nLinha dois.".encode()).hexdigest()
    assert chunks_created == 1
    assert embedding_client.inputs == [["Linha um.\nLinha dois."]]
    assert session.committed is True


@pytest.mark.asyncio
async def test_ingest_plain_text_can_create_mcp_source() -> None:
    session = FakeSession()

    source, chunks_created = await ingest_plain_text(
        session=session,
        title="Confirmed note",
        content="persist this confirmed note",
        category_ids=[3],
        embedding_client=FakeEmbeddingClient(),
        source_type="mcp",
        metadata={"note_type": "decision"},
    )

    assert source.id == 99
    assert source.title == "Confirmed note"
    assert source.source_type == "mcp"
    assert source.uri == "mcp:Confirmed note"
    assert chunks_created == 1
    assert session.committed is True
    chunk = next(entity for entity in session.added if isinstance(entity, KnowledgeChunk))
    assert chunk.metadata_json["location"]["chunk_index"] == 0  # type: ignore[index]
    assert chunk.metadata_json["metadata"] == {"note_type": "decision"}  # type: ignore[index]


@pytest.mark.asyncio
async def test_ingest_plain_text_rejects_duplicate_content() -> None:
    duplicate = DocumentSource(
        id=8,
        public_id="33333333-3333-4333-8333-333333333333",
        title="old title",
        source_type="text",
        uri="text:notes",
        content_text="updated content",
        content_hash=sha256(b"updated content").hexdigest(),
    )
    session = FakeSession(duplicate_source=duplicate)
    embedding_client = FakeEmbeddingClient()

    with pytest.raises(Exception, match="identical content"):
        await ingest_plain_text(
            session=session,
            title="notes",
            content="updated content",
            category_ids=[3],
            embedding_client=embedding_client,
        )

    assert embedding_client.inputs == []
    assert session.committed is False


@pytest.mark.asyncio
async def test_ingest_plain_text_rejects_unknown_category() -> None:
    embedding_client = FakeEmbeddingClient()

    with pytest.raises(CategoryNotFoundError, match="Category 999 does not exist"):
        await ingest_plain_text(
            session=FakeSession(),
            title="notes",
            content="content",
            category_ids=[999],
            embedding_client=embedding_client,
        )

    assert embedding_client.inputs == []


@pytest.mark.asyncio
async def test_list_categories_returns_id_and_name() -> None:
    class FakeCategorySession:
        async def execute(self, statement: object) -> FakeExecuteResult:
            _ = statement
            return FakeExecuteResult(
                [
                    FakeCategoryRow(id=2, name="engineering"),
                    FakeCategoryRow(id=1, name="finance"),
                ]
            )

    categories = await list_categories(FakeCategorySession())  # type: ignore[arg-type]

    assert categories == [
        {"id": 2, "name": "engineering"},
        {"id": 1, "name": "finance"},
    ]


@pytest.mark.asyncio
async def test_get_source_detail_returns_public_contract() -> None:
    source = DocumentSource(
        id=10,
        public_id="44444444-4444-4444-8444-444444444444",
        title="notes",
        source_type="text",
        uri="text:notes",
        content_text="source content",
        content_hash=sha256(b"source content").hexdigest(),
    )
    source.categories = [Category(id=3, name="docs")]

    detail = await get_source_detail(  # type: ignore[arg-type]
        FakeSession(source_by_public_id=source), source.public_id
    )

    assert detail["source_id"] == "44444444-4444-4444-8444-444444444444"
    assert detail["content"] == "source content"
    assert detail["categories"] == [{"id": 3, "name": "docs"}]


@pytest.mark.asyncio
async def test_update_source_metadata_does_not_call_embeddings() -> None:
    source = DocumentSource(
        id=10,
        public_id="55555555-5555-4555-8555-555555555555",
        title="old",
        source_type="text",
        uri="text:old",
        content_text="same content",
        content_hash=sha256(b"same content").hexdigest(),
    )
    source.categories = [Category(id=3, name="docs")]
    embedding_client = FakeEmbeddingClient()

    detail, chunks_created = await update_source(
        session=FakeSession(source_by_public_id=source),
        source_id=source.public_id,
        title="new",
        category_ids=[3],
        embedding_client=embedding_client,
    )

    assert detail["title"] == "new"
    assert chunks_created is None
    assert embedding_client.inputs == []


@pytest.mark.asyncio
async def test_update_source_content_replaces_chunks() -> None:
    source = DocumentSource(
        id=10,
        public_id="66666666-6666-4666-8666-666666666666",
        title="old",
        source_type="text",
        uri="text:old",
        content_text="old content",
        content_hash=sha256(b"old content").hexdigest(),
    )
    source.categories = [Category(id=3, name="docs")]
    session = FakeSession(source_by_public_id=source)
    embedding_client = FakeEmbeddingClient()

    detail, chunks_created = await update_source(
        session=session,
        source_id=source.public_id,
        content="new content",
        embedding_client=embedding_client,
    )

    assert detail["content"] == "new content"
    assert detail["content_hash"] == sha256(b"new content").hexdigest()
    assert chunks_created == 1
    assert session.deleted_old_chunks is True
    assert embedding_client.inputs == [["new content"]]


@pytest.mark.asyncio
async def test_update_source_content_embedding_failure_leaves_source_unchanged() -> None:
    source = DocumentSource(
        id=10,
        public_id="77777777-7777-4777-8777-777777777777",
        title="old",
        source_type="text",
        uri="text:old",
        content_text="old content",
        content_hash=sha256(b"old content").hexdigest(),
    )
    source.categories = [Category(id=3, name="docs")]
    session = FakeSession(source_by_public_id=source)

    with pytest.raises(RuntimeError, match="embedding failed"):
        await update_source(
            session=session,
            source_id=source.public_id,
            content="new content",
            embedding_client=FailingEmbeddingClient(),  # type: ignore[arg-type]
        )

    assert source.content_text == "old content"
    assert session.deleted_old_chunks is False
    assert session.committed is False


@pytest.mark.asyncio
async def test_delete_source_removes_source_when_confirmed() -> None:
    source = DocumentSource(
        id=10,
        public_id="88888888-8888-4888-8888-888888888888",
        title="old",
        source_type="text",
        uri="text:old",
        content_text="old content",
        content_hash=sha256(b"old content").hexdigest(),
    )
    session = FakeSession(source_by_public_id=source)

    await delete_source(session, source.public_id, confirm=True)

    assert session.deleted_source is True
    assert session.committed is True


@pytest.mark.asyncio
async def test_create_category_normalizes_and_rejects_duplicates() -> None:
    class FakeCategorySession:
        def __init__(self, existing: Category | None = None) -> None:
            self.existing = existing
            self.added: list[Category] = []
            self.committed = False

        async def scalar(self, statement: object) -> Category | None:
            _ = statement
            return self.existing

        def add(self, entity: object) -> None:
            assert isinstance(entity, Category)
            entity.id = 10
            self.added.append(entity)

        async def commit(self) -> None:
            self.committed = True

        async def refresh(self, entity: object) -> None:
            _ = entity

    session = FakeCategorySession()

    category = await create_category(session, "  Finance  ")  # type: ignore[arg-type]

    assert category.name == "finance"
    assert session.committed is True

    with pytest.raises(CategoryConflictError):
        await create_category(
            FakeCategorySession(existing=Category(id=1, name="finance")),  # type: ignore[arg-type]
            "FINANCE",
        )


@pytest.mark.asyncio
async def test_search_knowledge_returns_similarity_scores() -> None:
    results = await search_knowledge(
        session=FakeSession(),
        query="find this",
        limit=5,
        embedding_client=FakeEmbeddingClient(),
    )

    assert results == [
        KnowledgeChunkRead(
            id=1,
            source_id="99999999-9999-4999-8999-999999999999",
            source_title="Stored Source",
            source_type="text",
            uri="text:Stored Source",
            categories=[{"id": 3, "name": "docs"}],
            location={
                "chunk_index": 0,
                "page": None,
                "section": "Intro",
                "start_char": 0,
                "end_char": 14,
            },
            content="stored content",
            score=0.8,
            metadata={"note_type": "decision"},
        )
    ]


@pytest.mark.asyncio
async def test_search_knowledge_filters_results_below_min_score() -> None:
    session = FakeSession()
    low_score_row = session.rows[0]

    high_score_source = DocumentSource(
        id=4,
        public_id="88888888-8888-4888-8888-888888888888",
        title="High Score Source",
        source_type="text",
        uri="text:High Score Source",
        content_text="approved content",
        content_hash=sha256(b"approved content").hexdigest(),
    )
    high_score_source.categories = [Category(id=3, name="docs")]
    high_score_chunk = KnowledgeChunk(
        id=2,
        source_id=4,
        content="approved content",
        metadata_json={
            "location": {"chunk_index": 1, "start_char": 0, "end_char": 16},
        },
    )
    session.rows = [
        low_score_row,
        FakeRow(
            KnowledgeChunk=high_score_chunk,
            DocumentSource=high_score_source,
            distance=0.1,
        ),
    ]

    results = await search_knowledge(
        session=session,
        query="find this",
        limit=5,
        embedding_client=FakeEmbeddingClient(),
        min_score=0.85,
    )

    assert [result.id for result in results] == [2]
    assert results[0].score == 0.9


@pytest.mark.asyncio
async def test_search_knowledge_keeps_score_equal_to_min_score() -> None:
    results = await search_knowledge(
        session=FakeSession(),
        query="find this",
        limit=5,
        embedding_client=FakeEmbeddingClient(),
        min_score=0.8,
    )

    assert [result.id for result in results] == [1]


@pytest.mark.asyncio
async def test_search_knowledge_logs_filtering_without_query_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger="backend.app.services.search"):
        await search_knowledge(
            session=FakeSession(),
            query="sensitive customer question",
            limit=5,
            embedding_client=FakeEmbeddingClient(),
            min_score=0.9,
        )

    record = next(
        record
        for record in caplog.records
        if record.message == "knowledge_search_relevance_filter"
    )
    assert record.threshold == 0.9
    assert record.threshold_source == "request"
    assert record.raw_count == 1
    assert record.filtered_count == 0
    assert record.min_score == 0.8
    assert record.max_score == 0.8
    assert "sensitive customer question" not in record.__dict__.values()


def test_filter_results_by_score_rejects_missing_and_non_finite_scores() -> None:
    template = KnowledgeChunkRead(
        id=1,
        source_id="99999999-9999-4999-8999-999999999999",
        source_title="Stored Source",
        source_type="text",
        uri="text:Stored Source",
        categories=[{"id": 3, "name": "docs"}],
        location={
            "chunk_index": 0,
            "page": None,
            "section": "Intro",
            "start_char": 0,
            "end_char": 14,
        },
        content="stored content",
        score=0.8,
        metadata={},
    )
    results = [
        template.model_copy(update={"id": 1, "score": None}),
        template.model_copy(update={"id": 2, "score": math.nan}),
        template.model_copy(update={"id": 3, "score": math.inf}),
        template.model_copy(update={"id": 4, "score": "0.9"}),
        template.model_copy(update={"id": 5, "score": 0.9}),
    ]

    assert [result.id for result in filter_results_by_score(results, 0.5)] == [5]


def test_fuse_hybrid_results_promotes_exact_text_matches_without_duplicates() -> None:
    vector_chunk = build_test_chunk(chunk_id=1, content="semantic result", score=0.91)
    shared_chunk = build_test_chunk(chunk_id=2, content="ERR_CONN_RESET details", score=0.7)
    text_only_chunk = build_test_chunk(chunk_id=3, content="ABC-1234 incident", score=None)

    results = fuse_hybrid_results(
        vector_results=[vector_chunk, shared_chunk],
        text_results=[
            TextSearchChunk(chunk=shared_chunk.model_copy(update={"score": None}), text_rank=1.0),
            TextSearchChunk(chunk=text_only_chunk, text_rank=0.9),
        ],
        limit=5,
        min_score=0.35,
        include_match_reasons=True,
    )

    assert [result.id for result in results] == [2, 1, 3]
    assert results[0].score == 0.7
    assert results[0].match_reasons == ["vector", "text"]
    assert results[2].score is None
    assert results[2].match_reasons == ["text"]


def test_fuse_hybrid_results_keeps_text_only_when_vector_score_is_filtered() -> None:
    low_vector_chunk = build_test_chunk(chunk_id=1, content="weak semantic", score=0.2)
    text_only_chunk = build_test_chunk(chunk_id=2, content="ERR_CONN_RESET", score=None)

    results = fuse_hybrid_results(
        vector_results=[low_vector_chunk],
        text_results=[TextSearchChunk(chunk=text_only_chunk, text_rank=1.0)],
        limit=5,
        min_score=0.8,
    )

    assert [result.id for result in results] == [2]
    assert not hasattr(results[0], "match_reasons")


@pytest.mark.asyncio
async def test_answer_knowledge_uses_search_sources() -> None:
    answer, sources = await answer_knowledge(
        session=FakeSession(),
        query="question",
        limit=5,
        embedding_client=FakeEmbeddingClient(),
        answer_client=FakeAnswerClient(),
    )

    assert answer == "answer for question with 1 sources"
    assert sources[0].content == "stored content"


@pytest.mark.asyncio
async def test_answer_knowledge_uses_empty_sources_when_scores_are_filtered() -> None:
    answer_client = FakeAnswerClient()

    answer, sources = await answer_knowledge(
        session=FakeSession(),
        query="question",
        limit=5,
        embedding_client=FakeEmbeddingClient(),
        answer_client=answer_client,
        min_score=0.9,
    )

    assert answer == "answer for question with 0 sources"
    assert sources == []
    assert answer_client.sources_seen == []


def build_test_chunk(
    chunk_id: int,
    content: str,
    score: float | None,
) -> KnowledgeChunkRead:
    return KnowledgeChunkRead(
        id=chunk_id,
        source_id="99999999-9999-4999-8999-999999999999",
        source_title="Stored Source",
        source_type="text",
        uri="text:Stored Source",
        categories=[{"id": 3, "name": "docs"}],
        location={
            "chunk_index": chunk_id,
            "page": None,
            "section": None,
            "start_char": 0,
            "end_char": len(content),
        },
        content=content,
        score=score,
        metadata={},
    )


@pytest.mark.asyncio
async def test_openai_embedding_client_requires_api_key() -> None:
    client = OpenAIEmbeddingClient(
        Settings(
            llm_provider="api",
            api_key="",
            api_llm_base_url="https://api.openai.com/v1",
            vector_dim=3,
        )
    )

    with pytest.raises(EmbeddingConfigurationError):
        await client.embed_texts(["content"])


@pytest.mark.asyncio
async def test_answer_client_requires_api_key_for_api_provider() -> None:
    client = OpenAICompatibleAnswerClient(Settings(llm_provider="api", api_key=""))

    with pytest.raises(LLMConfigurationError):
        await client.answer("question", [])
