"""Tests for tools/check_records.py — the current-state records checker.

The checker guards the harness's paired-history rule (base definitions
section 8.4): the brief's Current frame must equal the fold of its
frame revisions, and the ADR index must match the ADR files' own
status lines. Fixtures are minimal projects written to a temp dir;
the checker runs as a subprocess so the CLI contract (output lines,
exit code) is what is tested.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools" / "check_records.py"
ASSET = (
    REPO
    / "packs"
    / "core"
    / "skills"
    / "sdlc-workspace-init"
    / "assets"
    / "records-check"
    / "check_records.py"
)

FRAME = {
    "Problem and users": "Solo developers tracking habits",
    "Capabilities and boundary": "CRUD for habits and check-ins; no social features",
    "Project type": "api",
    "Stack": "python",
    "Data and sensitivity": "none",
    "Integrations and target": "none",
    "Scale signals": "about 5 user-facing operations",
    "Approval posture": "attended",
    "Run envelope": "Small band (base definitions section 8.2)",
}
FIELDS = list(FRAME)
MINIMUM = FIELDS[:5]


def brief_text(frame=None, statuses=None, revisions=None):
    frame = frame or FRAME
    statuses = statuses or {f: "confirmed" for f in FIELDS[:7]}
    revisions = revisions or [(1, FRAME)]
    lines = ["# Design Brief — Habit Tracker", "", "## Current frame", ""]
    lines += [f"- {f}: {frame[f]}" for f in FIELDS]
    for i, field in enumerate(FIELDS[:7], start=1):
        lines += ["", f"## {i}. {field}", "", f"Status: {statuses[field]}", "",
                  "Detail recorded at intake."]
    lines += ["", "## Frame revisions", ""]
    for number, sets in revisions:
        lines += [f"### Frame revision {number} — 2026-11-12", ""]
        lines += [f"- Sets {f}: {v}" for f, v in sets.items()]
        lines += [""]
    return "\n".join(lines)


def adr_text(status):
    return (
        "# ADR-001: Storage choice\n\n## Metadata\n"
        f"- **Status:** {status}\n- **Date:** 2026-11-12\n"
    )


def write_project(root: Path, brief=None, adrs=None, index=None):
    if brief is not None:
        (root / ".SDLC").mkdir(parents=True, exist_ok=True)
        (root / ".SDLC" / "design-brief.md").write_text(brief, encoding="utf-8")
    if adrs is not None:
        (root / "docs" / "adr").mkdir(parents=True, exist_ok=True)
        for name, status in adrs:
            (root / "docs" / "adr" / name).write_text(adr_text(status), encoding="utf-8")
    if index is not None:
        (root / "docs" / "adr").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "adr" / "README.md").write_text(index, encoding="utf-8")


def run_checker(root: Path, *extra):
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root), *extra],
        capture_output=True,
        text=True,
    )


def test_valid_project_passes(tmp_path):
    write_project(
        tmp_path,
        brief=brief_text(),
        adrs=[("ADR-001-storage.md", "Accepted")],
        index="# ADR Index\n\n- ADR-001: Storage choice — Accepted\n",
    )
    result = run_checker(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "records check: PASS" in result.stdout
    assert "minimum_set: complete" in result.stdout


def test_stale_current_frame_fails(tmp_path):
    stale = dict(FRAME, Stack="rust")
    write_project(tmp_path, brief=brief_text(frame=stale))
    result = run_checker(tmp_path)
    assert result.returncode == 1
    assert "Current frame is stale" in result.stdout


def test_frame_revision_fold_passes(tmp_path):
    revised = dict(FRAME, Stack="rust")
    revisions = [(1, FRAME), (2, {"Stack": "rust"})]
    write_project(
        tmp_path, brief=brief_text(frame=revised, revisions=revisions)
    )
    result = run_checker(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_minimum_set_incomplete_reports_but_passes_by_default(tmp_path):
    statuses = {f: "confirmed" for f in FIELDS[:7]}
    statuses["Data and sensitivity"] = "proposed"
    write_project(tmp_path, brief=brief_text(statuses=statuses))
    result = run_checker(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "minimum_set: incomplete" in result.stdout

    strict = run_checker(tmp_path, "--require-minimum")
    assert strict.returncode == 1
    assert "minimum set is not fully confirmed" in strict.stdout


def test_adr_index_status_mismatch_fails(tmp_path):
    write_project(
        tmp_path,
        adrs=[("ADR-001-storage.md", "Proposed")],
        index="# ADR Index\n\n- ADR-001: Storage choice — Accepted\n",
    )
    result = run_checker(tmp_path)
    assert result.returncode == 1
    assert "index says 'Accepted'" in result.stdout


def test_adr_missing_from_index_fails(tmp_path):
    write_project(
        tmp_path,
        adrs=[("ADR-001-storage.md", "Accepted"), ("ADR-002-auth.md", "Proposed")],
        index="# ADR Index\n\n- ADR-001: Storage choice — Accepted\n",
    )
    result = run_checker(tmp_path)
    assert result.returncode == 1
    assert "not listed in the ADR index" in result.stdout


def test_supersession_pointer_in_index_is_not_a_duplicate_entry(tmp_path):
    """An index line's 'Superseded by ADR-002' pointer names the
    successor; it must not count as a second entry for ADR-002.
    (Caught by verification scenario (g) of the intake design.)"""
    write_project(
        tmp_path,
        adrs=[("ADR-001-storage.md", "Superseded"), ("ADR-002-storage-v2.md", "Accepted")],
        index=(
            "# ADR Index\n\n"
            "- ADR-001: Storage choice — Superseded by ADR-002\n"
            "- ADR-002: Storage choice v2 — Accepted\n"
        ),
    )
    result = run_checker(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_empty_project_skips_cleanly(tmp_path):
    result = run_checker(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "records check: PASS" in result.stdout


def test_deployed_asset_matches_tool():
    """The copy workspace-init deploys into projects must not drift
    from the plugin's own checker."""
    assert ASSET.exists(), "workspace-init records-check asset is missing"
    assert ASSET.read_bytes() == TOOL.read_bytes()
