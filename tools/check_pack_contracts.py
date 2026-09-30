#!/usr/bin/env python3
"""Phase 1+2 pack contracts check (ADR-0001).

Enforces the pack contracts on every PR:

1. Canonical agent source: ``com.github.copilot/agents/`` is the single source of
   truth for the flat layout. ``.github/agents/`` must be byte-identical; any
   divergence fails the check. (Until Phase 3 CI assembly lands, both directories
   stay checked in.)
2. Pack manifest schema: every ``packs/*/pack.json`` (except the ``_template/``
   skeleton) must validate against ``schemas/cloud-pack.schema.json``.
3. Reference integrity: every agent file and skill directory referenced by a pack
   manifest must exist. Reference resolution:
     - ``agents/<file>`` -> ``packs/<name>/agents/<file>`` (pack-local, required)
     - ``skills/<name>`` -> ``packs/<name>/skills/<name>`` (pack-local, required)
     - bare ``<file>`` (agents) -> pack-local ``agents/`` first, then the core
       pack's agents (``packs/core/agents/`` in Phase 3, the canonical flat
       directory until then). This is how cloud packs inherit core agents such
       as the generic deployer (ADR-0001, decision A).
     - bare ``<name>`` (skills) -> root ``skills/<name>`` compatibility layout.
4. Pack-source sync (Phase 2): a pack-local file is the canonical home for that
   file, so the flat-layout copies must be byte-identical:
     - ``packs/<name>/agents/<file>`` == ``com.github.copilot/agents/<file>``
     - ``packs/<name>/skills/<name>/`` tree == ``skills/<name>/`` tree

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
CORE_AGENTS_DIR = PACKS_DIR / "core" / "agents"  # Phase 3 layout; may not exist yet
SCHEMA_PATH = REPO_ROOT / "schemas" / "cloud-pack.schema.json"
TEMPLATE_DIR_NAME = "_template"

failures: list[str] = []


def rel(path: Path) -> str:
    """Repository-relative path for readable failure messages."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def fail(message: str) -> None:
    failures.append(message)
    print(f"FAIL: {message}")


def _dir_trees_identical(left: Path, right: Path) -> bool:
    """Recursively compare two directory trees (names + file contents)."""
    cmp = filecmp.dircmp(left, right)
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    for sub in cmp.common_dirs:
        if not _dir_trees_identical(left / sub, right / sub):
            return False
    for name in cmp.common_files:
        if not filecmp.cmp(left / name, right / name, shallow=False):
            return False
    return True


def check_agent_drift() -> None:
    """Contract 1: the mirror agent directory must match the canonical source."""
    print(f"Checking agent drift: {rel(MIRROR_AGENTS)} vs canonical {rel(CANONICAL_AGENTS)} ...")
    if not CANONICAL_AGENTS.is_dir():
        fail(f"canonical agent directory missing: {rel(CANONICAL_AGENTS)}")
        return
    if not MIRROR_AGENTS.is_dir():
        fail(f"mirror agent directory missing: {rel(MIRROR_AGENTS)}")
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


def _resolve_agent(pack_dir: Path, ref: str) -> Path | None:
    """Resolve an agent reference to a file, or None if it exists nowhere."""
    if ref.startswith("agents/"):
        candidate = pack_dir / ref
        return candidate if candidate.is_file() else None
    for base in (pack_dir / "agents", CORE_AGENTS_DIR, CANONICAL_AGENTS):
        candidate = base / ref
        if candidate.is_file():
            return candidate
    return None


def check_pack_manifests() -> None:
    """Contracts 2-4: schema validation, reference integrity, pack-source sync."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)

    pack_dirs = sorted(p for p in PACKS_DIR.iterdir() if p.is_dir())
    if not pack_dirs:
        fail(f"no pack directories found under {rel(PACKS_DIR)}")

    for pack_dir in pack_dirs:
        if pack_dir.name == TEMPLATE_DIR_NAME:
            print(f"Skipping template skeleton: {pack_dir.name}/")
            continue
        manifest_path = pack_dir / "pack.json"
        print(f"Checking pack manifest: {rel(manifest_path)} ...")
        if not manifest_path.is_file():
            fail(f"pack {pack_dir.name}/ is missing pack.json")
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"{rel(manifest_path)}: invalid JSON: {exc}")
            continue

        for error in validator.iter_errors(manifest):
            fail(f"{rel(manifest_path)}: schema violation at '{error.json_path}': {error.message}")

        # Agents + reviewers: resolve, then verify pack-source sync for pack-local files.
        agents = manifest.get("agents") or {}
        agent_refs = [(role, ref) for role, ref in agents.items() if isinstance(ref, str)]
        agent_refs += [("reviewer", ref) for ref in manifest.get("reviewers") or [] if isinstance(ref, str)]
        seen_refs: set[str] = set()
        for role, ref in agent_refs:
            if ref in seen_refs:
                continue
            seen_refs.add(ref)
            resolved = _resolve_agent(pack_dir, ref)
            if resolved is None:
                fail(f"{rel(manifest_path)}: agent '{role}' -> {ref} not found in pack or core agent dirs")
                continue
            if ref.startswith("agents/"):
                # Pack-local file is canonical: the flat copy must match it.
                flat_copy = CANONICAL_AGENTS / Path(ref).name
                if not flat_copy.is_file():
                    fail(
                        f"{rel(manifest_path)}: pack-local agent {ref} has no flat-layout copy "
                        f"at {rel(flat_copy)} (kept for compatibility until Phase 3)"
                    )
                elif not filecmp.cmp(pack_dir / ref, flat_copy, shallow=False):
                    fail(
                        f"{rel(manifest_path)}: pack-local agent {ref} diverged from its "
                        f"flat-layout copy -- edit only packs/{pack_dir.name}/agents/, then sync"
                    )

        # Skills: resolve, then verify pack-source sync for pack-local skill trees.
        for skill in manifest.get("skills") or []:
            if skill.startswith("skills/"):
                name = skill[len("skills/"):]
                pack_skill = pack_dir / "skills" / name
                flat_skill = SKILLS_DIR / name
                if not pack_skill.is_dir():
                    fail(f"{rel(manifest_path)}: skill '{skill}' not found under packs/{pack_dir.name}/skills/")
                    continue
                if not (pack_skill / "SKILL.md").is_file():
                    fail(f"{rel(manifest_path)}: skill '{skill}' is missing SKILL.md")
                if not flat_skill.is_dir():
                    fail(
                        f"{rel(manifest_path)}: pack-local skill {skill} has no flat-layout copy "
                        f"at {rel(flat_skill)} (kept for compatibility until Phase 3)"
                    )
                elif not _dir_trees_identical(pack_skill, flat_skill):
                    fail(
                        f"{rel(manifest_path)}: pack-local skill {skill} diverged from its "
                        f"flat-layout copy -- edit only packs/{pack_dir.name}/skills/, then sync"
                    )
            else:
                if not (SKILLS_DIR / skill).is_dir():
                    fail(f"{rel(manifest_path)}: skill '{skill}' not found under skills/")

        # mcpServers, when declared, must point at a real file inside the pack.
        mcp = manifest.get("mcpServers")
        if isinstance(mcp, str) and not (pack_dir / mcp).is_file():
            fail(f"{rel(manifest_path)}: mcpServers -> {mcp} not found in {pack_dir.name}/")


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
