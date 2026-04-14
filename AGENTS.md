# SDLC Harness - Agent Context

## Project Overview

**Repo:** https://github.com/Dongbumlee/sdlc-harness
**Working branch:** `evo`
**Working directory:** `/home/donlee/works/sdlc-harness-dev`
**GitHub account:** `Dongbumlee` (use `gh auth switch --user Dongbumlee` before git operations)

This is an SDLC (Software Development Lifecycle) Harness — a multi-agent orchestration system that drives software projects through 9 SDLC phases using 18 specialized AI agents running as VS Code GitHub Copilot plugin agents.

## V2 Architecture (Current — Fully Implemented)

The v2 specification is at `docs/specs/2026-04-13-sdlc-harness-v2-spec.md`. All 5 implementation steps are complete.

### Core Principles

1. **Agents evaluate, not Python** — The 8 QA reviewer agents ARE the evaluators. No Python graders.
2. **Canaries = E2E integration tests** — Canary specs test "does the harness work correctly?", NOT model comparison.
3. **No Python orchestration** — The Harness agent orchestrates everything. Python evaluation layer removed.
4. **User stays in agent flow** — No terminal, no scripts. User makes strategic decisions only.

### Agent Architecture (18 Agents)

| Role | Agent | Phases |
|------|-------|--------|
| **Orchestrator** | Harness | Routes all SDLC work |
| **Phase Workers** | Analyst, Scaffolder, Deployer, Implementer, Documenter, QA Coordinator, RAI Reviewer, Release Manager | 1-9 |
| **QA Reviewers** (8) | Architecture, Azure Compliance, Code Quality, Security, Test Coverage, UX/A11y, LLM Behavior, Deployment Readiness | QA phase |
| **Standalone** | QA Bug Checklist Reviewer | Cross-cutting |

Agent definitions: `.github/plugin/agents/`
Skills: `.github/plugin/skills/`

### Skills Inventory

| Skill | Purpose |
|-------|---------|
| `sdlc-reviewer-output-format` | Shared structured YAML output format for all 8 reviewers |
| `sdlc-canary-runner` | E2E canary test runner procedure |
| `sdlc-project-qa` | Comprehensive product QA checklist |
| `sdlc-qa-bug-checklist` | Known bug patterns from real bugs |
| `sdlc-security-review` | Security review checklist |
| `sdlc-code-quality` | Code quality review checklist |
| `sdlc-architecture-review` | Architecture review checklist |
| `sdlc-project-scaffolding` | Project scaffolding patterns |
| `sdlc-workspace-init` | Workspace initialization (contains prompt assets) |
| `sdlc-project-manifest` | Project manifest schema |

### Structured Reviewer Output Format

All 8 QA reviewers emit structured YAML between delimiters:
```
---sdlc-review-output---
reviewer: "<agent-name>"
score: <1-10>
verdict: PASS | FAIL | CRITICAL_FAIL
findings:
  - severity: critical | high | medium | low
    category: <domain-specific>
    description: "<finding>"
    location: "<file:line>"
    recommendation: "<fix>"
reasoning: "<evaluation summary>"
---end-sdlc-review-output---
```

### Evaluation Gates

- **Weighted scoring**: security × 1.5, others × 1.0 → composite = `(security × 1.5 + sum(others)) / 8.5`
- **Hard-fail rules**: composite < 7, security < 8, any Critical finding
- **3-tier escalation**: auto-retry → targeted retry → user decision (max 3 rounds)
- **Phase-specific routing**: Not all phases need all 8 reviewers

### Canary Testing

- 9 canary specs in `bench/canaries/` (one per SDLC phase), all using unified v2 format
- Harness supports canary mode (trigger: "run canary tests" / "canary mode")
- Results stored in `bench/results/` as structured JSON
- CI validates spec schema on PRs touching agents/skills

## Known Issues / Future Work

### Library Placeholder Hardcoding (Resolved)

Previously contained ~309 references to placeholder library names (`your-org/your-*`) that assumed every project uses specific internal SDK wrapper libraries. Resolved in `0e41994` (MCP gate removal) and `b0a470c` (full placeholder refactoring, 61 files, 412 replacements).

**What changed:**
- All hardcoded `your-org/your-cosmosdb-library`, `your-storage-lib`, `your-org/your-app-template`, etc. replaced with configurable references
- `copilot-instructions.template.md` now uses `{{PLACEHOLDER}}` variables (e.g., `{{COSMOSDB_LIB_PACKAGE}}`, `{{STORAGE_LIB_PACKAGE}}`) that get filled during workspace-init
- Agent/skill instructions now reference "the approved Cosmos DB library (from copilot-instructions.md)" instead of hardcoded package names
- MCP readiness gate in harness agent removed — no longer blocks on probing private org repos
- Agents teach **patterns** (Repository Pattern, SDK abstraction, `async with`) rather than prescribing specific libraries

### External Repo References (Resolved)

Previously referenced `microsoft/content-processing-solution-accelerator` and `microsoft/Container-Migration-Solution-Accelerator` as architectural pattern examples. Both were removed in `09c3adf` to make the harness self-contained. Architectural patterns are now described inline in agent/skill instructions.

## Git Operations - Critical Lessons

### GITHUB_TOKEN Conflict (ROOT CAUSE OF PUSH FAILURES)

