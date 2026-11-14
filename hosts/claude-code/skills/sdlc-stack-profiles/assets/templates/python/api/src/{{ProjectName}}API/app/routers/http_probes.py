from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.get("/health/ready")
async def ready():
    return {"status": "ready"}
