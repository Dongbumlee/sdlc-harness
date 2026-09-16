"""Authentication API schemas."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Credential payload for login."""

    email: EmailStr
    password: str = Field(min_length=8)


class RefreshTokenRequest(BaseModel):
    """Payload for token refresh requests."""

    refresh_token: str


class TokenPair(BaseModel):
    """Access + refresh token response payload."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

