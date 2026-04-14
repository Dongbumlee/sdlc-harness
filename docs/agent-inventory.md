# SDLC Harness — Agent Inventory

**Version:** 1.0.0
**Date:** 2026-04-11
**Source branch:** `evo`
**Total agents:** 19 (18 agent files + 1 dual-role)
**Total skills:** 12

> Generated from codebase exploration of `vscode-extension/agents/` and
> `vscode-extension/skills/*/SKILL.md`, cross-referenced against
> `docs/specs/2026-04-10-sdlc-harness-spec.md` §1 (`sub_agents_by_phase`).

---

## 1. Summary Table

| # | Agent File | Name | Role Type | Phase(s) | User-Invocable | Skills (from frontmatter/body) |
|---|---|---|---|---|---|---|
| 1 | `harness.agent.md` | Harness | Orchestrator | All (1–9) | Yes (entry point) | sdlc-workspace-init (via first-run) |
| 2 | `qa-coordinator.agent.md` | QA Coordinator | Orchestrator + Phase Worker | 6 | No | sdlc-code-quality, sdlc-security-review, sdlc-project-qa, sdlc-qa-bug-checklist (per spec) |
| 3 | `analyst.agent.md` | Analyst | Phase Worker | 1–2 | No | sdlc-workspace-init (per spec) |
| 4 | `scaffolder.agent.md` | Scaffolder | Phase Worker | 3 | No | sdlc-project-scaffolding, sdlc-project-manifest |
| 5 | `deployer.agent.md` | Deployer | Phase Worker | 3+8 | No | sdlc-azure-deployment |
| 6 | `implementer.agent.md` | Implementer | Phase Worker | 4 | No | sdlc-project-manifest, sdlc-cosmos-repository, sdlc-blob-storage |
| 7 | `documenter.agent.md` | Documenter | Phase Worker | 5 | No | sdlc-adr-authoring, sdlc-project-manifest (per spec) |
| 8 | `rai-reviewer.agent.md` | RAI Reviewer | Phase Worker | 7 | No | _(external: ai-prompt-engineering-safety-review via awesome-copilot)_ |
| 9 | `release-manager.agent.md` | Release Manager | Phase Worker | 8–9 | No | _(none — uses GitHub MCP directly)_ |
| 10 | `architecture-reviewer.agent.md` | Architecture Reviewer | QA Reviewer | 6 (sub) | No | sdlc-architecture-review |
| 11 | `azure-compliance-reviewer.agent.md` | Azure Compliance Reviewer | QA Reviewer | 6 (sub) | No | _(none in frontmatter — uses awesome-copilot for Bicep)_ |
| 12 | `code-quality-reviewer.agent.md` | Code Quality Reviewer | QA Reviewer | 6 (sub) | No | sdlc-code-quality |
| 13 | `security-reviewer.agent.md` | Security Reviewer | QA Reviewer | 6 (sub) | No | sdlc-security-review |
| 14 | `test-coverage-reviewer.agent.md` | Test Coverage Reviewer | QA Reviewer | 6 (sub) | No | _(none in frontmatter — references test-quality instruction files)_ |
| 15 | `ux-accessibility-reviewer.agent.md` | UX & Accessibility Reviewer | QA Reviewer | 6 (sub) | No | sdlc-project-qa |
| 16 | `llm-behavior-reviewer.agent.md` | LLM Behavior Reviewer | QA Reviewer | 6 (sub) | No | sdlc-project-qa, sdlc-security-review |
| 17 | `deployment-readiness-reviewer.agent.md` | Deployment Readiness Reviewer | QA Reviewer | 6 (sub) | No | sdlc-project-qa |
| 18 | `qa-bug-checklist-reviewer.agent.md` | QA Bug Checklist Reviewer | Standalone | On-demand | **Yes** | sdlc-qa-bug-checklist, sdlc-security-review, sdlc-azure-deployment |

### Agent Counts by Role Type

| Role Type | Count | Agents |
|---|---|---|
| Orchestrator | 2 | Harness, QA Coordinator (dual-role) |
| Phase Worker | 8 | Analyst, Scaffolder, Deployer, Implementer, Documenter, QA Coordinator (dual-role), RAI Reviewer, Release Manager |
| QA Reviewer (sub-agent) | 8 | Architecture, Azure Compliance, Code Quality, Security, Test Coverage, UX & Accessibility, LLM Behavior, Deployment Readiness |
| Standalone (user-invocable) | 1 | QA Bug Checklist Reviewer |

