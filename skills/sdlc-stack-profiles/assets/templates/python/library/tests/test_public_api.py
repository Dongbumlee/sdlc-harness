"""Black-box tests for {{ProjectName}}.

These tests exercise the library exactly as a consumer would:
imports come from the package root only, never from internal
modules. A test that reaches into internals locks in the wrong
contract.
"""

import pytest

import {{project_name}}
from {{project_name}} import slugify, truncate


def test_public_surface_is_exactly_as_declared() -> None:
    assert {{project_name}}.__all__ == ["slugify", "truncate"]


def test_slugify() -> None:
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_folds_accents() -> None:
    assert slugify("Déjà vu") == "deja-vu"


def test_truncate() -> None:
    assert truncate("hello world", 8) == "hello w…"
    assert truncate("short", 10) == "short"


def test_truncate_rejects_negative_length() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        truncate("abc", -1)
