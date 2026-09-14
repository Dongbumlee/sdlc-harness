#!/usr/bin/env python3
"""Regenerate docs/agent-inventory.md from the agent and skill sources.

The inventory used to be maintained by hand and drifted out of date
(missing agents, missing skills, wrong counts). This script derives every
table from the actual files so the document cannot silently go stale:

  python3 tools/generate_agent_inventory.py            # rewrite the doc
  python3 tools/generate_agent_inventory.py --check    # CI: fail if stale

Sources:
  com.github.copilot/agents/*.agent.md   (frontmatter + title line)
  skills/*/SKILL.md                       (frontmatter)
  plugin.json                             (version)
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
AGENT_DIR = REPO_ROOT / "com.github.copilot" / "agents"
SKILL_DIR = REPO_ROOT / "skills"
DOC_PATH = REPO_ROOT / "docs" / "agent-inventory.md"

PHASE_RE = re.compile(r"SDLC\s+Phases?\s+([0-9+\-–—,.\s]+?)\s*:", re.IGNORECASE)
GENERATED_RE = re.compile(r"^\*\*Generated:\*\* \d{4}-\d{2}-\d{2}$", re.M)


def without_generated_date(text: str) -> str:
    """Normalize the generation-date line so --check is reproducible.

    The date is informative when generating, but it must not make the
    freshness check fail just because a new day has begun.
    """
    return GENERATED_RE.sub("**Generated:** <date>", text)


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Return (frontmatter dict, first '# ' title line) for an agent/skill file."""
    text = path.read_text(encoding="utf-8")
    fm: dict = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = yaml.safe_load(text[3:end]) or {}
            text = text[end + 4 :]
    title = ""
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    return fm, title


def phase_of(filename: str, title: str) -> str:
    """Derive the SDLC phase label from the agent title line."""
    if filename == "harness.agent.md":
        return "All (1–9)"
    if filename == "qa-bug-checklist-reviewer.agent.md":
        return "On-demand"
    if "QA Perspective" in title:
        return "6 (sub)"
    m = PHASE_RE.search(title)
    if m:
        return m.group(1).replace("–", "-").replace("—", "-").strip()
    return "—"


def role_of(filename: str) -> str:
    """Derive the agent role type from the filename."""
    if filename == "harness.agent.md":
        return "Orchestrator"
    if filename == "qa-coordinator.agent.md":
        return "Orchestrator + Phase Worker"
    if filename == "qa-bug-checklist-reviewer.agent.md":
        return "Standalone"
    if filename.endswith("-reviewer.agent.md"):
        return "QA Reviewer"
    return "Phase Worker"


def cell(value: object) -> str:
    """Make a value safe for a Markdown table cell."""
    return str(value).replace("|", "\\|").replace("\n", " ")


