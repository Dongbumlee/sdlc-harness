"""The CLI's library core: the testable logic lives here, free of
argument parsing and I/O, and the commands in `cli` are a thin shell
over it.
"""


def slugify(text: str) -> str:
    """Convert text to a lowercase, hyphen-separated slug.

    Letters and digits are kept, every other run of characters
    becomes one hyphen, and leading/trailing hyphens are trimmed.

    >>> slugify("Hello, World!")
    'hello-world'
    """
    out: list[str] = []
    last_hyphen = True  # trims leading separators
    for char in text:
        if char.isalnum():
            out.append(char.lower())
            last_hyphen = False
        elif not last_hyphen:
            out.append("-")
            last_hyphen = True
    return "".join(out).rstrip("-")


def truncate(text: str, max_length: int) -> str:
    """Shorten text to at most `max_length` characters.

    An ellipsis marks truncation. A `max_length` below 1 returns an
    empty string.

    >>> truncate("a longer sentence", 6)
    'a lon…'
    """
    if max_length < 1:
        return ""
    if len(text) <= max_length:
        return text
    if max_length == 1:
        return "…"
    return text[: max_length - 1] + "…"
