#!/usr/bin/env bash
# Canary spec validation runner.
#
# Validates all canary YAML specs against the JSON schema using
# tools/validate_canaries.py. Does NOT run agents — actual E2E canary
# testing is done manually via the harness agent ("run canary tests").
#
# Usage:
#   ./tests/e2e-agent-test/run-canaries.sh
#   ./tests/e2e-agent-test/run-canaries.sh --list
#
# Exit codes:
#   0 — all specs valid
#   1 — one or more specs invalid or missing

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CANARY_DIR="$REPO_ROOT/bench/canaries"
VALIDATE_SCRIPT="$REPO_ROOT/tools/validate_canaries.py"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
RESET='\033[0m'

# ── List mode ────────────────────────────────────────────────────────────────

if [[ "${1:-}" == "--list" ]]; then
  echo -e "${BOLD}Canary specs found:${RESET}"
  for spec in "$CANARY_DIR"/*/canary-spec.yaml; do
    phase=$(basename "$(dirname "$spec")")
    printf "  %-20s %s\n" "$phase" "$spec"
  done
  exit 0
fi

# ── Pre-flight checks ─────────────────────────────────────────────────────────

if [[ ! -d "$CANARY_DIR" ]]; then
  echo -e "${RED}ERROR: canary directory not found: $CANARY_DIR${RESET}"
  exit 1
fi

canary_count=$(find "$CANARY_DIR" -name "canary-spec.yaml" | wc -l | tr -d ' ')
if [[ "$canary_count" -eq 0 ]]; then
  echo -e "${YELLOW}WARNING: No canary specs found in $CANARY_DIR${RESET}"
  exit 0
fi

echo -e "${BOLD}=== SDLC Harness — Canary Spec Validation ===${RESET}"
echo "Found $canary_count canary spec(s) in bench/canaries/"
echo ""

# ── Schema validation via Python ──────────────────────────────────────────────

if command -v python3 &>/dev/null && [[ -f "$VALIDATE_SCRIPT" ]]; then
  echo "Running schema validation (tools/validate_canaries.py)..."
  echo ""
  if python3 "$VALIDATE_SCRIPT"; then
    echo ""
    echo -e "${GREEN}✅ All canary specs are valid.${RESET}"
    echo ""
    echo "NOTE: Spec validation passed. To run E2E canary tests, use the"
    echo "harness agent in VS Code Copilot Chat: 'run canary tests'"
    exit 0
  else
    echo ""
    echo -e "${RED}❌ Canary spec validation failed. Fix errors above before running.${RESET}"
    exit 1
  fi
fi

# ── Fallback: basic existence check (no Python/jsonschema) ────────────────────

echo -e "${YELLOW}Python or validate_canaries.py not available — running basic existence check.${RESET}"
echo "Install dependencies for full validation: pip install jsonschema pyyaml"
echo ""

errors=0
for dir in "$CANARY_DIR"/*/; do
  phase=$(basename "$dir")
  spec="$dir/canary-spec.yaml"
  if [[ ! -f "$spec" ]]; then
    echo -e "  ${RED}FAIL${RESET} $phase — missing canary-spec.yaml"
    errors=$((errors + 1))
  else
    echo -e "  ${GREEN}PASS${RESET} $phase — canary-spec.yaml exists"
  fi
done

echo ""
if [[ $errors -gt 0 ]]; then
  echo -e "${RED}❌ $errors canary spec(s) missing.${RESET}"
  exit 1
fi

echo -e "${GREEN}✅ All $canary_count canary specs present (basic check only).${RESET}"
echo ""
echo "NOTE: Install jsonschema + pyyaml for full schema validation."
