"""Core text utilities for {{ProjectName}}.

The public surface is deliberately small: everything a consumer may
rely on is re-exported from the package root and listed in
``__all__``. Anything not re-exported is internal and may change
without notice.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["slugify", "truncate"]

_NON_SLUG_CHARS = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Return a URL-safe slug for *text*.

    Accents are folded to their ASCII base letters and every run of
    remaining non-alphanumeric characters becomes one hyphen.

    >>> slugify("Hello, World!")
    'hello-world'
    >>> slugify("Déjà vu")
    'deja-vu'
    """
    folded = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    )
    return _NON_SLUG_CHARS.sub("-", folded.strip().lower()).strip("-")


def truncate(text: str, max_length: int, *, ellipsis: str = "…") -> str:
    """Shorten *text* to at most *max_length* characters.

    Truncated text ends with *ellipsis*, which counts toward the
    limit. Text that already fits is returned unchanged.

    >>> truncate("hello world", 8)
    'hello w…'
    >>> truncate("short", 10)
    'short'
    """
    if max_length < 0:
        raise ValueError("max_length must be non-negative")
    if len(text) <= max_length:
        return text
    if max_length <= len(ellipsis):
        return ellipsis[:max_length]
    return text[: max_length - len(ellipsis)] + ellipsis
