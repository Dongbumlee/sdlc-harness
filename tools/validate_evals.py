#!/usr/bin/env python3
"""Validate all skill eval specification files against the schema.

Eval specs are frozen cases for the plugin's skills (bench/evals/). This
validator is the zero-cost gate: it checks spec shape against
schemas/skill-eval-spec.schema.json and the semantic rules a schema
cannot express — the named skill exists, case names are unique, trigger
cases declare whether the skill must fire, capability cases declare an
output expectation. Running the cases against a live model is a
separate, explicitly opened step; nothing here spends tokens.
"""

import json
import sys
from pathlib import Path

import yaml

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent


def load_schema() -> dict:
    schema_path = REPO_ROOT / "schemas" / "skill-eval-spec.schema.json"
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}")
        sys.exit(1)
    with open(schema_path) as f:
        return json.load(f)


def find_specs() -> list[Path]:
    eval_dir = REPO_ROOT / "bench" / "evals"
    if not eval_dir.exists():
        print(f"Eval directory not found: {eval_dir}")
        return []
    return sorted(eval_dir.rglob("*.yaml"))


def known_skills() -> set:
    skills = set()
    for skill_md in REPO_ROOT.glob("packs/*/skills/*/SKILL.md"):
        skills.add(skill_md.parent.name)
    return skills


def validate_spec(path: Path, validator: Draft7Validator, skills: set) -> list[str]:
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
    if errors:
        return errors

    if spec["skill"] != path.stem:
        errors.append(
            f"skill '{spec['skill']}' does not match file name '{path.stem}'"
        )
    if spec["skill"] not in skills:
        errors.append(f"skill '{spec['skill']}' not found under packs/*/skills/")

    seen = set()
    for case in spec["cases"]:
        if case["name"] in seen:
            errors.append(f"duplicate case name: {case['name']}")
        seen.add(case["name"])
        expect = case["expect"]
        if case["category"] == "trigger" and "skill_invoked" not in expect:
            errors.append(
                f"case {case['name']}: trigger cases must declare expect.skill_invoked"
            )
        if case["category"] == "capability" and "output_must_contain" not in expect:
            errors.append(
                f"case {case['name']}: capability cases must declare "
                "expect.output_must_contain"
            )
    return errors


def main() -> int:
    validator = Draft7Validator(load_schema())
    skills = known_skills()
    specs = find_specs()
    if not specs:
        print("No eval specs found.")
        return 1
    failed = 0
    for path in specs:
        errors = validate_spec(path, validator, skills)
        if errors:
            failed += 1
            print(f"FAIL {path.relative_to(REPO_ROOT)}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK   {path.relative_to(REPO_ROOT)}")
    print(f"\n{len(specs)} spec(s), {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
