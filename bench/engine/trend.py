"""Trend analysis for benchmark scores over time."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TrendPoint:
    """A single data point in a trend series."""

    timestamp: str
    score: float
    canary_id: str
    phase: str
    metadata: dict[str, Any] = field(default_factory=dict)


class TrendAnalyzer:
    """Analyze score trends across benchmark runs.

    Reads historical reports from the reports directory and computes
    regression/improvement trends per canary and phase.
    """

    def __init__(self, reports_dir: str | Path = "bench/reports") -> None:
        self.reports_dir = Path(reports_dir)
        self._history: list[TrendPoint] = []

    def load_history(self) -> None:
        """Load all historical report JSON files."""
        self._history.clear()
        for report_file in sorted(self.reports_dir.glob("report-*.json")):
            with open(report_file) as f:
                data = json.load(f)
            for entry in data.get("scores", []):
                self._history.append(
                    TrendPoint(
                        timestamp=data.get("timestamp", report_file.stem),
                        score=entry["overall_score"],
                        canary_id=entry["canary_id"],
                        phase=entry["phase"],
                    )
                )

    def get_trend(self, canary_id: str) -> list[TrendPoint]:
        """Get score history for a specific canary."""
        return [p for p in self._history if p.canary_id == canary_id]

    def detect_regression(
        self, canary_id: str, threshold: float = 0.1
    ) -> bool:
        """Detect if latest score regressed by more than threshold."""
        points = self.get_trend(canary_id)
        if len(points) < 2:
            return False
        return (points[-2].score - points[-1].score) > threshold

    def summary(self) -> dict[str, Any]:
        """Produce a summary of all trends."""
        canaries = {p.canary_id for p in self._history}
        result: dict[str, Any] = {}
        for cid in sorted(canaries):
            points = self.get_trend(cid)
            result[cid] = {
                "count": len(points),
                "latest": points[-1].score if points else None,
                "best": max(p.score for p in points) if points else None,
                "worst": min(p.score for p in points) if points else None,
                "regressed": self.detect_regression(cid),
            }
        return result
