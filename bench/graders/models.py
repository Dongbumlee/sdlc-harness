"""Shared data models for benchmark grading."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GradeResult(Enum):
    PASS = "pass"
    PARTIAL = "partial"
    FAIL = "fail"


@dataclass
class GraderOutput:
    """Standard output from any grader."""

    result: GradeResult
    score: float  # 0.0 - 1.0
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "result": self.result.value,
            "score": self.score,
            "reason": self.reason,
            "details": self.details,
        }


@dataclass
class CanarySpec:
    """Parsed canary test specification."""

    id: str
    phase: str
    title: str
    prompt: str
    expected: dict[str, Any]
    graders: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)
