"""Evaluator module for orchestrating grading pipelines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bench.graders.models import GraderResult
from orchestrator.evaluator_config import EvaluatorConfig


@dataclass
class EvaluationReport:
    """Complete evaluation report for a single canary."""

    canary_id: str
    results: list[GraderResult] = field(default_factory=list)
    aggregate_score: float = 0.0
    passed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class Evaluator:
    """Orchestrates grading pipelines for canary evaluation.

    Supports multiple grading strategies:
    - keyword: check for required terms/patterns
    - ast: validate code structure via AST parsing
    - structural: validate document structure
    - file: check for expected files/directories
    - judge: LLM-based quality assessment
    - consensus: multi-judge agreement
    - rubric: detailed rubric scoring
    """

    def __init__(self, config: EvaluatorConfig | None = None) -> None:
        self.config = config or EvaluatorConfig()

    def evaluate(self, canary_id: str, code: str, spec: dict[str, Any]) -> EvaluationReport:
        """Run all configured graders against code output.

        Args:
            canary_id: Identifier for the canary spec
            code: The generated code to evaluate
            spec: The canary specification with expected criteria

        Returns:
            Complete evaluation report with all grader results
        """
        results: list[GraderResult] = []

        # Run code graders
        for grader_name in self.config.code_graders:
            result = self._run_code_grader(grader_name, code, spec)
            results.append(result)

        # Run LLM graders
        for grader_name in self.config.llm_graders:
            result = self._run_llm_grader(grader_name, code, spec)
            results.append(result)

        aggregate = self.aggregate_results(results)

        return EvaluationReport(
            canary_id=canary_id,
            results=results,
            aggregate_score=aggregate["weighted_score"],
            passed=aggregate["passed"],
            metadata={"config": self.config.__dict__},
        )

    def aggregate_results(self, results: list[GraderResult]) -> dict[str, Any]:
        """Aggregate multiple grader results into a weighted score.

        Args:
            results: List of individual grader results

        Returns:
            Dict with weighted_score, passed, and per-grader breakdown
        """
        if not results:
            return {"weighted_score": 0.0, "passed": False, "breakdown": {}}

        breakdown: dict[str, Any] = {}
        total_weight = 0.0
        weighted_sum = 0.0

        for result in results:
            weight = self.config.weights.get(result.grader, 1.0)
            weighted_sum += result.score * weight
            total_weight += weight
            breakdown[result.grader] = {
                "score": result.score,
                "weight": weight,
                "passed": result.passed,
            }

        weighted_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        passed = weighted_score >= self.config.pass_threshold

        return {
            "weighted_score": round(weighted_score, 4),
            "passed": passed,
            "breakdown": breakdown,
        }

    def _run_code_grader(self, name: str, code: str, spec: dict[str, Any]) -> GraderResult:
        """Run a single code grader."""
        from bench.graders.code import keyword_grader, ast_grader, structural_grader, file_grader

        graders = {
            "keyword": keyword_grader.KeywordGrader,
            "ast": ast_grader.ASTGrader,
            "structural": structural_grader.StructuralGrader,
            "file": file_grader.FileGrader,
        }

        grader_cls = graders.get(name)
        if not grader_cls:
            return GraderResult(
                grader=name,
                score=0.0,
                passed=False,
                details={"error": f"Unknown grader: {name}"},
            )

        grader = grader_cls()
        return grader.grade(code, spec)

    def _run_llm_grader(self, name: str, code: str, spec: dict[str, Any]) -> GraderResult:
        """Run a single LLM grader."""
        from bench.graders.llm import judge_grader, consensus_grader, rubric_grader

        graders = {
            "judge": judge_grader.JudgeGrader,
            "consensus": consensus_grader.ConsensusGrader,
            "rubric": rubric_grader.RubricGrader,
        }

        grader_cls = graders.get(name)
        if not grader_cls:
            return GraderResult(
                grader=name,
                score=0.0,
                passed=False,
                details={"error": f"Unknown grader: {name}"},
            )

        grader = grader_cls()
        return grader.grade(code, spec)

    def score(self, results: list[GraderResult]) -> float:
        """Quick shortcut to get just the weighted score."""
        return self.aggregate_results(results)["weighted_score"]

    def create_report(
        self, canary_id: str, results: list[GraderResult]
    ) -> EvaluationReport:
        """Create a report from pre-computed results."""
        aggregate = self.aggregate_results(results)
        return EvaluationReport(
            canary_id=canary_id,
            results=results,
            aggregate_score=aggregate["weighted_score"],
            passed=aggregate["passed"],
        )
