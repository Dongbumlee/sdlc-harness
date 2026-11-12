"""Sample handlers. Replace with your own job types; the contract is
what matters: return the effect's result string, raise
PermanentError for payloads that can never succeed, and let
everything else surface as retryable.
"""

from __future__ import annotations

from .worker import Handler, PermanentError


def slugify(payload: dict) -> str:
    """Turn payload['text'] into a slug — the sample job's effect.

    Lowercase, letters and digits kept, every other run of characters
    becomes one hyphen, leading/trailing hyphens trimmed — the same
    sample semantics as the other bundled templates.
    """
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise PermanentError("payload.text must be a non-empty string")
    out: list[str] = []
    last_hyphen = True  # trims leading separators
    for char in text.lower():
        if char.isalnum():
            out.append(char)
            last_hyphen = False
        elif not last_hyphen:
            out.append("-")
            last_hyphen = True
    return "".join(out).rstrip("-")


HANDLERS: dict[str, Handler] = {"slugify": slugify}
