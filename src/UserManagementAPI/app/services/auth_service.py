"""Authentication service for issuing and validating JWT tokens."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.schemas.auth import LoginRequest, TokenPair

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication and token lifecycle operations."""

    def __init__(self):
        self._settings = get_settings()

    async def authenticate_and_issue_tokens(self, payload: LoginRequest) -> TokenPair | None:
        """Placeholder auth flow; replace with repository-backed validation in implementation phase."""
        # This scaffold intentionally avoids business logic and uses a placeholder credential check.
        if payload.email != "admin@example.com" or payload.password != "adminpassword":
            return None
        subject = "00000000-0000-0000-0000-000000000001"
        return TokenPair(
            access_token=self._create_token(subject, self._settings.access_token_expire_minutes, "access"),
            refresh_token=self._create_token(subject, self._settings.refresh_token_expire_minutes, "refresh"),
        )

    def refresh_tokens(self, refresh_token: str) -> TokenPair | None:
        """Validate refresh token and return a new token pair."""
        payload = self.decode_token(refresh_token)
        if payload is None or payload.get("typ") != "refresh":
            return None
        subject = payload.get("sub")
        if not subject:
            return None
        return TokenPair(
            access_token=self._create_token(subject, self._settings.access_token_expire_minutes, "access"),
            refresh_token=self._create_token(subject, self._settings.refresh_token_expire_minutes, "refresh"),
        )

    def _create_token(self, subject: str, expires_in_minutes: int, token_type: str) -> str:
        """Create a signed JWT for access or refresh usage."""
        now = datetime.now(UTC)
        payload = {
            "sub": subject,
            "typ": token_type,
            "iat": now,
            "exp": now + timedelta(minutes=expires_in_minutes),
        }
        return jwt.encode(payload, self._settings.jwt_secret_key, algorithm=self._settings.jwt_algorithm)

    def _decode_token(self, token: str) -> dict | None:
        """Decode and validate a JWT token."""
        try:
            return jwt.decode(token, self._settings.jwt_secret_key, algorithms=[self._settings.jwt_algorithm])
        except jwt.PyJWTError:
            return None

    def decode_token(self, token: str) -> dict | None:
        """Public wrapper to decode a JWT token."""
        return self._decode_token(token)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash plaintext password for storage."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify plaintext password against hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def parse_subject_as_uuid(subject: str) -> UUID:
        """Convert token subject to UUID."""
        return UUID(subject)
