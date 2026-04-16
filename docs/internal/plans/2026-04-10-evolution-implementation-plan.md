# SDLC Harness Evolution — Implementation Plan

**Version:** 1.0.0
**Date:** 2026-04-10
**Target Repo:** sdlc-harness (Dongbumlee/sdlc-harness)
**Working Branch:** evo
**Merge Target:** dev
**Spec Reference:** docs/specs/2026-04-10-sdlc-harness-spec.md
**Research Reference:** docs/specs/2026-04-10-sdlc-harness-research-analysis.md

---

## Overview

We are building a **Copilot-native, benchmark-driven, multi-cloud SDLC harness framework**. The harness orchestrates 18 agents across 9 SDLC phases, uses a 3-agent meta-layer (Planner → Generator → Evaluator), and includes a comprehensive evaluation system with canary-based benchmarking, multi-strategy graders, and CI-gated regression detection.

This plan covers 4 phases with 17 tasks total, taking the current sdlc-harness from its Azure/Python-locked state to a config-driven, benchmark-instrumented, orchestrated system.

---

## Phase 1: Architecture + Agent Authoring (Weeks 1–3)

### Task 1.1: Agent Organization & Standardization

**Scope:** Audit and organize all 18 agents (1 orchestrator + 8 phase workers + 8 QA reviewers + 1 standalone reviewer). Document role assignments, validate phase mappings against the spec's `sub_agents_by_phase` structure, and ensure each agent has consistent metadata (role_type, capabilities, tool_access, skills).

**Deliverables:**
- Agent inventory document mapping each agent to its role_type, phase(s), and skills
- Updated agent files with consistent frontmatter/metadata across `vscode-extension/` and `.github/plugin/`
- Validated phase-to-agent mapping matching spec §1 (Architecture) sub_agents_by_phase

**Acceptance Criteria:**
- All 18 agents enumerated and classified by role_type
- Every agent has documented: purpose, phase assignment, skill dependencies, tool requirements
- No orphaned agents (agents not referenced by any phase)
- Agent metadata is consistent between vscode-extension/ and .github/plugin/ copies

**Effort Estimate:** Medium (2–3 days)

---

### Task 1.2: Dual-Directory Consolidation

**Scope:** Resolve the divergence between `vscode-extension/agents/` + `vscode-extension/skills/` and `.github/plugin/agents/` + `.github/plugin/skills/`. Establish a single source of truth with a CI check that detects drift.

**Deliverables:**
- Diff report of current divergences between the two directories
- Consolidated agent/skill content (reconcile any differences)
- CI check script (shell or GitHub Action) that fails if directories diverge
- Documentation of the canonical-source convention

**Acceptance Criteria:**
- `diff -r` between the two directories produces zero differences for agent/skill content
- CI check runs on every PR and blocks merge if drift is detected
- Contributing guide updated with the single-source convention

**Effort Estimate:** Medium (2–3 days)

---

### Task 1.3: Skill Standardization

**Scope:** Standardize all 12 skills against the spec's skill schema. Validate phase assignments, ensure each skill's `Used By` agents are correct, and confirm stack-specific skills are properly tagged.

**Deliverables:**
- Skill inventory table matching spec §2 (Skill Reference) taxonomy
- Updated skill files with consistent structure (trigger, scope, phases, inputs, outputs)
- Validated skill-to-agent and skill-to-phase mappings
- Stack-specific skill pack documentation (Azure pack implemented, AWS/GCP planned)

**Acceptance Criteria:**
- All 12 skills documented with scope, phases, and consuming agents
- 3 Azure-specific skills correctly tagged as stack-specific
- No skill referenced by an agent that doesn't exist
- No agent referencing a skill that doesn't exist

**Effort Estimate:** Medium (2–3 days)

---

### Task 1.4: Agent Behavior Verification

**Scope:** Diff-test to verify that no behavioral regression was introduced by the standardization work in Tasks 1.1–1.3. Compare agent prompt content before and after changes.