---

## 2. Skill Inventory

| # | Skill Directory | Name | Description | Used By (agents) |
|---|---|---|---|---|
| 1 | `sdlc-workspace-init` | Workspace Init | Bootstrap `.github/copilot-instructions.md`, MCP config, quality instruction files, prompt files | Harness (first-run), Analyst (per spec) |
| 2 | `sdlc-project-scaffolding` | Project Scaffolding | Scaffold project structures from templates with CI/CD, Docker, devcontainers | Scaffolder |
| 3 | `sdlc-project-manifest` | Project Manifest | Generate/read `.SDLC/project-manifest.md` for cross-agent pattern persistence | Scaffolder (write), Implementer, Documenter, Architecture Reviewer, Code Quality Reviewer, Deployer (read) |
| 4 | `sdlc-azure-deployment` | Azure Deployment | Bicep + AVM + azd infrastructure templates and deployment lifecycle | Deployer, QA Bug Checklist Reviewer |
| 5 | `sdlc-cosmos-repository` | Cosmos Repository | Azure Cosmos DB data access with the approved Cosmos DB library (Repository Pattern) | Implementer |
| 6 | `sdlc-blob-storage` | Blob Storage | Azure Blob/Queue operations with the approved Storage library | Implementer |
| 7 | `sdlc-adr-authoring` | ADR Authoring | Architecture Decision Records following SDLC + awesome-copilot patterns | Documenter |
| 8 | `sdlc-code-quality` | Code Quality | Code quality review with quality instruction files + awesome-copilot | Code Quality Reviewer, Implementer (per spec) |
| 9 | `sdlc-security-review` | Security Review | OWASP Top 10 + project-specific Azure security patterns | Security Reviewer, LLM Behavior Reviewer, QA Bug Checklist Reviewer |
| 10 | `sdlc-project-qa` | Project QA | Product-level QA checklist (10 categories, UX/a11y/LLM/data/errors/security/perf/deploy/ops) | UX & Accessibility Reviewer, LLM Behavior Reviewer, Deployment Readiness Reviewer, QA Coordinator (per spec) |
| 11 | `sdlc-qa-bug-checklist` | QA Bug Checklist | 338 real production bugs across 9 projects — bug-driven QA validation | QA Bug Checklist Reviewer, QA Coordinator (per spec) |
| 12 | `sdlc-architecture-review` | Architecture Review | Structural alignment with SDLC layering rules and project patterns | Architecture Reviewer |

---

## 3. Detailed Agent Profiles

### 3.1 Harness (Orchestrator)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/harness.agent.md` |
| **Role** | Master orchestrator — single entry point for all SDLC workflows |
| **Phase(s)** | All (1–9) — delegates to phase workers |
| **User-invocable** | Yes (implicit — no `user-invocable: false` in frontmatter) |
| **Tools** | `agent`, `read`, `search`, `edit`, `execute`, `terminal`, `fetch`, `web`, `browser`, `todo`, `github/*`, `awesome-copilot/*`, `context7/*`, `azure-devops/*`, `azure/*`, `azure-mcp/*`, `microsoft-learn/*`, `microsoft-docs/*`, `playwright/*` |
| **Sub-agents** | Analyst, Scaffolder, Deployer, Implementer, Documenter, QA Coordinator, RAI Reviewer, Release Manager |
| **Skills** | sdlc-workspace-init (via first-run bootstrap) |
| **MCP gates** | awesome-copilot (hard stop), GitHub MCP (optional — graceful degradation), Context7 (warn), Azure DevOps (warn) |
| **Key behaviors** | First-run workspace init, progressive placeholder filling, ADR generation rule, iterative feedback loops, QA feedback loop (max 3 rounds) |

