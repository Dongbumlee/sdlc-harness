"""Architecture conformance tests.

The template's dependency direction is enforced mechanically, not left to
review: routers may depend on services; services must never depend on
routers; the shared libs depend on neither; and only the composition root
(``app.application`` / ``app.main``) may import the composition root. A
violation fails the test run instead of waiting for a reviewer to notice.
"""

import ast
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"

# Layer -> layers it must never import (first component under `app.`).
FORBIDDEN = {
    "services": {"routers", "application", "main"},
    "libs": {"routers", "services", "application", "main"},
    "routers": {"application", "main"},
}


def _layer_of(path: Path) -> str:
    parts = path.relative_to(APP_DIR).parts
    if len(parts) > 1:
        return parts[0]
    return parts[0].removesuffix(".py")


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_dependency_direction() -> None:
    violations: list[str] = []
    for path in sorted(APP_DIR.rglob("*.py")):
        layer = _layer_of(path)
        banned = FORBIDDEN.get(layer, set())
        if not banned:
            continue
        for module in _imports_of(path):
            if module.startswith("app."):
                target = module.split(".")[1]
                if target in banned:
                    violations.append(
                        f"{path.relative_to(APP_DIR)} ({layer}) imports {module}"
                    )
    assert not violations, "Layering violations:\n" + "\n".join(violations)
