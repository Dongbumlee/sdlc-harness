#!/bin/bash
# Pre-flight MCP server check for sdlc-harness
# Verifies that required MCP servers are configured before running the harness.
# Checks VSCode, Copilot CLI, Claude Code, and Claude Desktop config locations.
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

# Config locations: "path|tool_name"
if [ -n "$CONFIG_OVERRIDE" ]; then
    CONFIG_LIST=("$CONFIG_OVERRIDE|Custom")
else
    CONFIG_LIST=(
        ".vscode/mcp.json|VSCode"
        "$HOME/.copilot/mcp.json|Copilot CLI"
        "$HOME/.claude.json|Claude Code"
        "$HOME/Library/Application Support/Claude/claude_desktop_config.json|Claude Desktop"
        "$HOME/.config/Claude/claude_desktop_config.json|Claude Desktop (Linux)"
    )
fi

echo "=== sdlc-harness MCP pre-flight check ==="
echo ""

FOUND_CONFIG=""
FOUND_TOOL=""
for entry in "${CONFIG_LIST[@]}"; do
    p="${entry%%|*}"
    t="${entry##*|}"
    if [ -f "$p" ]; then
        FOUND_CONFIG="$p"
        FOUND_TOOL="$t"
        echo "Config found ($t): $p"
        break
    fi
done

if [ -z "$FOUND_CONFIG" ]; then
    echo "No MCP config found. Checked:"
    for entry in "${CONFIG_LIST[@]}"; do
        p="${entry%%|*}"
        t="${entry##*|}"
        echo "  - [$t] $p"
    done
    echo ""

    TARGET="${CONFIG_LIST[0]%%|*}"
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
        echo "Restart your session for the servers to load."
        FOUND_CONFIG="$TARGET"
    else
        echo ""
        echo "Skipped. See Step 0 in the Harness agent for manual setup."
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
    exit 1
else
    echo "RESULT: PASS — all required MCP servers are configured."
    exit 0
fi
