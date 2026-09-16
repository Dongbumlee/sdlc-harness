"""Application factory and startup wiring for the User Management API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.correlation import CorrelationIdMiddleware
from app.routers import health


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Lifespan hook for startup/shutdown initialization."""
    settings = get_settings()
    configure_logging(settings.log_level)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.include_router(health.router, tags=["health"])
    app.include_router(api_router, prefix=settings.api_prefix)
    return app
