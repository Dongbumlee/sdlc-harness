#!/bin/bash
# Pre-flight MCP server check and auto-setup for sdlc-harness
# Checks VSCode, Copilot CLI, Claude Code, and Claude Desktop config locations.
# Automatically creates missing configs and adds missing servers. No prompts.
# Usage: ./check-mcp.sh
# Requires: python3 (for JSON merging)

set -e

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is required for JSON config merging."
    exit 1
fi

echo "=== sdlc-harness MCP setup ==="
echo ""

# "path|tool|claude_format(0/1)"
CONFIG_LIST=(
    ".vscode/mcp.json|VSCode|0"
    "$HOME/.copilot/mcp.json|Copilot CLI|0"
    "$HOME/.claude.json|Claude Code|1"
    "$HOME/Library/Application Support/Claude/claude_desktop_config.json|Claude Desktop|1"
    "$HOME/.config/Claude/claude_desktop_config.json|Claude Desktop (Linux)|1"
)

ALL_OK=1

for entry in "${CONFIG_LIST[@]}"; do
    P="${entry%%|*}"
    REST="${entry#*|}"
    TOOL="${REST%%|*}"
    IS_CLAUDE="${REST##*|}"

    python3 - "$P" "$TOOL" "$IS_CLAUDE" << 'PYEOF'
import json, os, sys

path, tool, is_claude = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
key = "mcpServers" if is_claude else "servers"

servers = {
    "awesome-copilot": {"command": "docker", "args": ["run", "--rm", "-i", "ghcr.io/github/awesome-copilot:latest"]},
    "github": {"type": "http", "url": "https://api.githubcopilot.com/mcp/"},
    "context7": {"command": "npx", "args": ["-y", "@upstash/context7-mcp@latest"]},
}

config = {}
if os.path.exists(path):
    try:
        with open(path) as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError):
        print(f"[{tool}] WARNING: existing config is invalid JSON, skipping: {path}")
        sys.exit(2)

if key not in config:
    config[key] = {}

added = []
for name, definition in servers.items():
    if name not in config[key]:
        if is_claude:
            entry = {}
            if "command" in definition:
                entry["command"] = definition["command"]
            if "args" in definition:
                entry["args"] = definition["args"]
            if definition.get("type") == "http":
                entry["type"] = "http"
                entry["url"] = definition["url"]
        else:
            entry = dict(definition)
            if "type" not in entry:
                entry["type"] = "stdio"
        config[key][name] = entry
        added.append(name)

if added:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"[{tool}] Added: {', '.join(added)} -> {path}")
else:
    print(f"[{tool}] OK (all servers present)")
PYEOF

    RC=$?
    if [ $RC -eq 2 ]; then
        ALL_OK=0
    elif [ $RC -ne 0 ]; then
        echo "[$TOOL] ERROR during setup."
        ALL_OK=0
    fi
done

echo ""
if [ $ALL_OK -eq 1 ]; then
    echo "RESULT: PASS - all tools configured."
    echo "Restart your sessions for the servers to load."
    exit 0
else
    echo "RESULT: WARNING - some configs need manual attention (see above)."
    exit 1
fi
