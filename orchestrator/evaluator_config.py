"""Evaluator configuration — weights, thresholds, and grader lists."""

from __future__ import annotations

from dataclasses import dataclass, field

@dataclass
class EvaluatorConfig:
    """Configuration for the Evaluator pipeline.

    Attributes:
        weights: Mapping of grader name to its weight in the aggregate score.
        pass_threshold: Minimum weighted score required to pass.
        code_graders: Names of deterministic code graders to run.
        llm_graders: Names of LLM-based graders to run.
    """

    weights: dict[str, float] = field(default_factory=dict)
    pass_threshold: float = 0.7
    code_graders: list[str] = field(default_factory=list)
    llm_graders: list[str] = field(default_factory=list)


@dataclass
class EvalCriterion:
    """A single evaluation criterion used by phase-specific configs."""

    name: str
    description: str
    weight: float = 1.0
    threshold: float = 0.5
