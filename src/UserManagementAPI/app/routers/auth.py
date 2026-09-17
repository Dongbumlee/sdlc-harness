"""Authentication endpoints for token issuance and refresh."""

from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenPair
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest) -> TokenPair:
    """Authenticate a user and issue access + refresh tokens."""
    token_pair = await auth_service.authenticate_and_issue_tokens(payload)
    if token_pair is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return token_pair


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(payload: RefreshTokenRequest) -> TokenPair:
    """Refresh a token pair using a valid refresh token."""
    token_pair = auth_service.refresh_tokens(payload.refresh_token)
    if token_pair is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return token_pair

