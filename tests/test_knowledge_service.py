from __future__ import annotations

from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from backend.app.cli.config import generate_auth_token, validate_auth_token
from backend.app.core.auth import is_valid_token
from backend.app.core.settings import Settings
from backend.app.db.models import Category, DocumentSource
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
from backend.app.services.documents.chunker import chunk_text
from backend.app.services.documents.extractors import UnsupportedFileTypeError, extract_text
from backend.app.services.ingestion import ingest_plain_text, ingest_uploaded_file
from backend.app.services.rag import LLMConfigurationError, OpenAICompatibleAnswerClient
from backend.app.services.search import answer_knowledge, search_knowledge


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.inputs: list[list[str]] = []

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.inputs.append(texts)
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeAnswerClient:
    async def answer(self, query: str, sources: list[KnowledgeChunkRead]) -> str:
        return f"answer for {query} with {len(sources)} sources"


@dataclass
class FakeRow:
    id: int
    source_id: int
    content: str
    distance: float


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
        categories: list[Category] | None = None,
    ) -> None:
        self.existing_source = existing_source
        self.categories = categories or [Category(id=3, name="docs")]
        self.added: list[object] = []
        self.deleted_old_chunks = False
        self.committed = False
        self.rows = [FakeRow(id=1, source_id=2, content="stored content", distance=0.2)]

    async def scalar(self, statement: object) -> DocumentSource | None:
        _ = statement
        return self.existing_source

    async def get(self, entity: object, entity_id: int) -> Category | None:
        assert entity is Category
        for category in self.categories:
            if category.id == entity_id:
                return category
        return None

    async def execute(self, statement: object) -> FakeExecuteResult:
        if statement.__class__.__name__ == "Delete":
            self.deleted_old_chunks = True
        if "categories" in str(statement):
            return FakeExecuteResult(self.categories)  # type: ignore[arg-type]
        return FakeExecuteResult(self.rows)

    def add(self, entity: object) -> None:
        if isinstance(entity, DocumentSource) and entity.id is None:
            entity.id = 99
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


def test_chunk_text_uses_overlap() -> None:
    chunks = chunk_text("abcdefghij", chunk_size=6, overlap=2)

    assert chunks == ["abcdef", "efghij"]


def test_chunk_text_prefers_sentence_boundaries() -> None:
    chunks = chunk_text("Primeira frase. Segunda frase. Terceira frase.", chunk_size=32, overlap=0)

    assert chunks == ["Primeira frase. Segunda frase.", "Terceira frase."]


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
async def test_ingest_uploaded_file_replaces_existing_source() -> None:
    source = DocumentSource(
        id=7,
        title="old.md",
        source_type="upload",
        uri="upload:notes.md",
    )
    session = FakeSession(
        existing_source=source,
        categories=[Category(id=3, name="manuals"), Category(id=4, name="docs")],
    )

    updated_source, chunks_created = await ingest_uploaded_file(
        session=session,
        filename="notes.md",
        content=b"new content",
        category_ids=[3, 4],
        embedding_client=FakeEmbeddingClient(),
    )

    assert updated_source.id == 7
    assert updated_source.title == "notes.md"
    assert [category.id for category in updated_source.categories] == [3, 4]
    assert chunks_created == 1
    assert session.deleted_old_chunks is True
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


@pytest.mark.asyncio
async def test_ingest_plain_text_replaces_existing_text_source() -> None:
    source = DocumentSource(
        id=8,
        title="old title",
        source_type="text",
        uri="text:notes",
    )
    session = FakeSession(existing_source=source)

    updated_source, chunks_created = await ingest_plain_text(
        session=session,
        title="notes",
        content="updated content",
        category_ids=[3],
        embedding_client=FakeEmbeddingClient(),
    )

    assert updated_source.id == 8
    assert updated_source.title == "notes"
    assert [category.id for category in updated_source.categories] == [3]
    assert updated_source.source_type == "text"
    assert chunks_created == 1
    assert session.deleted_old_chunks is True
    assert session.committed is True


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
        KnowledgeChunkRead(id=1, source_id=2, content="stored content", score=0.8)
    ]


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
