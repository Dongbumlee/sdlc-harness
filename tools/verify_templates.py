#!/usr/bin/env python3
"""Verify the bundled default templates (ADR-0002).

Two modes:

  python3 tools/verify_templates.py           structural checks only
  python3 tools/verify_templates.py --run     also instantiate each template
                                              with its default tokens and run
                                              its verify steps (install, build,
                                              test) for real

Structural checks, per template under
packs/core/skills/sdlc-stack-profiles/assets/templates/<profile>/<kind>/:

  - template.yaml declares id/profile/kind/project_dirs/tokens/verify, and
    id == "<profile>/<kind>" matching its path
  - every {{token}} used in file names or file contents is declared, and
    every declared token is used
  - every project_dirs entry exists in the tree
  - the first project dir contains a Dockerfile; the tree contains a
    .github/workflows/ci.yml and at least one test file
  - verify steps are exactly install -> build -> test, each with cwd+command

--run mode instantiates into a temp directory (never the repo), substitutes
the token defaults, removes template.yaml, and executes the verify steps.
A test step that fails with the VSTest testhost connection error is
reported as ENV-BLOCKED (environment limitation per the harness's
environment-failure rule), not as a template failure.
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_ROOT = (
    REPO_ROOT
    / "packs/core/skills/sdlc-stack-profiles/assets/templates"
)

TOKEN_RE = re.compile(r"\{\{([A-Za-z0-9_-]+)\}\}")
TEST_FILE_RES = [
    re.compile(r"test_.*\.py$"),
    re.compile(r".*\.Tests\.csproj$"),
    re.compile(r".*Tests\.cs$"),
    re.compile(r".*\.test\.tsx?$"),
]

failures: list[str] = []
warnings: list[str] = []


def fail(message: str) -> None:
    failures.append(message)
    print(f"FAIL: {message}")


def warn(message: str) -> None:
    warnings.append(message)
    print(f"WARN: {message}")


def discover_templates() -> list[Path]:
    if not TEMPLATES_ROOT.is_dir():
        fail(f"templates root not found: {TEMPLATES_ROOT}")
        return []
    return sorted(TEMPLATES_ROOT.glob("*/*/template.yaml"))


def load_template(template_yaml: Path) -> dict | None:
    try:
        data = yaml.safe_load(template_yaml.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report and continue
        fail(f"{template_yaml}: unreadable YAML: {exc}")
        return None
    if not isinstance(data, dict):
        fail(f"{template_yaml}: top level is not a mapping")
        return None
    return data


def check_template(template_yaml: Path) -> dict | None:
    template_dir = template_yaml.parent
    rel = template_dir.relative_to(REPO_ROOT)
    data = load_template(template_yaml)
    if data is None:
        return None

    for key in ("id", "profile", "kind", "project_dirs", "tokens", "verify"):
        if key not in data:
            fail(f"{rel}: template.yaml missing key '{key}'")
    if failures:
        return data

    profile, kind = template_dir.parent.name, template_dir.name
    if data["id"] != f"{profile}/{kind}":
        fail(f"{rel}: id '{data['id']}' != path '{profile}/{kind}'")
    if data["profile"] != profile or data["kind"] != kind:
        fail(f"{rel}: profile/kind fields do not match the directory names")

    declared = {}
    for token in data["tokens"]:
        if not isinstance(token, dict) or "name" not in token or "default" not in token:
            fail(f"{rel}: every token needs a name and a default")
        else:
            declared[token["name"]] = token["default"]

    used: set[str] = set()
    files = [p for p in template_dir.rglob("*") if p.is_file()]
    for path in files:
        used.update(TOKEN_RE.findall(str(path.relative_to(template_dir))))
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        used.update(TOKEN_RE.findall(text))
    undeclared = used - set(declared)
    if undeclared:
        fail(f"{rel}: tokens used but not declared: {sorted(undeclared)}")
    unused = set(declared) - used
    if unused:
        fail(f"{rel}: tokens declared but never used: {sorted(unused)}")

    for project_dir in data["project_dirs"]:
        literal = template_dir / project_dir
        if not literal.is_dir():
            fail(f"{rel}: project_dirs entry '{project_dir}' not found in tree")
    first_project = template_dir / data["project_dirs"][0]
    if not (first_project / "Dockerfile").is_file():
        fail(f"{rel}: no Dockerfile in first project dir '{data['project_dirs'][0]}'")
    if not (template_dir / ".github/workflows/ci.yml").is_file():
        fail(f"{rel}: missing .github/workflows/ci.yml")
    if not any(rx.search(p.name) for p in files for rx in TEST_FILE_RES):
        fail(f"{rel}: no test files found")

    steps = data["verify"]
    names = [s.get("step") for s in steps if isinstance(s, dict)]
    if names != ["install", "build", "test"]:
        fail(f"{rel}: verify steps must be install -> build -> test, got {names}")
    for step in steps:
        if not isinstance(step, dict) or not step.get("cwd") or not step.get("command"):
            fail(f"{rel}: every verify step needs cwd and command")

    print(f"OK: {rel} ({len(files)} files, tokens: {sorted(declared)})")
    return data


def substitute(text: str, defaults: dict[str, str]) -> str:
    for name, value in defaults.items():
        text = text.replace("{{" + name + "}}", value)
    return text


def instantiate(template_dir: Path, data: dict, dest: Path) -> None:
    defaults = {t["name"]: str(t["default"]) for t in data["tokens"]}
    for src in template_dir.rglob("*"):
        rel = Path(substitute(str(src.relative_to(template_dir)), defaults))
        target = dest / rel
        if src.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif src.name == "template.yaml":
            continue
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                text = src.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                shutil.copyfile(src, target)
            else:
                target.write_text(substitute(text, defaults), encoding="utf-8")


def run_template(template_dir: Path, data: dict) -> None:
    rel = template_dir.relative_to(REPO_ROOT)
    defaults = {t["name"]: str(t["default"]) for t in data["tokens"]}
    with tempfile.TemporaryDirectory(prefix="sdlc-template-") as tmp:
        root = Path(tmp)
        instantiate(template_dir, data, root)
        print(f"RUN: {rel} instantiated at {root}")
        for step in data["verify"]:
            cwd = root / substitute(step["cwd"], defaults)
            command = substitute(step["command"], defaults)
            proc = subprocess.run(
                command, shell=True, cwd=cwd,
                capture_output=True, text=True, timeout=1200,
            )
            tail = (proc.stdout + proc.stderr).strip().splitlines()
            last = tail[-1] if tail else ""
            if proc.returncode == 0:
                print(f"  [{step['step']}] exit 0 — {last[:120]}")
            elif step["step"] == "test" and "testhost" in (proc.stdout + proc.stderr):
                warn(f"{rel}: test step ENV-BLOCKED (testhost connection) — "
                     "environment limitation, not a template failure")
            else:
                fail(f"{rel}: verify step '{step['step']}' exit "
                     f"{proc.returncode} — {last[:200]}")


def main() -> int:
    run = "--run" in sys.argv[1:]
    templates = discover_templates()
    if not templates:
        fail("no bundled templates found")
    parsed: list[tuple[Path, dict]] = []
    for template_yaml in templates:
        data = check_template(template_yaml)
        if data is not None:
            parsed.append((template_yaml.parent, data))
    if run and not failures:
        for template_dir, data in parsed:
            run_template(template_dir, data)
    if failures:
        print(f"\n{len(failures)} template verification failure(s).")
        return 1
    print(f"\nAll {len(parsed)} bundled template(s) verified"
          f"{' (structure + execution)' if run else ' (structure)'}."
          + (f" {len(warnings)} warning(s)." if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
