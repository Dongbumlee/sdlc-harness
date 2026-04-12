"""Tests for deterministic code graders.

Covers keyword, AST, structural, and file graders with known-good
and known-bad outputs to verify scoring correctness.
"""

import pytest

from bench.graders.models import GraderResult, Severity
from bench.graders.code.keyword_grader import KeywordGrader
from bench.graders.code.ast_grader import ASTGrader
from bench.graders.code.structural_grader import StructuralGrader
from bench.graders.code.file_grader import FileGrader


# ---------------------------------------------------------------------------
# KeywordGrader
# ---------------------------------------------------------------------------
class TestKeywordGrader:
    """Verify keyword presence / absence scoring."""

    def test_all_required_present(self):
        grader = KeywordGrader(
            required_keywords=["def main", "import os"],
            forbidden_keywords=[],
        )
        result = grader.grade("import os\n\ndef main():\n    pass")
        assert result.score >= 0.9
        assert result.passed

    def test_missing_required(self):
        grader = KeywordGrader(
            required_keywords=["def main", "import os"],
            forbidden_keywords=[],
        )
        result = grader.grade("print('hello')")
        assert result.score < 0.5
        assert not result.passed

    def test_forbidden_present(self):
        grader = KeywordGrader(
            required_keywords=[],
            forbidden_keywords=["eval(", "exec("],
        )
        result = grader.grade("result = eval('1+1')")
        assert result.score < 1.0
        assert any("eval" in d for d in result.details)

    def test_empty_input(self):
        grader = KeywordGrader(required_keywords=["def"], forbidden_keywords=[])
        result = grader.grade("")
        assert result.score == 0.0


# ---------------------------------------------------------------------------
# ASTGrader
# ---------------------------------------------------------------------------
class TestASTGrader:
    """Verify AST-based structural checks."""

    def test_valid_python(self):
        grader = ASTGrader(
            required_constructs=["FunctionDef"],
            min_functions=1,
        )
        result = grader.grade("def hello():\n    return 'hi'")
        assert result.passed

    def test_syntax_error(self):
        grader = ASTGrader(required_constructs=[], min_functions=0)
        result = grader.grade("def broken(:\n    pass")
        assert not result.passed
        assert result.severity == Severity.ERROR

    def test_missing_construct(self):
        grader = ASTGrader(
            required_constructs=["ClassDef"],
            min_functions=0,
        )
        result = grader.grade("x = 1")
        assert result.score < 1.0


# ---------------------------------------------------------------------------
# StructuralGrader
# ---------------------------------------------------------------------------
class TestStructuralGrader:
    """Verify structural pattern matching."""

    def test_matches_pattern(self):
        grader = StructuralGrader(
            patterns=[r"class \w+\(BaseModel\):"],
        )
        code = "from pydantic import BaseModel\n\nclass User(BaseModel):\n    name: str"
        result = grader.grade(code)
        assert result.passed

    def test_no_match(self):
        grader = StructuralGrader(patterns=[r"class \w+\(BaseModel\):"])
        result = grader.grade("x = 1")
        assert result.score == 0.0


# ---------------------------------------------------------------------------
# FileGrader
# ---------------------------------------------------------------------------
class TestFileGrader:
    """Verify file-level checks (existence, naming, size)."""

    def test_required_files_present(self, tmp_path):
        (tmp_path / "main.py").write_text("print('ok')")
        (tmp_path / "requirements.txt").write_text("flask")

        grader = FileGrader(
            required_files=["main.py", "requirements.txt"],
        )
        result = grader.grade_directory(str(tmp_path))
        assert result.passed

    def test_missing_files(self, tmp_path):
        grader = FileGrader(required_files=["main.py", "Dockerfile"])
        result = grader.grade_directory(str(tmp_path))
        assert not result.passed
        assert result.score < 1.0
