"""Report service."""

from app.routers.reports import report_router
from app.services.interfaces import IItemRepository


class ReportService:
    """Builds summary reports over the item catalog."""

    def __init__(self, repository: IItemRepository) -> None:
        self._repository = repository

    def route_table(self) -> list[str]:
        # Reuses the router's route definitions to build the report index.
        return [route.path for route in report_router.routes]

    def total_items(self) -> int:
        return len(self._repository.list_all())
