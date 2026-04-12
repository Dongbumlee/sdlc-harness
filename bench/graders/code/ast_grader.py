"""AST-based grader — validates Python code structure."""
from __future__ import annotations

import ast
from typing import Any

from bench.graders.models import GradeResult, GraderOutput


class ASTGrader:
    """Grade Python code by parsing its AST and checking structural properties."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.require_functions: list[str] = config.get("require_functions", [])
        self.require_classes: list[str] = config.get("require_classes", [])
        self.require_imports: list[str] = config.get("require_imports", [])
        self.max_complexity: int | None = config.get("max_complexity")

    def grade(self, code: str) -> GraderOutput:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return GraderOutput(GradeResult.FAIL, 0.0, f"Syntax error: {e}")

        functions = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }
        classes = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        }
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)

        checks: list[tuple[str, bool]] = []

        for fn in self.require_functions:
            checks.append((f"function '{fn}'", fn in functions))
        for cls in self.require_classes:
            checks.append((f"class '{cls}'", cls in classes))
        for imp in self.require_imports:
            checks.append((f"import '{imp}'", any(imp in i for i in imports)))

        if self.max_complexity is not None:
            complexity = self._estimate_complexity(tree)
            checks.append((
                f"complexity <= {self.max_complexity}",
                complexity <= self.max_complexity,
            ))

        if not checks:
            return GraderOutput(GradeResult.PASS, 1.0, "Valid Python, no structural checks")

        passed = sum(1 for _, ok in checks if ok)
        score = passed / len(checks)
        failed = [(name, ok) for name, ok in checks if not ok]

        if failed:
            result = GradeResult.FAIL if score < 0.5 else GradeResult.PARTIAL
            reason = "Missing: " + ", ".join(name for name, _ in failed)
            return GraderOutput(result, score, reason,
                                {"passed": passed, "total": len(checks)})

        return GraderOutput(GradeResult.PASS, 1.0, "All structural checks passed",
                            {"passed": passed, "total": len(checks)})

    @staticmethod
    def _estimate_complexity(tree: ast.AST) -> int:
        """Simple cyclomatic complexity estimate."""
        branch_types = (ast.If, ast.For, ast.While, ast.ExceptHandler,
                        ast.With, ast.BoolOp)
        return sum(1 for node in ast.walk(tree) if isinstance(node, branch_types))
