from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...api.dependencies import get_answer_client, get_embedding_client
from ...schemas.knowledge import (
    CategoryRead,
    CategoryWrite,
    KnowledgeAnswerRequest,
    KnowledgeAnswerResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeTextIngestRequest,
    KnowledgeUploadRequest,
    KnowledgeUploadResponse,
)
from ...services.embeddings import (
    EmbeddingClient,
    EmbeddingConfigurationError,
    EmbeddingError,
)
from ...services.categories import (
    CategoryConflictError,
    CategoryInUseError,
    CategoryNotFoundError,
    create_category,
    delete_category,
    list_categories,
    update_category,
)
from ...services.documents.extractors import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from ...services.ingestion import KnowledgeIngestionError, ingest_plain_text
from ...services.ingestion import ingest_uploaded_file
from ...services.rag import AnswerClient, LLMConfigurationError, LLMError
from ...services.search import answer_knowledge, list_sources, search_knowledge

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/search", response_model=KnowledgeSearchResponse)
async def knowledge_search(
    payload: KnowledgeSearchRequest,
    session: AsyncSession = Depends(get_session),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
) -> KnowledgeSearchResponse:
    try:
        results = await search_knowledge(
            session=session,
            query=payload.query,
            limit=payload.limit,
            category_ids=payload.category_ids,
            embedding_client=embedding_client,
        )
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmbeddingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return KnowledgeSearchResponse(query=payload.query, limit=payload.limit, results=results)


@router.post(
    "/uploads",
    response_model=KnowledgeUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_knowledge_file(
    file: UploadFile = File(...),
    payload: KnowledgeUploadRequest = Depends(KnowledgeUploadRequest.as_form),
    session: AsyncSession = Depends(get_session),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
) -> KnowledgeUploadResponse:
    content = await file.read()

    try:
        source, chunks_created = await ingest_uploaded_file(
            session=session,
            filename=file.filename or "upload",
            content=content,
            category_ids=payload.category_ids,
            embedding_client=embedding_client,
        )
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)
        ) from exc
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (UnsupportedFileTypeError, EmptyDocumentError, KnowledgeIngestionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EmbeddingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return KnowledgeUploadResponse(
        source_id=source.id,
        title=source.title,
        categories=source.categories,
        chunks_created=chunks_created,
    )


@router.post(
    "/texts",
    response_model=KnowledgeUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_knowledge_text(
    payload: KnowledgeTextIngestRequest,
    session: AsyncSession = Depends(get_session),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
) -> KnowledgeUploadResponse:
    try:
        source, chunks_created = await ingest_plain_text(
            session=session,
            title=payload.title,
            content=payload.content,
            category_ids=payload.category_ids,
            embedding_client=embedding_client,
        )
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (EmptyDocumentError, KnowledgeIngestionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EmbeddingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return KnowledgeUploadResponse(
        source_id=source.id,
        title=source.title,
        categories=source.categories,
        chunks_created=chunks_created,
    )


@router.post("/answer", response_model=KnowledgeAnswerResponse)
async def knowledge_answer(
    payload: KnowledgeAnswerRequest,
    session: AsyncSession = Depends(get_session),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
    answer_client: AnswerClient = Depends(get_answer_client),
) -> KnowledgeAnswerResponse:
    try:
        answer, sources = await answer_knowledge(
            session=session,
            query=payload.query,
            limit=payload.limit,
            category_ids=payload.category_ids,
            embedding_client=embedding_client,
            answer_client=answer_client,
        )
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (EmbeddingConfigurationError, LLMConfigurationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except (EmbeddingError, LLMError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return KnowledgeAnswerResponse(query=payload.query, answer=answer, sources=sources)


@router.get("/sources")
async def knowledge_sources(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    return await list_sources(session)


@router.get("/categories", response_model=list[CategoryRead])
async def knowledge_categories(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, str | int]]:
    return await list_categories(session)


@router.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_category(
    payload: CategoryWrite,
    session: AsyncSession = Depends(get_session),
) -> CategoryRead:
    try:
        return await create_category(session, payload.name)
    except CategoryConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/categories/{category_id}", response_model=CategoryRead)
async def update_knowledge_category(
    category_id: int,
    payload: CategoryWrite,
    session: AsyncSession = Depends(get_session),
) -> CategoryRead:
    try:
        return await update_category(session, category_id, payload.name)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CategoryConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        await delete_category(session, category_id)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CategoryInUseError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
