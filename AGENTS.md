# SDLC Harness - Agent Context

## Project Overview

**Repo:** https://github.com/Dongbumlee/sdlc-harness
**Working branch:** `evo`
**Working directory:** `/home/donlee/works/sdlc-harness-dev`
**GitHub account:** `Dongbumlee` (use `gh auth switch --user Dongbumlee` before git operations)

This is an SDLC (Software Development Lifecycle) Harness — a multi-agent orchestration system that drives software projects through 9 SDLC phases using 18 specialized AI agents running as VS Code GitHub Copilot plugin agents.

## V2 Architecture (Current Direction)

The v2 specification is at `docs/specs/2026-04-13-sdlc-harness-v2-spec.md`. Key architecture decisions:

### Core Principles

1. **Agents evaluate, not Python** — The 8 QA reviewer agents ARE the evaluators. No Python graders.
2. **Canaries = E2E integration tests** — Canary specs test "does the harness work correctly?", NOT model comparison.
3. **No Python orchestration** — The Harness agent orchestrates everything. Python code is being removed.
4. **User stays in agent flow** — No terminal, no scripts. User makes strategic decisions only.

### Agent Architecture (18 Agents)

| Role | Agent | Phases |
|------|-------|--------|
| **Orchestrator** | Harness | Routes all SDLC work |
| **Phase Workers** | Analyst, Scaffolder, Deployer, Implementer, Documenter, QA Coordinator, RAI Reviewer, Release Manager | 1-9 |
| **QA Reviewers** (8) | Architecture, Azure Compliance, Code Quality, Security, Test Coverage, UX/A11y, LLM Behavior, Deployment Readiness | QA phase |
| **Standalone** | QA Bug Checklist Reviewer | Cross-cutting |

Agent definitions: `.github/plugin/agents/`
Skills (12): `.github/plugin/skills/`

### What Python Code EXISTS vs What Should Be REMOVED

**REMOVE (per migration plan in v2 spec):**
- `orchestrator/` — entire directory (planner, generator, evaluator, state machine replaced by agents)
- `bench/graders/` — entire directory (code + LLM graders replaced by reviewer agents)
- `bench/engine/` — entire directory (scorer, provider, report, trend)
- `tools/run_benchmark.py` — user never runs Python
- `pyproject.toml` — no Python packaging needed
- `tests/` for removed modules

**KEEP:**
- `bench/canaries/` — 9 canary specs (E2E test scenarios)
- `.github/plugin/` — all agent and skill definitions (THE system)
- `docs/` — specifications, plans, architecture docs
- `config/` — harness configuration schema and profiles

## Git Operations - Critical Lessons

### Push Verification (ALWAYS DO THIS)

Sub-agent git pushes are unreliable. Always push directly and verify:

```bash
# 1. Switch auth
gh auth switch --user Dongbumlee

# 2. Stage, commit, push
git add <files>
git commit -m "message"
git push origin evo

# 3. Verify from remote (REQUIRED)
gh api repos/Dongbumlee/sdlc-harness/commits?sha=evo --jq '.[0] | "\(.sha[0:7]) \(.commit.message | split("\n")[0])"'
```

Never trust sub-agent reports of successful pushes. Always verify with `gh api` or `git ls-remote`.

### GitHub MCP Server (Configured)

The official GitHub MCP server (`@github/mcp-server`) is configured in `~/.amplifier/settings.yaml`. Use its tools (`push_files`, `list_commits`, `create_pull_request`, etc.) instead of bash git commands when available.

Env var: `GITHUB_PERSONAL_ACCESS_TOKEN` in `~/.amplifier/keys.env`

## Next Steps (Implementation Plan)

Priority order with dependencies:

### Step 1: Clean the Codebase
Remove Python evaluation layer per migration plan above. This unblocks everything.

### Step 2: Standardize Reviewer Agent Output Format
Update the 8 QA reviewer agent `.agent.md` files to emit structured, parseable output:
```yaml
reviewer: <agent-name>
phase: <sdlc-phase>
score: <1-10>
verdict: PASS | FAIL | CRITICAL_FAIL
findings:
  - severity: critical | high | medium | low
    category: <domain>
    description: "<finding>"
    location: "<file:line>"
    recommendation: "<fix>"
reasoning: "<evaluation summary>"
```
Consider creating a shared skill (`sdlc-reviewer-output-format`) for consistency.

### Step 3: Build E2E Canary Test Runner
Create mechanism to feed canary specs through the actual harness agent and capture pass/fail results.
- Skill or prompt for "canary mode" in the harness
- Result capture to `bench/results/` as structured JSON
- Pass/fail assertions on agent outputs

