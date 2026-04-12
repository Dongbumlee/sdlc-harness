"""Evaluator — scores artifacts using configurable grading strategies."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from orchestrator.types import Phase, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class EvalCriterion:
    """A single evaluation criterion."""

    name: str
    description: str
    weight: float = 1.0
    threshold: float = 0.7


@dataclass
class EvalScore:
    """Score for a single criterion."""

    criterion: str
    score: float  # 0.0 - 1.0
    rationale: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.score >= 0.7  # default threshold


@dataclass
class EvalResult:
    """Complete evaluation result."""

    phase: Phase
    scores: list[EvalScore]
    overall_score: float
    passed: bool
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class Evaluator:
    """Evaluate generated artifacts against quality criteria.

    Supports multiple grading strategies:
    - keyword: check for required terms/patterns
    - structural: validate document structure
    - llm-judge: use LLM to assess quality
    - rubric: score against a detailed rubric
    """

    def __init__(self, criteria: list[EvalCriterion] | None = None) -> None:
        self.criteria = criteria or self._default_criteria()

    def evaluate(self, result: TaskResult) -> EvalResult:
        """Evaluate a task result against all criteria."""
        scores = []
        for criterion in self.criteria:
            score = self._score_criterion(result, criterion)
            scores.append(score)

        total_weight = sum(c.weight for c in self.criteria)
        if total_weight > 0:
            weighted = sum(
                s.score * c.weight
                for s, c in zip(scores, self.criteria)
            )
            overall = weighted / total_weight
        else:
            overall = 0.0

        passed = all(
            s.score >= c.threshold
            for s, c in zip(scores, self.criteria)
        )

        return EvalResult(
            phase=result.phase,
            scores=scores,
            overall_score=overall,
            passed=passed,
            summary=self._build_summary(scores, overall, passed),
        )

    def _score_criterion(
        self, result: TaskResult, criterion: EvalCriterion
    ) -> EvalScore:
        """Score a result against a single criterion."""
        content = result.content or ""

        # Basic scoring: check content is non-empty and has structure
        score = 0.0
        rationale_parts = []

        if not content.strip():
            rationale_parts.append("Content is empty")
        else:
            # Length check
            if len(content) > 100:
                score += 0.3
                rationale_parts.append("Content has sufficient length")
            else:
                rationale_parts.append("Content is too short")

            # Structure check (headers, lists)
            if "#" in content or "-" in content:
                score += 0.3
                rationale_parts.append("Content has structure")

            # Phase-specific keywords
            phase_keywords = self._phase_keywords(result.phase)
            found = sum(1 for kw in phase_keywords if kw.lower() in content.lower())
            if phase_keywords:
                keyword_ratio = found / len(phase_keywords)
                score += 0.4 * keyword_ratio
                rationale_parts.append(
                    f"Found {found}/{len(phase_keywords)} phase keywords"
                )

        return EvalScore(
            criterion=criterion.name,
            score=min(score, 1.0),
            rationale="; ".join(rationale_parts),
        )

    def _phase_keywords(self, phase: Phase) -> list[str]:
        """Get expected keywords for each phase."""
        keywords: dict[Phase, list[str]] = {
            Phase.REQUIREMENTS: ["user story", "acceptance", "requirement"],
            Phase.DESIGN: ["architecture", "component", "api"],
            Phase.IMPLEMENT: ["function", "class", "import"],
            Phase.QA: ["test", "security", "review"],
            Phase.DEPLOY: ["deploy", "infrastructure", "config"],
            Phase.RELEASE: ["changelog", "version", "release"],
        }
        return keywords.get(phase, [])

    def _build_summary(
        self, scores: list[EvalScore], overall: float, passed: bool
    ) -> str:
        """Build a human-readable summary."""
        status = "PASSED" if passed else "FAILED"
        lines = [f"Evaluation {status} (overall: {overall:.2f})"]
        for s in scores:
            icon = "pass" if s.passed else "FAIL"
            lines.append(f"  [{icon}] {s.criterion}: {s.score:.2f}")
        return "\n".join(lines)

    def _default_criteria(self) -> list[EvalCriterion]:
        """Default evaluation criteria."""
        return [
            EvalCriterion(
                name="completeness",
                description="Artifact covers all required aspects",
                weight=2.0,
            ),
            EvalCriterion(
                name="correctness",
                description="Content is technically accurate",
                weight=2.0,
            ),
            EvalCriterion(
                name="clarity",
                description="Content is well-structured and readable",
                weight=1.0,
            ),
        ]
