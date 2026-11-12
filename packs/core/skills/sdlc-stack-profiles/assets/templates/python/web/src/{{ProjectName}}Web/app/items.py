"""The sample vertical slice: an in-memory items store.

Replace with the real data layer; the page, form, and tests around
it are the template. Items are the same sample resource the API
templates use, here rendered server-side instead of serialized.
"""

from dataclasses import dataclass, field


@dataclass
class ItemStore:
    """A tiny in-memory store: ids from 1, insertion order kept."""

    _items: dict[int, str] = field(default_factory=dict)
    _next_id: int = 1

    def list_items(self) -> list[tuple[int, str]]:
        return sorted(self._items.items())

    def add(self, name: str) -> int:
        item_id = self._next_id
        self._next_id += 1
        self._items[item_id] = name
        return item_id


def seeded_store() -> ItemStore:
    store = ItemStore()
    store.add("First item")
    store.add("Second item")
    return store
