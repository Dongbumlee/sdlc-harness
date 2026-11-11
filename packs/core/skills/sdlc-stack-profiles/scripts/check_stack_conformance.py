#!/usr/bin/env python3
"""Mechanical stack-conformance check for the Phase 1-2 exit gate.

Compares the stack claims written in a run's REQ / ADR against the
bundled template's own project files — the version source of truth.
Written because the seat-performed version comparison failed twice
in live runs (2026-11-10): the spec claimed an ASP.NET Core 8.0 /
Mvc.Testing 8.0 stack over a .NET 10 template, and the gate passed
anyway. Numbers are compared by this script, not by a reader.

Usage:
    python3 check_stack_conformance.py --stack dotnet \
        --docs docs/requirements/REQ-001.md docs/adr/ADR-001.md

Facts are read from the bundled template next to this script
(--template-dir overrides). Output lines:

    CONTRADICTION <doc>:<line>: <claim> vs template <fact>
    NOT-IN-TEMPLATE <doc>:<line>: '<name>' is not in the template

Exit codes: 0 = no contradictions; 1 = at least one contradiction;
2 = the stack has no mechanical extractor (manual check required).
NOT-IN-TEMPLATE lines do not change the exit code: adding packages
is legitimate when deliberate — the gate requires each one to be
corrected or recorded in the manifest as a deliberate deviation.
Mentions under an "Alternative(s)" heading are skipped (an option
considered and rejected is not a stack claim).
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SUPPORTED = {"dotnet"}

# Common .NET libraries that are NOT in the bundled template. A spec
# naming one as part of its stack is claiming a deliberate addition.
WATCHLIST = [
    "Moq",
    "NSubstitute",
    "FluentAssertions",
    "FakeItEasy",
    "AutoMapper",
    "Shouldly",
    "FluentValidation",
    "Testcontainers",
]

# Short names a spec may use for a template package.
ALIASES = {
    "Microsoft.AspNetCore.Mvc.Testing": ["Mvc.Testing"],
    "Microsoft.NET.Test.Sdk": ["Test.Sdk", "Microsoft.NET.Test.Sdk"],
    "coverlet.collector": ["coverlet"],
    "xunit": ["xUnit", "xunit"],
    "xunit.runner.visualstudio": ["xunit.runner.visualstudio"],
}


def parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(p) for p in text.split(".") if p != "")


def versions_equal(a: str, b: str) -> bool:
    va, vb = parse_version(a), parse_version(b)
    n = max(len(va), len(vb))
    return va + (0,) * (n - len(va)) == vb + (0,) * (n - len(vb))


def dotnet_facts(template_dir: Path) -> dict:
    """Target framework + package pins from the template's csproj files."""
    tfm: str | None = None
    packages: dict[str, str] = {}
    for csproj in sorted(template_dir.rglob("*.csproj")):
        root = ET.parse(csproj).getroot()
        for el in root.iter("TargetFramework"):
            if tfm is None and el.text:
                tfm = el.text.strip()
        for el in root.iter("PackageReference"):
            name, version = el.get("Include"), el.get("Version")
            if name and version:
                packages[name] = version.strip()
    if tfm is None or not packages:
        raise ValueError(f"no stack facts found under {template_dir}")
    return {"tfm": tfm, "packages": packages}


def framework_claims(line: str) -> list[tuple[str, str]]:
    """(label, version) framework claims on one line."""
    claims: list[tuple[str, str]] = []
    for m in re.finditer(r"ASP\.NET Core\s+(\d+(?:\.\d+)?)", line):
        claims.append(("ASP.NET Core", m.group(1)))
    for m in re.finditer(r"(?<!\w)\.NET\s+(\d+(?:\.\d+)?)\b", line):
        claims.append((".NET", m.group(1)))
    for m in re.finditer(r"\bnet(\d+\.\d+)\b", line):
        claims.append(("target framework", m.group(1)))
    return claims


