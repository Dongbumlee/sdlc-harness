#!/usr/bin/env python3
"""Validate all canary specification files against the schema."""

import json
import sys
from pathlib import Path

import yaml

try:
    from jsonschema import Draft7Validator, ValidationError
except ImportError:
    print("jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)


def load_schema() -> dict:
    """Load the canary specification schema."""
    schema_path = Path(__file__).parent.parent / "schemas" / "canary-spec.schema.json"
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}")
        sys.exit(1)
    with open(schema_path) as f:
        return json.load(f)


def find_canaries() -> list[Path]:
    """Find all canary YAML files."""
    canary_dir = Path(__file__).parent.parent / "bench" / "canaries"
    if not canary_dir.exists():
        print(f"Canary directory not found: {canary_dir}")
        return []
    return sorted(canary_dir.rglob("*.yaml"))


def validate_canary(path: Path, validator: Draft7Validator) -> list[str]:
    """Validate a single canary file. Returns list of error messages."""
    errors = []
    try:
        with open(path) as f:
            spec = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]

    if spec is None:
        return ["Empty file"]

    for error in validator.iter_errors(spec):
        errors.append(f"{error.json_path}: {error.message}")

    return errors


def main() -> int:
    schema = load_schema()
    validator = Draft7Validator(schema)
    canaries = find_canaries()

    if not canaries:
        print("No canary files found")
        return 0

    total_errors = 0
    for path in canaries:
        rel_path = path.relative_to(Path(__file__).parent.parent)
        errors = validate_canary(path, validator)
        if errors:
            print(f"FAIL {rel_path}")
            for err in errors:
                print(f"  - {err}")
            total_errors += len(errors)
        else:
            print(f"  OK {rel_path}")

    print(f"\n{len(canaries)} canaries checked, {total_errors} errors")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