### 3.2 QA Coordinator (Orchestrator + Phase Worker)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/qa-coordinator.agent.md` |
| **Role** | Phase 6 worker AND sub-agent orchestrator for 8 parallel QA reviewers |
| **Phase(s)** | 6 (Quality Assurance) |
| **User-invocable** | No |
| **Tools** | `read`, `agent`, `search`, `web`, `browser`, `azure-mcp/search`, `awesome-copilot/*`, `context7/*`, `azure/search`, `azure-devops/*`, `microsoft-learn/*`, `playwright/*`, `microsoft-docs/*`, `discogs/search`, `mermaidchart.vscode-mermaid-chart/*` |
| **Sub-agents** | Architecture Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Security Reviewer, Test Coverage Reviewer, UX & Accessibility Reviewer, LLM Behavior Reviewer, Deployment Readiness Reviewer |
| **Skills (per spec)** | sdlc-code-quality, sdlc-security-review, sdlc-project-qa, sdlc-qa-bug-checklist |
| **MCP gates** | awesome-copilot (warn), Azure DevOps (warn) — neither is a hard blocker |
| **Key behaviors** | Adversarial QA posture, parallel reviewer dispatch, numeric quality scores per domain, hard thresholds (security ≥8, others ≥7), manual QA checklist, QA Report generation, ADO bug filing, iterative fix loop |

### 3.3 Analyst (Phase Worker)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/analyst.agent.md` |
| **Role** | Requirements clarification, design proposals, Azure service mapping |
| **Phase(s)** | 1–2 (Requirements & Design) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `fetch`, `github/*`, `awesome-copilot/*`, `context7/*`, `azure-devops/*` |
| **Skills (per spec)** | sdlc-workspace-init |
| **MCP gates** | GitHub MCP (optional — enhances with live repo patterns), awesome-copilot (recommended), Azure DevOps (optional) |
| **Key behaviors** | ADR-ready output format, Mermaid diagrams, progressive config output, self-evaluation checklist, SDLC exit criteria |

### 3.4 Scaffolder (Phase Worker)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/scaffolder.agent.md` |
| **Role** | Project structure creation from templates, CI/CD pipeline stubs, Dockerfiles |
| **Phase(s)** | 3 (Repo Structure & CI/CD) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `edit`, `terminal`, `github/*`, `awesome-copilot/*`, `context7/*`, `azure-devops/*` |
| **Skills** | sdlc-project-scaffolding, sdlc-project-manifest |
| **MCP gates** | GitHub MCP (optional — enhances with template patterns), awesome-copilot (recommended) |
| **Key behaviors** | Strict `src/<ProjectName><Layer>/` rule, template fidelity validation, scope boundary (scaffolding only — no business logic), self-evaluation checklist |

### 3.5 Deployer (Phase Worker)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/deployer.agent.md` |
| **Role** | Azure infrastructure (Bicep/AVM), azd orchestration, deployment lifecycle |
| **Phase(s)** | 3+8 (Deployment & Infrastructure) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `edit`, `terminal`, `github/*`, `awesome-copilot/*`, `azure/*`, `microsoft-learn/*`, `azure-devops/*` |
| **Skills** | sdlc-azure-deployment |
| **MCP gates** | GitHub MCP (optional — enhances with deployment patterns), awesome-copilot (recommended), Azure DevOps (mandatory for Bicep — blocks infra creation) |
| **Key behaviors** | AVM module lookup, ADO wiki Bicep standards, WAF toggle parameters, two-tier parameter files, Managed Identity enforcement, self-evaluation checklist |

### 3.6 Implementer (Phase Worker)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/implementer.agent.md` |
| **Role** | Production code + tests, feature implementation with inline testing |
| **Phase(s)** | 4 (Implementation & Tests) |
| **User-invocable** | No |
| **Tools** | `execute`, `read`, `agent`, `edit`, `search`, `web`, `browser`, `azure-mcp/*`, `awesome-copilot/*`, `context7/*`, `github/*`, `azure/search`, `azure-devops/*`, `microsoft-learn/*`, `microsoft-docs/*`, `ms-python.python/*`, `todo` |
| **Skills** | sdlc-project-manifest, sdlc-cosmos-repository, sdlc-blob-storage |
| **MCP gates** | GitHub MCP (optional — enhances with SDK patterns), awesome-copilot (recommended) |
| **Key behaviors** | Acceptance criteria (sprint contract), strict 6-step workflow, service directory map, Agent Framework patterns, self-evaluation checklist |