def main() -> int:
    check = "--check" in sys.argv

    agent_files = sorted(AGENT_DIR.glob("*.agent.md"))
    agents = []
    for path in agent_files:
        fm, title = parse_frontmatter(path)
        agents.append(
            {
                "file": path.name,
                "name": fm.get("name", "—"),
                "role": role_of(path.name),
                "phase": phase_of(path.name, title),
                "user_invocable": fm.get("user-invocable", "—"),
                "skills": fm.get("skills") or [],
                "tools": fm.get("tools") or [],
                "sub_agents": fm.get("agents") or [],
                "description": (fm.get("description") or "").strip(),
            }
        )

    skill_dirs = sorted(p for p in SKILL_DIR.iterdir() if p.is_dir())
    skills = []
    for path in skill_dirs:
        fm, _ = parse_frontmatter(path / "SKILL.md")
        skills.append(
            {
                "dir": path.name,
                "name": fm.get("name", path.name),
                "description": (fm.get("description") or "").strip(),
            }
        )

    try:
        version = json.loads((REPO_ROOT / "plugin.json").read_text())["version"]
    except Exception:
        version = "?"

    # ---- cross-reference validation ----
    skill_names = {s["dir"] for s in skills}
    ref_problems: list[str] = []
    for a in agents:
        for s in a["skills"]:
            if s not in skill_names:
                ref_problems.append(
                    f"Agent `{a['file']}` references missing skill `{s}`"
                )

    def norm(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

    agent_slugs = {norm(a["name"]): a["file"] for a in agents}
    harness = next(a for a in agents if a["file"] == "harness.agent.md")
    for sub in harness["sub_agents"]:
        if norm(sub) not in agent_slugs:
            ref_problems.append(
                f"Harness frontmatter lists sub-agent `{sub}` with no matching agent file"
            )

    lines: list[str] = []
    add = lines.append
    add("# SDLC Harness — Agent Inventory")
    add("")
    add("> **Generated file — do not edit by hand.**")
    add("> Regenerate with `python3 tools/generate_agent_inventory.py`.")
    add("")
    add(f"**Version:** {version}")
    add(f"**Generated:** {date.today().isoformat()}")
    add(f"**Total agents:** {len(agents)} ({len(agent_files)} agent files)")
    add(f"**Total skills:** {len(skills)}")
    add("")

    # ---- summary table ----
    add("## 1. Agent Summary")
    add("")
    add("| # | Agent File | Name | Role | Phase(s) | User-Invocable | Skills (frontmatter) |")
    add("|---|---|---|---|---|---|---|")
    for i, a in enumerate(agents, 1):
        skills_cell = ", ".join(f"`{s}`" for s in a["skills"]) or "—"
        inv = a["user_invocable"]
        inv_cell = "Yes" if inv is True else ("No" if inv is False else "—")
        add(
            f"| {i} | `{a['file']}` | {cell(a['name'])} | {a['role']} | {a['phase']} "
            f"| {inv_cell} | {skills_cell} |"
        )
    add("")

    # ---- counts by role ----
    add("## 2. Counts by Role")
    add("")
    add("| Role | Count | Agents |")
    add("|---|---|---|")
    by_role: dict[str, list[str]] = {}
    for a in agents:
        by_role.setdefault(a["role"], []).append(a["name"])
    for role, names in by_role.items():
        add(f"| {role} | {len(names)} | {', '.join(names)} |")
    add("")

    # ---- skill inventory ----
    add("## 3. Skill Inventory")
    add("")
    add("| # | Skill Directory | Name | Description | Used By (frontmatter) |")
    add("|---|---|---|---|---|")
    for i, s in enumerate(skills, 1):
        users = [a["name"] for a in agents if s["dir"] in a["skills"]]
        desc = s["description"]
        if len(desc) > 140:
            desc = desc[:137] + "..."
        add(
            f"| {i} | `{s['dir']}` | {cell(s['name'])} | {cell(desc)} "
            f"| {', '.join(users) or '—'} |"
        )
    add("")

    # ---- phase-to-agent mapping ----
    add("## 4. Phase-to-Agent Mapping")
    add("")
    add("| Phase | Agent(s) |")
    add("|---|---|")
    by_phase: dict[str, list[str]] = {}
    for a in agents:
        by_phase.setdefault(a["phase"], []).append(a["name"])
    order = ["All (1–9)", "1-2", "3", "3+8", "4", "5", "6", "6 (sub)", "7", "8-9", "On-demand", "—"]
    phases = sorted(by_phase, key=lambda p: order.index(p) if p in order else 99)
    for p in phases:
        add(f"| {p} | {', '.join(by_phase[p])} |")
    add("")

    # ---- tool / MCP matrix ----
    add("## 5. Tool Requirements Matrix")
    add("")
    add("| Tool / MCP Server | Agents Using It |")
    add("|---|---|")
    tool_users: dict[str, list[str]] = {}
    for a in agents:
        for t in a["tools"]:
            tool_users.setdefault(t, []).append(a["name"])
    for tool in sorted(tool_users):
        add(f"| `{tool}` | {', '.join(tool_users[tool])} |")
    add("")

    # ---- delegation graph ----
    add("## 6. Delegation Graph")
    add("")
    add("```")
    add("User")
    add(" └── Harness (master orchestrator)")
    coord = next(a for a in agents if a["file"] == "qa-coordinator.agent.md")
    coord_subs = [agent_slugs.get(norm(s), f"{s} (unresolved)") for s in coord["sub_agents"]]
    for a in agents:
        if a["file"] in ("harness.agent.md", "qa-bug-checklist-reviewer.agent.md"):
            continue
        marker = "QA Coordinator" if a["file"] == "qa-coordinator.agent.md" else a["name"]
        add(f"      ├── {marker}")
        if a["file"] == "qa-coordinator.agent.md":
            for sub in coord_subs:
                add(f"      │    ├── {sub}")
    add(" └── QA Bug Checklist Reviewer (standalone, user-invocable)")
    add("```")
    add("")

    # ---- validation ----
    add("## 7. Cross-Reference Validation")
    add("")
    if ref_problems:
        add("⛔ Problems found:")
        add("")
        for p in ref_problems:
            add(f"- {p}")
    else:
        add("✅ All skill references resolve to `skills/<name>/SKILL.md`.")
        add("✅ All Harness sub-agent references resolve to agent files.")
    add("")

    # ---- notes ----
    add("## 8. Notes")
    add("")
    add("- Agent counts and skill usage are derived from frontmatter, not prose —")
    add("  if a number here looks wrong, fix the agent file, not this document.")
    add("- `user-invocable: —` means the field is not declared in frontmatter.")
    add("- Run with `--check` in CI to fail when this document is stale.")
    add("")

    output = "\n".join(lines)
    if check:
        current = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
        if without_generated_date(current) != without_generated_date(output):
            print("agent-inventory.md is stale — regenerate with:")
            print("  python3 tools/generate_agent_inventory.py")
            return 1
        print("agent-inventory.md is up to date.")
        return 0

    DOC_PATH.write_text(output, encoding="utf-8")
    print(f"Wrote {DOC_PATH} ({len(agents)} agents, {len(skills)} skills)")
    if ref_problems:
        print("Warnings:")
        for p in ref_problems:
            print(f"  - {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