**Deliverables:**
- Snapshot of pre-standardization agent prompts (git baseline)
- Diff report showing only structural/metadata changes, not behavioral changes
- Verification that generated Copilot `.agent.md` output is functionally identical

**Acceptance Criteria:**
- Core prompt content (system instructions, phase context) is unchanged
- Structural changes (metadata, frontmatter, formatting) are documented
- No agent's behavioral instructions were altered without explicit justification

**Effort Estimate:** Small (1–2 days)

---

## Phase 2: Configuration System (Weeks 3–5)

### Task 2.1: harness-config.yml Schema & Profiles

**Scope:** Define the `harness-config.yml` JSON Schema and create pre-built profiles for common stacks. Schema covers: project, organization, stack, cloud, cicd, evaluation, distribution, orchestrator, libraries, and templates. All MCP servers are mandatory — hard-stop on failure.

**Deliverables:**
- `harness-config.schema.json` — JSON Schema for validation
- Profile files: `profiles/azure-python.yml`, `profiles/azure-dotnet.yml`, `profiles/aws-node.yml`
- Schema documentation with field descriptions and valid values
- MCP server manifest with hard-stop/warn classification per profile

**Acceptance Criteria:**
- Schema validates all example profiles without errors
- Each profile specifies: stack, cloud, cicd, evaluation, distribution sections
- MCP readiness check enforces hard-stop for awesome-copilot; GitHub MCP degrades gracefully _(updated per 0e41994: GitHub MCP hard-stop removed)_
- Profiles are composable (base + override pattern)

**Effort Estimate:** Medium (3–4 days)

---

### Task 2.2: Bootstrap Pipeline with Profile System

**Scope:** Implement the bootstrap sequence: config load → profile selection → workspace initialization → workspace file generation → verification. Support both interactive wizard and `--profile` flag modes.

**Deliverables:**
- Bootstrap script/CLI that reads `harness-config.yml` or runs interactive wizard
- Profile selection logic with inheritance (profile → base → defaults)
- Workspace initialization implementation (probe awesome-copilot; GitHub MCP optional with graceful degradation) _(updated per 0e41994)_
- Generated `copilot-instructions.md` from template with placeholder filling

**Acceptance Criteria:**
- `harness init --profile azure-python` produces a valid workspace in under 30 seconds
- `harness init` (no args) launches interactive wizard and produces equivalent output
- Workspace initialization correctly identifies unavailable servers: awesome-copilot blocks; GitHub MCP degrades gracefully _(updated per 0e41994)_
- Generated `copilot-instructions.md` has all `{{PLACEHOLDER}}` tokens replaced

**Effort Estimate:** Large (4–5 days)

---

### Task 2.3: Config-Driven Template Conversion

**Scope:** Convert all hardcoded Azure/Python references in agents, skills, and templates to config-driven templates. Use `harness-config.yml` values to select cloud-specific skills, stack-specific tooling, and CI/CD platform.

**Deliverables:**
- Templatized versions of `copilot-instructions.md`, `reference-catalog.md`, and key agent files
- Template engine integration (Jinja2 or equivalent) for config-driven generation
- Migration guide for existing Azure/Python users

**Acceptance Criteria:**
- Changing `cloud.provider` from `azure` to `aws` in config produces valid AWS-specific output
- Changing `stack.backend.language` from `python` to `dotnet` produces valid .NET-specific output
- No hardcoded Azure/Python strings remain in template files
- Existing Azure/Python users see identical output when using `azure-python` profile

**Effort Estimate:** Large (4–5 days)

---

## Phase 3: Evaluation System (Weeks 4–7)

### Task 3.1: Benchmarking Directory Structure

**Scope:** Create the `bench/` directory with the canonical subdirectory structure for canaries, scenarios, graders, and scoring.

**Deliverables:**
- `bench/canaries/` — canary definitions and mutation configs
- `bench/scenarios/` — benchmark scenario definitions (e.g., canary-54, full-sdlc)
- `bench/graders/` — code-based and LLM-based grader implementations
- `bench/scoring/` — scoring engine, aggregation, and trend storage
- `bench/README.md` — directory structure documentation

