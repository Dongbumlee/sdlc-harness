# Orchestrator State Model

How the Harness agent drives work through the SDLC. This document describes the
**actual** orchestration implemented in `com.github.copilot/agents/harness.agent.md`
— the phase loop, validation gates, and failure handling. For the design rationale
(generator–evaluator separation, adversarial QA), see `docs/harness-design.md`.

## State diagram

```
                          ┌─────────────────────────────┐
                          │         INITIALIZE          │  (first run only)
                          │  MCP readiness · bootstrap  │   workspace files
                          └──────────────┬──────────────┘
                                         ▼
┌─────────┐    ┌──────────┐    ┌──────────────────┐    ┌──────────┐    ┌──────────┐
│ REQUEST │───▶│ DISPATCH │───▶│       WORK       │───▶│ VALIDATE │───▶│ ADVANCE  │
└─────────┘    └──────────┘    │  (worker agent,  │    │ (self-   │    │ (next    │
     │                         │  self-evaluation │    │  eval +  │    │  phase)  │
     │                         │  before handoff) │    │ harness  │    └────┬─────┘
     │                         └──────────────────┘    │ review)  │         │
     │                                                 └───┬────┘         │
     │                                                     │ issues?       │ all phases
     │                                                     ▼ done?         ▼ done
     │                                              ┌────────────┐   ┌──────────┐
     │                                              │  FIX LOOP  │   │ COMPLETE │
     │                                              │ (≤3 rounds)│   └──────────┘
     │                                              └─────┬──────┘
     │                                                    │ still failing
     │                                                    ▼
     │                                              ┌────────────┐
     └─────────────────────────────────────────────▶│  BLOCKED   │◀── CRITICAL_FAIL
                                                    │ (user      │    or 3 rounds
                                                    │  decision) │    exhausted
                                                    └────────────┘

Phase 6 takes a detour through the QA gate:

   VALIDATE ──▶ QA_GATE ──▶ PASS ──▶ ADVANCE
                   │
                   ▼ FAIL → 3-tier escalation (auto-retry → user-confirmed
                             retry → user decision), max 3 QA rounds
```

## States

### REQUEST
- Entry point for every run: user message, issue, or task description.
- Harness maps the request to one or more of the 9 SDLC phases.
- Shortcuts: bug fixes may skip the Analyst (`Implementer → QA Coordinator`);
  documentation-only changes go straight to the Documenter.

### INITIALIZE (first run only)
- **MCP server readiness check** — verifies the 7 configured MCP servers.
- **Bootstrap workspace files** if missing (templates, checklists, reference catalog).
- **Fill placeholders** in bootstrapped files. Never blocks the pipeline on a
  single MCP failure — workers degrade gracefully to local reads.

