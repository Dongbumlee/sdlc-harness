#!/usr/bin/env python3
"""Bootstrap the SDLC Harness environment for a new project.

Sets up the directory structure, validates configuration, and
prepares the workspace for benchmark execution.
"""

import argparse
import json
import sys
from pathlib import Path

import yaml


REQUIRED_DIRS = [
    "bench/canaries/requirements",
    "bench/canaries/design",
    "bench/canaries/implement",
    "bench/canaries/qa",
    "bench/canaries/deploy",
    "bench/canaries/document",
    "bench/canaries/rai",
    "bench/canaries/release",
    "bench/canaries/scaffold",
    "bench/graders/code",
    "bench/graders/llm",
    "bench/engine",
    "bench/reports",
    "config/profiles",
    "orchestrator",
    "schemas",
    "tools",
]


def create_directories(base: Path) -> None:
    """Create required directory structure."""
    for d in REQUIRED_DIRS:
        dir_path = base / d
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  DIR {d}/")


def validate_config(base: Path) -> list[str]:
    """Validate harness configuration."""
    issues = []

    # Check for harness config schema
    schema_path = base / "schemas" / "harness-config.schema.json"
    if not schema_path.exists():
        issues.append("Missing schemas/harness-config.schema.json")

    # Check for at least one profile
    profiles_dir = base / "config" / "profiles"
    if profiles_dir.exists():
        profiles = list(profiles_dir.glob("*.yaml"))
        if not profiles:
            issues.append("No profiles found in config/profiles/")
    else:
        issues.append("Missing config/profiles/ directory")

    # Check for canary specs
    canary_dir = base / "bench" / "canaries"
    if canary_dir.exists():
        canaries = list(canary_dir.rglob("*.yaml"))
        if not canaries:
            issues.append("No canary specs found in bench/canaries/")
    else:
        issues.append("Missing bench/canaries/ directory")

    return issues


def print_status(base: Path) -> None:
    """Print current harness status."""
    canary_dir = base / "bench" / "canaries"
    canaries = list(canary_dir.rglob("*.yaml")) if canary_dir.exists() else []
    phases = set()
    for c in canaries:
        phases.add(c.parent.name)

    profiles_dir = base / "config" / "profiles"
    profiles = list(profiles_dir.glob("*.yaml")) if profiles_dir.exists() else []

    print(f"\nHarness Status:")
    print(f"  Canary specs:  {len(canaries)}")
    print(f"  Phases covered: {', '.join(sorted(phases)) or 'none'}")
    print(f"  Profiles:      {len(profiles)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap SDLC Harness")
    parser.add_argument("--check", action="store_true", help="Validate only, don't create")
    parser.add_argument("--base", type=Path, default=Path("."), help="Base directory")
    args = parser.parse_args()

    base = args.base.resolve()
    print(f"SDLC Harness Bootstrap: {base}")

    if args.check:
        issues = validate_config(base)
        if issues:
            print("\nIssues found:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
        print("\nAll checks passed")
        print_status(base)
        return 0

    print("\nCreating directory structure...")
    create_directories(base)

    issues = validate_config(base)
    if issues:
        print(f"\n{len(issues)} issues to address:")
        for issue in issues:
            print(f"  - {issue}")

    print_status(base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
