# {{ProjectName}}

<!-- One line: what the library does and who uses it. The design
phase expands this stub into the full project README. -->

## Install

```bash
pip install {{project-name}}
```

## Quickstart

```python
from {{project_name}} import slugify, truncate

slugify("Hello, World!")  # 'hello-world'
truncate("hello world", 8)  # 'hello w…'
```

The same example ships as a runnable file (`examples/quickstart.py`)
that CI executes, and as doctests inside the package — the quickstart
cannot drift from the library it demonstrates.

## Supported versions

Python 3.10–3.13. The ranges declared in `pyproject.toml` are the
contract, and they are tested, not aspirational: CI runs the test
suite on every supported Python version and once against the lowest
allowed dependency resolution.

## Versioning and deprecation

This library follows strict Semantic Versioning. The public surface
is exactly the names in `{{project_name}}.__all__`; anything else is
internal and may change without notice. Deprecation path: a public
name is marked deprecated (a runtime `DeprecationWarning` plus a
changelog entry) in one release and removed no earlier than the
next major version. CI diffs the public API against the last
release, so an accidental breaking change fails the PR instead of
a consumer's build.

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability.

## Changelog

See [CHANGELOG.md](CHANGELOG.md). Releases are cut from version
tags (`vX.Y.Z`) that must match the version in `pyproject.toml`:
the release workflow verifies the tagged tree, builds the sdist
and wheel, smoke-tests the wheel in a clean environment, and
publishes to PyPI by trusted publishing (no stored registry
token) before creating the GitHub Release.
