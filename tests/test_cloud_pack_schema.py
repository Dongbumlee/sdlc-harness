"""
Tests for cloud-pack JSON Schema (draft-07) validation.
Task: Create Cloud Pack JSON Schema
"""

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "cloud-pack.schema.json"
AZURE_PACK_PLUGIN = REPO_ROOT / ".github" / "plugin" / "packs" / "azure" / "pack.json"
AZURE_PACK_VSCODE = REPO_ROOT / "vscode-extension" / "packs" / "azure" / "pack.json"


class TestSchemaFileExists:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

    def test_schema_is_valid_json(self):
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
        assert isinstance(schema, dict)

    def test_schema_is_draft_07(self):
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
        assert schema.get("$schema") == "http://json-schema.org/draft-07/schema#"


class TestSchemaStructure:
    """Tests that the schema defines the correct structure."""

    @pytest.fixture
    def schema(self):
        with open(SCHEMA_PATH) as f:
            return json.load(f)

    def test_schema_has_required_fields(self, schema):
        required = schema.get("required", [])
        assert "name" in required
        assert "displayName" in required
        assert "version" in required
        assert "cloud" in required
        assert "agents" in required
        assert "skills" in required

    def test_schema_disallows_additional_properties(self, schema):
        assert schema.get("additionalProperties") is False

    def test_name_pattern_lowercase_hyphens(self, schema):
        name_prop = schema["properties"]["name"]
        assert "pattern" in name_prop
        # Pattern should enforce lowercase letters and hyphens
        pattern = name_prop["pattern"]
        import re
        assert re.match(pattern, "azure")
        assert re.match(pattern, "my-pack")
        assert not re.match(pattern, "MyPack")
        assert not re.match(pattern, "my_pack")
        assert not re.match(pattern, "my pack")

    def test_version_semver_pattern(self, schema):
        version_prop = schema["properties"]["version"]
        assert "pattern" in version_prop
        import re
        pattern = version_prop["pattern"]
        assert re.match(pattern, "1.0.0")
        assert re.match(pattern, "0.1.0")
        assert re.match(pattern, "10.20.30")
        assert not re.match(pattern, "1.0")
        assert not re.match(pattern, "v1.0.0")

    def test_cloud_enum(self, schema):
        cloud_prop = schema["properties"]["cloud"]
        assert "enum" in cloud_prop
        assert set(cloud_prop["enum"]) == {"azure", "aws", "gcp"}

    def test_agents_has_required_deployer(self, schema):
        agents_prop = schema["properties"]["agents"]
        assert "deployer" in agents_prop.get("required", [])

    def test_agents_deployer_is_string(self, schema):
        agents_prop = schema["properties"]["agents"]
        assert agents_prop["properties"]["deployer"]["type"] == "string"

    def test_agents_compliance_reviewer_optional_string(self, schema):
        agents_prop = schema["properties"]["agents"]
        # complianceReviewer should be defined but not in required
        assert "complianceReviewer" in agents_prop["properties"]
        assert agents_prop["properties"]["complianceReviewer"]["type"] == "string"
        assert "complianceReviewer" not in agents_prop.get("required", [])

    def test_agents_additional_properties_are_strings(self, schema):
        agents_prop = schema["properties"]["agents"]
        # additionalProperties should allow strings
        add_props = agents_prop.get("additionalProperties")
        assert add_props == {"type": "string"}

    def test_skills_is_array_of_strings(self, schema):
        skills_prop = schema["properties"]["skills"]
        assert skills_prop["type"] == "array"
        assert skills_prop["items"]["type"] == "string"

    def test_skills_min_items_zero(self, schema):
        skills_prop = schema["properties"]["skills"]
        assert skills_prop.get("minItems", 0) == 0

    def test_description_optional_string(self, schema):
        props = schema["properties"]
        assert "description" in props
        assert props["description"]["type"] == "string"
        assert "description" not in schema.get("required", [])

    def test_mcp_servers_optional_string(self, schema):
        props = schema["properties"]
        assert "mcpServers" in props
        assert props["mcpServers"]["type"] == "string"
        assert "mcpServers" not in schema.get("required", [])

    def test_reviewers_optional_array_of_strings(self, schema):
        props = schema["properties"]
        assert "reviewers" in props
        assert props["reviewers"]["type"] == "array"
        assert props["reviewers"]["items"]["type"] == "string"
        assert "reviewers" not in schema.get("required", [])


class TestAzurePackValidation:
    """Tests that Azure pack.json passes schema validation."""

    @pytest.fixture
    def schema(self):
        with open(SCHEMA_PATH) as f:
            return json.load(f)

    def test_plugin_azure_pack_validates_against_schema(self, schema):
        with open(AZURE_PACK_PLUGIN) as f:
            pack = json.load(f)
        # Should not raise
        jsonschema.validate(instance=pack, schema=schema)

    def test_vscode_azure_pack_validates_against_schema(self, schema):
        with open(AZURE_PACK_VSCODE) as f:
            pack = json.load(f)
        # Should not raise
        jsonschema.validate(instance=pack, schema=schema)

    def test_azure_pack_has_all_required_fields(self, schema):
        """Explicitly verify all required fields are present in azure pack.json."""
        with open(AZURE_PACK_PLUGIN) as f:
            pack = json.load(f)
        required_fields = schema.get("required", [])
        for field in required_fields:
            assert field in pack, f"Required field '{field}' missing from Azure pack.json"

    def test_invalid_pack_fails_validation(self, schema):
        """Invalid pack should fail validation."""
        invalid_pack = {
            "name": "InvalidName",  # uppercase not allowed
            "displayName": "Test",
            "version": "1.0.0",
            "cloud": "azure",
            "agents": {"deployer": "test.md"},
            "skills": [],
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_pack, schema=schema)

    def test_missing_required_field_fails_validation(self, schema):
        """Pack missing required field should fail validation."""
        incomplete_pack = {
            "name": "test-pack",
            "displayName": "Test Pack",
            # version missing
            "cloud": "azure",
            "agents": {"deployer": "test.md"},
            "skills": [],
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=incomplete_pack, schema=schema)
