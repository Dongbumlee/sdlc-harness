"""Tests for LLM-based graders.

These tests mock the LLM calls to verify grader logic without
requiring actual API keys. Integration tests with real LLMs
should be marked with @pytest.mark.integration.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from bench.graders.models import GraderResult, Severity
from bench.graders.llm.judge_grader import JudgeGrader
from bench.graders.llm.consensus_grader import ConsensusGrader
from bench.graders.llm.rubric_grader import RubricGrader


# ---------------------------------------------------------------------------
# JudgeGrader
# ---------------------------------------------------------------------------
class TestJudgeGrader:
    """Verify single-judge LLM evaluation."""

    @pytest.fixture
    def mock_llm_response(self):
        """Create a mock LLM response with score and reasoning."""
        return {
            "score": 0.85,
            "reasoning": "Code follows best practices with minor style issues.",
            "passed": True,
        }

    def test_judge_parses_response(self, mock_llm_response):
        grader = JudgeGrader(
            criteria="Code quality and best practices",
            model="gpt-4",
        )
        result = grader._parse_response(json.dumps(mock_llm_response))
        assert result.score == 0.85
        assert result.passed

    def test_judge_handles_malformed_response(self):
        grader = JudgeGrader(criteria="Quality", model="gpt-4")
        result = grader._parse_response("not json")
        assert result.severity == Severity.ERROR
        assert not result.passed

    def test_judge_clamps_score(self):
        grader = JudgeGrader(criteria="Quality", model="gpt-4")
        result = grader._parse_response(
            json.dumps({"score": 1.5, "reasoning": "Perfect", "passed": True})
        )
        assert result.score <= 1.0


# ---------------------------------------------------------------------------
# ConsensusGrader
# ---------------------------------------------------------------------------
class TestConsensusGrader:
    """Verify multi-judge consensus logic."""

    def test_unanimous_pass(self):
        grader = ConsensusGrader(
            num_judges=3,
            threshold=0.7,
            model="gpt-4",
        )
        scores = [
            GraderResult(score=0.9, passed=True, details=["good"]),
            GraderResult(score=0.85, passed=True, details=["solid"]),
            GraderResult(score=0.8, passed=True, details=["decent"]),
        ]
        result = grader._aggregate(scores)
        assert result.passed
        assert 0.84 <= result.score <= 0.86  # average

    def test_split_decision(self):
        grader = ConsensusGrader(num_judges=3, threshold=0.7, model="gpt-4")
        scores = [
            GraderResult(score=0.9, passed=True, details=[]),
            GraderResult(score=0.3, passed=False, details=[]),
            GraderResult(score=0.4, passed=False, details=[]),
        ]
        result = grader._aggregate(scores)
        assert not result.passed  # majority failed

    def test_empty_scores(self):
        grader = ConsensusGrader(num_judges=3, threshold=0.7, model="gpt-4")
        result = grader._aggregate([])
        assert not result.passed
        assert result.score == 0.0


# ---------------------------------------------------------------------------
# RubricGrader
# ---------------------------------------------------------------------------
class TestRubricGrader:
    """Verify rubric-based multi-dimension scoring."""

    def test_rubric_weights(self):
        grader = RubricGrader(
            rubric={
                "correctness": {"weight": 0.5, "description": "Does it work?"},
                "style": {"weight": 0.3, "description": "Is it clean?"},
                "docs": {"weight": 0.2, "description": "Is it documented?"},
            },
            model="gpt-4",
        )
        dimension_scores = {
            "correctness": 0.9,
            "style": 0.7,
            "docs": 0.5,
        }
        result = grader._compute_weighted(dimension_scores)
        expected = 0.9 * 0.5 + 0.7 * 0.3 + 0.5 * 0.2  # 0.76
        assert abs(result.score - expected) < 0.01

    def test_missing_dimension(self):
        grader = RubricGrader(
            rubric={
                "correctness": {"weight": 0.5, "description": "Works?"},
                "style": {"weight": 0.5, "description": "Clean?"},
            },
            model="gpt-4",
        )
        # Only one dimension scored
        result = grader._compute_weighted({"correctness": 0.8})
        assert result.score < 0.8  # penalized for missing dimension
