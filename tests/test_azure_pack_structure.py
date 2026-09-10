# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Validate the Azure pack metadata and plugin-discoverable skill layout."""

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
        assert agents["deployer"] == "azure-deployer.agent.md"
        assert agents["complianceReviewer"] == "azure-compliance-reviewer.agent.md"

    def test_pack_json_has_skills(self):
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        assert "skills" in data
        skills = data["skills"]
        assert "sdlc-azure-deployment" in skills
        assert "sdlc-cosmos-repository" in skills
        assert "sdlc-blob-storage" in skills

    def test_pack_json_has_mcp_servers(self):
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        assert data["mcpServers"] == "mcp-servers.json"

    def test_pack_json_has_reviewers(self):
        with open(PLUGIN_PACK_JSON) as f:
            data = json.load(f)
        assert "reviewers" in data
        reviewers = data["reviewers"]
        assert "azure-compliance-reviewer.agent.md" in reviewers


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
