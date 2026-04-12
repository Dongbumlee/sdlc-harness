"""File grader — validates file system artifacts produced by AI."""
from __future__ import annotations

import os
from typing import Any

from bench.graders.models import GradeResult, GraderOutput


class FileGrader:
    """Grade based on file existence, content, and structure."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.require_files: list[str] = config.get("require_files", [])
        self.forbid_files: list[str] = config.get("forbid_files", [])
        self.require_dirs: list[str] = config.get("require_dirs", [])

    def grade(self, workspace: str) -> GraderOutput:
        checks: list[tuple[str, bool]] = []

        for f in self.require_files:
            path = os.path.join(workspace, f)
            checks.append((f"file '{f}' exists", os.path.isfile(path)))

        for f in self.forbid_files:
            path = os.path.join(workspace, f)
            checks.append((f"file '{f}' absent", not os.path.exists(path)))

        for d in self.require_dirs:
            path = os.path.join(workspace, d)
            checks.append((f"dir '{d}' exists", os.path.isdir(path)))

        if not checks:
            return GraderOutput(GradeResult.PASS, 1.0, "No file checks configured")

        passed = sum(1 for _, ok in checks if ok)
        score = passed / len(checks)
        failed = [(name, ok) for name, ok in checks if not ok]

        if failed:
            result = GradeResult.FAIL if score < 0.5 else GradeResult.PARTIAL
            reason = "Failed: " + ", ".join(name for name, _ in failed)
            return GraderOutput(result, score, reason,
                                {"passed": passed, "total": len(checks)})

        return GraderOutput(GradeResult.PASS, 1.0, "All file checks passed",
                            {"passed": passed, "total": len(checks)})