### Step 4: Strengthen Harness Evaluation Gates
Update `harness.agent.md` to:
- Parse structured reviewer scores
- Enforce scoring rules (>=7 pass, >=8 security, any Critical = fail)
- Implement feedback loop (QA fail -> Implementer fix -> QA re-review, max 3 rounds)

### Step 5: CI/CD Integration
Create `.github/workflows/canary-test.yml`:
- Trigger on PRs touching `agents/**` or `skills/**`
- Run harness in canary mode
- Pass/fail gate for PR merge

### Dependency Order
```
Step 1 (clean) --> Step 2 (output format) --> Step 3 (test runner) --> Step 4 (gates) --> Step 5 (CI)
```
Steps 1 and 2 can be done in parallel. Steps 3-5 are sequential.

## Key Files

| File | Purpose |
|------|---------|
| `docs/specs/2026-04-13-sdlc-harness-v2-spec.md` | V2 architecture specification |
| `docs/specs/2026-04-10-sdlc-harness-spec.md` | Original v1 specification |
| `docs/specs/2026-04-10-sdlc-harness-research-analysis.md` | Industry landscape research |
| `docs/plans/2026-04-10-evolution-implementation-plan.md` | Implementation plan (needs update for v2) |
| `.github/plugin/agents/harness.agent.md` | Main orchestrator agent |
| `.github/plugin/agents/qa-coordinator.agent.md` | QA orchestrator (dispatches 8 reviewers) |
| `bench/canaries/` | 9 E2E test scenarios (one per SDLC phase) |

## Session History

| Date | Session | Key Outcomes |
|------|---------|-------------|
| 2026-04-12/13 | `aa3398f9-62bd-473d-bb7f-c5caba7bb385` | V2 spec written, architecture decisions (agent-native eval, no Python, E2E canaries), GitHub MCP configured |

## Today's Deliverables (2026-04-12/13)

### 1. V2 Architecture Specification
**File:** `docs/specs/2026-04-13-sdlc-harness-v2-spec.md` (461 lines)

Comprehensive specification capturing the architectural shift from Python-centric evaluation to agent-native evaluation. Covers:
- 18-agent architecture with full inventory
- Agent-native evaluation flow (reviewer agents ARE the evaluators)
- E2E canary testing (validates harness works, not model comparison)
- Structured reviewer output format (YAML with score/verdict/findings)
- SDLC production flow with evaluation gates at every phase transition
- Migration plan (what to remove, what to keep)

### 2. Codebase Infrastructure (committed but will be removed per v2 migration)
- 6 new canary specs covering all 9 SDLC phases (deploy, design, document, rai, release, scaffold)
- LLM provider abstraction (`bench/engine/provider.py` - MockProvider + OpenAIProvider)
- Orchestrator LLM client wrapper (`orchestrator/llm_client.py`)
- Type system fixes across graders and evaluator
- Benchmark runner test (`tests/bench/test_run_benchmark.py`)
- `.gitignore` for Python artifacts

Note: The Python infrastructure code (items above) was built before the v2 architecture decision to go fully agent-native. Per the v2 spec migration plan, `orchestrator/`, `bench/graders/`, `bench/engine/`, and `tools/` will be removed in Step 1 of the next implementation phase.

### 3. Architecture Decisions Made (via discussion)

| Decision | Rationale |
|----------|-----------|
| Agents evaluate, not Python | The 8 QA reviewer agents already do evaluation — Python graders duplicate this with inferior quality |
| No model benchmarking feature | Benchmarking = E2E testing the harness, not comparing models |
| No Python code needed | Agents produce, evaluate, and orchestrate — Python was filling gaps agents already cover |
| Structured reviewer output | Reviewers emit YAML (score/verdict/findings) so results are parseable for debugging |
| Canaries = integration tests | Feed scenario into harness → verify agents fired correctly → pass/fail |

### 4. GitHub MCP Server Configured
- Official `@github/mcp-server` configured in `~/.amplifier/settings.yaml`
- Env var: `GITHUB_PERSONAL_ACCESS_TOKEN` in `~/.amplifier/keys.env`
- Provides 40+ tools: `push_files`, `list_commits`, `create_pull_request`, etc.
- Available after Amplifier session restart

## Commits on `evo` Branch (Latest First)

```
1a7f52d chore: add AGENTS.md for session context persistence
68f75c9 docs: add v2 specification - agent-native evaluation, E2E canary testing
14d0a5f fix: resolve type system mismatches and implement LLM provider pipeline
49661cd fix: add Python packaging for testable module imports
798779d feat: implement Phases 2-4 - benchmarking, orchestrator, CI/tooling
31e0184 test: verify push works
6cd9226 docs: split spec into research + specification, add implementation plan
```
