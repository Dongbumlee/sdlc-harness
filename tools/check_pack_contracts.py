#!/usr/bin/env python3
"""Phase 1 pack contracts check (ADR-0001).

Enforces three contracts on every PR:

1. Canonical agent source: ``com.github.copilot/agents/`` is the single source of
   truth for agent files. ``.github/agents/`` must be byte-identical; any divergence
   fails the check. (Until Phase 3 CI assembly lands, both directories stay checked in.)
2. Pack manifest schema: every ``packs/*/pack.json`` (except the ``_template/``
   skeleton) must validate against ``schemas/cloud-pack.schema.json``.
3. Reference integrity: every agent file and skill directory referenced by a pack
   manifest must exist (agents resolve against the canonical agent directory,
   skills against the root ``skills/`` compatibility layout).

Exit code is 0 when all contracts hold, 1 otherwise.
"""

from __future__ import annotations

import filecmp
import json
import sys
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_AGENTS = REPO_ROOT / "com.github.copilot" / "agents"
MIRROR_AGENTS = REPO_ROOT / ".github" / "agents"
SKILLS_DIR = REPO_ROOT / "skills"
PACKS_DIR = REPO_ROOT / "packs"
SCHEMA_PATH = REPO_ROOT / "schemas" / "cloud-pack.schema.json"
TEMPLATE_DIR_NAME = "_template"

failures: list[str] = []


def fail(message: str) -> None:
    failures.append(message)
    print(f"FAIL: {message}")


def check_agent_drift() -> None:
    """Contract 1: the mirror agent directory must match the canonical source."""
    print(f"Checking agent drift: {MIRROR_AGENTS} vs canonical {CANONICAL_AGENTS} ...")
    if not CANONICAL_AGENTS.is_dir():
        fail(f"canonical agent directory missing: {CANONICAL_AGENTS}")
        return
    if not MIRROR_AGENTS.is_dir():
        fail(f"mirror agent directory missing: {MIRROR_AGENTS}")
        return

    canonical = {p.name for p in CANONICAL_AGENTS.glob("*.agent.md")}
    mirror = {p.name for p in MIRROR_AGENTS.glob("*.agent.md")}
    for name in sorted(canonical - mirror):
        fail(f"agent {name} exists in canonical source but not in .github/agents/")
    for name in sorted(mirror - canonical):
        fail(f"agent {name} exists in .github/agents/ but not in canonical source")
    for name in sorted(canonical & mirror):
        if not filecmp.cmp(CANONICAL_AGENTS / name, MIRROR_AGENTS / name, shallow=False):
            fail(
                f"agent {name} diverged between com.github.copilot/agents/ and "
                f".github/agents/ -- edit only the canonical source, then sync the mirror"
            )


def check_pack_manifests() -> None:
    """Contracts 2 + 3: schema validation and reference integrity per pack."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)

    pack_dirs = sorted(p for p in PACKS_DIR.iterdir() if p.is_dir())
    if not pack_dirs:
        fail(f"no pack directories found under {PACKS_DIR}")

    for pack_dir in pack_dirs:
        if pack_dir.name == TEMPLATE_DIR_NAME:
            print(f"Skipping template skeleton: {pack_dir.name}/")
            continue
        manifest_path = pack_dir / "pack.json"
        print(f"Checking pack manifest: {manifest_path.relative_to(REPO_ROOT)} ...")
        if not manifest_path.is_file():
            fail(f"pack {pack_dir.name}/ is missing pack.json")
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"{manifest_path}: invalid JSON: {exc}")
            continue

        for error in validator.iter_errors(manifest):
            fail(f"{manifest_path}: schema violation at '{error.json_path}': {error.message}")

        # Reference integrity: agents resolve against the canonical directory.
        agents = manifest.get("agents") or {}
        for role, filename in agents.items():
            if not isinstance(filename, str):
                continue
            agent_file = CANONICAL_AGENTS / filename
            if not agent_file.is_file():
                fail(f"{manifest_path}: agent '{role}' -> {filename} not found in canonical agent dir")
            # Warn (don't fail): pack-local agent files are a Phase 2 concept.
            pack_local = pack_dir / "agents" / filename
            if pack_local.is_file():
                print(f"  note: {filename} also exists under {pack_dir.name}/agents/ (Phase 2 layout)")

        for extra in manifest.get("reviewers") or []:
            if isinstance(extra, str) and not (CANONICAL_AGENTS / extra).is_file():
                fail(f"{manifest_path}: reviewer agent {extra} not found in canonical agent dir")

        # Reference integrity: skills resolve against the root skills/ layout.
        for skill in manifest.get("skills") or []:
            if not (SKILLS_DIR / skill).is_dir():
                fail(f"{manifest_path}: skill '{skill}' not found under skills/")

        # mcpServers, when declared, must point at a real file inside the pack.
        mcp = manifest.get("mcpServers")
        if isinstance(mcp, str) and not (pack_dir / mcp).is_file():
            fail(f"{manifest_path}: mcpServers -> {mcp} not found in {pack_dir.name}/")


def main() -> int:
    check_agent_drift()
    check_pack_manifests()
    if failures:
        print(f"\n{len(failures)} contract violation(s) found.")
        return 1
    print("\nAll pack contracts hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
