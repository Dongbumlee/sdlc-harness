# SDLC Harness Evolution Specification v2

**Version:** 2.0  
**Date:** 2026-04-13  
**Status:** Draft  
**Supersedes:** v1 specification at `docs/specs/2026-04-10-sdlc-harness-spec.md`

---

## 1. Executive Summary

The SDLC Harness v2 represents three fundamental architectural shifts from the v1 specification:

1. **Agents evaluate, not Python** — The 8 QA reviewer agents ARE the evaluation system. Python graders, scorers, and the evaluator module are removed entirely.

2. **Canaries = E2E integration tests** — Canary specs validate "does the harness agent system work correctly?", NOT "which model produces better output?" There is no model comparison or benchmarking feature.

3. **No Python orchestration** — The Harness agent orchestrates all SDLC phases. The Python orchestrator module (planner, generator, evaluator, state machine) is removed. Python code exists nowhere in the production system.

**The user never leaves the agent flow.** No terminal commands, no Python scripts, no JSON interpretation. Users make strategic decisions at phase transitions; agents handle everything else.

---

## 2. Architecture Philosophy

### Agents for Judgment, Code for Nothing

The v1 spec maintained a Python evaluation layer alongside agent reviewers, creating duplicate evaluation paths. V2 eliminates this duplication:

| Concern | v1 Approach | v2 Approach |
|---------|-------------|-------------|
| Artifact generation | Worker agents + Python generator | Worker agents only |
| Quality evaluation | Python graders + reviewer agents | Reviewer agents only |
| Orchestration | Python state machine + Harness agent | Harness agent only |
| Score aggregation | Python scorer | QA Coordinator agent |
| Trend tracking | Python trend module | Not needed (E2E pass/fail) |
| Benchmarking | Python benchmark runner | E2E canary tests |

### Why No Python?

- **Agents already evaluate** — The 8 QA reviewers produce numeric scores, identify issues, and make pass/fail verdicts. Python graders duplicated this with inferior quality (keyword matching vs. contextual understanding).
- **Agents already orchestrate** — The Harness agent routes work, manages phase transitions, and handles escalation. A Python state machine duplicated this.
- **Users don't run scripts** — The harness is a VS Code Copilot plugin. Users interact via chat, not terminal.

---

## 3. System Components

### 3a. Agent Layer (18 Agents)

The core system. All agent definitions live in `.github/plugin/agents/`.

| Role | Agent | File | Phases |
|------|-------|------|--------|
| **Orchestrator** | Harness | `harness.agent.md` | All |
| **Phase Workers** | | | |
| | Analyst | `analyst.agent.md` | Requirements, Design |
| | Scaffolder | `scaffolder.agent.md` | Scaffold |
| | Deployer | `deployer.agent.md` | Deploy |
| | Implementer | `implementer.agent.md` | Implement |
| | Documenter | `documenter.agent.md` | Document |
| | QA Coordinator | `qa-coordinator.agent.md` | QA |
| | RAI Reviewer | `rai-reviewer.agent.md` | RAI |
| | Release Manager | `release-manager.agent.md` | Release |
| **QA Reviewers** (8) | | | |
| | Architecture Reviewer | `architecture-reviewer.agent.md` | QA |
| | Azure Compliance Reviewer | `azure-compliance-reviewer.agent.md` | QA |
| | Code Quality Reviewer | `code-quality-reviewer.agent.md` | QA |
| | Security Reviewer | `security-reviewer.agent.md` | QA |
| | Test Coverage Reviewer | `test-coverage-reviewer.agent.md` | QA |
| | UX/Accessibility Reviewer | `ux-accessibility-reviewer.agent.md` | QA |
| | LLM Behavior Reviewer | `llm-behavior-reviewer.agent.md` | QA |
| | Deployment Readiness Reviewer | `deployment-readiness-reviewer.agent.md` | QA |
| **Standalone** | QA Bug Checklist Reviewer | `qa-bug-checklist-reviewer.agent.md` | Cross-cutting |

