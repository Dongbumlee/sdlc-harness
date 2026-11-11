"""Verify the mechanical stack-conformance checker (Phase 1-2 gate).

The checker exists because a seat-performed version comparison
failed twice in live runs: a spec claimed an 8.0-era stack over the
bundled .NET 10 template and the gate passed anyway. These tests
pin the checker's contract against the real bundled template.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SCRIPT = (
    REPO_ROOT
    / "packs/core/skills/sdlc-stack-profiles/scripts/check_stack_conformance.py"
)
TEMPLATE_DIR = (
    REPO_ROOT / "packs/core/skills/sdlc-stack-profiles/assets/templates/dotnet/api"
)


def run_checker(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def write_doc(tmp_path: Path, text: str) -> Path:
    doc = tmp_path / "ADR-001.md"
    doc.write_text(text, encoding="utf-8")
    return doc


BAD_ADR = """# ADR-001

| Area | Choice |
|---|---|
| API Framework | ASP.NET Core 8.0 (Microsoft.AspNetCore.App) |
| Testing | xUnit 2.7 + Microsoft.AspNetCore.Mvc.Testing 8.0 + NSubstitute 5.1 |
"""

CLEAN_SPEC = """# REQ-001

Tech stack: .NET 10 (ASP.NET Core), EF Core, SQLite.
Tests: xUnit 2.9.2 with Microsoft.AspNetCore.Mvc.Testing 10.0.0,
Microsoft.NET.Test.Sdk 17.11.1, coverlet 6.0.2.
"""

ALTERNATIVES_DOC = """# ADR-001

Stack: ASP.NET Core on .NET 10, xUnit.

## Alternatives Considered

### Alternative 3: FluentValidation for Request Validation

An older ASP.NET Core 8.0 example used FluentValidation and Moq.
Rejected in favour of the template stack.
"""


class TestStackConformance:
    def test_template_facts_are_the_bundled_pins(self):
        spec = importlib.util.spec_from_file_location("csc", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        facts = module.dotnet_facts(TEMPLATE_DIR)
        assert facts["tfm"] == "net10.0"
        assert facts["packages"]["Microsoft.AspNetCore.Mvc.Testing"] == "10.0.0"
        assert facts["packages"]["xunit"] == "2.9.2"

    def test_contradicting_adr_fails_with_named_lines(self, tmp_path):
        doc = write_doc(tmp_path, BAD_ADR)
        result = run_checker("--stack", "dotnet", "--docs", str(doc))
        assert result.returncode == 1
        assert "ASP.NET Core 8" in result.stdout
        assert "Mvc.Testing" in result.stdout and "8.0" in result.stdout
        assert "xUnit 2.7" in result.stdout or "xunit" in result.stdout.lower()
        assert "NOT-IN-TEMPLATE" in result.stdout
        assert "NSubstitute" in result.stdout

    def test_clean_spec_passes(self, tmp_path):
        doc = write_doc(tmp_path, CLEAN_SPEC)
        result = run_checker("--stack", "dotnet", "--docs", str(doc))
        assert result.returncode == 0
        assert "0 contradiction(s)" in result.stdout
        assert "NOT-IN-TEMPLATE" not in result.stdout

    def test_alternatives_section_is_not_a_claim(self, tmp_path):
        doc = write_doc(tmp_path, ALTERNATIVES_DOC)
        result = run_checker("--stack", "dotnet", "--docs", str(doc))
        assert result.returncode == 0
        assert "CONTRADICTION" not in result.stdout
        assert "NOT-IN-TEMPLATE" not in result.stdout

    def test_generic_row_label_is_not_a_package_claim(self, tmp_path):
        # "Testing" (the Mvc.Testing package's last segment) must not
        # match a table row label next to another package's version.
        doc = write_doc(
            tmp_path,
            "| Testing | xUnit 2.9.2 + Microsoft.AspNetCore.Mvc.Testing 10.0.0 |\n",
        )
        result = run_checker("--stack", "dotnet", "--docs", str(doc))
        assert result.returncode == 0
        assert "CONTRADICTION" not in result.stdout

    def test_negated_mention_outside_alternatives_is_not_a_claim(self, tmp_path):
        doc = write_doc(
            tmp_path,
            "Manual extension methods (no AutoMapper) are used.\n"
            "Simple mappings do not justify AutoMapper's overhead.\n",
        )
        result = run_checker("--stack", "dotnet", "--docs", str(doc))
        assert result.returncode == 0
        assert "NOT-IN-TEMPLATE" not in result.stdout

    def test_unsupported_stack_is_unverified_not_passed(self, tmp_path):
        doc = write_doc(tmp_path, CLEAN_SPEC)
        result = run_checker("--stack", "python", "--docs", str(doc))
        assert result.returncode == 2
        assert "UNVERIFIED" in result.stdout
