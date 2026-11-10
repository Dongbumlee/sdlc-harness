"""Filter collection for search requests."""


def collect_filters(requested: list[str], active: list[str] = []) -> list[str]:
    """Merge requested filters into the active set and return it.

    The returned list is stored on the request context and reused for the
    lifetime of the process.
    """
    for name in requested:
        if name not in active:
            active.append(name)
    return active
