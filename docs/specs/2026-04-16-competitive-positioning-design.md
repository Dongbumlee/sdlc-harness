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
