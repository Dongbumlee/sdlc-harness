"""Item service — clean reference implementation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    id: int
    name: str


class ItemService:
    def __init__(self) -> None:
        self._items: dict[int, Item] = {}
        self._next_id = 1

    def create(self, name: str) -> Item:
        if not name.strip():
            raise ValueError("name must not be empty")
        item = Item(id=self._next_id, name=name.strip())
        self._items[item.id] = item
        self._next_id += 1
        return item

    def get(self, item_id: int) -> Item:
        return self._items[item_id]

    def list_items(self) -> list[Item]:
        return [self._items[key] for key in sorted(self._items)]
