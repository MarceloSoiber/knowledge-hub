from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...schemas.configuration import AIConfigurationRead, AIConfigurationWrite
from ...services.config import (
    ConfigurationError,
    VectorDimensionChangeRequired,
    get_effective_ai_configuration,
    update_ai_configuration,
)


router = APIRouter(prefix="/configuration", tags=["configuration"])


@router.get("/ai", response_model=AIConfigurationRead)
async def get_ai_configuration(
    session: AsyncSession = Depends(get_session),
) -> AIConfigurationRead:
    try:
        return await get_effective_ai_configuration(session)
    except ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.put("/ai", response_model=AIConfigurationRead)
async def put_ai_configuration(
    payload: AIConfigurationWrite,
    session: AsyncSession = Depends(get_session),
) -> AIConfigurationRead:
    try:
        return await update_ai_configuration(session, payload)
    except VectorDimensionChangeRequired as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
