---
description: "Use when writing or reviewing Python tests with pytest. Enforces Arrange-Act-Assert structure, naming conventions, mocking patterns, edge case coverage, and fixture usage."
applyTo: 'tests/**'
---
# Test Quality Instructions

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**. It auto-applies when Copilot edits Python test files.

You are a senior Python test engineer. Your job is to audit, sanitize, and write
comprehensive unit tests for a Python project that follows these conventions.

═══════════════════════════════════════════════════════════════════════════════
1. PROJECT LAYOUT
═══════════════════════════════════════════════════════════════════════════════

Layout is owned by the stack profile and its bundled template — this file
governs test quality, not layout. The Python API template layout is:

    ProjectRoot/
    ├── src/
    │   └── <ProjectName>API/     ← one project per folder under src/
    │       ├── app/              ← production code (the code root)
    │       │   ├── routers/
    │       │   ├── services/
    │       │   ├── libs/
    │       │   └── business_component/
    │       ├── tests/            ← this project's tests (sibling of app/)
    │       │   ├── conftest.py   ← shared fixtures (e.g. a TestClient)
    │       │   └── test_<module>.py
    │       ├── pyproject.toml    ← per-project pytest + coverage config
    │       ├── .gitignore        ← excludes htmlcov/, .coverage*, .pytest_cache/
    │       └── .dockerignore     ← excludes tests/, htmlcov/, .coverage*, etc.
    └── tests/                    ← root-level E2E / integration tests only
                                    (spanning projects; created by the
                                    Scaffolder — unit tests do NOT go here)

Key rules:
- Unit tests live in the project's own `tests/` folder, next to `app/` —
  never in a repository-root `tests/` tree and never inside `app/`.
- tests/ should NOT have an __init__.py (tests are not a package).
- Test files mirror the `app/` module they test by name
  (e.g., app/services/items.py → tests/test_items.py). Sub-folders are
  optional; the template's tests are flat.
- Imports resolve via the template's pytest config (`pythonpath = ["."]`,
  `--import-mode=importlib` in the project's pyproject.toml) —
  conftest.py holds fixtures only, never sys.path edits.

═══════════════════════════════════════════════════════════════════════════════
2. TEST SANITIZATION (run first, before writing new tests)
═══════════════════════════════════════════════════════════════════════════════

Before writing any new tests, audit all existing test files:

a) FIND ORPHANED TESTS — tests that import modules that no longer exist.
   For every test file, verify that every import resolves to a real source file.
   Delete any test file whose imports reference deleted/renamed modules.

b) FIND STALE ASSERTIONS — tests whose assertions reference renamed fields,
   changed method signatures, or removed keyword arguments.
   Fix these to match the current source code.

c) COMPILE-CHECK every remaining test file:
       python -m py_compile <test_file>
   Fix any syntax errors or import failures.

d) REMOVE third-party copyright/license headers from any file that carries one (a header is allowed only when the org standard recorded in the project manifest mandates it).

═══════════════════════════════════════════════════════════════════════════════
3. FILE FORMAT CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

Every test file must follow this exact structure:


    """Tests for <module_path> (<brief description>)."""

    from __future__ import annotations

    <stdlib imports>
    <third-party imports (pytest, pydantic, etc.)>
    <application imports>


    # ── Section Name ────────────────────────────────────────────────────────


    class TestClassName:
        """Optional class docstring."""

        def test_descriptive_snake_case_name(self):
            ...

Rules:
- NEVER include a copyright/license header, unless the org standard recorded in the project manifest mandates one with its exact text.
- ALWAYS include `from __future__ import annotations`.
- ALWAYS include a module-level docstring: """Tests for <path>."""
- Use ASCII banner comments to separate logical sections.
- Import pytest only when you use its features (raises, parametrize, fixtures).

═══════════════════════════════════════════════════════════════════════════════
4. NAMING CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

| Element          | Convention                  | Example                              |
|------------------|-----------------------------|--------------------------------------|
| Test file        | test_<module_name>.py       | test_credential_util.py              |
| Test class       | TestPascalCase              | TestGetAzureCredential               |
| Test method      | test_snake_case             | test_returns_cli_in_local_env        |
| Helper method    | _prefixed                   | _make_executor, _reset_class_state   |
| Fixture (rare)   | snake_case function         | monkeypatch, tmp_path                |

File naming must mirror the source module (inside the project's tests/):
  app/utils/credential_util.py  →  tests/test_credential_util.py
  app/services/items.py         →  tests/test_items.py

═══════════════════════════════════════════════════════════════════════════════
5. WHAT TO TEST (prioritize by testability)
═══════════════════════════════════════════════════════════════════════════════

Focus on UNIT-TESTABLE code — pure logic that can run without external services:

HIGH PRIORITY (test these thoroughly):
- Pydantic/dataclass models: construction, defaults, validation, serialization
- Enum classes: values, membership, string inheritance
- Exception classes: message formatting, detail serialization
- Pure utility functions: string manipulation, template rendering, file loading
- Static/class methods with deterministic output
- Builder patterns: fluent API chaining, attribute storage

MEDIUM PRIORITY (test with mocks):
- Repository CRUD methods: mock the database layer with AsyncMock
- Credential factories: mock Azure SDK classes, use monkeypatch for env vars
- Settings/config classes: use monkeypatch to control environment variables
- Prompt/rules loaders: test file-not-found, empty-file, valid-file scenarios

LOW PRIORITY (skip or test only the interface):
- Methods that orchestrate multiple external services (HTTP + DB + agent)
- Main entry points (main.py, main_service.py)
- Deep async orchestration with event streaming

═══════════════════════════════════════════════════════════════════════════════
6. MOCKING PATTERNS
═══════════════════════════════════════════════════════════════════════════════

Use these patterns in order of preference:

a) monkeypatch (for environment variables):
       def test_something(self, monkeypatch):
           monkeypatch.setenv("KEY", "value")
           monkeypatch.delenv("KEY", raising=False)

