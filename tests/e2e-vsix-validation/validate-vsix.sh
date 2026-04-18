#!/usr/bin/env bash
# =============================================================
# SDLC Harness — VSIX E2E Validation Script
# Extracts the VSIX, validates all files ship correctly,
# checks content integrity, and produces a pass/fail report.
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VSIX_DIR="$REPO_ROOT/vscode-extension"
VSIX_FILE="$VSIX_DIR/sdlc-harness-1.0.0.vsix"
EXTRACT_DIR=$(mktemp -d)

trap 'rm -rf "$EXTRACT_DIR"' EXIT

# Counters
PASS=0
FAIL=0
WARN=0
FAILURES=()
WARNINGS=()

pass()  { PASS=$((PASS+1)); echo "  ✅ $1"; }
fail()  { FAIL=$((FAIL+1)); FAILURES+=("$1"); echo "  ❌ $1"; }
warn()  { WARN=$((WARN+1)); WARNINGS+=("$1"); echo "  ⚠️  $1"; }

section() { echo -e "\n━━━ $1 ━━━"; }

# =============================================================
section "1. VSIX Package Exists"
# =============================================================
if [[ -f "$VSIX_FILE" ]]; then
    SIZE=$(du -h "$VSIX_FILE" | cut -f1)
    pass "VSIX found: sdlc-harness-1.0.0.vsix ($SIZE)"
else
    fail "VSIX not found at $VSIX_FILE"
    echo "Run: cd vscode-extension && npx @vscode/vsce package --no-dependencies"
    exit 1
fi

# Extract (using python3 since unzip may not be installed)
python3 -c "
import zipfile, sys
with zipfile.ZipFile('$VSIX_FILE', 'r') as z:
    z.extractall('$EXTRACT_DIR')
"
EXT="$EXTRACT_DIR/extension"

# =============================================================
section "2. Package.json Integrity"
# =============================================================
PKG="$EXT/package.json"
if [[ -f "$PKG" ]]; then
    pass "package.json present"
else
    fail "package.json missing from VSIX"
fi

