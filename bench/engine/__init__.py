"""Benchmark engine — scoring, trend analysis, and reporting."""

from bench.engine.scorer import score_canary
from bench.engine.trend import TrendAnalyzer
from bench.engine.report import generate_report

__all__ = ["score_canary", "TrendAnalyzer", "generate_report"]
