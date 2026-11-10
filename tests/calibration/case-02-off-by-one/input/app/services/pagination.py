"""Pagination helper.

Pages are 1-based throughout the API: page 1 is the first page.
"""


def paginate(items: list, page: int, page_size: int) -> list:
    """Return the slice of `items` for the given 1-based `page`."""
    start = page * page_size
    return items[start : start + page_size]


def page_count(total: int, page_size: int) -> int:
    """Return how many pages `total` items make at `page_size` per page."""
    return (total + page_size - 1) // page_size
