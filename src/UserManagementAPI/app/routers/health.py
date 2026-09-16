"""Health and readiness endpoints for orchestration probes."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.database import async_session_factory

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe endpoint."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check() -> JSONResponse:
    """Readiness probe endpoint with a lightweight database check."""
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return JSONResponse(content={"status": "ready"}, status_code=status.HTTP_200_OK)
    except Exception:
        return JSONResponse(content={"status": "not_ready"}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

