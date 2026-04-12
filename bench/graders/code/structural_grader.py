"""Structural grader — validates output structure (JSON schema, sections, etc.)."""
from __future__ import annotations

import json
from typing import Any

from bench.graders.models import GradeResult, GraderOutput


class StructuralGrader:
    """Grade based on structural properties of the output."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.format: str = config.get("format", "text")  # json, yaml, markdown, text
        self.require_keys: list[str] = config.get("require_keys", [])
        self.require_sections: list[str] = config.get("require_sections", [])
        self.min_length: int = config.get("min_length", 0)
        self.max_length: int | None = config.get("max_length")

    def grade(self, output: str) -> GraderOutput:
        checks: list[tuple[str, bool]] = []

        # Length checks
        if self.min_length:
            checks.append((f"min_length >= {self.min_length}", len(output) >= self.min_length))
        if self.max_length:
            checks.append((f"max_length <= {self.max_length}", len(output) <= self.max_length))

        # Format-specific checks
        if self.format == "json":
            checks.extend(self._check_json(output))
        elif self.format == "markdown":
            checks.extend(self._check_markdown(output))

        if not checks:
            return GraderOutput(GradeResult.PASS, 1.0, "No structural checks configured")

        passed = sum(1 for _, ok in checks if ok)
        score = passed / len(checks)
        failed = [(name, ok) for name, ok in checks if not ok]

        if failed:
            result = GradeResult.FAIL if score < 0.5 else GradeResult.PARTIAL
            reason = "Failed: " + ", ".join(name for name, _ in failed)
            return GraderOutput(result, score, reason)

        return GraderOutput(GradeResult.PASS, 1.0, "All structural checks passed")

    def _check_json(self, output: str) -> list[tuple[str, bool]]:
        checks = []
        try:
            data = json.loads(output)
            checks.append(("valid JSON", True))
            for key in self.require_keys:
                checks.append((f"key '{key}'", key in data))
        except json.JSONDecodeError:
            checks.append(("valid JSON", False))
        return checks

    def _check_markdown(self, output: str) -> list[tuple[str, bool]]:
        checks = []
        for section in self.require_sections:
            pattern = f"# {section}" if not section.startswith("#") else section
            checks.append((f"section '{section}'", pattern in output))
        return checks
