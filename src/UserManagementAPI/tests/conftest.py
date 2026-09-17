"""Shared pytest fixtures for async API testing."""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def api_client() -> AsyncClient:
    """Create an async test client wired directly to the ASGI app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client

