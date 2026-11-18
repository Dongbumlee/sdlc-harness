"""Verify every version surface in the repo agrees with plugin.json.

The plugin version is restated across the manifests, the marketplace,
the pack metadata, the generated inventory, the README badge, and the
terminal-image generator. A bump that misses one surface ships a repo
that disagrees with itself, so the surfaces are gated here instead of
being synced by hand from a checklist. The canonical value is the root
plugin.json version; packs/_template/pack.json is excluded — it is a
scaffold for new packs and stays 0.0.0 by design.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

PACKS = ["core", "azure", "aws", "gcp", "onprem"]


def canonical_version() -> str:
    data = json.loads((REPO_ROOT / "plugin.json").read_text(encoding="utf-8"))
    return data["version"]


def all_version_values(node) -> list:
    """Collect every "version" value in a parsed JSON document."""
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "version":
                found.append(value)
            else:
                found.extend(all_version_values(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(all_version_values(item))
    return found


class TestVersionSync:
    """Every restated version equals the root plugin.json version."""

    def test_claude_plugin_manifest(self):
        data = json.loads(
            (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        assert data["version"] == canonical_version()

    def test_marketplace_versions(self):
        data = json.loads(
            (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        versions = all_version_values(data)
        assert len(versions) >= 2, "marketplace should restate the version"
        assert all(v == canonical_version() for v in versions), versions

    def test_pack_versions(self):
        for pack in PACKS:
            data = json.loads(
                (REPO_ROOT / "packs" / pack / "pack.json").read_text(encoding="utf-8")
            )
            assert data["version"] == canonical_version(), pack

    def test_agent_inventory_header(self):
        text = (REPO_ROOT / "docs" / "agent-inventory.md").read_text(encoding="utf-8")
        assert f"**Version:** {canonical_version()}" in text

    def test_readme_release_badge(self):
        text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        version = canonical_version()
        assert f"release-v{version}-" in text
        assert f"/releases/tag/v{version}" in text

    def test_terminal_image_generator(self):
        text = (REPO_ROOT / "tools" / "generate_terminal_images.py").read_text(
            encoding="utf-8"
        )
        assert re.search(rf"v{re.escape(canonical_version())}\b", text)