### 3b. Skill Layer (12 Skills)

Domain knowledge packages in `.github/plugin/skills/`:

| Skill | Scope | Phases |
|-------|-------|--------|
| `sdlc-workspace-init` | Project bootstrap | Init |
| `sdlc-project-manifest` | Config generation | Init |
| `sdlc-project-scaffolding` | Template generation | Scaffold |
| `sdlc-architecture-review` | Design evaluation | Design, QA |
| `sdlc-code-quality` | Lint, type check | Implement, QA |
| `sdlc-security-review` | Vulnerability scan | Implement, QA |
| `sdlc-adr-authoring` | Decision records | Design |
| `sdlc-accelerator-qa` | QA workflow | QA |
| `sdlc-qa-bug-checklist` | Bug patterns | QA |
| `sdlc-azure-deployment` | Azure IaC | Deploy |
| `sdlc-cosmos-repository` | Cosmos DB patterns | Implement |
| `sdlc-blob-storage` | Blob storage patterns | Implement |

### 3c. Canary Test Specs

E2E test scenarios in `bench/canaries/`, one per SDLC phase:

```
bench/canaries/
  requirements/req-001-ecommerce-api.yaml
  design/des-001-ecommerce-architecture.yaml
  scaffold/scf-001-fastapi-project.yaml
  deploy/dep-001-azure-webapp.yaml
  implement/impl-001-rest-endpoint.yaml
  document/doc-001-api-documentation.yaml
  qa/qa-001-unit-test-generation.yaml
  release/rel-001-changelog-generation.yaml
  rai/rai-001-bias-assessment.yaml
```

Each canary defines: input scenario, expected agent behavior, pass/fail criteria. Purpose is validating the harness works correctly — NOT comparing model quality.

---

## 4. SDLC Production Flow

### Phase Execution

```
User: "@harness build me an e-commerce API"
  │
  ▼
Harness Agent (Orchestrator)
  │
  ├─ REQUIREMENTS PHASE
  │   ├─ Analyst agent produces requirements spec
  │   ├─ Self-evaluation checklist
  │   └─ Pass → next phase
  │
  ├─ DESIGN PHASE
  │   ├─ Analyst agent produces architecture design
  │   ├─ Architecture Reviewer evaluates
  │   ├─ Score < threshold? → feedback loop
  │   └─ Pass → next phase
  │
  ├─ SCAFFOLD PHASE
  │   ├─ Scaffolder agent creates project structure
  │   ├─ Self-evaluation checklist
  │   └─ Pass → next phase
  │
  ├─ DEPLOY PHASE
  │   ├─ Deployer agent creates IaC
  │   ├─ Deployment Readiness Reviewer evaluates
  │   ├─ Azure Compliance Reviewer evaluates
  │   └─ Pass → next phase
  │
  ├─ IMPLEMENT PHASE
  │   ├─ Implementer agent writes code
  │   ├─ Code Quality Reviewer evaluates
  │   ├─ Security Reviewer evaluates
  │   ├─ Test Coverage Reviewer evaluates
  │   ├─ Issues found? → feedback loop (max 3 rounds)
  │   └─ Pass → next phase
  │
  ├─ DOCUMENT PHASE
  │   ├─ Documenter agent produces docs
  │   └─ Pass → next phase
  │
  ├─ QA PHASE
  │   ├─ QA Coordinator dispatches ALL 8 reviewers in parallel
  │   ├─ Each reviewer produces structured score + findings
  │   ├─ QA Coordinator aggregates scores
  │   ├─ Verdict: PASS (all ≥7, security ≥8) or FAIL
  │   ├─ FAIL → feedback to Implementer → re-review (max 3 rounds)
  │   └─ PASS → next phase
  │
  ├─ RAI PHASE
  │   ├─ RAI Reviewer evaluates responsible AI concerns
  │   └─ Pass → next phase
  │
  └─ RELEASE PHASE
      ├─ Release Manager prepares release artifacts
      └─ Done → User gets artifacts + quality report
```

