import os

from app.libs.base.application_base import Application_Base
from app.libs.base.typed_fastapi import TypedFastAPI
from app.routers import http_probes, items
from app.services.implementations import InMemoryItemRepository, ItemService
from app.services.interfaces import IItemRepository, IItemService


class Application(Application_Base):
    """Application composition root.

    Builds the FastAPI app, registers services in the application context
    (dependency injection), and wires the routers. Mirrors the harness's
    application pattern: main.py never creates a bare FastAPI() — it goes
    through this factory.
    """

    app: TypedFastAPI

    def __init__(self):
        super().__init__(
            env_file_path=os.path.join(os.path.dirname(__file__), ".env")
        )

    def initialize(self):
        config = self.application_context.configuration
        self.app = TypedFastAPI(title=config.app_name, version="0.1.0")
        self.app.set_app_context(self.application_context)

        # Health probes
        self.app.include_router(http_probes.router)

        # DI registration, then routers that depend on the registrations
        self._register_dependencies()
        self._config_routers()

    def _register_dependencies(self):
        repository = InMemoryItemRepository()
        self.application_context.add_singleton(IItemRepository, repository)
        self.application_context.add_singleton(
            IItemService, ItemService(repository)
        )

    def _config_routers(self):
        for router in (items.router,):
            self.app.include_router(router)
