"""User service layer for orchestrating repository operations."""

from uuid import UUID

from app.core.database import async_session_factory
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead


class UserService:
    """Application-facing service for user read operations."""

    async def get_user_profile(self, user_id: UUID) -> UserRead | None:
        """Resolve a user by ID and map it to an API schema."""
        async with async_session_factory() as session:
            repository = UserRepository(session)
            user = await repository.get_by_id(user_id)
            if user is None:
                return None
            return UserRead.model_validate(user)