**Acceptance Criteria:**
- Directory structure matches spec §5 (Evaluation & Benchmarking) architecture
- Each subdirectory has a README explaining its purpose
- `bench/` is importable as a Python package (or structured for the chosen runtime)

**Effort Estimate:** Small (1–2 days)

---

### Task 3.2: Canary System v2 Schema

**Scope:** Define a structured YAML schema for the 54 canaries, replacing the current flat keyword-matching approach. Each canary gets: severity, category, difficulty tier, detection signals, and expected findings.

**Deliverables:**
- `bench/canaries/canary-schema.yaml` — YAML schema definition
- 54 canary definition files converted to structured format
- Canary metadata: severity (critical/high/medium/low), category (8 reviewer domains), difficulty (easy/medium/hard/expert)
- Detection signal definitions (keyword, AST pattern, LLM rubric)

**Acceptance Criteria:**
- All 54 canaries have valid YAML definitions conforming to schema
- Each canary specifies at least one detection signal
- Difficulty distribution is balanced across tiers
- Schema validates all canary files without errors

**Effort Estimate:** Medium (3–4 days)

---

### Task 3.3: Code-Based Graders

**Scope:** Implement deterministic code-based graders that use real tools (linters, type checkers, coverage tools, security scanners, schema validators) to grade phase output.

**Deliverables:**
- Lint grader: runs ruff/eslint/golangci-lint and scores based on violation count/severity
- Typecheck grader: runs pyright/tsc and scores based on error count
- Coverage grader: runs pytest-cov/vitest and scores based on coverage percentage
- Security grader: runs bandit/semgrep and scores based on finding severity
- Schema grader: validates JSON artifacts against defined schemas

**Acceptance Criteria:**
- Each grader produces a standardized score (0–10 scale) and findings list
- Graders are composable (phase evaluation combines multiple graders)
- Graders run in under 60 seconds for typical project sizes
- Grader output conforms to the evaluation report JSON schema

**Effort Estimate:** Large (5–7 days)

---

### Task 3.4: LLM-as-Judge Graders

**Scope:** Implement model-based graders that use LLM evaluation for subjective quality dimensions: rubric scoring, pairwise comparison, and canary detection.

**Deliverables:**
- Rubric grader: scores output against a structured rubric (e.g., design completeness, code quality)
- Comparison grader: pairwise comparison between current and baseline outputs
- Detection grader: LLM-based canary detection for bugs that evade keyword matching

**Acceptance Criteria:**
- Rubric grader produces reproducible scores (within ±0.5 on repeated runs)
- Comparison grader correctly identifies regressions vs. improvements
- Detection grader catches at least 80% of "hard" canaries that keyword matching misses
- All graders include cost tracking (tokens used, API cost)

**Effort Estimate:** Large (5–7 days)

---

### Task 3.5: Scoring Engine & Trend Tracking

**Scope:** Build the aggregation engine that combines grader scores into phase scores and overall project scores. Implement results storage and regression detection.

**Deliverables:**
- Scoring engine: weighted aggregation of code-based and model-based scores per phase
- Results storage: JSON files in `bench/scoring/results/` with run metadata
- Trend tracking: compare current run against historical baselines
- Regression detection: flag score drops exceeding `regression_threshold`

**Acceptance Criteria:**
- Scoring engine produces the full benchmark report JSON matching spec §5.4 schema
- Results are stored with run_id, model, timestamp, and full per-phase breakdown
- Regression detection correctly flags drops > 0.5 points from baseline
- Trend data supports at least 100 historical runs

**Effort Estimate:** Medium (3–4 days)

---

### Task 3.6: GitHub Actions CI-Gated Regression

**Scope:** Create a GitHub Actions workflow that runs benchmarks on PRs touching agents or skills, compares against baseline, and posts results as PR comments.

**Deliverables:**
- `.github/workflows/benchmark.yml` — PR-triggered and weekly scheduled benchmark runs
- Baseline management: store and update baseline scores
- PR comment integration: post benchmark results as formatted PR comments
- Gate logic: block merge if regression exceeds threshold

