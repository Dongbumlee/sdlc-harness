"""Keyword presence grader — checks for required terms in output."""
from __future__ import annotations

import re
from typing import Any

from bench.graders.models import GradeResult, GraderOutput


class KeywordGrader:
    """Grade based on presence/absence of keywords in text output."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.required: list[str] = config.get("required", [])
        self.forbidden: list[str] = config.get("forbidden", [])
        self.case_sensitive: bool = config.get("case_sensitive", False)

    def grade(self, output: str) -> GraderOutput:
        text = output if self.case_sensitive else output.lower()
        found: list[str] = []
        missing: list[str] = []

        for kw in self.required:
            target = kw if self.case_sensitive else kw.lower()
            if re.search(re.escape(target), text):
                found.append(kw)
            else:
                missing.append(kw)

        violations: list[str] = []
        for kw in self.forbidden:
            target = kw if self.case_sensitive else kw.lower()
            if re.search(re.escape(target), text):
                violations.append(kw)

        total_checks = len(self.required) + len(self.forbidden)
        if total_checks == 0:
            return GraderOutput(GradeResult.PASS, 1.0, "No keywords to check")

        passed = len(found) + (len(self.forbidden) - len(violations))
        score = passed / total_checks

        if missing or violations:
            result = GradeResult.FAIL if score < 0.5 else GradeResult.PARTIAL
            reason = ""
            if missing:
                reason += f"Missing: {', '.join(missing)}. "
            if violations:
                reason += f"Forbidden found: {', '.join(violations)}."
            return GraderOutput(result, score, reason.strip(),
                                {"found": found, "missing": missing, "violations": violations})

        return GraderOutput(GradeResult.PASS, 1.0, "All keywords present, none forbidden",
                            {"found": found})
