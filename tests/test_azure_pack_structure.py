# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Validate the Azure pack metadata and plugin-discoverable skill layout."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

REQUIRED_DIRS = [
    "skills/sdlc-azure-deployment",
    "skills/sdlc-cosmos-repository",
    "skills/sdlc-blob-storage",
]

PLUGIN_PACK_JSON = REPO_ROOT / "packs/azure/pack.json"
PLUGIN_JSON = REPO_ROOT / "plugin.json"


class TestDirectoryStructure:
    """Verify that Azure skills are immediate plugin skill directories."""

    def test_azure_skill_directories_exist(self):
        """Ensure every Azure skill is discoverable by current clients."""
        for relative_path in REQUIRED_DIRS:
            path = REPO_ROOT / relative_path
            assert path.is_dir(), f"Directory missing: {path}"
            assert (path / "SKILL.md").is_file(), f"Skill file missing: {path / 'SKILL.md'}"


class TestPluginPackJson:
    """Verify the Azure cloud pack metadata."""

    def test_pack_json_exists(self):
        assert PLUGIN_PACK_JSON.exists(), f"File missing: {PLUGIN_PACK_JSON}"

    def test_pack_json_is_valid_json(self):
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)  # raises if invalid JSON
        assert isinstance(data, dict)

    def test_pack_json_has_name_azure(self):
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        assert data["name"] == "azure"

    def test_pack_json_has_display_name(self):
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        assert data["displayName"] == "Azure Cloud Pack"

    def test_pack_json_has_version(self):
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        assert data["version"] == "1.0.0"

    def test_pack_json_has_cloud_azure(self):
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        assert data["cloud"] == "azure"

    def test_pack_json_has_agents(self):
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        assert "agents" in data
        agents = data["agents"]
        # deployer is owned by the core pack and inherited here (ADR-0001, decision A)
        assert agents["deployer"] == "deployer.agent.md"
        # pack-local agents use pack-relative paths (Phase 2 layout)
        assert agents["complianceReviewer"] == "agents/azure-compliance-reviewer.agent.md"

    def test_pack_json_agent_files_exist(self):
        """Every agent file referenced by the pack must exist on disk."""
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        agents = data["agents"]
        assert set(agents) == {"deployer", "complianceReviewer"}
        # Inherited core agents resolve against the canonical flat agent dirs.
        for agent_dir in ("com.github.copilot/agents", ".github/agents"):
            path = REPO_ROOT / agent_dir / agents["deployer"]
            assert path.is_file(), f"Pack agent missing: deployer -> {path}"
        # Pack-local agents live under packs/azure/agents/; the flat copy is a
        # compatibility mirror until Phase 3 CI assembly lands.
        pack_agent = REPO_ROOT / "packs" / "azure" / agents["complianceReviewer"]
        assert pack_agent.is_file(), f"Pack agent missing: {pack_agent}"
        flat_agent = REPO_ROOT / "com.github.copilot" / "agents" / pack_agent.name
        assert flat_agent.is_file(), f"Flat mirror missing: {flat_agent}"
        assert pack_agent.read_bytes() == flat_agent.read_bytes(), (
            f"Pack-local agent diverged from flat mirror: {pack_agent}"
        )
        for ref in data.get("reviewers", []):
            path = REPO_ROOT / "packs" / "azure" / ref
            assert path.is_file(), f"Pack reviewer missing: {path}"

    def test_pack_json_has_skills(self):
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        assert "skills" in data
        skills = data["skills"]
        # Pack-local skills use pack-relative paths (Phase 2 layout).
        assert "skills/sdlc-azure-deployment" in skills
        assert "skills/sdlc-cosmos-repository" in skills
        assert "skills/sdlc-blob-storage" in skills

    def test_pack_json_has_mcp_servers(self):
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        assert data["mcpServers"] == "mcp-servers.json"

    def test_pack_mcp_servers_file_exists_and_valid(self):
        """The mcpServers file referenced by the pack must exist and define the azure server."""
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        mcp_path = REPO_ROOT / "packs/azure" / data["mcpServers"]
        assert mcp_path.is_file(), f"File missing: {mcp_path}"
        with open(mcp_path) as f:
            mcp = json.load(f)  # raises if invalid JSON
        assert "azure" in mcp.get("servers", {}), "azure server missing from pack mcp-servers.json"

    def test_pack_skills_all_exist(self):
        """Every skill listed in the pack must exist under packs/azure/skills/."""
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        assert set(data["skills"]) == {
            "skills/sdlc-azure-deployment",
            "skills/sdlc-cosmos-repository",
            "skills/sdlc-blob-storage",
        }
        for skill in data["skills"]:
            name = skill.removeprefix("skills/")
            pack_skill = REPO_ROOT / "packs" / "azure" / "skills" / name / "SKILL.md"
            assert pack_skill.is_file(), f"Pack skill missing: {pack_skill}"
            # The root skills/ copy is a compatibility mirror until Phase 3.
            flat_skill = REPO_ROOT / "skills" / name / "SKILL.md"
            assert flat_skill.is_file(), f"Flat skill mirror missing: {flat_skill}"

    def test_pack_json_has_reviewers(self):
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        assert "reviewers" in data
        reviewers = data["reviewers"]
        assert "agents/azure-compliance-reviewer.agent.md" in reviewers


class TestPluginManifest:
    """Verify the root manifest uses the current Agent Plugins format."""

    def test_root_manifest_exists(self):
        """Ensure clients can find the plugin manifest at the package root."""
        assert PLUGIN_JSON.is_file(), f"File missing: {PLUGIN_JSON}"

    def test_root_manifest_uses_agent_plugins_schema(self):
        """Ensure the manifest opts into the portable plugin specification."""
        with open(PLUGIN_JSON) as f:
            data = json.load(f)
        assert data["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
        assert "agents" not in data
        assert "skills" not in data
