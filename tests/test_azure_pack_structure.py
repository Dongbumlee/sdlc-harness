"""
Tests for Azure cloud pack directory structure and manifest files.
Task: Create Pack Directory Structure and Azure Pack Manifest
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Required directories
REQUIRED_DIRS = [
    ".github/plugin/packs/azure/skills",
    ".github/plugin/packs/_template/skills",
]

# Required pack.json locations
PLUGIN_PACK_JSON = REPO_ROOT / ".github/plugin/packs/azure/pack.json"


class TestDirectoryStructure:
    def test_github_plugin_azure_skills_dir_exists(self):
        path = REPO_ROOT / ".github/plugin/packs/azure/skills"
        assert path.is_dir(), f"Directory missing: {path}"

    def test_github_plugin_template_skills_dir_exists(self):
        path = REPO_ROOT / ".github/plugin/packs/_template/skills"
        assert path.is_dir(), f"Directory missing: {path}"


class TestPluginPackJson:
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
