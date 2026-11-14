#!/usr/bin/env python3
"""Mechanical consistency check for a project's current-state records.

The harness keeps two kinds of truth side by side (base definitions
section 8.4): append-only histories (the design brief's frame
revisions, the ADR set) and current-state readings derived from them
(the brief's Current frame section, the ADR index). The readings are
what a resumed run trusts, so they must never drift from the
histories. This checker verifies, mechanically:

1. Brief fold — the Current frame section of `.SDLC/design-brief.md`
   equals the fold of its Frame revisions (revision 1 is the initial
   frame and sets every field; each later revision's `Sets` lines
   override). A mismatch means the current-state reading is stale.
2. Field statuses — every checklist field section of the brief
   carries a `Status:` line (`confirmed` / `proposed` / `open`), and
   the minimum set (fields 1-5) is reported: `complete` only when all
   five are `confirmed`. Incompleteness is reported, not failed,
   unless `--require-minimum` is given (the Phase 1 gate uses it;
   an unattended run legitimately carries `proposed` fields until
   its first attended checkpoint).
3. ADR index — `docs/adr/README.md` lists every `ADR-*.md` file
   exactly once, with the status the file's own Status line carries,
   and lists no ADR that has no file.

Exit code 0 means every structural check passed. The check is
read-only and uses only the standard library, so the copy deployed
into a project (`.SDLC/tools/check_records.py`, via the
sdlc-workspace-init skill) runs anywhere Python 3 does.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FRAME_FIELDS = [
    "Problem and users",
    "Capabilities and boundary",
    "Project type",
    "Stack",
    "Data and sensitivity",
    "Integrations and target",
    "Scale signals",
    "Approval posture",
    "Run envelope",
]
MINIMUM_FIELDS = FRAME_FIELDS[:5]
FIELD_SECTIONS = FRAME_FIELDS[:7]  # the seven checklist fields carry statuses
STATUSES = ("confirmed", "proposed", "open")
ADR_STATUSES = ("Proposed", "Accepted", "Superseded", "Deprecated")

_failures: list[str] = []


def fail(message: str) -> None:
    _failures.append(message)
    print(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


def skip(message: str) -> None:
    print(f"SKIP: {message}")


def section(text: str, heading: str) -> str | None:
    """Return the body of a `## <heading>` section, or None if absent."""
    match = re.search(
        rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S
    )
    return match.group(1) if match else None


def parse_frame_lines(body: str) -> dict[str, str]:
    """Parse `- <Field>: <value>` lines for known frame fields."""
    values: dict[str, str] = {}
    for line in body.splitlines():
        m = re.match(r"^\s*-\s*([^:]+):\s*(.+?)\s*$", line)
        if m and m.group(1).strip() in FRAME_FIELDS:
            values[m.group(1).strip()] = m.group(2).strip()
    return values


def check_brief(path: Path, require_minimum: bool) -> None:
    text = path.read_text(encoding="utf-8")

    current_body = section(text, "Current frame")
    if current_body is None:
        fail(f"{path}: no '## Current frame' section")
        return
    current = parse_frame_lines(current_body)
    missing = [f for f in FRAME_FIELDS if f not in current]
    if missing:
        fail(f"{path}: Current frame is missing fields: {', '.join(missing)}")

    revisions_body = section(text, "Frame revisions")
    if revisions_body is None:
        fail(f"{path}: no '## Frame revisions' section")
        return
    revision_blocks = re.findall(
        r"^### Frame revision (\d+)\b[^\n]*$(.*?)(?=^### |\Z)",
        revisions_body,
        re.M | re.S,
    )
    if not revision_blocks:
        fail(f"{path}: Frame revisions section holds no revision entries")
        return
    numbers = [int(n) for n, _ in revision_blocks]
    if numbers != sorted(numbers) or len(set(numbers)) != len(numbers):
        fail(f"{path}: frame revision numbers are not strictly increasing: {numbers}")

    folded: dict[str, str] = {}
    for number, body in revision_blocks:
        sets = {}
        for line in body.splitlines():
            m = re.match(r"^\s*-\s*Sets\s+([^:]+):\s*(.+?)\s*$", line)
            if m:
                field = m.group(1).strip()
                if field not in FRAME_FIELDS:
                    fail(
                        f"{path}: frame revision {number} sets unknown "
                        f"field '{field}'"
                    )
                else:
                    sets[field] = m.group(2).strip()
        if int(number) == 1:
            unset = [f for f in FRAME_FIELDS if f not in sets]
            if unset:
                fail(
                    f"{path}: frame revision 1 (initial frame) does not "
                    f"set: {', '.join(unset)}"
                )
        folded.update(sets)

    drift = [
        f"{f}: current='{current.get(f)}' vs folded='{folded.get(f)}'"
        for f in FRAME_FIELDS
        if current.get(f) != folded.get(f)
    ]
    if drift:
        for line in drift:
            fail(f"{path}: Current frame is stale — {line}")
    else:
        ok(f"{path}: Current frame equals the fold of {len(numbers)} revision(s)")

    statuses: dict[str, str] = {}
    for index, field in enumerate(FIELD_SECTIONS, start=1):
        body = section(text, f"{index}. {field}")
        if body is None:
            fail(f"{path}: no section for field {index} ({field})")
            continue
        m = re.search(r"^Status:\s*(\w+)\s*$", body, re.M)
        if not m:
            fail(f"{path}: field {index} ({field}) has no Status line")
            continue
        if m.group(1) not in STATUSES:
            fail(
                f"{path}: field {index} ({field}) has invalid status "
                f"'{m.group(1)}' (expected one of {', '.join(STATUSES)})"
            )
            continue
        statuses[field] = m.group(1)
    incomplete = [f for f in MINIMUM_FIELDS if statuses.get(f) != "confirmed"]
    if incomplete:
        print(
            f"minimum_set: incomplete ({', '.join(incomplete)} not confirmed)"
        )
        if require_minimum:
            fail(
                f"{path}: minimum set is not fully confirmed: "
                f"{', '.join(incomplete)}"
            )
    else:
        print("minimum_set: complete")


def adr_status_of(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"\*\*Status:\*\*\s*([A-Za-z]+)", text)
    if m and m.group(1) in ADR_STATUSES:
        return m.group(1)
    return None


def check_adr_index(adr_dir: Path) -> None:
    files = sorted(
        p for p in adr_dir.glob("ADR-*.md") if p.name.upper() != "README.MD"
    )
    if not files:
        skip(f"{adr_dir}: no ADR files — nothing to index-check")
        return
    index_path = adr_dir / "README.md"
    if not index_path.exists():
        fail(f"{adr_dir}: ADR files exist but the index (README.md) is missing")
        return
    index_text = index_path.read_text(encoding="utf-8")

    indexed: dict[str, list[str]] = {}
    for line in index_text.splitlines():
        # An entry line names its own ADR first; later mentions on the
        # same line are pointers (e.g. "Superseded by ADR-002"), not
        # entries for the pointed-to ADR.
        entry = re.search(r"ADR-(\d+)", line)
        if not entry:
            continue
        status = next(
            (s for s in ADR_STATUSES if re.search(rf"\b{s}\b", line)), None
        )
        indexed.setdefault(entry.group(1), []).append(status or "")

    problems = 0
    for adr_file in files:
        adr_id = re.match(r"ADR-(\d+)", adr_file.name).group(1)
        entries = indexed.get(adr_id)
        if entries is None:
            fail(f"{adr_file}: not listed in the ADR index")
            problems += 1
            continue
        if len(entries) > 1:
            fail(f"{adr_file}: listed {len(entries)} times in the ADR index")
            problems += 1
            continue
        file_status = adr_status_of(adr_file)
        if file_status is None:
            fail(f"{adr_file}: no readable Status line to check against the index")
            problems += 1
        elif entries[0] != file_status:
            fail(
                f"{adr_file}: index says '{entries[0] or 'no status'}' "
                f"but the ADR's Status is '{file_status}'"
            )
            problems += 1
    known_ids = {re.match(r"ADR-(\d+)", p.name).group(1) for p in files}
    for adr_id in sorted(set(indexed) - known_ids):
        fail(f"{index_path}: index lists ADR-{adr_id} but no such file exists")
        problems += 1
    if problems == 0:
        ok(f"{adr_dir}: ADR index matches all {len(files)} ADR file(s)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="project root (default: .)")
    parser.add_argument(
        "--brief",
        default=None,
        help="path to the design brief (default: <root>/.SDLC/design-brief.md)",
    )
    parser.add_argument(
        "--adr-dir",
        default=None,
        help="path to the ADR directory (default: <root>/docs/adr)",
    )
    parser.add_argument(
        "--require-minimum",
        action="store_true",
        help="fail when the brief's minimum set is not fully confirmed",
    )
    args = parser.parse_args()

    root = Path(args.root)
    brief_path = Path(args.brief) if args.brief else root / ".SDLC" / "design-brief.md"
    adr_dir = Path(args.adr_dir) if args.adr_dir else root / "docs" / "adr"

    if brief_path.exists():
        check_brief(brief_path, args.require_minimum)
    elif args.brief:
        fail(f"{brief_path}: brief not found")
    else:
        skip(f"{brief_path}: no design brief — nothing to fold-check")

    if adr_dir.exists():
        check_adr_index(adr_dir)
    else:
        skip(f"{adr_dir}: no ADR directory — nothing to index-check")

    if _failures:
        print(f"records check: FAIL ({len(_failures)} failure(s))")
        return 1
    print("records check: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
