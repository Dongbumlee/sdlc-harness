#!/bin/bash
# Pre-flight MCP server check for sdlc-harness
# Verifies that required MCP servers are configured before running the harness.
# Usage: ./tools/check-mcp.sh [--config <path>]
# Default config locations checked: .vscode/mcp.json, ~/.copilot/mcp.json

set -e

CONFIG_PATHS=(".vscode/mcp.json" "$HOME/.copilot/mcp.json")
if [ "$1" = "--config" ] && [ -n "$2" ]; then
    CONFIG_PATHS=("$2")
fi

REQUIRED_SERVERS=("awesome-copilot" "github" "context7")
OPTIONAL_SERVERS=("azure" "azure-devops")

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
    echo "ERROR: No MCP config found. Checked:"
    for p in "${CONFIG_PATHS[@]}"; do echo "  - $p"; done
    echo ""
    echo "Copy the template from the harness repo:"
    echo "  cp <harness>/.vscode/mcp.json .vscode/mcp.json"
    exit 1
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
