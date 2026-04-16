# SDLC Harness Competitive Positioning & Go-To-Market Readiness

## Goal

Transform SDLC Harness from an Azure-specific prototype into a cloud-agnostic, community-adoptable harness that demonstrably accelerates software engineering — delivered as a GitHub Copilot plugin.

## Background

The SDLC Harness currently ships 18 agents, 15 skills, and 11 canary specs in a fully implemented v2 architecture. However, the harness is Azure-centric — the deployer, compliance reviewer, and several skills are tightly coupled to Azure. This limits adoption to Azure users and obscures the harness's core value: full-lifecycle SDLC orchestration.

Industry analysts (Forbes, PwC, Microsoft, HCLTech) all validate "Agentic SDLC" as the next frontier. No dominant open-source framework owns full-lifecycle SDLC orchestration with real infrastructure integration. This is the window.

## Strategic Position

| Layer | Competitors | SDLC Harness's Edge |
|-------|-------------|---------------------|
| Benchmarks | SWE-bench, DevBench | Not competing — canaries are internal engineering hygiene |
| Coding agents | OpenHands, Claude Code, Devin | Not competing — task-level tools, not lifecycle orchestrators |
| Multi-agent frameworks | LangGraph, CrewAI, MetaGPT | Not competing — generic orchestration infrastructure |
| Full-lifecycle SDLC orchestration | MetaGPT (research-only), StrongDM (proprietary), GitLab+TCS (enterprise) | The only open-source, Copilot-native, production-grade SDLC harness with real infrastructure integration |

**Competitive thesis:** Nobody else offers an open-source, installable-in-one-command harness that orchestrates 18 specialized agents through 9 SDLC phases with adversarial QA gates and real cloud integration. MetaGPT simulates; SDLC Harness orchestrates.

## Architecture

### Cloud-Agnostic Core

The big refactor separates the harness into a **cloud-agnostic core** and **pluggable cloud packs**.

**Core (cloud-agnostic) retains:**

- Harness orchestrator agent (phase routing, feedback loops, escalation)
- QA Coordinator + 6 universal reviewers (Architecture, Code Quality, Security, Test Coverage, UX/A11y, LLM Behavior)
- Analyst, Scaffolder, Implementer, Documenter, Release Manager agents
- All evaluation gates (weighted scoring, hard-fail thresholds, 3-tier escalation)
- Structured reviewer output format (YAML schema)
- Living Reference Catalog
- Canary testing framework
- Skills: `reviewer-output-format`, `canary-runner`, `project-qa`, `qa-bug-checklist`, `code-quality`, `architecture-review`, `security-review`, `project-manifest`, `reference-catalog`

### Pluggable Cloud Packs

**Azure Pack (first pack, extracted from current codebase):**

- Deployer agent (Azure Bicep/AVM specific)
- Azure Compliance Reviewer agent
- Deployment Readiness Reviewer (cloud-specific checks extracted)
- Skills: `azure-deployment`, `cosmos-repository`, `blob-storage`
- `.github/instructions/` quality files that reference Azure patterns
- MCP servers: Azure MCP, Azure DevOps MCP, Microsoft Learn MCP

**The pluggable pattern:**

- Cloud packs live under `packs/` (e.g., `packs/azure/`, `packs/aws/`, `packs/gcp/`)
- Each pack contributes: deployer agent, compliance reviewer, cloud-specific skills, MCP config
- `workspace-init` skill asks "Which cloud?" and loads the appropriate pack
- Core agents reference cloud pack content via the project manifest, not hardcoded

### Pack Directory Structure

```
packs/
  azure/
    agents/
      deployer.agent.md
      azure-compliance-reviewer.agent.md
    skills/
      azure-deployment/
      cosmos-repository/
      blob-storage/
    mcp-config/
  _template/          # Skeleton for community contributors
```

## Requirements-to-Specification Capability

### The Problem

Today the Analyst asks 3-5 clarifying questions and immediately jumps to proposing architecture. Phase 1 (Requirements) and Phase 2 (Design) are collapsed into a single agent pass with no intermediate specification artifact. This means the Analyst is designing before it truly understands what the user wants — producing "AI's best guess at what you meant" rather than "exactly what you told me to build."