### User Decision Points

The user intervenes ONLY at strategic moments:

| Decision Point | What User Sees |
|----------------|---------------|
| **Design approval** | "Here's the proposed architecture. Proceed?" |
| **QA verdict** | "8 reviewers scored. Overall: PASS. Deploy?" |
| **QA failure** | "Security scored 6.1 (threshold 8.0). Fix or override?" |
| **Deployment** | "Ready to deploy to staging?" |
| **Release** | "Release artifacts ready. Publish?" |

---

## 5. Evaluation Architecture

### Reviewer Agents ARE the Evaluators

The 8 QA reviewer agents perform all quality evaluation. There are no Python graders, no LLM-as-judge wrappers, no scoring engines. The reviewer agents:

1. **Receive** the artifacts from the current phase
2. **Evaluate** against their domain expertise (security, architecture, code quality, etc.)
3. **Score** on a 1-10 scale with findings
4. **Verdict** PASS, FAIL, or CRITICAL_FAIL

### Structured Reviewer Output Format

All reviewer agents emit structured output for consistency and parseability:

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

### Scoring Rules

| Rule | Threshold |
|------|-----------|
| General pass | Score ≥ 7.0 |
| Security pass | Score ≥ 8.0 |
| Critical finding | Any Critical = automatic FAIL |
| Retry limit | Max 3 feedback rounds |
| Escalation | 3 consecutive failures → escalate to user |

### Feedback Loop

```
Worker Agent produces artifact
  → Reviewer Agents evaluate
  → Score < threshold?
    → YES: Findings sent back to Worker Agent
    → Worker Agent revises artifact
    → Reviewer Agents re-evaluate
    → (max 3 rounds, then escalate to user)
  → NO: Pass, proceed to next phase
```

---

## 6. E2E Testing with Canaries

### Purpose

Canaries validate that the **harness agent system works correctly**. They are integration tests, not benchmarks.

### What Canaries Test

| Dimension | What's Verified |
|-----------|----------------|
| **Agent output** | Did the worker agent produce valid artifacts for this phase? |
| **State transitions** | Did the harness correctly transition between phases? |
| **Reviewer dispatch** | Did the QA Coordinator dispatch the right reviewers? |
| **Feedback loops** | When QA failed, did the feedback loop fire correctly? |
| **MCP integration** | Did agents correctly use MCP tools when available? |
| **Skill loading** | Did agents load and follow the correct skills? |

### Canary Execution Flow

```
Canary spec (YAML) → Feed into Harness agent
  → Harness orchestrates the phase
  → Worker agents produce output
  → Reviewer agents evaluate
  → Capture: Did agents fire? Did scores appear? Did transitions work?
  → Result: PASS (harness works) or FAIL (bug in agent/skill/harness)
```

### Test Results

Results are stored as structured JSON in `bench/results/`:

```json
{
  "run_id": "canary-2026-04-13-001",
  "timestamp": "2026-04-13T12:00:00Z",
  "canary_id": "req-001-ecommerce-api",
  "phase": "requirements",
  "result": "PASS",
  "agents_fired": ["analyst"],
  "reviewers_fired": [],
  "duration_seconds": 45,
  "debug_info": {
    "agent_output_length": 1234,
    "phase_transitions": ["INIT → REQUIREMENTS → COMPLETE"],
    "errors": []
  }
}
```

The focus is on **debugging the harness** — identifying which agent failed, at what step, with what output — not on measuring output quality.

---

## 7. Configuration

### harness-config.yml

```yaml
project:
  name: "my-project"
  description: "Project description"

stack:
  backend: python
  frontend: react
  testing: pytest

cloud:
  provider: azure
  services: [app-service, cosmos-db, blob-storage]

evaluation:
  e2e:
    canary_path: bench/canaries
    results_path: bench/results
    timeout_seconds: 300

orchestrator:
  max_retries: 3
  fail_fast: false
```

