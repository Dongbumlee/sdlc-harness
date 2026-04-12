"""Evaluator configuration — phase-specific criteria and thresholds."""

from __future__ import annotations

from orchestrator.evaluator import EvalCriterion
from orchestrator.types import Phase

# Phase-specific evaluation criteria
PHASE_CRITERIA: dict[Phase, list[EvalCriterion]] = {
    Phase.REQUIREMENTS: [
        EvalCriterion("user_stories", "Has user stories with acceptance criteria", 2.0, 0.7),
        EvalCriterion("nfr", "Includes non-functional requirements", 1.0, 0.5),
        EvalCriterion("completeness", "Covers all aspects of the task", 2.0, 0.7),
    ],
    Phase.DESIGN: [
        EvalCriterion("architecture", "Has clear architecture overview", 2.0, 0.7),
        EvalCriterion("api_contracts", "Defines API contracts", 1.5, 0.6),
        EvalCriterion("data_models", "Includes data model definitions", 1.0, 0.5),
    ],
    Phase.IMPLEMENT: [
        EvalCriterion("functionality", "Code implements required functionality", 2.0, 0.8),
        EvalCriterion("error_handling", "Has proper error handling", 1.5, 0.6),
        EvalCriterion("type_hints", "Uses type hints at boundaries", 1.0, 0.5),
    ],
    Phase.QA: [
        EvalCriterion("test_coverage", "Covers key test scenarios", 2.0, 0.7),
        EvalCriterion("security", "Addresses security concerns", 1.5, 0.6),
        EvalCriterion("edge_cases", "Identifies edge cases", 1.0, 0.5),
    ],
    Phase.DEPLOY: [
        EvalCriterion("iac", "Has infrastructure as code", 2.0, 0.7),
        EvalCriterion("rollback", "Includes rollback procedures", 1.5, 0.6),
        EvalCriterion("monitoring", "Defines monitoring setup", 1.0, 0.5),
    ],
    Phase.RELEASE: [
        EvalCriterion("changelog", "Has structured changelog", 2.0, 0.7),
        EvalCriterion("migration", "Includes migration guide", 1.0, 0.5),
        EvalCriterion("communication", "Has stakeholder communication", 1.0, 0.5),
    ],
}


def get_criteria(phase: Phase) -> list[EvalCriterion]:
    """Get evaluation criteria for a phase, falling back to defaults."""
    return PHASE_CRITERIA.get(phase, [
        EvalCriterion("completeness", "Covers required aspects", 2.0, 0.7),
        EvalCriterion("correctness", "Technically accurate", 2.0, 0.7),
        EvalCriterion("clarity", "Well-structured and readable", 1.0, 0.5),
    ])
