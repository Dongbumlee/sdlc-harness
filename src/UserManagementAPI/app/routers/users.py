"""User resource endpoints."""

from fastapi import APIRouter, Depends, status

from app.dependencies.security import get_current_user
from app.schemas.user import UserRead

router = APIRouter()


@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_me(current_user: UserRead = Depends(get_current_user)) -> UserRead:
    """Return the currently authenticated user profile."""
    return current_user