**Acceptance Criteria:**
- PR changes to `agents/**` or `skills/**` trigger benchmark run
- Weekly scheduled run updates baseline scores
- PR comments show per-phase scores, delta from baseline, and pass/fail verdict
- Merge is blocked if any phase score regresses below threshold

**Effort Estimate:** Medium (3–4 days)

---

## Phase 4: 3-Agent Orchestrator (Weeks 7–10)

### Task 4.1: Deterministic Orchestrator State Machine

**Scope:** Define the orchestrator's state machine: states (idle, planning, generating, evaluating, retrying, replanning, complete, failed), transitions, and phase ordering rules.

**Deliverables:**
- State machine definition (states, transitions, guards)
- Session management: start, checkpoint, resume, complete
- Retry logic: per-phase retry counter (max 3), escalation to replan (max 2)
- Progress tracking: structured progress file updated after each state transition

**Acceptance Criteria:**
- State machine handles all happy-path and error-path transitions
- Session can be checkpointed and resumed without data loss
- Retry counter correctly escalates FAIL → retry (3x) → CRITICAL_FAIL → replan
- Progress file provides human-readable and machine-parseable status

**Effort Estimate:** Large (5–7 days)

---

### Task 4.2: Planner Agent (Evolution of @Harness)

**Scope:** Evolve the current `@Harness` coordinator into the Planner role. Narrow scope to strategic decomposition: turn user intent into an ordered execution plan with phase selection, dependency ordering, and skip logic.

**Deliverables:**
- Planner agent definition with updated prompts focused on planning only
- Execution plan JSON schema matching spec §1.2 (Planner Agent) output format
- Decision protocol: intent-type → phase-selection mapping
- Re-planning logic: triggered by CRITICAL_FAIL or scope mismatch

**Acceptance Criteria:**
- Planner produces valid execution plan JSON for all 5 intent types (new project, feature, bug fix, docs, infra)
- Phase dependencies are correctly ordered
- Skip logic correctly omits phases based on intent type and project context
- Re-planning produces a revised plan that addresses the failure feedback

**Effort Estimate:** Large (5–7 days)

---

### Task 4.3: Generator Coordinator with Sub-Agent Delegation

**Scope:** Implement the Generator as a coordinator that delegates to phase-specific sub-agents. Handles context injection, artifact collection, and the context-reset protocol between phases.

**Deliverables:**
- Generator coordinator implementation with sub-agent dispatch
- Context injection: phase scope, constraints, prior artifacts, evaluator feedback (on retry)
- Artifact collection: validate output against phase-specific schemas
- Context reset: fresh LLM context per phase, only structured artifacts bridge gaps

**Acceptance Criteria:**
- Generator correctly dispatches to the right sub-agent for each phase
- Context injection includes all required inputs per the spec §3 (Per-Phase Workflow) tables
- Artifact validation catches malformed or incomplete outputs before passing to Evaluator
- Context reset verified: no conversation history leaks between phases

**Effort Estimate:** Large (5–7 days)

---

### Task 4.4: Evaluator Integration with Graders

**Scope:** Connect the Evaluator agent to the `bench/` graders. The Evaluator invokes code-based and model-based graders per phase, aggregates scores, and produces the evaluation report JSON that drives the orchestrator's pass/fail/retry decisions.

**Deliverables:**
- Evaluator agent that invokes graders from `bench/graders/`
- Per-phase grader configuration: which graders run for each phase
- Verdict logic: PASS (≥7.0), FAIL (5.0–6.9), CRITICAL_FAIL (<5.0) with dimension minimums
- Feedback generation: actionable instructions for Generator (on FAIL) and Planner (on CRITICAL_FAIL)

**Acceptance Criteria:**
- Evaluator produces valid evaluation report JSON matching spec §1.4 (Evaluator) schema
- Correct graders are invoked for each phase
- Verdict logic correctly applies dimension minimums (Security ≥8, others ≥7)
- Feedback is specific and actionable (not generic "improve quality" messages)

