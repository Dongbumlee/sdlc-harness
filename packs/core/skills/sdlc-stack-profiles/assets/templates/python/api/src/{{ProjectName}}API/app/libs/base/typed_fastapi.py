from fastapi import FastAPI

from app.libs.application.context import AppContext


class TypedFastAPI(FastAPI):
    """FastAPI application that carries the AppContext.

    Routers and dependencies resolve services through the context instead
    of importing concrete implementations.
    """

    def set_app_context(self, context: AppContext) -> None:
        self.app_context = context

    def get_app_context(self) -> AppContext:
        return self.app_context
