#!/usr/bin/env python3
"""Run SDLC Harness benchmark suite.

Executes canary tests against an AI agent and produces a benchmark report.
"""

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml


def load_profile(profile_name: str) -> dict:
    """Load a benchmark profile configuration."""
    profile_path = Path("config/profiles") / f"{profile_name}.yaml"
    if not profile_path.exists():
        print(f"Profile not found: {profile_path}")
        sys.exit(1)
    with open(profile_path) as f:
        return yaml.safe_load(f)


def discover_canaries(
    filter_phases: str | None = None,
    canary_dir: Path | None = None,
) -> list[dict]:
    """Discover and load canary specifications."""
    canary_dir = canary_dir or Path("bench/canaries")
    if not canary_dir.exists():
        return []

    canaries = []
    for yaml_file in sorted(canary_dir.rglob("*.yaml")):
        with open(yaml_file) as f:
            spec = yaml.safe_load(f)
        if spec is None:
            continue

        # Apply phase filter
        if filter_phases:
            phases = [p.strip() for p in filter_phases.split(",")]
            if spec.get("phase") not in phases:
                continue

        spec["_source_file"] = str(yaml_file)
        canaries.append(spec)

    return canaries


def execute_canary(
    canary: dict,
    timeout: int = 300,
    provider_type: str = "mock",
    model: str = "gpt-4o",
) -> dict:
    """Execute a single canary test against the LLM provider.

    Steps:
        1. Extract prompt from the canary spec.
        2. Call the LLM provider for a response.
        3. Run each configured grader on the response.
        4. Compute a weighted score across graders.
        5. Return a result dict with status pass/fail/error.
    """
    import asyncio
    import importlib

    from bench.engine.provider import create_provider

    start_time = time.time()
    canary_id = canary.get("id", "unknown")

    try:
        prompt = canary.get("prompt")
        if not prompt:
            raise ValueError("Canary spec is missing 'prompt' field")

        provider = create_provider(provider_type)
        response = asyncio.run(provider.complete(prompt=prompt, model=model))

        grader_specs = canary.get("graders", [])
        grader_scores: list[dict] = []
        weights: list[float] = []

        builtin_graders = {
            "keyword": ("bench.graders.code.keyword_grader", "KeywordGrader"),
            "ast": ("bench.graders.code.ast_grader", "ASTGrader"),
            "structural": ("bench.graders.code.structural_grader", "StructuralGrader"),
            "file": ("bench.graders.code.file_grader", "FileGrader"),
        }

        for spec in grader_specs:
            grader_type = spec.get("type", "")
            config = spec.get("config", {})
            weight = spec.get("weight", 1.0)

            if grader_type in builtin_graders:
                module_path, class_name = builtin_graders[grader_type]
            else:
                module_path = spec.get("module", "")
                class_name = spec.get("class", grader_type)

            mod = importlib.import_module(module_path)
            grader_cls = getattr(mod, class_name)
            grader = grader_cls(**config)
            result = grader.grade(response)

            grader_scores.append({
                "grader": class_name,
                "score": result.score,
                "passed": result.passed,
            })
            weights.append(weight)

        if grader_scores:
            total_w = sum(weights)
            overall = sum(
                s["score"] * w / total_w for s, w in zip(grader_scores, weights)
            )
        else:
            overall = 1.0 if response else 0.0

        passed = overall >= 0.7
        status = "pass" if passed else "fail"

        return {
            "canary_id": canary_id,
            "status": status,
            "scores": {"overall": round(overall, 4), "by_grader": grader_scores},
            "duration_seconds": round(time.time() - start_time, 3),
        }

    except Exception as exc:
        return {
            "canary_id": canary_id,
            "status": "error",
            "scores": {"overall": 0.0, "by_grader": []},
            "error": str(exc),
            "duration_seconds": round(time.time() - start_time, 3),
        }


def generate_report(
    results: list[dict],
    profile: dict,
    run_id: str,
) -> dict:
    """Generate a benchmark report from results."""
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    errored = sum(1 for r in results if r["status"] == "error")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    total = len(results)

    scores = [r["scores"]["overall"] for r in results if r["status"] in ("pass", "fail")]
    overall_score = sum(scores) / len(scores) if scores else 0.0

    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "harness_version": "1.0.0",
        "config": {
            "profile": profile.get("name", "unknown"),
        },
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errored": errored,
            "skipped": skipped,
            "overall_score": round(overall_score, 4),
            "duration_seconds": round(
                sum(r.get("duration_seconds", 0) for r in results), 3
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SDLC Harness Benchmarks")
    parser.add_argument("--profile", default="ci-quick", help="Benchmark profile")
    parser.add_argument("--filter", default="", help="Filter by phase (comma-separated)")
    parser.add_argument("--output", type=Path, help="Output report path")
    parser.add_argument("--provider", default="mock", help="LLM provider (mock/openai)")
    parser.add_argument("--model", default="gpt-4o", help="Model name")
    args = parser.parse_args()

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    print(f"Benchmark run: {run_id}")
    print(f"Profile: {args.profile}")

    profile = load_profile(args.profile)
    canaries = discover_canaries(args.filter or None)

    if not canaries:
        print("No canaries found matching filter")
        return 0

    print(f"Found {len(canaries)} canaries")
    print()

    # Execute canaries
    results = []
    for i, canary in enumerate(canaries, 1):
        cid = canary.get("id", "unknown")
        print(f"  [{i}/{len(canaries)}] {cid}...", end=" ", flush=True)
        timeout = canary.get("timeout_seconds", profile.get("timeout_seconds", 300))
        result = execute_canary(canary, timeout, args.provider, args.model)
        print(result["status"])
        results.append(result)

    # Generate report
    report = generate_report(results, profile, run_id)

    # Write report
    reports_dir = Path("bench/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    output_path = args.output or reports_dir / f"{run_id}.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {output_path}")

    # Also write as latest
    latest_path = reports_dir / "latest.json"
    with open(latest_path, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    s = report["summary"]
    print(f"\nSummary: {s['passed']}/{s['total']} passed, score: {s['overall_score']:.2%}")

    return 0 if s.get("failed", 0) == 0 and s.get("errored", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