**Effort Estimate:** Large (5–7 days)

---

## Dependencies & Critical Path

```
Phase 1 ──────────────────────────────────────────────────────────
  Task 1.1 ─────┐
  Task 1.2 ─────┤── Task 1.4 (verification requires 1.1–1.3 complete)
  Task 1.3 ─────┘

Phase 2 ──────────────────────────────────────── (starts Week 3)
  Task 2.1 ──── Task 2.2 ──── Task 2.3
  (schema)     (bootstrap)    (templates)

Phase 3 ──────────────────────────────────────── (starts Week 4)
  Task 3.1 ──── Task 3.2 ─┬── Task 3.3 ─┬── Task 3.5 ── Task 3.6
  (directory)  (canaries)  └── Task 3.4 ─┘   (scoring)    (CI)
                            (graders)

Phase 4 ──────────────────────────────────────── (starts Week 7)
  Task 4.1 ─┬── Task 4.2 ─┐
  (state)    │             ├── Task 4.4 (needs 4.2, 4.3, and Phase 3 graders)
             └── Task 4.3 ─┘
             (generator)
```

**Critical path:** Task 2.1 → 2.2 → 2.3 → 3.1 → 3.2 → 3.3/3.4 → 3.5 → 3.6 → 4.1 → 4.2/4.3 → 4.4

---

## Summary

| Phase | Tasks | Key Deliverables | Weeks |
|---|---|---|---|
| **Phase 1:** Architecture + Agent Authoring | 4 | Agent inventory, directory consolidation, skill taxonomy, behavior verification | 1–3 |
| **Phase 2:** Configuration System | 3 | Config schema, bootstrap pipeline, config-driven templates | 3–5 |
| **Phase 3:** Evaluation System | 6 | bench/ directory, canary v2, code + LLM graders, scoring engine, CI gate | 4–7 |
| **Phase 4:** 3-Agent Orchestrator | 4 | State machine, Planner agent, Generator coordinator, Evaluator integration | 7–10 |
| **Total** | **17** | | **10 weeks** |

---

## Risk Mitigation

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| LLM-as-Judge graders produce inconsistent scores | Scoring reliability undermined | Medium | Calibrate with human baselines; use temperature=0; run 3x and average |
| Agent standardization introduces behavioral regression | User-facing quality drop | Medium | Task 1.4 diff-test catches regressions before merge |
| Config schema doesn't cover all stack/cloud combinations | Users can't adopt new profiles | Low | Start with 3 profiles; schema is extensible by design |
| MCP server availability varies across environments | Bootstrap fails for some users | Medium | Hard-stop only for critical servers; graceful degradation for optional |
| Canary v2 migration breaks existing benchmark baselines | Historical trend data lost | Low | Maintain v1 compatibility mode during transition; store v1 baselines separately |
| Phase 3 (Evaluation) delays block Phase 4 (Orchestrator) | Overall timeline extends | Medium | Phase 4 Tasks 4.1–4.3 can start in parallel; only 4.4 needs Phase 3 graders |

---

## Scope Boundaries

| In Scope | Out of Scope |
|---|---|
| 18-agent organization and standardization | New agent creation (use existing agents) |
| harness-config.yml with 3 profiles (azure-python, azure-dotnet, aws-node) | Full AWS/GCP skill pack implementation (planned, not in this plan) |
| bench/ directory with canary v2, code-based and LLM graders | Harness IR / multi-platform generation (Cursor, Claude Code, Amplifier targets) |
| Scoring engine with trend tracking and CI gate | AI-SDLC / Open Agent Spec interoperability adapters |
| 3-agent orchestrator (Planner, Generator, Evaluator) | Interactive wizard UI (CLI-only in this plan) |
| GitHub Copilot as sole platform target | Multi-platform distribution (deferred to future plan) |
| Config-driven template conversion | Fully automated canary generation via code mutation |
| MCP readiness check (awesome-copilot hard-stop; GitHub MCP graceful degradation) | Custom MCP server development |
