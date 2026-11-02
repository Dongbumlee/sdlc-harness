#!/usr/bin/env python3
"""Collect a deterministic QA evidence pack for the SDLC Phase 6 reviewer panel.

The Phase 6 panel's measured bottleneck is duplicated cold reading: every
reviewer independently opens the same manifest, requirements, and source
files, guesses at paths, and re-derives facts that a few commands settle
exactly. This collector runs BEFORE the panel (invoked by the Harness, which
has a terminal) and writes one Markdown pack that every reviewer starts
from:

  1. File inventory (path + size) — reviewers never guess paths.
  2. The project manifest, inlined.
  3. Requirements and ADR files, inlined up to a size cap.
  4. Dependency summary per project file (counts + package ids).
  5. CI workflow step names per workflow file.
  6. Requirements <-> test traceability: every FR/NFR id found in the
     requirements docs, with the number of test files mentioning it
     (ids with zero test mentions are listed explicitly).
  7. The recorded full-suite test run, when the Harness has saved one to
     <out>/qa-evidence/test-run.txt (tail inlined verbatim).

Pure standard library, no network, deterministic ordering. The pack is
evidence, not a verdict: it records facts; reviewers judge them.

Usage:
    python collect-qa-evidence.py --root . --out .SDLC
Writes: <out>/qa-evidence-pack.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {
    ".git", "bin", "obj", "node_modules", ".venv", "venv", "dist", "build",
    "__pycache__", ".next", "target", "vendor", ".idea", ".vs",
}
INLINE_CAP = 30_000
MANIFEST_CAP = 40_000
MAX_INVENTORY = 2_000
TEST_SUFFIXES = {".cs", ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs"}
REQ_ID_RE = re.compile(r"\b(?:FR|NFR)-\d+\b")
TEST_NAME_PATTERNS = [
    re.compile(r"\[(?:Fact|Theory|Test|TestCase)\b"),
    re.compile(r"\bdef test_\w+"),
    re.compile(r"\b(?:it|test|describe)\s*\("),
    re.compile(r"\bfunc Test\w+"),
    re.compile(r"#\[test\]"),
]


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        yield path, rel


def read_capped(path: Path, cap: int) -> tuple[str, bool]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > cap:
        return text[:cap], True
    return text, False


def section_inventory(files: list[tuple[Path, Path]]) -> str:
    lines = ["## 1. File inventory", ""]
    shown = files[:MAX_INVENTORY]
    for path, rel in shown:
        lines.append(f"- `{rel.as_posix()}` — {path.stat().st_size} bytes")
    if len(files) > MAX_INVENTORY:
        lines.append(f"- … and {len(files) - MAX_INVENTORY} more files (listing capped)")
    lines.append(f"\nTotal files: {len(files)}")
    return "\n".join(lines)


def section_manifest(root: Path) -> str:
    manifest = root / ".SDLC" / "project-manifest.md"
    if not manifest.is_file():
        return "## 2. Project manifest\n\nNo `.SDLC/project-manifest.md` found."
    text, truncated = read_capped(manifest, MANIFEST_CAP)
    note = " (truncated at cap)" if truncated else ""
    return f"## 2. Project manifest (`.SDLC/project-manifest.md`){note}\n\n{text.rstrip()}"


def find_docs(root: Path) -> tuple[list[Path], list[Path]]:
    reqs, adrs = [], []
    for base in (root / "docs" / "requirements", root / "docs"):
        if base.is_dir():
            reqs.extend(sorted(base.glob("REQ-*.md")))
    req_dir = root / "docs" / "requirements"
    if not reqs and req_dir.is_dir():
        reqs = sorted(req_dir.glob("*.md"))
    adr_dir = root / "docs" / "adr"
    if adr_dir.is_dir():
        adrs = sorted(adr_dir.glob("*.md"))
    return reqs, adrs


def section_docs(root: Path, reqs: list[Path], adrs: list[Path]) -> str:
    lines = ["## 3. Requirements and ADRs", ""]
    if not reqs and not adrs:
        lines.append("No requirements or ADR files found under `docs/`.")
        return "\n".join(lines)
    for label, paths in (("Requirements", reqs), ("ADRs", adrs)):
        for path in paths:
            rel = path.relative_to(root).as_posix()
            text, truncated = read_capped(path, INLINE_CAP)
            note = " — truncated at cap, read the file for the remainder" if truncated else ""
            lines.append(f"### {label}: `{rel}` ({path.stat().st_size} bytes){note}")
            lines.append("")
            lines.append(text.rstrip())
            lines.append("")
    return "\n".join(lines)


def section_dependencies(root: Path, files: list[tuple[Path, Path]]) -> str:
    lines = ["## 4. Dependency summary", ""]
    found = False
    for path, rel in files:
        name = path.name
        if name.endswith(".csproj"):
            text = path.read_text(encoding="utf-8", errors="replace")
            ids = re.findall(r'<PackageReference\s+Include="([^"]+)"', text)
            lines.append(f"- `{rel.as_posix()}` — {len(ids)} PackageReference: {', '.join(ids) if ids else '(none)'}")
            found = True
        elif name == "package.json":
            try:
                data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except json.JSONDecodeError:
                lines.append(f"- `{rel.as_posix()}` — package.json present (unparseable)")
                found = True
                continue
            deps = sorted((data.get("dependencies") or {}).keys())
            dev = sorted((data.get("devDependencies") or {}).keys())
            lines.append(f"- `{rel.as_posix()}` — {len(deps)} dependencies, {len(dev)} devDependencies")
            found = True
        elif name.startswith("requirements") and name.endswith(".txt"):
            count = sum(
                1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
                if line.strip() and not line.strip().startswith("#")
            )
            lines.append(f"- `{rel.as_posix()}` — {count} requirement lines")
            found = True
        elif name == "pyproject.toml":
            text = path.read_text(encoding="utf-8", errors="replace")
            block = re.search(r"dependencies\s*=\s*\[(.*?)\]", text, re.S)
            count = len(re.findall(r'"[^"]+"', block.group(1))) if block else 0
            lines.append(f"- `{rel.as_posix()}` — {count} project dependencies")
            found = True
        elif name == "Cargo.toml":
            text = path.read_text(encoding="utf-8", errors="replace")
            block = re.search(r"\[dependencies\](.*?)(?:\n\[|\Z)", text, re.S)
            count = len(re.findall(r"^\s*[\w-]+\s*=", block.group(1), re.M)) if block else 0
            lines.append(f"- `{rel.as_posix()}` — {count} dependencies")
            found = True
        elif name in ("go.mod", "pom.xml", "build.gradle", "build.gradle.kts"):
            lines.append(f"- `{rel.as_posix()}` — present (summary not extracted for this ecosystem)")
            found = True
    if not found:
        lines.append("No dependency manifests recognized.")
    return "\n".join(lines)


def section_ci(root: Path) -> str:
    lines = ["## 5. CI workflows", ""]
    wf_dir = root / ".github" / "workflows"
    workflows = sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")) if wf_dir.is_dir() else []
    if not workflows:
        lines.append("No GitHub Actions workflows found under `.github/workflows/`.")
        return "\n".join(lines)
    for wf in workflows:
        text = wf.read_text(encoding="utf-8", errors="replace")
        names = re.findall(r"^\s*-\s+name:\s*(.+)$", text, re.M)
        uses = re.findall(r"^\s*-\s+uses:\s*(.+)$", text, re.M)
        rel = wf.relative_to(root).as_posix()
        lines.append(f"### `{rel}`")
        lines.append(f"- Named steps ({len(names)}): {'; '.join(n.strip() for n in names) if names else '(none)'}")
        lines.append(f"- Action uses ({len(uses)}): {'; '.join(u.strip() for u in uses) if uses else '(none)'}")
        lines.append("")
    return "\n".join(lines)


def section_deployment(files: list[tuple[Path, Path]]) -> str:
    lines = ["## 8. Deployment artifacts", ""]
    found = []
    for path, rel in files:
        name = path.name
        parts = set(rel.parts)
        if (
            name.startswith("Dockerfile")
            or name.startswith("docker-compose")
            or name == "azure.yaml"
            or path.suffix == ".bicep"
            or "infra" in parts
            or ".devcontainer" in parts
        ):
            found.append((rel, path.stat().st_size))
    if not found:
        lines.append("No deployment artifacts found (no Dockerfile, compose file, "
                     "devcontainer, azure.yaml, or Bicep/infra files).")
    else:
        lines.append("Deployment-related files present in the tree, so the "
                     "Deployment Readiness reviewer does not need to re-derive them:")
        lines.append("")
        for rel, size in sorted(found):
            lines.append(f"- `{rel}` ({size} bytes)")
    lines.append("")
    return "\n".join(lines)


def is_test_file(rel: Path) -> bool:
    parts = [p.lower() for p in rel.parts]
    name = rel.name.lower()
    return (
        rel.suffix in TEST_SUFFIXES
        and ("test" in parts or "tests" in parts or "test" in name or name.startswith("test_"))
    )


def section_traceability(root: Path, reqs: list[Path], files: list[tuple[Path, Path]]) -> str:
    lines = ["## 6. Requirements <-> test traceability", ""]
    req_ids: set[str] = set()
    for req in reqs:
        req_ids.update(REQ_ID_RE.findall(req.read_text(encoding="utf-8", errors="replace")))
    test_files = [(p, r) for p, r in files if is_test_file(r)]
    test_count = 0
    mentions: dict[str, int] = {rid: 0 for rid in req_ids}
    for path, _rel in test_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in TEST_NAME_PATTERNS:
            test_count += len(pattern.findall(text))
        for rid in req_ids:
            if rid in text:
                mentions[rid] += 1
    lines.append(f"Test files: {len(test_files)}; test cases detected (pattern count): {test_count}")
    if not req_ids:
        lines.append("No FR/NFR ids found in the requirements docs.")
        return "\n".join(lines)
    lines.append("")
    lines.append("| Requirement | Test files mentioning it |")
    lines.append("|---|---|")
    for rid in sorted(req_ids, key=lambda r: (r.split("-")[0], int(r.split("-")[1]))):
        lines.append(f"| {rid} | {mentions[rid]} |")
    zero = [rid for rid in sorted(req_ids) if mentions[rid] == 0]
    lines.append("")
    lines.append(f"Requirements with ZERO test-file mentions: {', '.join(zero) if zero else '(none)'}")
    lines.append("")
    lines.append("Note: a mention is a string occurrence in a test file (traceability "
                 "tables included); it shows a claimed link, not proof of a passing test.")
    return "\n".join(lines)


def section_test_run(out_dir: Path) -> str:
    run_file = out_dir / "qa-evidence" / "test-run.txt"
    lines = ["## 7. Recorded test run", ""]
    if not run_file.is_file():
        lines.append("No recorded test run yet. The Harness saves the full-suite raw "
                     "output to `.SDLC/qa-evidence/test-run.txt` before the panel; "
                     "its absence must be stated in the QA summary, never passed over.")
        return "\n".join(lines)
    text = run_file.read_text(encoding="utf-8", errors="replace")
    tail = "\n".join(text.rstrip().splitlines()[-40:])
    lines.append("Tail of `.SDLC/qa-evidence/test-run.txt` (verbatim):")
    lines.append("")
    lines.append("```")
    lines.append(tail)
    lines.append("```")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root (default: current directory)")
    parser.add_argument("--out", default=".SDLC", help="Output directory for the pack (default: .SDLC)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    files = list(iter_files(root))
    reqs, adrs = find_docs(root)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    parts = [
        "# QA Evidence Pack",
        "",
        f"Project root: `{root}`  ",
        f"Collected (UTC): {stamp}  ",
        "Collector: `sdlc-project-qa/assets/collect-qa-evidence.py` (deterministic; facts only, no verdicts)",
        "",
        section_inventory(files),
        "",
        section_manifest(root),
        "",
        section_docs(root, reqs, adrs),
        "",
        section_dependencies(root, files),
        "",
        section_ci(root),
        "",
        section_traceability(root, reqs, files),
        "",
        section_test_run(out_dir),
        "",
        section_deployment(files),
        "",
    ]
    pack_path = out_dir / "qa-evidence-pack.md"
    pack_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"evidence pack written: {pack_path} "
          f"({len(files)} files inventoried, {len(reqs)} requirements docs, {len(adrs)} ADRs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