### The Two-Phase Model

#### Phase 1A: Collaborative Discovery (Iterative)

The Analyst becomes a **discovery partner**, not a question machine:

- Asks questions **one at a time** — no questionnaire dumps
- Explores purpose, constraints, success criteria, edge cases, user workflows
- Restates understanding back to the user after each answer ("So what I'm hearing is...")
- Proposes multiple choice options when possible to make decisions faster
- Continues iterating until the user explicitly says **"this is what I want to build"**
- No fixed question limit — the process takes as long as it takes
- The Analyst does NOT propose solutions during this phase — it only listens and clarifies

**Exit gate:** User explicitly approves the requirements summary. No auto-progression.

#### Phase 1B: Requirements Specification

Once the user confirms the requirements, the Analyst produces a formal spec:

- Structured document with FR/NFR, acceptance criteria, constraints, scope boundaries
- Every requirement is testable and traceable
- The spec is the **contract** — downstream agents implement exactly what it says, nothing more
- User reviews and approves the spec before Phase 2 begins

**Output artifact:** Standalone Requirements Spec (`docs/specs/REQ-XXX-<topic>.md`)

#### Phase 2: Design (Unchanged Conceptually)

The Design Analyst takes the approved spec and produces an ADR. The spec constrains the design — no creative reinterpretation of what the user wanted.

### Agent Refactoring

| Phase | Agent | Output Artifact | Reviewer Gate |
|-------|-------|-----------------|---------------|
| Phase 1: Requirements | **Analyst** (refocused) | Standalone Requirements Spec (`docs/specs/REQ-XXX-<topic>.md`) | Requirements Completeness Reviewer (new) |
| Phase 2: Design | **Design Analyst** (new or Analyst Phase 2 mode) | ADR (`docs/adr/ADR-XXX-<topic>.md`) referencing the Requirements Spec | Architecture + Security Reviewers |

### Requirements Spec Artifact Structure

- Problem statement and business context
- Goals / Non-goals / Out-of-scope
- Functional requirements (FR-1, FR-2…) — each with a testable acceptance criterion
- Non-functional requirements (NFR-1, NFR-2…) — measurable targets
- Constraints and assumptions
- User stories (optional, if applicable)
- Open questions

### New Skill: `sdlc-requirements-discovery`

Guides the Analyst through the collaborative discovery process:

- Elicitation patterns (one question at a time, restate understanding)
- When to use multiple choice vs. open-ended questions
- How to probe for non-obvious requirements (edge cases, error scenarios, scale)
- The explicit approval checkpoint pattern
- Requirements document template for Phase 1B output

### New Reviewer: Requirements Completeness Reviewer

- Every FR has a testable acceptance criterion
- No ambiguous language ("appropriate," "reasonable," "as needed")
- Non-functional requirements have measurable targets (not "fast" but "< 200ms p95")
- No scope gaps (requirements cover all stated goals)

### Traceability (Lightweight)

- Implementer references FR-N tags in code comments and commit messages
- Test Coverage Reviewer checks that each FR-N has at least one corresponding test
- Project manifest tracks FR → implementation file → test file mapping

### Competitive Significance

This is the feature that none of the competitors have:

- **MetaGPT** — The Product Manager generates a PRD from a one-line prompt, no iteration
- **ChatDev** — The CEO agent makes decisions without user collaboration
- **Coding agents** (OpenHands, Devin, Claude Code) — No requirements phase at all

An SDLC harness that actually collaborates on requirements before building — that's a genuine differentiator. It's the difference between "AI builds what it thinks you want" and "AI builds exactly what you told it to build."

## Community Infrastructure

| Asset | Purpose | Priority |
|-------|---------|----------|
| CONTRIBUTING.md | How to contribute agents, skills, cloud packs | Week 1 |
| Cloud pack template | Skeleton for community-contributed packs | Week 1 |
| Architecture diagram | Visual overview: core vs. cloud packs vs. agent roles | Week 1 |
| Issue templates | Bug report, feature request, new cloud pack proposal | Week 2 |
| Quick-start guide | "First 10 minutes" — install, init workspace, run first phase | Week 3 |

### README Overhaul

