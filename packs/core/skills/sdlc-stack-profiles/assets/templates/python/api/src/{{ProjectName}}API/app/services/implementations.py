from app.services.interfaces import IItemRepository
from app.services.models import Item, ItemCreate


class InMemoryItemRepository:
    """In-memory repository (sample slice).

    Swap for a persistent implementation behind IItemRepository when the
    project adopts a real data store.
    """

    def __init__(self):
        self._items: dict[int, Item] = {}
        self._next_id = 1

    async def add_async(self, item: ItemCreate) -> Item:
        stored = Item(id=self._next_id, name=item.name, description=item.description)
        self._items[stored.id] = stored
        self._next_id += 1
        return stored

    async def get_async(self, item_id: int) -> Item | None:
        return self._items.get(item_id)

    async def list_async(self) -> list[Item]:
        return list(self._items.values())


class ItemService:
    def __init__(self, repository: IItemRepository):
        self._repository = repository

    async def create_item_async(self, request: ItemCreate) -> Item:
        return await self._repository.add_async(request)

    async def get_item_async(self, item_id: int) -> Item | None:
        return await self._repository.get_async(item_id)

    async def list_items_async(self) -> list[Item]:
        return await self._repository.list_async()