---

## 8. CI/CD Integration

### GitHub Actions Canary Workflow

```yaml
# .github/workflows/canary-test.yml
name: Canary E2E Tests
on:
  pull_request:
    paths:
      - '.github/plugin/agents/**'
      - '.github/plugin/skills/**'

jobs:
  canary:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run canary tests
        run: |
          # Feed each canary spec through the harness
          # Capture pass/fail results
          # Fail the PR check if any canary fails
```

Simple pass/fail — no regression scoring, no baseline comparison, no trend tracking.

---

## 9. Repository Structure

```
sdlc-harness/
  .github/
    plugin/
      agents/           # 18 agent definitions (THE system)
        harness.agent.md
        analyst.agent.md
        ... (16 more)
      skills/           # 12 skill definitions
        sdlc-workspace-init/
        sdlc-code-quality/
        ... (10 more)
      plugin.json
    workflows/          # CI/CD
    SDLC-with-Copilot-and-Azure.md
  bench/
    canaries/           # 9 E2E test scenarios
      requirements/
      design/
      scaffold/
      deploy/
      implement/
      document/
      qa/
      release/
      rai/
    results/            # Test run results (JSON)
  config/               # Configuration schema and profiles
  docs/
    specs/              # Architecture specifications
    plans/              # Implementation plans
    adr/                # Architecture Decision Records
    api/                # API documentation
    agent-inventory.md
    skill-inventory.md
    orchestrator-states.md
    placeholder-mapping.md
  .mcp.json             # MCP server configuration
  harness-config.yml    # Project configuration
  AGENTS.md             # Agent context for AI sessions
  README.md
```

---

## 10. Migration Plan

### Remove (Python Evaluation Layer)

| Path | Reason |
|------|--------|
| `orchestrator/` | Entire directory — planner, generator, evaluator, state machine all replaced by agents |
| `bench/graders/` | Entire directory — code + LLM graders replaced by reviewer agents |
| `bench/engine/` | Entire directory — scorer, provider, report, trend no longer needed |
| `tools/run_benchmark.py` | User never runs Python; canary tests run via agents |
| `pyproject.toml` | No Python packaging needed |
| `tests/orchestrator/` | Tests for removed orchestrator module |
| `tests/bench/test_code_graders.py` | Tests for removed code graders |
| `tests/bench/test_llm_graders.py` | Tests for removed LLM graders |
| `tests/bench/test_run_benchmark.py` | Tests for removed benchmark runner |

### Keep

| Path | Reason |
|------|--------|
| `.github/plugin/agents/` | THE agent system — 18 agent definitions |
| `.github/plugin/skills/` | Domain knowledge — 12 skill definitions |
| `bench/canaries/` | E2E test scenarios — 9 canary specs |
| `docs/` | Specifications, plans, architecture docs |
| `config/` | Configuration schema and profiles |
| `README.md` | Project documentation |
| `AGENTS.md` | AI session context persistence |
| `.mcp.json` | MCP server configuration |

### Create

| Path | Purpose |
|------|---------|
| `bench/results/` | Directory for canary test run results (JSON) |

---

## 11. Key Design Principles

1. **Agents evaluate, not code** — Quality judgment comes from the 8 QA reviewer agents, not from keyword matchers or AST parsers.

2. **Canaries = E2E integration tests** — Canary specs validate "does the harness work?" not "which model is better?" There is no model comparison feature.

3. **No Python in production** — The Harness agent orchestrates everything. No Python scripts, no CLI tools, no orchestrator module.

4. **User stays in agent flow** — No terminal, no scripts, no JSON files. Users make strategic decisions at phase transitions.

5. **Structured reviewer output** — All reviewers emit YAML with score/verdict/findings for consistency and debuggability.

6. **Feedback loops, not one-shot** — Failed evaluations loop back to worker agents for revision (max 3 rounds) before escalating to the user.

7. **Git-native results** — Test results stored as JSON files in the repo, not in external databases or services.