### 3.7 Documenter (Phase Worker)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/documenter.agent.md` |
| **Role** | ADRs, API docs, README updates |
| **Phase(s)** | 5 (Repository Documentation) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `edit`, `github/*`, `microsoft-learn/*` |
| **Skills** | sdlc-adr-authoring |
| **MCP gates** | GitHub MCP (optional — enhances with repo context) |
| **Key behaviors** | Template-driven docs from `.design/`, Mermaid diagram conversion, ADR creation workflow, self-evaluation checklist |

### 3.8 RAI Reviewer (Phase Worker)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/rai-reviewer.agent.md` |
| **Role** | AI and data risk assessment, responsible AI compliance |
| **Phase(s)** | 7 (Responsible AI Review) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `awesome-copilot/*`, `microsoft-learn/*` |
| **Skills** | _(external: `ai-prompt-engineering-safety-review` loaded via awesome-copilot MCP)_ |
| **MCP gates** | awesome-copilot (recommended) |
| **Key behaviors** | 7-item RAI checklist (prompt injection, data leakage, bias, transparency, human oversight, data retention, hallucination) |

### 3.9 Release Manager (Phase Worker)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/release-manager.agent.md` |
| **Role** | Release scripts, PR creation, changelogs, environment promotion |
| **Phase(s)** | 8–9 (Release & Publish) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `edit`, `github/*` |
| **Skills** | _(none — uses GitHub MCP tools directly)_ |
| **MCP gates** | GitHub MCP (recommended — needed for PR creation; other tasks degrade gracefully) |
| **Key behaviors** | SDLC-compliant PR bodies, post-deployment monitoring, rollback procedure, release checklist |

### 3.10 Architecture Reviewer (QA Reviewer)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/architecture-reviewer.agent.md` |
| **Role** | Layering rules, dependency boundaries, pattern consistency |
| **Phase(s)** | 6 (sub-agent of QA Coordinator) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `github/*` |
| **Skills** | sdlc-architecture-review |
| **MCP gates** | GitHub MCP (optional — enhances with architecture patterns) |
| **Key behaviors** | Reads project manifest, cross-repo pattern search, adversarial posture, numeric score |

### 3.11 Azure Compliance Reviewer (QA Reviewer)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/azure-compliance-reviewer.agent.md` |
| **Role** | Azure SDK usage, AVM patterns, identity management, tags, diagnostics |
| **Phase(s)** | 6 (sub-agent of QA Coordinator) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `github/*`, `awesome-copilot/*` |
| **Skills** | _(none declared — uses awesome-copilot for Bicep best practices)_ |
| **MCP gates** | GitHub MCP (optional — enhances with compliance patterns), awesome-copilot (recommended) |
| **Key behaviors** | Fetches live SDK APIs from GitHub MCP, Bicep best practices from awesome-copilot, adversarial posture, numeric score |

### 3.12 Code Quality Reviewer (QA Reviewer)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/code-quality-reviewer.agent.md` |
| **Role** | Naming, docstrings, dead code, comments, type safety, DRY |
| **Phase(s)** | 6 (sub-agent of QA Coordinator) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `awesome-copilot/*` |
| **Skills** | sdlc-code-quality |
| **Key behaviors** | Reads project manifest, loads quality instruction files per language, project-specific checks (placeholder text, debug code), adversarial posture, numeric score |

### 3.13 Security Reviewer (QA Reviewer)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/security-reviewer.agent.md` |
| **Role** | OWASP Top 10, secrets, injection risks, auth patterns, CORS |
| **Phase(s)** | 6 (sub-agent of QA Coordinator) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `awesome-copilot/*` |
| **Skills** | sdlc-security-review |
| **Key behaviors** | Higher threshold (8/10 vs 7/10), OWASP-mapped checklist, project-specific checks (XSS, CDN audit, error opacity), adversarial posture, numeric score |

### 3.14 Test Coverage Reviewer (QA Reviewer)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/test-coverage-reviewer.agent.md` |
| **Role** | Test quality, coverage gaps, assertion effectiveness, Playwright e2e |
| **Phase(s)** | 6 (sub-agent of QA Coordinator) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `terminal`, `awesome-copilot/*`, `playwright/*` |
| **Skills** | _(none declared in frontmatter — references test-quality instruction files and sdlc-project-qa in body)_ |
| **Key behaviors** | Runs pytest/vitest for coverage, Playwright e2e if frontend present, project-specific checks (file upload edge cases, international chars, error paths), adversarial posture, numeric score |

