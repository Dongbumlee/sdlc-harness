#!/usr/bin/env python3
"""Doc census check — numbers stated in reader docs vs the tree itself.

Reader-facing documents state counts ("22 agents", "60 canary specs",
"338 patterns"). Those numbers drift when the tree changes and nobody
re-reads the prose. This check computes each count from the tree (or,
for the bug corpus, from the skill that owns the number) and fails on
any stated number that disagrees.

Scope: reader docs only. docs/base-definitions.md is excluded on
purpose — the canon carries decision records whose numbers are
history, not current-state claims. docs/agent-inventory.md is
generated and has its own freshness check.

Usage: python3 tools/check_doc_census.py [--root PATH]
Exit: 0 when every stated number matches the census, 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DOC_FILES = [
    "README.md",
    "TRANSPARENCY_FAQ.md",
    "index.html",
    "bench/README.md",
    "docs/adopting.md",
    "docs/first-run.md",
    "docs/hands-on-guide.md",
    "docs/harness-design.md",
    "docs/host-support.md",
    "docs/orchestrator-states.md",
    "docs/quick-reference.md",
    "docs/troubleshooting.md",
    "docs/workflow-guide.md",
]

# Stated noun -> census key. Longest nouns first so "bundled templates"
# wins over "templates" at the same position.
NOUN_TO_KEY = {
    "bundled templates": "templates",
    "skill evaluation specs": "eval_specs",
    "canary specs": "canaries",
    "eval specs": "eval_specs",
    "prompt files": "prompt_files",
    "instruction files": "instruction_files",
    "templates": "templates",
    "canaries": "canaries",
    "checklists": "checklists",
    "patterns": "bug_corpus",
    "agents": "agents",
    "skills": "skills",
    "stacks": "stacks",
}

STATEMENT_RE = re.compile(
    r"(\d+)[\s\-–](%s)\b" % "|".join(re.escape(n) for n in NOUN_TO_KEY),
    re.IGNORECASE,
)

# The Pages site labels agent subgroups with counts ("02 AGENTS" over the
# Orchestration group). Those are subtotals, not totals — strip the
# labelled spans before scanning HTML so only total claims are checked.
GROUP_COUNT_SPAN_RE = re.compile(
    r'<span class="group-count">.*?</span>', re.IGNORECASE
)


def compute_census(root: Path) -> dict[str, int]:
    packs = root / "packs"
    templates_root = (
        packs / "core" / "skills" / "sdlc-stack-profiles" / "assets" / "templates"
    )
    template_yamls = sorted(templates_root.rglob("template.yaml"))
    stacks = {
        p.relative_to(templates_root).parts[0]
        for p in template_yamls
        if p.relative_to(templates_root).parts[0] != "system"
    }
    bug_skill = packs / "azure" / "skills" / "sdlc-qa-bug-checklist" / "SKILL.md"
    bug_text = bug_skill.read_text(encoding="utf-8")
    corpus_match = re.search(r"distilled from (\d+) real bugs", bug_text)
    init_assets = packs / "core" / "skills" / "sdlc-workspace-init" / "assets"
    return {
        "agents": len(list(packs.glob("*/agents/*.agent.md"))),
        "skills": len(list(packs.glob("*/skills/*/SKILL.md"))),
        "templates": len(template_yamls),
        "stacks": len(stacks),
        "canaries": len(list((root / "bench" / "canaries").rglob("*.yaml"))),
        "eval_specs": len(list((root / "bench" / "evals").glob("*.yaml"))),
        "prompt_files": len(list((init_assets / "prompts").glob("*.prompt.md"))),
        "instruction_files": len(
            list((init_assets / "instructions").glob("*.instructions.md"))
        ),
        "checklists": len(
            re.findall(r"^## Checklist", bug_text, flags=re.MULTILINE)
        ),
        "bug_corpus": int(corpus_match.group(1)) if corpus_match else -1,
    }


def find_mismatches(
    root: Path, census: dict[str, int]
) -> list[tuple[str, int, str, int, int]]:
    """Return (file, line, noun, stated, actual) for every disagreement."""
    mismatches = []
    for rel in DOC_FILES:
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".html":
            text = GROUP_COUNT_SPAN_RE.sub("", text)
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in STATEMENT_RE.finditer(line):
                stated = int(match.group(1))
                noun = match.group(2).lower()
                actual = census[NOUN_TO_KEY[noun]]
                if stated != actual:
                    mismatches.append((rel, lineno, noun, stated, actual))
    return mismatches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="repository root (default: the tool's own repo)",
    )
    args = parser.parse_args(argv)
    root = args.root

    census = compute_census(root)
    print("Census (computed from the tree):")
    for key in sorted(census):
        print(f"  {key}: {census[key]}")

    instructions_template = (
        root
        / "packs"
        / "core"
        / "skills"
        / "sdlc-workspace-init"
        / "assets"
        / "copilot-instructions.template.md"
    )
    if instructions_template.exists():
        chars = len(instructions_template.read_text(encoding="utf-8"))
        print(
            f"  copilot-instructions template: {chars} chars "
            "(informational — the always-on map every project starts with)"
        )

    mismatches = find_mismatches(root, census)
    if mismatches:
        print("\nStated numbers that disagree with the census:")
        for rel, lineno, noun, stated, actual in mismatches:
            print(f"  {rel}:{lineno}: states {stated} {noun}, census is {actual}")
        return 1
    print("\nAll stated numbers in the reader docs match the census.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
