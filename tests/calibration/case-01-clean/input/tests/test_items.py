import pytest

from app.services.items import ItemService


def test_create_assigns_sequential_ids():
    service = ItemService()
    first = service.create("alpha")
    second = service.create("beta")
    assert (first.id, second.id) == (1, 2)


def test_create_rejects_empty_name():
    service = ItemService()
    with pytest.raises(ValueError):
        service.create("  ")


def test_get_missing_item_raises_key_error():
    service = ItemService()
    with pytest.raises(KeyError):
        service.get(999)