### 3.15 UX & Accessibility Reviewer (QA Reviewer)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/ux-accessibility-reviewer.agent.md` |
| **Role** | ARIA labels, keyboard nav, color contrast, responsive layout, dark mode |
| **Phase(s)** | 6 (sub-agent of QA Coordinator) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `playwright/*` |
| **Skills** | sdlc-project-qa (declared in frontmatter `skills:` field) |
| **Key behaviors** | Proactive Playwright MCP testing (does not wait for user URL), saves artifacts to `.playwright-mcp/`, Category 1+2 checklists, adversarial posture, numeric score |

### 3.16 LLM Behavior Reviewer (QA Reviewer)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/llm-behavior-reviewer.agent.md` |
| **Role** | Prompt injection guards, system prompt security, grounding, citations, token limits |
| **Phase(s)** | 6 (sub-agent of QA Coordinator) |
| **User-invocable** | No |
| **Tools** | `read`, `search` |
| **Skills** | sdlc-project-qa, sdlc-security-review (declared in frontmatter `skills:` field) |
| **Key behaviors** | Category 3+4 checklists (LLM & Agent Behavior, Data & File Handling), no external MCP directly required, adversarial posture, numeric score |

### 3.17 Deployment Readiness Reviewer (QA Reviewer)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/deployment-readiness-reviewer.agent.md` |
| **Role** | Error handling, health endpoints, logging, performance, repo hygiene, observability |
| **Phase(s)** | 6 (sub-agent of QA Coordinator) |
| **User-invocable** | No |
| **Tools** | `read`, `search`, `terminal` |
| **Skills** | sdlc-project-qa (declared in frontmatter `skills:` field) |
| **Key behaviors** | Category 5+7+8+9 checklists (Error Handling, Performance, Deployment Hygiene, Observability), runs `pip audit`/`npm audit` if possible, adversarial posture, numeric score |

### 3.18 QA Bug Checklist Reviewer (Standalone)

| Field | Value |
|---|---|
| **File** | `vscode-extension/agents/qa-bug-checklist-reviewer.agent.md` |
| **Role** | Bug-driven validation against 338 real production bugs across 9 projects |
| **Phase(s)** | On-demand (not dispatched by QA Coordinator) |
| **User-invocable** | **Yes** |
| **Tools** | `read`, `search`, `agent` |
| **Skills** | sdlc-qa-bug-checklist, sdlc-security-review, sdlc-azure-deployment (declared in frontmatter `skills:` field) |
| **MCP gates** | awesome-copilot (warn only) |
| **Key behaviors** | 6 checklists (Deployment, AI/ML, Frontend, API/Backend, Identity, cross-cutting), cross-references with security review, cites bug counts per finding |

---

## 4. Phase-to-Agent Mapping (from spec `sub_agents_by_phase`)

Cross-referenced from `docs/specs/2026-04-10-sdlc-harness-spec.md` §1.3:

| Phase | Primary Agent | Supporting / Post-Gate | Skills |
|---|---|---|---|
| **Requirements** | Analyst | — | sdlc-workspace-init |
| **Design** | Analyst | Documenter (ADR gate) | sdlc-adr-authoring |
| **Scaffold** | Scaffolder | — (entry gate: reference-catalog) | sdlc-project-scaffolding, sdlc-project-manifest |
| **Deploy** | Deployer | — | sdlc-azure-deployment |
| **Implement** | Implementer | — (entry gate: reference-catalog) | sdlc-code-quality, sdlc-cosmos-repository, sdlc-blob-storage |
| **Document** | Documenter | — | sdlc-adr-authoring, sdlc-project-manifest |
| **QA** | QA Coordinator | 8 parallel reviewers + 1 standalone | sdlc-code-quality, sdlc-security-review, sdlc-project-qa, sdlc-qa-bug-checklist |
| **RAI** | RAI Reviewer | — | _(ai-prompt-engineering-safety-review via awesome-copilot)_ |
| **Release** | Release Manager | Deployer (Phase 8 infra) | _(none — GitHub MCP direct)_ |

---

## 5. Tool Requirements Matrix

