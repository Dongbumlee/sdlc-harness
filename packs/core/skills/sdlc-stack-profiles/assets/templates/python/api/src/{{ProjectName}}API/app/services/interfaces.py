from typing import Protocol

from app.services.models import Item, ItemCreate


class IItemRepository(Protocol):
    """Storage contract for items. Replace the in-memory implementation
    with a database-backed one without touching the service or routers."""

    async def add_async(self, item: ItemCreate) -> Item: ...

    async def get_async(self, item_id: int) -> Item | None: ...

    async def list_async(self) -> list[Item]: ...


class IItemService(Protocol):
    """Service contract used by the routers."""

    async def create_item_async(self, request: ItemCreate) -> Item: ...

    async def get_item_async(self, item_id: int) -> Item | None: ...

    async def list_items_async(self) -> list[Item]: ...
