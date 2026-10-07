#!/bin/bash
# Pre-flight MCP server check for sdlc-harness
# Verifies that required MCP servers are configured before running the harness.
# If no config exists, offers to create one automatically.
# Usage: ./tools/check-mcp.sh [--config <path>] [--auto]

set -e

AUTO=0
CONFIG_OVERRIDE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --config) CONFIG_OVERRIDE="$2"; shift 2 ;;
        --auto) AUTO=1; shift ;;
        *) shift ;;
    esac
done

CONFIG_PATHS=(".vscode/mcp.json" "$HOME/.copilot/mcp.json")
if [ -n "$CONFIG_OVERRIDE" ]; then
    CONFIG_PATHS=("$CONFIG_OVERRIDE")
fi

REQUIRED_SERVERS=("awesome-copilot" "github" "context7")
OPTIONAL_SERVERS=("azure" "azure-devops")

read -r -d '' DEFAULT_MCP_JSON << 'JSONEOF' || true
{
  "servers": {
    "awesome-copilot": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "--rm", "-i", "ghcr.io/github/awesome-copilot:latest"]
    },
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
JSONEOF

echo "=== sdlc-harness MCP pre-flight check ==="
echo ""

FOUND_CONFIG=""
for p in "${CONFIG_PATHS[@]}"; do
    if [ -f "$p" ]; then
        FOUND_CONFIG="$p"
        echo "Config found: $p"
        break
    fi
done

if [ -z "$FOUND_CONFIG" ]; then
    echo "No MCP config found. Checked:"
    for p in "${CONFIG_PATHS[@]}"; do echo "  - $p"; done
    echo ""

    TARGET="${CONFIG_PATHS[0]}"
    DO_CREATE=0

    if [ $AUTO -eq 1 ]; then
        DO_CREATE=1
    else
        read -p "Create default MCP config at $TARGET ? (y/n) " ANSWER
        if [ "$ANSWER" = "y" ] || [ "$ANSWER" = "Y" ]; then
            DO_CREATE=1
        fi
    fi

    if [ $DO_CREATE -eq 1 ]; then
        mkdir -p "$(dirname "$TARGET")"
        echo "$DEFAULT_MCP_JSON" > "$TARGET"
        echo ""
        echo "Created: $TARGET"
        echo "Restart your Copilot session for the servers to load."
        FOUND_CONFIG="$TARGET"
    else
        echo ""
        echo "Skipped. Manual setup:"
        echo "  1. Create .vscode/mcp.json with the required servers"
        echo "  2. See Step 0 in the Harness agent for the JSON template"
        exit 1
    fi
fi

echo ""
echo "--- Required servers ---"
MISSING=0
for srv in "${REQUIRED_SERVERS[@]}"; do
    if grep -q "\"$srv\"" "$FOUND_CONFIG"; then
        echo "  [OK] $srv"
    else
        echo "  [MISSING] $srv"
        MISSING=1
    fi
done

echo ""
echo "--- Optional servers (degraded mode if missing) ---"
for srv in "${OPTIONAL_SERVERS[@]}"; do
    if grep -q "\"$srv\"" "$FOUND_CONFIG"; then
        echo "  [OK] $srv"
    else
        echo "  [--] $srv (not configured, will use degraded mode)"
    fi
done

echo ""
if [ $MISSING -eq 1 ]; then
    echo "RESULT: FAIL — required MCP servers are missing."
    echo "See Step 0 in the Harness agent for installation instructions."
    exit 1
else
    echo "RESULT: PASS — all required MCP servers are configured."
    exit 0
fi