Slim down the current 920-line README into a short hero + quick start + architecture overview + links to breakout docs. Detailed content moves into separate files under `docs/`.

### Contributing a Cloud Pack

The contribution path is explicit: Fork, copy `packs/azure/` as template, replace deployer agent + compliance reviewer + cloud skills, submit PR. CONTRIBUTING.md includes a checklist for this workflow.

## Near-Term Sprint (Weeks 1-4)

### Week 1-2: Core/Pack Separation + Community Foundation

| Task | Description |
|------|-------------|
| Create `packs/` directory structure | `packs/azure/agents/`, `packs/azure/skills/`, `packs/azure/mcp-config/` |
| Move Azure-specific agents | Deployer to `packs/azure/agents/deployer.agent.md`, Azure Compliance Reviewer to `packs/azure/agents/` |
| Move Azure-specific skills | `azure-deployment`, `cosmos-repository`, `blob-storage` to `packs/azure/skills/` |
| Create cloud pack schema | `schemas/cloud-pack.schema.json` — defines what a pack must contain |
| Update workspace-init skill | Add "Which cloud?" prompt, load appropriate pack |
| Update Harness agent | Reference pack agents dynamically via project manifest instead of hardcoded `@deployer` |
| Create pack template | `packs/_template/` — skeleton for community contributors |
| Refactor Analyst agent into collaborative discovery mode | Phase 1A (iterative discovery) + Phase 1B (requirements spec output) |
| Create `sdlc-requirements-discovery` skill | Elicitation patterns, approval checkpoint, requirements document template |
| Create Requirements Completeness Reviewer agent | FR acceptance criteria, ambiguity detection, NFR measurability, scope gap checks |
| Add requirements spec template | `docs/specs/REQ-XXX-<topic>.md` template with FR/NFR structure and traceability tags |
| Write CONTRIBUTING.md | How to contribute agents, skills, and cloud packs |
| Write architecture overview doc | Core vs. packs vs. agent roles (with diagram) |
| Slim down README.md | Hero + quick start + architecture overview + links to docs |

### Week 3-4: Community Readiness + Demo

| Task | Description |
|------|-------------|
| Issue templates | Bug report, feature request, new cloud pack proposal |
| Quick-start guide | `docs/getting-started.md` — install, init, run first phase (10 min experience) |
| Demo walkthrough | Written end-to-end walkthrough: requirements to implemented app using the harness |
| Run internal canaries | Validate nothing broke during refactoring |
| Update canary specs | Ensure canaries work with the pack-based architecture |
| Marketplace listing | VS Code marketplace + Copilot Extensions catalog |
| Update CI workflows | Sync check and canary validation aware of `packs/` structure |

## Medium-Term Roadmap (Months 2-3)

| Item | Purpose |
|------|---------|
| AWS cloud pack | Doubles addressable audience (community or self-authored) |
| GCP pack stub | Signals platform ambition, invites contributors |
| Canary suite expansion | Pack-aware canaries validating each cloud pack independently |
| Blog post / announcement | LinkedIn article authored when ready |

## Success Metrics

### Near-Term (End of Week 4)

- Core harness runs end-to-end without any Azure-specific content loaded (cloud-agnostic validated)
- Azure pack loads cleanly as an add-on and all existing canaries pass
- A new user can go from `copilot plugin install` to running their first SDLC phase in under 10 minutes
- VS Code marketplace listing is live
- CONTRIBUTING.md + pack template exist and are clear enough for an external contributor to submit a cloud pack PR

### Medium-Term (End of Month 3)

- At least one community-contributed cloud pack (AWS or GCP)
- Demo walkthrough used as the primary adoption driver
- LinkedIn announcement published
- Internal canary suite expanded to validate each cloud pack independently

## Open Questions

- Cloud pack schema: what's the minimum viable contract a pack must satisfy?
- Deployment Readiness Reviewer: how much stays in core vs. moves to pack? Need to define the split boundary.
- MCP server configuration: how does pack-contributed MCP config merge with user's existing `mcp.json`?
- Marketplace listing: what screenshots and description best convey "SDLC orchestration" to someone browsing the catalog?
- Analyst split: Should the Analyst remain one agent with two modes (discovery vs. design), or split into two separate agents (Requirements Analyst + Design Analyst)?
