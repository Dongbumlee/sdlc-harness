"""ASGI entry point used by uvicorn to start the service."""

from app.application import create_app

app = create_app()

