from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
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
    KnowledgeSourceDetail,
    KnowledgeSourcePatchRequest,
    KnowledgeSourceRead,
    KnowledgeTextIngestRequest,
    KnowledgeUploadRequest,
    KnowledgeUploadResponse,
    TagRead,
    TagWrite,
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
from ...services.ingestion import (
    DuplicateSourceContentError,
    KnowledgeIngestionError,
    ingest_plain_text,
)
from ...services.ingestion import ingest_uploaded_file
from ...services.rag import AnswerClient, LLMConfigurationError, LLMError
from ...services.search import answer_knowledge, list_sources, search_knowledge
from ...services.sources import (
    SourceDeleteConfirmationError,
    SourceNotFoundError,
    delete_source,
    get_source_detail,
    update_source,
)
from ...services.tags import (
    TagConflictError,
    TagInUseError,
    TagNotFoundError,
    autocomplete_tags,
    create_tag,
    delete_tag,
    list_tags,
    update_tag,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


async def parse_text_ingest_payload(request: Request) -> KnowledgeTextIngestRequest:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith(("multipart/form-data", "application/x-www-form-urlencoded")):
        form = await request.form()
        payload = {
            "title": form.get("title"),
            "content": form.get("content"),
            "category_ids": form.getlist("category_ids"),
        }
        tag_ids = form.getlist("tag_ids")
        if tag_ids:
            payload["tag_ids"] = tag_ids
    else:
        payload = await request.json()

    try:
        return KnowledgeTextIngestRequest.model_validate(payload)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


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
            tag_ids=payload.tag_ids,
            min_score=payload.min_score,
            include_match_reasons=payload.include_match_reasons,
            embedding_client=embedding_client,
        )
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TagNotFoundError as exc:
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
            tag_ids=payload.tag_ids,
            embedding_client=embedding_client,
        )
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)
        ) from exc
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TagNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateSourceContentError as exc:
        raise _duplicate_source_http_error(exc) from exc
    except (UnsupportedFileTypeError, EmptyDocumentError, KnowledgeIngestionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EmbeddingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return KnowledgeUploadResponse(
        source_id=source.public_id,
        title=source.title,
        categories=source.categories,
        tags=getattr(source, "tags", []),
        chunks_created=chunks_created,
    )


@router.post(
    "/texts",
    response_model=KnowledgeUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_knowledge_text(
    payload: KnowledgeTextIngestRequest = Depends(parse_text_ingest_payload),
    session: AsyncSession = Depends(get_session),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
) -> KnowledgeUploadResponse:
    try:
        source, chunks_created = await ingest_plain_text(
            session=session,
            title=payload.title,
            content=payload.content,
            category_ids=payload.category_ids,
            tag_ids=payload.tag_ids,
            embedding_client=embedding_client,
        )
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TagNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateSourceContentError as exc:
        raise _duplicate_source_http_error(exc) from exc
    except (EmptyDocumentError, KnowledgeIngestionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EmbeddingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return KnowledgeUploadResponse(
        source_id=source.public_id,
        title=source.title,
        categories=source.categories,
        tags=getattr(source, "tags", []),
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
            tag_ids=payload.tag_ids,
            min_score=payload.min_score,
            include_match_reasons=payload.include_match_reasons,
            embedding_client=embedding_client,
            answer_client=answer_client,
        )
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TagNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (EmbeddingConfigurationError, LLMConfigurationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except (EmbeddingError, LLMError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return KnowledgeAnswerResponse(query=payload.query, answer=answer, sources=sources)


@router.get("/sources", response_model=list[KnowledgeSourceRead])
async def knowledge_sources(
    session: AsyncSession = Depends(get_session),
) -> list[KnowledgeSourceRead]:
    return await list_sources(session)


@router.get("/sources/{source_id}", response_model=KnowledgeSourceDetail)
async def knowledge_source_detail(
    source_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> KnowledgeSourceDetail:
    try:
        return await get_source_detail(session, str(source_id))
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/sources/{source_id}", response_model=KnowledgeSourceDetail)
async def patch_knowledge_source(
    source_id: UUID,
    payload: KnowledgeSourcePatchRequest,
    session: AsyncSession = Depends(get_session),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
) -> KnowledgeSourceDetail:
    try:
        source, _chunks_created = await update_source(
            session=session,
            source_id=str(source_id),
            embedding_client=embedding_client,
            title=payload.title,
            category_ids=payload.category_ids,
            tag_ids=payload.tag_ids,
            content=payload.content,
        )
        return source
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TagNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateSourceContentError as exc:
        raise _duplicate_source_http_error(exc) from exc
    except (EmptyDocumentError, KnowledgeIngestionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EmbeddingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_source(
    source_id: UUID,
    confirm: bool = False,
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        await delete_source(session, str(source_id), confirm=confirm)
    except SourceDeleteConfirmationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/categories", response_model=list[CategoryRead])
async def knowledge_categories(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, str | int]]:
    return await list_categories(session)


@router.get("/tags", response_model=list[TagRead])
async def knowledge_tags(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, str | int]]:
    return await list_tags(session)


@router.get("/tags/autocomplete", response_model=list[TagRead])
async def autocomplete_knowledge_tags(
    q: str,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, str | int]]:
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="limit must be between 1 and 50.",
        )
    return await autocomplete_tags(session, q, limit)


@router.post(
    "/tags",
    response_model=TagRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_tag(
    payload: TagWrite,
    session: AsyncSession = Depends(get_session),
) -> TagRead:
    try:
        return await create_tag(session, payload.name)
    except TagConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/tags/{tag_id}", response_model=TagRead)
async def update_knowledge_tag(
    tag_id: int,
    payload: TagWrite,
    session: AsyncSession = Depends(get_session),
) -> TagRead:
    try:
        return await update_tag(session, tag_id, payload.name)
    except TagNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TagConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_tag(
    tag_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        await delete_tag(session, tag_id)
    except TagNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TagInUseError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


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


def _duplicate_source_http_error(exc: DuplicateSourceContentError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "message": str(exc),
            "existing_source_id": exc.existing_source.public_id,
        },
    )
