"""Contract tests for the CLI surface: golden files pin the help
and primary outputs, and exit-code tests pin the documented map
(0 success, 1 failure, 2 usage error). Regenerate goldens
deliberately with UPDATE_GOLDEN=1 pytest and review the diff like
an API change.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from {{project_name}}.cli import cli

TESTDATA = Path(__file__).parent / "testdata"


def golden(name: str, actual: str) -> None:
    path = TESTDATA / f"{name}.golden"
    if os.environ.get("UPDATE_GOLDEN") == "1":
        path.write_text(actual, encoding="utf-8")
        return
    assert actual == path.read_text(encoding="utf-8"), (
        f"output drifted from golden {path.name}"
    )


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("help-root", ["--help"]),
        ("help-text", ["text", "--help"]),
        ("slugify", ["text", "slugify", "Hello, World!"]),
        ("slugify-json", ["text", "slugify", "--json", "Hello, World!"]),
        ("truncate", ["text", "truncate", "--max", "6", "a longer sentence"]),
        (
            "truncate-json",
            ["text", "truncate", "--max", "6", "--json", "a longer sentence"],
        ),
        ("version", ["--version"]),
    ],
)
def test_golden_outputs(runner: CliRunner, name: str, args: list[str]) -> None:
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.output
    golden(name, result.output)


@pytest.mark.parametrize(
    ("args", "want"),
    [
        (["text", "slugify", "Hello"], 0),
        (["frobnicate"], 2),
        (["text", "slugify"], 2),
        (["text", "truncate", "--max", "abc", "text"], 2),
        (["text", "truncate", "--max", "0", "text"], 2),
        (["--format", "yaml", "text", "slugify", "Hi"], 2),
        (["text", "slugify", "--out", "/nonexistent-dir/x.txt", "Hi"], 1),
    ],
)
def test_exit_codes(runner: CliRunner, args: list[str], want: int) -> None:
    result = runner.invoke(cli, args)
    assert result.exit_code == want


def test_format_precedence(runner: CliRunner) -> None:
    """Flags beat the environment, the environment beats the default."""
    result = runner.invoke(
        cli, ["text", "slugify", "Hi There"], env={"SAMPLE_FORMAT": "json"}
    )
    assert result.output.startswith("{")
    result = runner.invoke(
        cli,
        ["--format", "plain", "text", "slugify", "Hi There"],
        env={"SAMPLE_FORMAT": "json"},
    )
    assert result.output == "hi-there\n"


def test_file_delivery(runner: CliRunner, tmp_path: Path) -> None:
    """Dry-run writes nothing; overwrite needs --force."""
    target = tmp_path / "out.txt"

    result = runner.invoke(
        cli, ["text", "slugify", "--dry-run", "--out", str(target), "Hello World"]
    )
    assert result.exit_code == 0
    assert not target.exists()

    result = runner.invoke(
        cli, ["text", "slugify", "--out", str(target), "Hello World"]
    )
    assert result.exit_code == 0
    assert target.read_text(encoding="utf-8") == "hello-world\n"

    result = runner.invoke(
        cli, ["text", "slugify", "--out", str(target), "Changed Text"]
    )
    assert result.exit_code == 1
    assert target.read_text(encoding="utf-8") == "hello-world\n"

    result = runner.invoke(
        cli, ["text", "slugify", "--out", str(target), "--force", "Changed Text"]
    )
    assert result.exit_code == 0
    assert target.read_text(encoding="utf-8") == "changed-text\n"