| Tool / MCP Server | Agents Using It |
|---|---|
| `github/*` | Harness, Analyst, Scaffolder, Deployer, Implementer, Documenter, Release Manager, Architecture Reviewer, Azure Compliance Reviewer |
| `awesome-copilot/*` | Harness, QA Coordinator, Analyst, Scaffolder, Deployer, Implementer, RAI Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Security Reviewer, Test Coverage Reviewer |
| `context7/*` | Harness, QA Coordinator, Analyst, Scaffolder, Implementer |
| `azure-devops/*` | Harness, QA Coordinator, Analyst, Scaffolder, Deployer, Implementer |
| `azure/*` or `azure-mcp/*` | Harness, QA Coordinator, Deployer, Implementer |
| `microsoft-learn/*` | Harness, QA Coordinator, Deployer, Implementer, Documenter, RAI Reviewer |
| `microsoft-docs/*` | Harness, QA Coordinator, Implementer |
| `playwright/*` | Harness, QA Coordinator, Test Coverage Reviewer, UX & Accessibility Reviewer |
| `terminal` | Scaffolder, Deployer, Implementer, Test Coverage Reviewer, Deployment Readiness Reviewer |
| `edit` | Harness, Scaffolder, Deployer, Implementer, Documenter, Release Manager |
| `agent` | Harness, QA Coordinator, Implementer, QA Bug Checklist Reviewer |
| `ms-python.python/*` | Implementer |
| `mermaidchart.vscode-mermaid-chart/*` | QA Coordinator |
| `todo` | Harness, Implementer |

---

## 6. Delegation Graph

```
User
 └── @Harness (master orchestrator)
      ├── Analyst            (Phase 1-2)
      ├── Scaffolder         (Phase 3)
      ├── Deployer           (Phase 3+8)
      ├── Implementer        (Phase 4)
      ├── Documenter         (Phase 5, also ADR gate after design)
      ├── QA Coordinator     (Phase 6)
      │    ├── Architecture Reviewer
      │    ├── Azure Compliance Reviewer
      │    ├── Code Quality Reviewer
      │    ├── Security Reviewer
      │    ├── Test Coverage Reviewer
      │    ├── UX & Accessibility Reviewer
      │    ├── LLM Behavior Reviewer
      │    └── Deployment Readiness Reviewer
      ├── RAI Reviewer       (Phase 7)
      └── Release Manager    (Phase 8-9)
           └── Deployer      (supporting, Phase 8 infra)

 └── @QA Bug Checklist Reviewer (standalone, user-invocable)
```

---

## 7. Cross-Reference Validation

### 7.1 Spec `sub_agents_by_phase` → Agent Files

Every agent referenced in the spec's `sub_agents_by_phase` mapping has a corresponding `.agent.md` file:

| Spec Reference | File Exists | Status |
|---|---|---|
| `analyst` | `analyst.agent.md` | ✅ |
| `scaffolder` | `scaffolder.agent.md` | ✅ |
| `deployer` | `deployer.agent.md` | ✅ |
| `implementer` | `implementer.agent.md` | ✅ |
| `documenter` | `documenter.agent.md` | ✅ |
| `qa-coordinator` | `qa-coordinator.agent.md` | ✅ |
| `rai-reviewer` | `rai-reviewer.agent.md` | ✅ |
| `release-manager` | `release-manager.agent.md` | ✅ |
| `architecture-reviewer` | `architecture-reviewer.agent.md` | ✅ |
| `azure-compliance-reviewer` | `azure-compliance-reviewer.agent.md` | ✅ |
| `code-quality-reviewer` | `code-quality-reviewer.agent.md` | ✅ |
| `security-reviewer` | `security-reviewer.agent.md` | ✅ |
| `test-coverage-reviewer` | `test-coverage-reviewer.agent.md` | ✅ |
| `ux-accessibility-reviewer` | `ux-accessibility-reviewer.agent.md` | ✅ |
| `llm-behavior-reviewer` | `llm-behavior-reviewer.agent.md` | ✅ |
| `deployment-readiness-reviewer` | `deployment-readiness-reviewer.agent.md` | ✅ |
| `qa-bug-checklist-reviewer` | `qa-bug-checklist-reviewer.agent.md` | ✅ |

**Result: All 17 sub-agents + 1 standalone from spec have matching files. No orphans, no missing files.**

### 7.2 Skill References → Skill Files

