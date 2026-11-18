"""Tests for the ban-ast edit-time gate (packs/core/hooks/check-bans.mjs).

The checker runs as a subprocess against fixture hook events, the same
way the Copilot preToolUse hook invokes it: event JSON on stdin, `{}`
(allow) or a permissionDecision deny object on stdout. Node is required;
the module skips where node is not on PATH.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CHECKER = REPO / "packs" / "core" / "hooks" / "check-bans.mjs"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is not on PATH"
)


def run_event(tool_args, tool_name="create_file", cwd="/tmp"):
    event = {"toolName": tool_name, "toolArgs": tool_args, "cwd": cwd}
    result = subprocess.run(
        ["node", str(CHECKER)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def create(file_path, content, cwd="/tmp"):
    return run_event({"filePath": file_path, "content": content}, cwd=cwd)


def test_python_eval_is_denied():
    out = create("app.py", "result = eval(user_input)\n")
    assert out["permissionDecision"] == "deny"
    assert "no-dynamic-code-execution" in out["permissionDecisionReason"]


def test_python_shell_true_is_denied():
    out = create("app.py", "import subprocess\nsubprocess.run(cmd, shell=True)\n")
    assert out["permissionDecision"] == "deny"
    assert "no-shell-string-execution" in out["permissionDecisionReason"]


def test_python_verify_false_is_denied():
    out = create("app.py", "requests.get(url, verify=False)\n")
    assert out["permissionDecision"] == "deny"
    assert "no-tls-verification-off" in out["permissionDecisionReason"]


def test_python_sql_fstring_is_denied():
    out = create("app.py", 'cursor.execute(f"SELECT * FROM t WHERE id = {uid}")\n')
    assert out["permissionDecision"] == "deny"
    assert "no-sql-string-building" in out["permissionDecisionReason"]


def test_python_hardcoded_secret_is_denied_but_short_placeholder_passes():
    out = create("app.py", 'password = "supersecretvalue"\n')
    assert out["permissionDecision"] == "deny"
    assert "no-hardcoded-secret" in out["permissionDecisionReason"]
    assert create("app.py", 'password = "short"\n') == {}


def test_clean_python_passes():
    content = (
        "import os\n"
        'password = os.environ["APP_PASSWORD"]\n'
        'cursor.execute("SELECT * FROM t WHERE id = %s", (uid,))\n'
    )
    assert create("app.py", content) == {}


def test_justification_comment_allows_the_match():
    content = (
        "# no-dynamic-code-execution justification: sandboxed admin REPL, reviewed\n"
        "result = eval(expr)\n"
    )
    assert create("app.py", content) == {}


def test_typescript_reject_unauthorized_is_denied():
    out = create("app.ts", "const opts = { rejectUnauthorized: false };\n")
    assert out["permissionDecision"] == "deny"
    assert "no-tls-verification-off" in out["permissionDecisionReason"]


def test_typescript_secret_pair_is_denied():
    out = create("app.ts", 'const config = { apiKey: "a-very-long-key-value" };\n')
    assert out["permissionDecision"] == "deny"
    assert "no-hardcoded-secret" in out["permissionDecisionReason"]


def test_edit_fragment_is_checked():
    out = run_event(
        {"filePath": "app.py", "newString": "os.system(cmd)\n"},
        tool_name="edit_file",
    )
    assert out["permissionDecision"] == "deny"
    assert "no-shell-string-execution" in out["permissionDecisionReason"]


def test_project_rule_file_extends_the_shipped_set(tmp_path):
    (tmp_path / "BANNED_AST.md").write_text(
        "---\n"
        "name: no-print-debugging\n"
        "languages: python\n"
        "message: print debugging is banned in this project.\n"
        "query: |\n"
        '  (call function: (identifier) @fn (#eq? @fn "print")) @match\n',
        encoding="utf-8",
    )
    out = create("src/app.py", 'print("debug")\n', cwd=str(tmp_path))
    assert out["permissionDecision"] == "deny"
    assert "no-print-debugging" in out["permissionDecisionReason"]


def test_unrelated_language_is_not_checked():
    assert create("Program.cs", "var x = eval(y);\n") == {}
