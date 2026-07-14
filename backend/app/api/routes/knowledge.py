from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...schemas.knowledge import (
    CategoryRead,
    KnowledgeAnswerRequest,
    KnowledgeAnswerResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeTextIngestRequest,
    KnowledgeUploadRequest,
    KnowledgeUploadResponse,
)
from ...services.embeddings import (
    EmbeddingConfigurationError,
    EmbeddingError,
    build_embedding_client,
)
from ...services.knowledge import (
    CategoryNotFoundError,
    EmptyDocumentError,
    FileTooLargeError,
    KnowledgeIngestionError,
    UnsupportedFileTypeError,
    answer_knowledge,
    ingest_plain_text,
    ingest_uploaded_file,
    list_categories,
    list_sources,
    search_knowledge,
)
from ...services.rag import LLMConfigurationError, LLMError, build_answer_client

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/search", response_model=KnowledgeSearchResponse)
async def knowledge_search(
    payload: KnowledgeSearchRequest,
    session: AsyncSession = Depends(get_session),
) -> KnowledgeSearchResponse:
    try:
        results = await search_knowledge(
            session=session,
            query=payload.query,
            limit=payload.limit,
            category_id=payload.category_id,
            embedding_client=build_embedding_client(),
        )
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
) -> KnowledgeUploadResponse:
    content = await file.read()

    try:
        source, chunks_created = await ingest_uploaded_file(
            session=session,
            filename=file.filename or "upload",
            content=content,
            category_id=payload.category_id,
            embedding_client=build_embedding_client(),
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
        category_id=source.category_id,
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
) -> KnowledgeUploadResponse:
    try:
        source, chunks_created = await ingest_plain_text(
            session=session,
            title=payload.title,
            content=payload.content,
            category_id=payload.category_id,
            embedding_client=build_embedding_client(),
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
        category_id=source.category_id,
        chunks_created=chunks_created,
    )


@router.post("/answer", response_model=KnowledgeAnswerResponse)
async def knowledge_answer(
    payload: KnowledgeAnswerRequest,
    session: AsyncSession = Depends(get_session),
) -> KnowledgeAnswerResponse:
    try:
        answer, sources = await answer_knowledge(
            session=session,
            query=payload.query,
            limit=payload.limit,
            category_id=payload.category_id,
            embedding_client=build_embedding_client(),
            answer_client=build_answer_client(),
        )
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
) -> list[dict[str, str | int]]:
    return await list_sources(session)


@router.get("/categories", response_model=list[CategoryRead])
async def knowledge_categories(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, str | int]]:
    return await list_categories(session)