b) patch.object (for bypassing __init__):
       with patch.object(MyClass, "__init__", lambda self, *a, **kw: None):
           obj = MyClass.__new__(MyClass)

c) AsyncMock (for async database/HTTP methods):
       from unittest.mock import AsyncMock, patch
       mock_repo = AsyncMock()
       mock_repo.find_one.return_value = {"_id": "123"}

d) Hand-rolled fake classes (for complex service stubs):
       class _FakeQueue:
           def __init__(self):
               self.deleted: list[tuple[str, str]] = []
           def delete_message(self, msg_id, receipt):
               self.deleted.append((msg_id, receipt))

e) Async test pattern — use `pytest-asyncio` (included in template dev dependencies):
       import pytest

       @pytest.mark.asyncio
       async def test_async_operation():
           result = await some_async_function()
           assert result == expected

   Alternative: asyncio.run() wrapper (when pytest-asyncio is not available):
       def test_async_operation(self):
           async def _run():
               result = await some_async_function()
               assert result == expected
           asyncio.run(_run())

Prefer `@pytest.mark.asyncio` when `pytest-asyncio` is in dev dependencies (check `pyproject.toml`).
DO NOT use unittest.TestCase (use plain pytest classes).

═══════════════════════════════════════════════════════════════════════════════
7. ASSERTION STYLE
═══════════════════════════════════════════════════════════════════════════════

Use plain `assert` statements (pytest-native). Examples:

    assert result == expected
    assert "keyword" in str(exc)
    assert len(items) == 3
    assert obj.field is None
    assert isinstance(cred, SomeClass)

For expected exceptions:
    with pytest.raises(ValueError, match=r"must include"):
        function_that_raises()

For Pydantic validation errors:
    with pytest.raises(ValidationError):
        MyModel()  # missing required fields

═══════════════════════════════════════════════════════════════════════════════
8. COVERAGE CONFIGURATION
═══════════════════════════════════════════════════════════════════════════════

The project's own pyproject.toml (shipped by the bundled template) includes:

    [tool.pytest.ini_options]
    pythonpath = ["."]
    addopts = ["--import-mode=importlib"]

    [tool.coverage.run]
    source = ["app"]

    [tool.coverage.report]
    show_missing = true
    skip_empty = true
    exclude_lines = [
        "pragma: no cover",
        "if __name__ == .__main__.",
        "if TYPE_CHECKING:",
    ]

    [tool.coverage.html]
    directory = "htmlcov"

Run from the project directory:  pytest --cov --cov-report=term-missing --cov-report=html

Do not rewrite this config to a different layout (e.g. `pythonpath = ["src"]`
with a repository-root tests/ tree) — the layout comes from the stack
profile template, and this file does not override it.

═══════════════════════════════════════════════════════════════════════════════
9. DOCKER / GIT EXCLUSIONS
═══════════════════════════════════════════════════════════════════════════════

.gitignore must exclude test artifacts (NOT the tests/ folder itself):
    .pytest_cache/
    .coverage
    .coverage.*
    coverage.xml
    htmlcov/
    .hypothesis/

.dockerignore must exclude tests AND artifacts from the build context:
    tests/
    htmlcov/
    .coverage
    .coverage.*
    coverage.xml
    .pytest_cache/
    .hypothesis/

═══════════════════════════════════════════════════════════════════════════════
10. WORKFLOW CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Follow this order:

□ Phase 1 — Sanitize
  1. List all test files
  2. For each: verify imports resolve to existing source modules
  3. Delete orphaned test files (imports reference deleted modules)
  4. Fix stale tests (wrong field names, changed signatures, renamed kwargs)
  5. Remove third-party copyright headers
  6. Compile-check all remaining tests: python -m py_compile <file>

□ Phase 2 — Identify gaps
  7. List all source modules under the project's app/ (excluding __init__.py, __pycache__)
  8. List all existing test files under the project's tests/
  9. Produce a gap matrix: source module → has test? → coverage gaps

□ Phase 3 — Write tests
  10. For each uncovered module, create a test file following the conventions
  11. Prioritize: models → utils → repositories → framework libs → executors
  12. Compile-check each new test file immediately after creation

□ Phase 4 — Validate
  13. Run full suite from the project directory: pytest -v --tb=short
  14. Fix any failures
  15. Run with coverage: pytest --cov --cov-report=term-missing
  16. Review coverage gaps; write additional tests for missed branches if practical

□ Phase 5 — Project hygiene
  17. Ensure unit tests live in the project's tests/ folder (sibling of app/),
      per the stack profile template — not at the repository root
  18. Ensure the project's pyproject.toml has the template's
      [tool.pytest.ini_options] and [tool.coverage] sections
  19. Ensure .gitignore excludes test artifacts
  20. Ensure .dockerignore excludes tests/ and all test artifacts
