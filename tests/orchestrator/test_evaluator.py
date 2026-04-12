"""Tests for the orchestrator evaluator module.

Verifies that the evaluator correctly selects graders, aggregates
results, and produces evaluation reports.
"""

import pytest
from unittest.mock import MagicMock, patch

from orchestrator.evaluator import Evaluator
from orchestrator.evaluator_config import EvaluatorConfig, GraderMapping
from orchestrator.types import PhaseType, EvaluationResult
from bench.graders.models import GraderResult, Severity


class TestEvaluator:
    """Core evaluator tests."""

    @pytest.fixture
    def config(self):
        return EvaluatorConfig(
            grader_mappings=[
                GraderMapping(
                    phase=PhaseType.IMPLEMENT,
                    grader_type="keyword",
                    config={"required_keywords": ["def ", "return"]},
                    weight=0.6,
                ),
                GraderMapping(
                    phase=PhaseType.IMPLEMENT,
                    grader_type="ast",
                    config={"required_constructs": ["FunctionDef"], "min_functions": 1},
                    weight=0.4,
                ),
            ],
            pass_threshold=0.7,
        )

    @pytest.fixture
    def evaluator(self, config):
        return Evaluator(config)

    def test_select_graders_for_phase(self, evaluator):
        graders = evaluator._select_graders(PhaseType.IMPLEMENT)
        assert len(graders) == 2

    def test_no_graders_for_unknown_phase(self, evaluator):
        graders = evaluator._select_graders(PhaseType.REQUIREMENTS)
        assert len(graders) == 0

    def test_aggregate_weighted_scores(self, evaluator):
        results = [
            (GraderResult(score=0.9, passed=True, details=[]), 0.6),
            (GraderResult(score=0.7, passed=True, details=[]), 0.4),
        ]
        final = evaluator._aggregate(results)
        expected = 0.9 * 0.6 + 0.7 * 0.4  # 0.82
        assert abs(final.score - expected) < 0.01
        assert final.passed

    def test_aggregate_below_threshold(self, evaluator):
        results = [
            (GraderResult(score=0.3, passed=False, details=["bad"]), 0.6),
            (GraderResult(score=0.5, passed=False, details=["poor"]), 0.4),
        ]
        final = evaluator._aggregate(results)
        assert not final.passed
        assert final.score < 0.7


class TestEvaluatorConfig:
    """Config parsing and validation."""

    def test_valid_config(self):
        config = EvaluatorConfig(
            grader_mappings=[
                GraderMapping(
                    phase=PhaseType.QA,
                    grader_type="keyword",
                    config={"required_keywords": ["test_"]},
                    weight=1.0,
                )
            ],
            pass_threshold=0.8,
        )
        assert config.pass_threshold == 0.8
        assert len(config.grader_mappings) == 1

    def test_weights_must_be_positive(self):
        with pytest.raises(ValueError):
            GraderMapping(
                phase=PhaseType.IMPLEMENT,
                grader_type="keyword",
                config={},
                weight=-0.5,
            )

    def test_threshold_bounds(self):
        with pytest.raises(ValueError):
            EvaluatorConfig(
                grader_mappings=[],
                pass_threshold=1.5,  # out of range
            )
