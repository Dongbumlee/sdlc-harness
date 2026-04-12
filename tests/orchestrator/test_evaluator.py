"""Tests for the orchestrator evaluator module.

Verifies that the evaluator correctly aggregates results,
computes weighted scores, and produces evaluation reports.
"""

import pytest

from bench.graders.models import GraderResult
from orchestrator.evaluator import Evaluator, EvaluationReport
from orchestrator.evaluator_config import EvaluatorConfig


class TestEvaluator:
    """Core evaluator tests."""

    @pytest.fixture
    def config(self):
        return EvaluatorConfig(
            weights={"keyword": 0.6, "ast": 0.4},
            pass_threshold=0.7,
        )

    @pytest.fixture
    def evaluator(self, config):
        return Evaluator(config)

    def test_aggregate_weighted_scores(self, evaluator):
        results = [
            GraderResult(grader="keyword", score=0.9, passed=True),
            GraderResult(grader="ast", score=0.7, passed=True),
        ]
        agg = evaluator.aggregate_results(results)
        expected = (0.9 * 0.6 + 0.7 * 0.4) / (0.6 + 0.4)
        assert abs(agg["weighted_score"] - expected) < 0.01
        assert agg["passed"]

    def test_aggregate_below_threshold(self, evaluator):
        results = [
            GraderResult(grader="keyword", score=0.3, passed=False),
            GraderResult(grader="ast", score=0.5, passed=False),
        ]
        agg = evaluator.aggregate_results(results)
        assert not agg["passed"]
        assert agg["weighted_score"] < 0.7

    def test_aggregate_empty_results(self, evaluator):
        agg = evaluator.aggregate_results([])
        assert agg["weighted_score"] == 0.0
        assert not agg["passed"]

    def test_score_shortcut(self, evaluator):
        results = [
            GraderResult(grader="keyword", score=0.8, passed=True),
            GraderResult(grader="ast", score=0.9, passed=True),
        ]
        score_val = evaluator.score(results)
        assert 0.0 <= score_val <= 1.0

    def test_create_report(self, evaluator):
        results = [
            GraderResult(grader="keyword", score=0.85, passed=True),
        ]
        report = evaluator.create_report("canary-001", results)
        assert isinstance(report, EvaluationReport)
        assert report.canary_id == "canary-001"
        assert report.aggregate_score > 0.0

    def test_default_config(self):
        evaluator = Evaluator()
        assert evaluator.config.pass_threshold == 0.7


class TestEvaluatorConfig:
    """Config construction and validation."""

    def test_valid_config(self):
        config = EvaluatorConfig(
            weights={"keyword": 1.0},
            pass_threshold=0.8,
        )
        assert config.pass_threshold == 0.8
        assert config.weights["keyword"] == 1.0

    def test_default_values(self):
        config = EvaluatorConfig()
        assert config.pass_threshold == 0.7
        assert config.weights == {}
        assert config.code_graders == []
        assert config.llm_graders == []
