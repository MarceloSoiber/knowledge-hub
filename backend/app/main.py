import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.health import router as health_router
from .api.routes.knowledge import router as knowledge_router
from .core.auth import require_auth_token
from .core.settings import get_settings
from .db.init import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Initializing database")
    await init_db()
    logger.info("Database initialization completed")
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(
        knowledge_router,
        prefix="/api/v1",
        dependencies=[Depends(require_auth_token)],
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "MCP Knowledge Hub API"}

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
