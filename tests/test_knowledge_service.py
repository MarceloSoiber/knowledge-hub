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
from backend.app.services.knowledge import (
    CategoryNotFoundError,
    UnsupportedFileTypeError,
    answer_knowledge,
    chunk_text,
    extract_text,
    ingest_plain_text,
    ingest_uploaded_file,
    list_categories,
    search_knowledge,
)
from backend.app.services.rag import LLMConfigurationError, OpenAICompatibleAnswerClient


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


@dataclass
class FakeCategoryRow:
    id: int
    name: str


class FakeSession:
    def __init__(
        self,
        existing_source: DocumentSource | None = None,
        category: Category | None = None,
    ) -> None:
        self.existing_source = existing_source
        self.category = category or Category(id=3, name="docs")
        self.added: list[object] = []
        self.deleted_old_chunks = False
        self.committed = False
        self.rows = [FakeRow(id=1, source_id=2, content="stored content", distance=0.2)]

    async def scalar(self, statement: object) -> DocumentSource | None:
        _ = statement
        return self.existing_source

    async def get(self, entity: object, entity_id: int) -> Category | None:
        assert entity is Category
        if self.category is not None and self.category.id == entity_id:
            return self.category
        return None

    async def execute(self, statement: object) -> FakeExecuteResult:
        if statement.__class__.__name__ == "Delete":
            self.deleted_old_chunks = True
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

    monkeypatch.setattr("backend.app.services.knowledge.build_pdf_reader", FakePdfReader)

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

    monkeypatch.setattr("backend.app.services.knowledge.build_pdf_reader", FakePdfReader)

    assert extract_text("paper.pdf", b"%PDF") == "Receita de Vendas de Imóveis Fonte: TRBL11"


def test_chunk_text_uses_overlap() -> None:
    chunks = chunk_text("abcdefghij", chunk_size=6, overlap=2)

    assert chunks == ["abcdef", "efghij"]


def test_chunk_text_prefers_sentence_boundaries() -> None:
    chunks = chunk_text("Primeira frase. Segunda frase. Terceira frase.", chunk_size=32, overlap=0)

    assert chunks == ["Primeira frase. Segunda frase.", "Terceira frase."]


def test_knowledge_schemas_trim_and_reject_blank_values() -> None:
    search = KnowledgeSearchRequest(query="  find me  ", category_id=3)
    answer = KnowledgeAnswerRequest(query="  answer me  ")
    upload = KnowledgeUploadRequest(category_id=4)
    text = KnowledgeTextIngestRequest(
        title="  Sprint notes  ",
        category_id=5,
        content="  decision log  ",
    )

    assert search.query == "find me"
    assert search.category_id == 3
    assert answer.query == "answer me"
    assert upload.category_id == 4
    assert text.title == "Sprint notes"
    assert text.category_id == 5
    assert text.content == "decision log"

    with pytest.raises(ValidationError):
        KnowledgeSearchRequest(query="   ")

    with pytest.raises(ValidationError):
        KnowledgeAnswerRequest(query="   ")

    with pytest.raises(ValidationError):
        KnowledgeUploadRequest(category_id=0)

    with pytest.raises(ValidationError):
        KnowledgeTextIngestRequest(title="   ", category_id=3, content="text")

    with pytest.raises(ValidationError):
        KnowledgeTextIngestRequest(title="notes", category_id=3, content="   ")


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
        category_id=2,
        source_type="upload",
        uri="upload:manuals:notes.md",
    )
    session = FakeSession(
        existing_source=source,
        category=Category(id=3, name="manuals"),
    )

    updated_source, chunks_created = await ingest_uploaded_file(
        session=session,
        filename="notes.md",
        content=b"new content",
        category_id=3,
        embedding_client=FakeEmbeddingClient(),
    )

    assert updated_source.id == 7
    assert updated_source.title == "notes.md"
    assert updated_source.category_id == 3
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
        category_id=3,
        embedding_client=embedding_client,
    )

    assert source.id == 99
    assert source.title == "Meeting notes"
    assert source.category_id == 3
    assert source.source_type == "text"
    assert source.uri == "text:docs:Meeting notes"
    assert chunks_created == 1
    assert embedding_client.inputs == [["Linha um.\nLinha dois."]]
    assert session.committed is True


@pytest.mark.asyncio
async def test_ingest_plain_text_replaces_existing_text_source() -> None:
    source = DocumentSource(
        id=8,
        title="old title",
        category_id=2,
        source_type="text",
        uri="text:docs:notes",
    )
    session = FakeSession(existing_source=source)

    updated_source, chunks_created = await ingest_plain_text(
        session=session,
        title="notes",
        content="updated content",
        category_id=3,
        embedding_client=FakeEmbeddingClient(),
    )

    assert updated_source.id == 8
    assert updated_source.title == "notes"
    assert updated_source.category_id == 3
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
            category_id=999,
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
