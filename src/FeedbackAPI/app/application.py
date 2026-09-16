from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return FastAPI(title="FeedbackAPI", version="0.1.0")