The `GITHUB_TOKEN` environment variable (loaded from `~/.amplifier/keys.env` for the GitHub MCP server) **conflicts with git's credential helper** and causes `git push` to silently fail — the command returns success output but nothing reaches the remote.

**ALWAYS unset GITHUB_TOKEN before git push:**

```bash
# The working push pattern (REQUIRED)
unset GITHUB_TOKEN && git add <files> && git commit -m "message" && git push origin evo
```

### Push Verification (ALWAYS DO THIS)

Sub-agent git pushes are unreliable. Always push directly and verify:

```bash
# 1. Switch auth (if needed)
gh auth switch --user Dongbumlee

# 2. Stage, commit, push (MUST unset GITHUB_TOKEN)
unset GITHUB_TOKEN && git add <files> && git commit -m "message" && git push origin evo

# 3. Verify from remote (REQUIRED)
gh api repos/Dongbumlee/sdlc-harness/commits?sha=evo --jq '.[0] | "\(.sha[0:7]) \(.commit.message | split("\n")[0])"'
```

### GitHub MCP Server (Configured)

The official GitHub MCP server (`@github/mcp-server`) is configured in `~/.amplifier/settings.yaml`.
Env var: `GITHUB_PERSONAL_ACCESS_TOKEN` in `~/.amplifier/keys.env`

## CI/CD Workflows

| Workflow | File | Triggers | Purpose |
|----------|------|----------|---------|
| **Sync Check** | `sync-check.yml` | Push to `evo`, PRs | Ensures `.github/plugin/` and `vscode-extension/` stay identical |
| **Canary Test** | `canary-test.yml` | PRs touching agents/skills/canaries | Validates canary spec schema + sync check |

## Key Files

| File | Purpose |
|------|---------|
| `docs/specs/2026-04-13-sdlc-harness-v2-spec.md` | V2 architecture specification |
| `docs/specs/2026-04-10-sdlc-harness-spec.md` | Original v1 specification |
| `.github/plugin/agents/harness.agent.md` | Main orchestrator agent |
| `.github/plugin/agents/qa-coordinator.agent.md` | QA orchestrator (dispatches 8 reviewers) |
| `bench/canaries/` | 9 E2E test scenarios (one per SDLC phase) |
| `schemas/canary-spec.schema.json` | JSON schema for canary specs |
| `tools/validate_canaries.py` | Canary spec validator |
| `tests/e2e-agent-test/run-canaries.sh` | Local canary validation script |

## Implementation History

### v2 Migration (2026-04-13) — All Steps Complete

| Step | Description | Commit | Status |
|------|-------------|--------|--------|
| 1 | Clean codebase (remove Python evaluation layer) | `c8fe3fa` | Done |
| 2 | Standardize reviewer output format | `b1e68ed` | Done |
| 3 | Build E2E canary test runner | `a21685e` | Done |
| 4 | Strengthen harness evaluation gates | `5096d10` | Done |
| 5 | CI/CD integration | `04eb992` | Done |
| — | Rename: accelerator → project | `58bd2ae`, `fb89842` | Done |
| — | Sync fix + benchmark workflow update | `542db34` | Done |
| — | Remove external repo dependencies | `09c3adf` | Done |
| — | Library placeholder refactoring | `b0a470c` | Done |
| — | MCP gate removal from harness | `0e41994` | Done |
| — | Docs: align all markdown with MCP gate changes | `9e332da` | Done |

### Commits on `evo` Branch (Latest First)

```
9e332da docs: align all markdown with MCP gate and placeholder refactoring
8cfdfc3 docs: update AGENTS.md - mark library placeholder refactoring as resolved
b0a470c refactor: replace hardcoded library placeholders with project-config references
0e41994 refactor: remove your-org MCP readiness gate from harness agent
a256a72 docs: update AGENTS.md with library placeholder issue and session history
09c3adf refactor: remove external repo dependencies from agents and skills
88fb48b docs: update AGENTS.md with v2 implementation status
04eb992 feat: add CI/CD canary validation workflow (v2 Step 5)
fb89842 refactor: complete accelerator to project rename across codebase
5096d10 feat: strengthen harness evaluation gates (v2 Step 4)
a21685e feat: build E2E canary test runner (v2 Step 3)
b1e68ed feat: standardize reviewer agent output format (v2 Step 2)
58bd2ae refactor: rename accelerator to project across codebase
542db34 fix: sync agent/skill directories and update benchmark workflow
c8fe3fa refactor: remove Python evaluation layer (v2 migration Step 1)
9cfc2ca docs: update AGENTS.md with session context and git workflow notes
5620d0f chore: add AGENTS.md for session context persistence
22acfb7 docs: add v2 specification - agent-native evaluation, E2E canary testing
14d0a5f fix: resolve type system mismatches and implement LLM provider pipeline
49661cd fix: add Python packaging for testable module imports
798779d feat: implement Phases 2-4 - benchmarking, orchestrator, CI/tooling
31e0184 test: verify push works
6cd9226 docs: split spec into research + specification, add implementation plan
```

## Session History

| Date | Session | Key Outcomes |
|------|---------|-------------|
| 2026-04-12/13 | `aa3398f9-...` | V2 spec written, architecture decisions, GitHub MCP configured |
| 2026-04-13 | `6f539128-...` | V2 migration Steps 1-5 implemented, accelerator→project rename, CI green, external repo refs removed, library placeholder issue documented |