# Validate every chatAgent path exists
AGENT_PATHS=$(python3 -c "
import json, sys
pkg = json.load(open('$PKG'))
for a in pkg.get('contributes',{}).get('chatAgents',[]):
    print(a['path'])
")
AGENT_COUNT=0
AGENT_MISSING=0
while IFS= read -r apath; do
    AGENT_COUNT=$((AGENT_COUNT+1))
    if [[ -f "$EXT/$apath" ]]; then
        : # ok
    else
        fail "Agent file missing: $apath"
        AGENT_MISSING=$((AGENT_MISSING+1))
    fi
done <<< "$AGENT_PATHS"
if [[ $AGENT_MISSING -eq 0 ]]; then
    pass "All $AGENT_COUNT agent files referenced in package.json exist"
else
    fail "$AGENT_MISSING/$AGENT_COUNT agent files missing"
fi

# Validate every chatSkill path exists
SKILL_PATHS=$(python3 -c "
import json, sys
pkg = json.load(open('$PKG'))
for s in pkg.get('contributes',{}).get('chatSkills',[]):
    print(s['path'])
")
SKILL_COUNT=0
SKILL_MISSING=0
while IFS= read -r spath; do
    SKILL_COUNT=$((SKILL_COUNT+1))
    if [[ -f "$EXT/$spath" ]]; then
        : # ok
    else
        fail "Skill file missing: $spath"
        SKILL_MISSING=$((SKILL_MISSING+1))
    fi
done <<< "$SKILL_PATHS"
if [[ $SKILL_MISSING -eq 0 ]]; then
    pass "All $SKILL_COUNT skill files referenced in package.json exist"
else
    fail "$SKILL_MISSING/$SKILL_COUNT skill files missing"
fi

# =============================================================
section "3. Agent File Validation (18 agents)"
# =============================================================
EXPECTED_AGENTS=(
    analyst architecture-reviewer azure-compliance-reviewer
    code-quality-reviewer deployer deployment-readiness-reviewer
    documenter harness implementer llm-behavior-reviewer
    qa-bug-checklist-reviewer qa-coordinator rai-reviewer
    release-manager scaffolder security-reviewer
    test-coverage-reviewer ux-accessibility-reviewer
)
for agent in "${EXPECTED_AGENTS[@]}"; do
    f="$EXT/agents/$agent.agent.md"
    if [[ -f "$f" ]]; then
        if [[ -s "$f" ]]; then
            pass "Agent: $agent ($(wc -l < "$f") lines)"
        else
            fail "Agent: $agent is empty"
        fi
    else
        fail "Agent: $agent NOT FOUND"
    fi
done

# =============================================================
section "4. Skill File Validation (12 skills)"
# =============================================================
EXPECTED_SKILLS=(
    sdlc-project-qa sdlc-adr-authoring sdlc-architecture-review
    sdlc-code-quality sdlc-project-manifest sdlc-project-scaffolding
    sdlc-qa-bug-checklist sdlc-security-review sdlc-workspace-init
)
for skill in "${EXPECTED_SKILLS[@]}"; do
    f="$EXT/skills/$skill/SKILL.md"
    if [[ -f "$f" ]]; then
        pass "Skill: $skill ($(wc -l < "$f") lines)"
    else
        fail "Skill: $skill NOT FOUND"
    fi
done

# Azure skills moved to packs/azure/skills/
AZURE_SKILLS=(
    sdlc-azure-deployment sdlc-blob-storage sdlc-cosmos-repository
)
for skill in "${AZURE_SKILLS[@]}"; do
    f="$EXT/packs/azure/skills/$skill/SKILL.md"
    if [[ -f "$f" ]]; then
        pass "Skill (azure pack): $skill ($(wc -l < "$f") lines)"
    else
        fail "Skill (azure pack): $skill NOT FOUND"
    fi
done

# =============================================================
section "5. Workspace-Init Assets (instruction files)"
# =============================================================
ASSETS="$EXT/skills/sdlc-workspace-init/assets"

EXPECTED_INSTRUCTIONS=(
    code-quality-py code-quality-ts code-quality-tsx
    code-quality-java code-quality-csharp code-quality-go code-quality-rust
    test-quality test-quality-ts test-quality-tsx
    test-quality-java test-quality-csharp test-quality-go test-quality-rust
)
for inst in "${EXPECTED_INSTRUCTIONS[@]}"; do
    f="$ASSETS/instructions/$inst.instructions.md"
    if [[ -f "$f" ]]; then
        lines=$(wc -l < "$f")
        if [[ $lines -lt 10 ]]; then
            warn "Instruction: $inst only $lines lines (suspiciously short)"
        else
            pass "Instruction: $inst ($lines lines)"
        fi
    else
        fail "Instruction: $inst NOT FOUND"
    fi
done

# =============================================================
section "6. Workspace-Init Assets (templates & prompts)"
# =============================================================
TPL="$ASSETS/copilot-instructions.template.md"
if [[ -f "$TPL" ]]; then
    PLACEHOLDERS=$(grep -c '{{' "$TPL" || true)
    if [[ $PLACEHOLDERS -ge 3 ]]; then
        pass "copilot-instructions.template.md has $PLACEHOLDERS placeholder tokens"
    else
        warn "copilot-instructions.template.md has only $PLACEHOLDERS placeholders"
    fi
else
    fail "copilot-instructions.template.md NOT FOUND"
fi

MCP="$ASSETS/mcp.template.json"
if [[ -f "$MCP" ]]; then
    if python3 -c "import json; json.load(open('$MCP'))" 2>/dev/null; then
        SERVER_COUNT=$(python3 -c "
import json
d = json.load(open('$MCP'))
servers = d.get('servers',d.get('mcp',{}).get('servers',{}))
print(len(servers) if isinstance(servers, dict) else len(servers))
")
        if [[ "$SERVER_COUNT" -eq 7 ]]; then
            pass "mcp.template.json: valid JSON, $SERVER_COUNT MCP servers"
        else
            warn "mcp.template.json: $SERVER_COUNT servers (expected 7)"
        fi
    else
        fail "mcp.template.json: invalid JSON"
    fi
else
    fail "mcp.template.json NOT FOUND"
fi

EXPECTED_PROMPTS=(
    deployment implementation-and-tests qa-rai-release
    repo-documentation repo-structure-and-cicd requirement-and-design
)
for prompt in "${EXPECTED_PROMPTS[@]}"; do
    f="$ASSETS/prompts/$prompt.prompt.md"
    if [[ -f "$f" ]]; then
        pass "Prompt: $prompt ($(wc -l < "$f") lines)"
    else
        fail "Prompt: $prompt NOT FOUND"
    fi
done

# =============================================================
section "7. Workspace-Init Template Assets"
# =============================================================
# These files are deployed to target repos by sdlc-workspace-init skill,
# not shipped at the VSIX root. Check they exist in the skill assets.
INIT_ASSETS="$EXT/skills/sdlc-workspace-init/assets"
for doc in copilot-instructions.template.md reference-catalog.template.md; do
    f="$INIT_ASSETS/$doc"
    if [[ -f "$f" ]]; then
        lines=$(wc -l < "$f")
        pass "Template asset: $doc ($lines lines)"
    else
        warn "Template asset: $doc not found in workspace-init assets"
    fi
done

# =============================================================
section "8. Branding Sanitization Check"
# =============================================================
BRAND_HITS=0
for pattern in "Solution Project" "GSA" "SAS-" "sas-cosmosdb" "sas-storage"; do
    hits=$(grep -rl "$pattern" "$EXT" 2>/dev/null | wc -l || true)
    if [[ $hits -gt 0 ]]; then
        BRAND_HITS=$((BRAND_HITS+hits))
        fail "Stale branding '$pattern' found in $hits file(s):"
        grep -rl "$pattern" "$EXT" 2>/dev/null | sed 's|^|    |' || true
    fi
done
if [[ $BRAND_HITS -eq 0 ]]; then
    pass "No stale SAS/GSA/Solution Project branding found"
fi

# =============================================================
section "9. Multi-Language Coverage"
# =============================================================
REF="$EXT/reference-catalog.md"
if [[ -f "$REF" ]]; then
    for lang in "Python" "TypeScript" "Java" "C#" "Go" "Rust"; do
        if grep -qi "$lang" "$REF"; then
            pass "reference-catalog.md mentions $lang"
        else
            fail "reference-catalog.md missing $lang"
        fi
    done

    for tier in "Tier 1" "Tier 2" "Tier 3"; do
        if grep -q "$tier" "$REF"; then
            pass "reference-catalog.md has $tier AI framework guidance"
        else
            warn "reference-catalog.md missing $tier"
        fi
    done

    for fw in "Agent Framework" "LangChain" "Azure OpenAI"; do
        if grep -qi "$fw" "$REF"; then
            pass "reference-catalog.md references $fw"
        else
            warn "reference-catalog.md missing $fw reference"
        fi
    done
fi

# =============================================================
section "10. Workspace-Init SKILL.md Steps"
# =============================================================
WS_SKILL="$EXT/skills/sdlc-workspace-init/SKILL.md"
if [[ -f "$WS_SKILL" ]]; then
    STEP_COUNT=$(grep -c "^### Step" "$WS_SKILL" || true)
    pass "workspace-init has $STEP_COUNT steps"

    for step_keyword in "MCP" "copilot-instructions" "instruction files" "prompt files" "filtered reference catalog"; do
        if grep -qi "$step_keyword" "$WS_SKILL"; then
            pass "workspace-init mentions '$step_keyword'"
        else
            warn "workspace-init missing '$step_keyword' step"
        fi
    done

    if grep -q "Java\|java" "$WS_SKILL" && grep -q "Rust\|rust" "$WS_SKILL"; then
        pass "workspace-init has multi-language mappings"
    else
        warn "workspace-init may be missing language mappings"
    fi
fi

# =============================================================
section "11. Code Quality Skill Multi-Language"
# =============================================================
CQ_SKILL="$EXT/skills/sdlc-code-quality/SKILL.md"
if [[ -f "$CQ_SKILL" ]]; then
    for lang in Python TypeScript Java "C#" Go Rust; do
        if grep -qi "$lang" "$CQ_SKILL"; then
            pass "code-quality skill references $lang"
        else
            fail "code-quality skill missing $lang"
        fi
    done
fi

# =============================================================
section "12. File Count Summary"
# =============================================================
TOTAL_FILES=$(find "$EXT" -type f | wc -l)
AGENT_FILES=$(find "$EXT/agents" -type f 2>/dev/null | wc -l)
SKILL_FILES=$(find "$EXT/skills" -type f 2>/dev/null | wc -l)
INSTRUCTION_FILES=$(find "$EXT/skills/sdlc-workspace-init/assets/instructions" -type f 2>/dev/null | wc -l)

echo "  Total files in VSIX:    $TOTAL_FILES"
echo "  Agent files:            $AGENT_FILES"
echo "  Skill files (all):      $SKILL_FILES"
echo "  Instruction files:      $INSTRUCTION_FILES"

if [[ $TOTAL_FILES -ge 55 ]]; then
    pass "File count $TOTAL_FILES ≥ 55 minimum"
else
    fail "File count $TOTAL_FILES < 55 minimum"
fi

# =============================================================
section "13. Source ↔ VSIX Sync Check"
# =============================================================
GITHUB_DIR="$REPO_ROOT/.github"
if [[ -d "$GITHUB_DIR" ]]; then
    # Template files are workspace-init assets, not top-level docs — skip sync check for them

    GH_INST="$GITHUB_DIR/instructions"
    VS_INST="$VSIX_DIR/skills/sdlc-workspace-init/assets/instructions"
    if [[ -d "$GH_INST" ]]; then
        SYNC_OK=0
        SYNC_FAIL=0
        for f in "$GH_INST"/*.instructions.md; do
            fname=$(basename "$f")
            target="$VS_INST/$fname"
            if [[ -f "$target" ]]; then
                if diff -q "$f" "$target" > /dev/null 2>&1; then
                    SYNC_OK=$((SYNC_OK+1))
                else
                    SYNC_FAIL=$((SYNC_FAIL+1))
                    warn "Instruction out of sync: $fname"
                fi
            fi
        done
        if [[ $SYNC_FAIL -eq 0 ]]; then
            pass "Instruction files in sync ($SYNC_OK files checked)"
        fi
    fi
fi

# =============================================================
# REPORT
# =============================================================
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║      VSIX E2E Validation Report         ║"
echo "╠══════════════════════════════════════════╣"
printf "║  ✅ PASS: %-30s║\n" "$PASS"
printf "║  ⚠️  WARN: %-30s║\n" "$WARN"
printf "║  ❌ FAIL: %-30s║\n" "$FAIL"
echo "╠══════════════════════════════════════════╣"

if [[ $FAIL -eq 0 ]]; then
    echo "║  RESULT: ALL CHECKS PASSED ✅           ║"
else
    echo "║  RESULT: $FAIL FAILURE(S) DETECTED ❌     ║"
    echo "╠══════════════════════════════════════════╣"
    echo "║  Failures:                               ║"
    for f in "${FAILURES[@]}"; do
        printf "║  • %-38s║\n" "$(echo "$f" | head -c 38)"
    done
fi
echo "╚══════════════════════════════════════════╝"

exit $FAIL
