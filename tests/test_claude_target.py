"""Contract tests for the generated Claude Code plugin tree.

The tree under hosts/claude-code/ is a build product of the packs (see
tools/hosts/claude_code.py). These tests pin the translation contract:
bodies byte-identical, every tool token mapped, slugs valid and unique,
MCP prefixes backed by declared servers, and versions in lockstep.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from hosts.claude_code import (  # noqa: E402
    CAPABILITY_SUBSTITUTIONS,
    MCP_SERVERS,
    TOOL_MAP,
    build_tree,
    parse_frontmatter,
)

TREE = REPO_ROOT / "hosts" / "claude-code"
_SLUG_RE = re.compile(r"\A[a-z0-9]+(-[a-z0-9]+)*\Z")
_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def _pack_agents() -> dict[str, Path]:
    agents: dict[str, Path] = {}
    for path in sorted((REPO_ROOT / "packs").glob("*/agents/*.agent.md")):
        agents[path.name] = path
    return agents


def _body(text: str) -> str:
    match = _FRONTMATTER_RE.match(text)
    assert match, "frontmatter block missing"
    return text[match.end():]


def _generated_agents() -> dict[str, str]:
    return {
        path.stem: path.read_text(encoding="utf-8")
        for path in sorted((TREE / "agents").glob("*.md"))
    }


class TestTokenCoverage:
    """Every Copilot tool token in every pack agent has a mapping."""

    def test_all_tokens_covered(self):
        """A new token type must fail here until the table is extended."""
        for name, path in _pack_agents().items():
            fields, _raw, _body_text = parse_frontmatter(
                path.read_text(encoding="utf-8"), str(path)
            )
            for token in fields.get("tools") or []:
                covered = (
                    token == "agent"
                    or token in TOOL_MAP
                    or (token.endswith("/*") and token[:-2] in MCP_SERVERS)
                    or token.startswith("azure/")
                    or any(
                        token.startswith(prefix) for prefix in CAPABILITY_SUBSTITUTIONS
                    )
                )
                assert covered, f"{name}: unmapped tool token {token!r}"


class TestGeneratedAgents:
    """The generated agent files honor the translation contract."""

    def test_count_and_slugs(self):
        """One generated file per pack agent, each with a valid slug."""
        generated = _generated_agents()
        assert len(generated) == len(_pack_agents())
        for slug in generated:
            assert _SLUG_RE.match(slug), f"invalid Claude Code agent name: {slug}"

    def test_bodies_byte_identical(self):
        """Agent bodies pass through the translation untouched."""
        index = (TREE / "NAME-INDEX.md").read_text(encoding="utf-8")
        generated = _generated_agents()
        for name, path in _pack_agents().items():
            fields, _raw, _b = parse_frontmatter(
                path.read_text(encoding="utf-8"), str(path)
            )
            slug = next(
                line.split("|")[1].strip().strip("`")
                for line in index.splitlines()
                if line.startswith("| `") and fields["name"] in line
            )
            assert _body(generated[slug]) == _body(
                path.read_text(encoding="utf-8")
            ), f"body differs for {name}"

    def test_allowlist_targets_exist(self):
        """Every slug inside an Agent(...) allowlist is a generated agent."""
        generated = _generated_agents()
        for slug, text in generated.items():
            for allowlist in re.findall(r"Agent\(([^)]*)\)", text.split("---")[1]):
                for target in allowlist.split(","):
                    assert target.strip() in generated, (
                        f"{slug}: allowlist target {target} not generated"
                    )

    def test_no_copilot_only_fields(self):
        """user-invocable has no Claude Code equivalent and is dropped;
        agents is folded into tools as Agent(...), not carried over."""
        for slug, text in _generated_agents().items():
            frontmatter = text.split("---")[1]
            assert "user-invocable" not in frontmatter, slug
            assert not re.search(r"^agents:", frontmatter, re.M), slug


class TestMcpConfig:
    """The generated .mcp.json backs every MCP wildcard the agents use."""

    def test_prefixes_backed_by_servers(self):
        """Each mcp__<server>__* in a tools list is a declared server."""
        config = json.loads((TREE / ".mcp.json").read_text(encoding="utf-8"))
        servers = set(config["mcpServers"])
        used = set()
        for text in _generated_agents().values():
            used.update(re.findall(r"mcp__([a-z0-9-]+)__\*", text))
        assert used <= servers, f"undeclared MCP servers used: {used - servers}"
        assert MCP_SERVERS <= servers

    def test_no_vscode_input_variables(self):
        """${input:...} placeholders are translated to env expansions."""
        raw = (TREE / ".mcp.json").read_text(encoding="utf-8")
        assert "${input:" not in raw


class TestManifestAndDeterminism:
    """Version lockstep and build determinism."""

    def test_plugin_version_matches_root(self):
        """The Claude plugin manifest carries the root plugin version."""
        root = json.loads((REPO_ROOT / "plugin.json").read_text(encoding="utf-8"))
        claude = json.loads(
            (TREE / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        assert claude["version"] == root["version"]
        assert claude["name"] == root["name"]

    def test_root_manifest_points_into_tree(self):
        """The generated root plugin.json resolves every component path."""
        manifest = json.loads(
            (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        root = json.loads((REPO_ROOT / "plugin.json").read_text(encoding="utf-8"))
        assert manifest["version"] == root["version"]
        agent_paths = manifest["agents"]
        assert len(agent_paths) == len(_generated_agents())
        for rel in agent_paths:
            assert (REPO_ROOT / rel).is_file(), rel
        for key in ("skills", "commands"):
            assert (REPO_ROOT / manifest[key]).is_dir(), key
        assert (REPO_ROOT / manifest["mcpServers"]).is_file()

    def test_build_is_deterministic(self):
        """Two builds from the same packs produce identical trees."""
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "assemble", REPO_ROOT / "tools" / "assemble_flat_layout.py"
        )
        assemble = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(assemble)
        agents, skills = assemble.collect()
        first = build_tree(REPO_ROOT, REPO_ROOT / "packs", agents, skills)
        second = build_tree(REPO_ROOT, REPO_ROOT / "packs", agents, skills)
        assert {k: v for k, v in first.items() if isinstance(v, bytes)} == {
            k: v for k, v in second.items() if isinstance(v, bytes)
        }


class TestCommands:
    """Prompt files become commands without their VS Code usage block."""

    def test_commands_generated_and_clean(self):
        """Six commands, none carrying the VS Code how-to comment."""
        commands = sorted((TREE / "commands").glob("*.md"))
        assert len(commands) == 6
        for path in commands:
            text = path.read_text(encoding="utf-8")
            assert "How to use (VS Code)" not in text, path.name
            fields, _raw, _b = parse_frontmatter(text, path.name)
            assert "description" in fields, path.name
            assert "agent" not in fields, path.name
