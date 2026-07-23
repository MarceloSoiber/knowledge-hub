from fastapi import APIRouter

from ...core.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "app_name": settings.app_name, "environment": settings.environment}