| Skill Referenced (in agents/spec) | Skill Directory Exists | Status |
|---|---|---|
| `sdlc-workspace-init` | `vscode-extension/skills/sdlc-workspace-init/` | ✅ |
| `sdlc-project-scaffolding` | `vscode-extension/skills/sdlc-project-scaffolding/` | ✅ |
| `sdlc-project-manifest` | `vscode-extension/skills/sdlc-project-manifest/` | ✅ |
| `sdlc-azure-deployment` | `vscode-extension/skills/sdlc-azure-deployment/` | ✅ |
| `sdlc-cosmos-repository` | `vscode-extension/skills/sdlc-cosmos-repository/` | ✅ |
| `sdlc-blob-storage` | `vscode-extension/skills/sdlc-blob-storage/` | ✅ |
| `sdlc-adr-authoring` | `vscode-extension/skills/sdlc-adr-authoring/` | ✅ |
| `sdlc-code-quality` | `vscode-extension/skills/sdlc-code-quality/` | ✅ |
| `sdlc-security-review` | `vscode-extension/skills/sdlc-security-review/` | ✅ |
| `sdlc-project-qa` | `vscode-extension/skills/sdlc-project-qa/` | ✅ |
| `sdlc-qa-bug-checklist` | `vscode-extension/skills/sdlc-qa-bug-checklist/` | ✅ |
| `sdlc-architecture-review` | `vscode-extension/skills/sdlc-architecture-review/` | ✅ |

**Result: All 12 skills referenced in agents/spec have matching SKILL.md files. No missing skills.**

---

## 8. Gaps and Issues Found

### 8.1 Frontmatter Inconsistencies

| Issue | Agent | Details |
|---|---|---|
| Missing `user-invocable` field | `harness.agent.md` | Harness is the entry point but does not declare `user-invocable: true` in frontmatter. All other phase workers declare `user-invocable: false`. |
| Missing `skills` frontmatter field | Most agents | Only 4 agents declare `skills:` in frontmatter (UX & Accessibility, LLM Behavior, Deployment Readiness, QA Bug Checklist). Other agents reference skills in their body text only. |
| Inconsistent `agents` frontmatter | QA Coordinator | Uses display names (e.g., `'UX & Accessibility Reviewer'`) which must match exactly. |

### 8.2 Skill Coverage Gaps

| Issue | Details |
|---|---|
| RAI Reviewer has no local skill | Depends entirely on `ai-prompt-engineering-safety-review` loaded via awesome-copilot MCP. If awesome-copilot is down, this agent has no skill fallback. Consider creating a local `sdlc-rai-review` skill. |
| Release Manager has no skills | Uses GitHub MCP directly. This is by design but means no standardized release patterns are captured as reusable knowledge. |
| Test Coverage Reviewer has no skills in frontmatter | References `sdlc-project-qa` in body text but does not declare it in `skills:` frontmatter. |
| Azure Compliance Reviewer has no skills | References awesome-copilot for Bicep best practices but has no local skill. Could benefit from a formal skill declaration. |

### 8.3 Spec vs. Implementation Discrepancies

| Issue | Details |
|---|---|
| Spec skill for `implement` phase lists `sdlc-code-quality` | The Implementer agent body references `sdlc-project-manifest`, `sdlc-cosmos-repository`, `sdlc-blob-storage` but not `sdlc-code-quality`. The spec says `implement` phase uses `sdlc-code-quality`. |
| Spec counts "18 agents" | The spec text says "17 sub-agents + 1 orchestrator = 18 agents" but there are actually 18 agent files (including the standalone QA Bug Checklist Reviewer) plus Harness = 19 logical agents. The count depends on whether Harness is counted. |
| `discogs/search` tool in QA Coordinator | The QA Coordinator's tool list includes `discogs/search` which appears unrelated to SDLC workflows. Likely a configuration artifact. |

### 8.4 Potential Improvements

| Suggestion | Details |
|---|---|
| Standardize `skills:` frontmatter | All agents that use skills should declare them in frontmatter for machine-readable discovery. |
| Add `user-invocable: true` to Harness | Make the entry-point status explicit. |
| Create `sdlc-rai-review` local skill | Provide a fallback for RAI reviews when awesome-copilot is unavailable. |
| Remove `discogs/search` from QA Coordinator | Appears to be a configuration artifact. |
| Declare `sdlc-project-qa` in Test Coverage Reviewer frontmatter | The skill is referenced in the body but not in `skills:`. |