"""Consensus grader — multiple LLM judges vote on quality."""
from __future__ import annotations

from typing import Any

from bench.graders.models import GradeResult, GraderOutput
from bench.graders.llm.judge_grader import JudgeGrader


class ConsensusGrader:
    """Run multiple LLM judges and aggregate by majority vote."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.num_judges: int = config.get("num_judges", 3)
        self.threshold: float = config.get("threshold", 0.6)
        self.judge_config: dict[str, Any] = config.get("judge_config", {})

    def aggregate(self, results: list[GraderOutput]) -> GraderOutput:
        """Aggregate multiple judge outputs into a consensus result."""
        if not results:
            return GraderOutput(GradeResult.FAIL, 0.0, "No judge results to aggregate")

        avg_score = sum(r.score for r in results) / len(results)

        votes = {
            GradeResult.PASS: 0,
            GradeResult.PARTIAL: 0,
            GradeResult.FAIL: 0,
        }
        for r in results:
            votes[r.result] += 1

        # Majority vote
        majority = max(votes, key=lambda k: votes[k])

        # If no clear majority, use score threshold
        if votes[majority] <= len(results) / 2:
            if avg_score >= self.threshold:
                majority = GradeResult.PASS
            elif avg_score >= self.threshold * 0.5:
                majority = GradeResult.PARTIAL
            else:
                majority = GradeResult.FAIL

        reasons = [r.reason for r in results]
        return GraderOutput(
            majority,
            avg_score,
            f"Consensus ({votes[GradeResult.PASS]}P/{votes[GradeResult.PARTIAL]}A/{votes[GradeResult.FAIL]}F): {reasons[0]}",
            {
                "votes": {k.value: v for k, v in votes.items()},
                "individual_scores": [r.score for r in results],
                "individual_reasons": reasons,
            },
        )