def check_doc(path: Path, facts: dict) -> tuple[list[str], list[str]]:
    contradictions: list[str] = []
    not_in_template: list[str] = []
    tfm = facts["tfm"]  # e.g. "net10.0"
    tfm_version = tfm.removeprefix("net")
    packages: dict[str, str] = facts["packages"]

    variants: list[tuple[str, str, str]] = []  # (variant, package, version)
    for name, version in packages.items():
        # Explicit aliases only — a bare last segment ("Testing") is a
        # generic word and false-matches unrelated claims.
        names = {name} | set(ALIASES.get(name, []))
        for variant in names:
            variants.append((variant, name, version))

    seen_watchlist: set[str] = set()
    in_alternatives = False
    heading_level = 0
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            level = len(heading.group(1))
            if re.search(r"alternative", heading.group(2), re.IGNORECASE):
                in_alternatives, heading_level = True, level
            elif in_alternatives and level <= heading_level:
                in_alternatives = False
            continue
        if in_alternatives:
            continue

        for label, claimed in framework_claims(line):
            if not versions_equal(claimed, tfm_version):
                contradictions.append(
                    f"CONTRADICTION {path}:{lineno}: {label} {claimed} "
                    f"vs template {label} {tfm_version} ({tfm})"
                )

        reported_pkgs: set[str] = set()
        for variant, name, version in variants:
            if name in reported_pkgs:
                continue
            for m in re.finditer(
                re.escape(variant) + r"\D{0,24}?(\d+\.\d+(?:\.\d+)?)", line
            ):
                if not versions_equal(m.group(1), version):
                    reported_pkgs.add(name)
                    contradictions.append(
                        f"CONTRADICTION {path}:{lineno}: {variant} "
                        f"{m.group(1)} vs template {name} {version}"
                    )
                    break

        for name in WATCHLIST:
            if name in packages or name in seen_watchlist:
                continue
            hit = re.search(rf"\b{re.escape(name)}\b", line)
            if not hit:
                continue
            # A negated mention ("no AutoMapper", "do not justify
            # AutoMapper's overhead") is a rejection, not a claim.
            before = line[max(0, hit.start() - 40) : hit.start()]
            if re.search(
                r"\b(no|not|without|avoid\w*|reject\w*|instead of|never)\b",
                before,
                re.IGNORECASE,
            ):
                continue
            seen_watchlist.add(name)
            not_in_template.append(
                f"NOT-IN-TEMPLATE {path}:{lineno}: '{name}' is not "
                f"in the bundled template's package set"
            )
    return contradictions, not_in_template


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stack", required=True)
    parser.add_argument("--docs", nargs="+", required=True, type=Path)
    parser.add_argument("--template-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.stack not in SUPPORTED:
        print(
            f"UNVERIFIED: no mechanical extractor for stack "
            f"'{args.stack}' — manual conformance check required"
        )
        return 2

    template_dir = args.template_dir or (
        Path(__file__).resolve().parent.parent
        / "assets"
        / "templates"
        / args.stack
        / "api"
    )
    try:
        facts = dotnet_facts(template_dir)
    except (ValueError, ET.ParseError) as exc:
        print(f"UNVERIFIED: could not read template facts: {exc}")
        return 2

    all_contradictions: list[str] = []
    all_not_in: list[str] = []
    for doc in args.docs:
        c, n = check_doc(doc, facts)
        all_contradictions += c
        all_not_in += n

    for line in all_contradictions + all_not_in:
        print(line)
    print(
        f"RESULT: {len(all_contradictions)} contradiction(s), "
        f"{len(all_not_in)} not-in-template, {len(args.docs)} doc(s) "
        f"checked against {args.stack} template "
        f"(TFM {facts['tfm']}, {len(facts['packages'])} packages)"
    )
    return 1 if all_contradictions else 0


if __name__ == "__main__":
    sys.exit(main())
