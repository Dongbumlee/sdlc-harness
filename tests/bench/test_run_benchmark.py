"""Tests for tools/run_benchmark.py.

Covers canary discovery, execution with mock provider, and report generation.
"""

from pathlib import Path

import pytest
import yaml

from tools.run_benchmark import discover_canaries, execute_canary, generate_report


@pytest.fixture
def canary_dir(tmp_path):
    """Create a temporary canary directory with sample specs."""
    d = tmp_path / "bench" / "canaries"
    d.mkdir(parents=True)
    spec = {
        "id": "test-canary-001",
        "phase": "implement",
        "title": "Test canary",
        "prompt": "Write a hello-world function",
        "graders": [],
    }
    (d / "test_canary.yaml").write_text(yaml.dump(spec))
    return d


class TestDiscoverCanaries:
    """Verify canary discovery and filtering."""

    def test_discover_from_directory(self, canary_dir):
        canaries = discover_canaries(canary_dir=canary_dir)
        assert len(canaries) == 1
        assert canaries[0]["id"] == "test-canary-001"

    def test_filter_by_phase(self, canary_dir):
        found = discover_canaries(filter_phases="implement", canary_dir=canary_dir)
        assert len(found) == 1

        found = discover_canaries(filter_phases="deploy", canary_dir=canary_dir)
        assert len(found) == 0

    def test_empty_directory(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        assert discover_canaries(canary_dir=empty) == []


class TestExecuteCanary:
    """Verify canary execution with mock provider."""

    def test_execute_returns_result(self):
        canary = {
            "id": "c-001",
            "phase": "implement",
            "prompt": "Write hello world",
            "graders": [],
        }
        result = execute_canary(canary, provider_type="mock")
        assert result["canary_id"] == "c-001"
        assert result["status"] in ("pass", "fail", "error", "skipped")
        assert "scores" in result

    def test_execute_with_graders(self):
        canary = {
            "id": "c-002",
            "phase": "implement",
            "prompt": "Write a function with def keyword",
            "graders": [
                {
                    "type": "keyword",
                    "config": {"required_keywords": ["def"]},
                    "weight": 1.0,
                },
            ],
        }
        result = execute_canary(canary, provider_type="mock")
        assert result["canary_id"] == "c-002"
        assert "duration_seconds" in result


class TestGenerateReport:
    """Verify report generation from results."""

    def test_report_structure(self):
        results = [
            {
                "canary_id": "c-001",
                "status": "pass",
                "scores": {"overall": 0.9, "by_grader": []},
                "duration_seconds": 0.1,
            },
            {
                "canary_id": "c-002",
                "status": "fail",
                "scores": {"overall": 0.4, "by_grader": []},
                "duration_seconds": 0.2,
            },
        ]
        report = generate_report(results, {"name": "test"}, "run-test")
        assert report["run_id"] == "run-test"
        assert report["summary"]["total"] == 2
        assert report["summary"]["passed"] == 1
        assert report["summary"]["failed"] == 1

    def test_empty_results(self):
        report = generate_report([], {"name": "test"}, "run-empty")
        assert report["summary"]["total"] == 0
        assert report["summary"]["overall_score"] == 0.0
