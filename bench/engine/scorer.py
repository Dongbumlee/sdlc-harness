"""Score a single canary run against its graders."""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any

from bench.graders.models import GraderOutput


@dataclass
class CanaryScore:
    """Aggregated score for a single canary execution."""

    canary_id: str
    phase: str
    overall_score: float
    grader_results: list[GraderOutput] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.overall_score >= 0.7


def _load_grader(grader_spec: dict[str, Any]) -> Any:
    """Dynamically load a grader from its spec."""
    module_path = grader_spec["module"]
    class_name = grader_spec["class"]
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    config = grader_spec.get("config", {})
    return cls(**config)


def score_canary(
    canary_id: str,
    phase: str,
    artifacts: dict[str, Any],
    grader_specs: list[dict[str, Any]],
    weights: list[float] | None = None,
) -> CanaryScore:
    """Run all graders on artifacts and produce an aggregated score.

    Args:
        canary_id: Identifier for the canary being scored.
        phase: SDLC phase (requirements, implement, qa, etc.).
        artifacts: Dict of artifact name -> content produced by the agent.
        grader_specs: List of grader specifications with module/class/config.
        weights: Optional per-grader weights (uniform if None).

    Returns:
        CanaryScore with individual and aggregated results.
    """
    if weights is None:
        weights = [1.0 / len(grader_specs)] * len(grader_specs)
    else:
        total = sum(weights)
        weights = [w / total for w in weights]

    results: list[GraderOutput] = []
    for spec in grader_specs:
        grader = _load_grader(spec)
        result = grader.grade(artifacts)
        results.append(result)

    weighted_score = sum(r.score * w for r, w in zip(results, weights))

    return CanaryScore(
        canary_id=canary_id,
        phase=phase,
        overall_score=round(weighted_score, 4),
        grader_results=results,
    )
