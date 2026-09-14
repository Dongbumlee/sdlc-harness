# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Regression tests for the inventory generator's date handling.

The generated doc carries a `**Generated:** <date>` line. The --check
freshness gate must ignore that line, otherwise CI starts failing the
day after the doc was last regenerated.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from generate_agent_inventory import without_generated_date


class TestGeneratedDateNormalization:
    def test_different_dates_compare_equal(self):
        a = "**Generated:** 2026-09-13"
        b = "**Generated:** 2026-09-14"
        assert without_generated_date(a) == without_generated_date(b)

    def test_other_content_is_untouched(self):
        text = "**Total agents:** 19\n**Generated:** 2026-09-13\n"
        out = without_generated_date(text)
        assert "**Total agents:** 19" in out
        assert "2026-09-13" not in out

    def test_multiline_document(self):
        text = "# Title\n\n**Generated:** 2026-01-01\n\n| a | b |\n"
        out = without_generated_date(text)
        assert out.count("**Generated:**") == 1
        assert "2026-01-01" not in out
        assert "| a | b |" in out
