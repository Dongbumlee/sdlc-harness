"""Validate the reviewer calibration corpus structure.

The corpus is a regression instrument: if a case loses its expected
verdict or its input tree, seats get scored against nothing. This test
keeps the instrument intact.
"""

from __future__ import annotations

from pathlib import Path

CORPUS = Path(__file__).parent / "calibration"

REQUIRED_CASES = {
    "case-01-clean",
    "case-02-off-by-one",
    "case-03-mutable-default",
    "case-04-hardcoded-secret",
    "case-05-layering-violation",
    "case-06-test-weakening",
    "case-07-untestable-requirement",
}


def _cases() -> list[Path]:
    return sorted(p for p in CORPUS.iterdir() if p.is_dir())


def test_all_required_cases_present():
    present = {p.name for p in _cases()}
    assert REQUIRED_CASES <= present, f"Missing cases: {REQUIRED_CASES - present}"


def test_every_case_has_input_and_expected_verdict():
    for case in _cases():
        input_dir = case / "input"
        assert input_dir.is_dir(), f"{case.name}: missing input/ directory"
        assert any(input_dir.rglob("*.*")), f"{case.name}: input/ is empty"
        expected = case / "expected.md"
        assert expected.is_file(), f"{case.name}: missing expected.md"
        text = expected.read_text(encoding="utf-8")
        assert "- Seat:" in text, f"{case.name}: expected.md lacks a Seat line"
        assert "- Minimum severity:" in text, (
            f"{case.name}: expected.md lacks a Minimum severity line"
        )
        assert "- Finding:" in text, f"{case.name}: expected.md lacks a Finding line"
