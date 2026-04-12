"""Generate benchmark reports in JSON and markdown formats."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bench.engine.scorer import CanaryScore


def generate_report(
    scores: list[CanaryScore],
    output_dir: str | Path = "bench/reports",
    baseline_path: str | Path | None = "bench/reports/baseline.json",
) -> dict[str, Any]:
    """Generate a benchmark report from canary scores.

    Args:
        scores: List of scored canary results.
        output_dir: Directory to write the report JSON.
        baseline_path: Path to baseline scores for comparison.

    Returns:
        Report dict with scores, comparisons, and summary.
    """
    now = datetime.now(timezone.utc).isoformat()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load baseline if available
    baseline: dict[str, float] = {}
    if baseline_path and Path(baseline_path).exists():
        with open(baseline_path) as f:
            baseline_data = json.load(f)
            baseline = {
                entry["canary_id"]: entry["score"]
                for entry in baseline_data.get("scores", [])
            }

    # Build report entries
    entries: list[dict[str, Any]] = []
    for score in scores:
        entry: dict[str, Any] = {
            "canary_id": score.canary_id,
            "phase": score.phase,
            "overall_score": score.overall_score,
            "passed": score.passed,
            "graders": [
                {
                    "name": gr.grader_name,
                    "score": gr.score,
                    "details": gr.details,
                }
                for gr in score.grader_results
            ],
        }
        if score.canary_id in baseline:
            delta = score.overall_score - baseline[score.canary_id]
            entry["baseline_delta"] = round(delta, 4)
            entry["regression"] = delta < -0.1
        entries.append(entry)

    report = {
        "timestamp": now,
        "total_canaries": len(scores),
        "passed": sum(1 for s in scores if s.passed),
        "failed": sum(1 for s in scores if not s.passed),
        "average_score": round(
            sum(s.overall_score for s in scores) / max(len(scores), 1), 4
        ),
        "scores": entries,
    }

    # Write JSON report
    report_filename = f"report-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    report_path = output_dir / report_filename
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


def report_to_markdown(report: dict[str, Any]) -> str:
    """Convert a report dict to markdown summary."""
    lines = [
        f"# Benchmark Report — {report['timestamp']}",
        "",
        f"**Total**: {report['total_canaries']} | "
        f"**Passed**: {report['passed']} | "
        f"**Failed**: {report['failed']} | "
        f"**Average**: {report['average_score']:.2%}",
        "",
        "| Canary | Phase | Score | Status | Δ Baseline |",
        "|--------|-------|-------|--------|------------|",
    ]
    for entry in report["scores"]:
        status = "PASS" if entry["passed"] else "FAIL"
        delta = entry.get("baseline_delta", "—")
        if isinstance(delta, float):
            delta = f"{delta:+.2%}"
        lines.append(
            f"| {entry['canary_id']} | {entry['phase']} "
            f"| {entry['overall_score']:.2%} | {status} | {delta} |"
        )
    return "\n".join(lines)