### DISPATCH
- Harness delegates to the phase's worker agent via subagents, using the
  [phase-to-agent mapping](#phase-to-agent-mapping). Workers execute; the
  Harness synthesizes their outputs.

### WORK
- The worker agent performs the phase task (requirements, scaffolding, code, docs…).
- Every worker runs a **domain-specific self-evaluation checklist** before
  reporting complete (template fidelity, acceptance-criteria coverage, no
  placeholders, link integrity, etc.).

### VALIDATE
- Harness reviews the worker's output against the phase's acceptance criteria.
- Issues found → **FIX LOOP**: send findings back to the worker, up to 3 rounds.
  Fixes applied without re-verification are not accepted — every phase
  transition is an evaluation point.
- Still failing after 3 rounds → **BLOCKED**.

### QA_GATE (Phase 6)
- Harness delegates to the **QA Coordinator**, specifying which reviewers to
  invoke per the [phase routing table](#phase-specific-qa-routing). Not all
  phases need all reviewers; `implement` and `qa` phases get the full set.
- The Coordinator dispatches reviewers **in parallel**, each in its own context
  window, and aggregates their structured YAML output:
  - **Scoring:** composite = `(security × 1.5 + Σ others) / 8.5`
  - **Hard-fail rules:** composite < 7, security < 8, or any Critical finding
  - **Finding scoping:** only requirement-tied findings affect score/verdict;
    out-of-scope hardening is recorded as suggestions, never as failures
- On `FAIL` verdict, the 3-tier escalation applies:
  1. **Auto-route** — forward the QA feedback template to the Implementer, then
     targeted re-review of failed domains only.
  2. **User-confirmed retry** — present score progression; retry with targeted
     guidance if the user agrees.
  3. **User decision** — present full results; the user chooses override,
     manual fix, or abandon. Hard limit: 3 QA rounds total.

### ADVANCE
- Move to the next requested phase. Two automatic rules:
  - **ADR generation:** a Phase 2 design proposal is automatically handed to the
    Documenter to save as an ADR in `docs/adr/` before implementation begins.
    (Phase 1B requirements specs are NOT ADRs.)
  - **Quality instruction compliance** is verified after every implementation
    phase via the QA Coordinator.

### COMPLETE
- All requested phases finished and validated. Harness synthesizes results into
  a coherent summary, including the QA improvement trajectory when applicable
  (e.g., "QA completed in 2 rounds. Composite: 6.4 → 8.2").

### BLOCKED
- Reached on `CRITICAL_FAIL`, 3 exhausted fix/QA rounds, or an unrecoverable
  worker error. Harness presents the full results and requires a user decision.
  Blockers are filed as GitHub issues for tracking. The run resumes only on
  explicit user direction.

## Phase-to-agent mapping

| Phase | Agent |
|---|---|
| 1: Requirements | Analyst (Discovery + Spec modes) |
| 2: Design | Analyst (Design mode) — only after the requirements spec is approved |
| 3: Repo Structure & CI/CD | Scaffolder |
| 3+8: Deployment & Infrastructure | Deployer |
| 4: Implementation & Tests | Implementer |
| 5: Documentation | Documenter |
| 6: QA Activities | QA Coordinator |
| 7: RAI Review | RAI Reviewer |
| 8-9: Release & Publish | Release Manager |

## Phase-specific QA routing

| Phase | Reviewers invoked |
|---|---|
| requirements | Requirements Completeness, Architecture |
| design | Architecture, Security |
| scaffold | Architecture, Code Quality, Deployment Readiness |
| implement | All 9 (full review) |
| document | Code Quality |
| qa | All 9 (full review) |
| deploy | Deployment Readiness, Security, Azure Compliance |
| rai | Security, LLM Behavior |
| release | Deployment Readiness, Code Quality |

## Transitions

| From | To | Trigger |
|---|---|---|
| REQUEST | INITIALIZE | First run (workspace not bootstrapped) |
| REQUEST | DISPATCH | Phase(s) identified |
| INITIALIZE | DISPATCH | MCP check passed, workspace ready |
| DISPATCH | WORK | Worker agent invoked |
| WORK | VALIDATE | Worker reports complete (self-evaluation done) |
| VALIDATE | FIX LOOP | Issues found, rounds remaining |
| VALIDATE | ADVANCE / QA_GATE | Phase output accepted |
| FIX LOOP | WORK | Findings sent back to worker |
| FIX LOOP | BLOCKED | 3 rounds exhausted |
| VALIDATE (phase 6) | QA_GATE | Delegate to QA Coordinator |
| QA_GATE | ADVANCE | Verdict PASS |
| QA_GATE | FIX LOOP | Verdict FAIL, escalation tier 1–2, rounds remaining |
| QA_GATE | BLOCKED | CRITICAL_FAIL, or tier 3 reached |
| ADVANCE | DISPATCH | More phases remain |
| ADVANCE | COMPLETE | All requested phases done |
| BLOCKED | DISPATCH | User directs resume/retry |

## Canary mode

Canary mode (`sdlc-canary-runner` skill) exercises this exact state model end to
end: each canary spec is routed phase → agent, outputs are graded, and results
are written to `bench/results/`. Same agents, same gates — only the input comes
from the spec's `prompt` field instead of the user.

## See also

- `com.github.copilot/agents/harness.agent.md` — the authoritative orchestration prompts
- `docs/harness-design.md` — why the model is built this way (Anthropic harness research)
- `docs/workflow-guide.md` — contributor-facing workflow walkthrough
- `docs/agent-inventory.md` — generated inventory of all 19 agents and 16 skills
