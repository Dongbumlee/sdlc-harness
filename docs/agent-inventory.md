# SDLC Harness — Agent Inventory

> **Generated file — do not edit by hand.**
> Regenerate with `python3 tools/generate_agent_inventory.py`.

**Version:** 1.0.1
**Generated:** 2026-09-13
**Total agents:** 19 (19 agent files)
**Total skills:** 16

## 1. Agent Summary

| # | Agent File | Name | Role | Phase(s) | User-Invocable | Skills (frontmatter) |
|---|---|---|---|---|---|---|
| 1 | `analyst.agent.md` | Analyst | Phase Worker | 1-2 | No | `sdlc-requirements-discovery` |
| 2 | `architecture-reviewer.agent.md` | Architecture Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format` |
| 3 | `azure-compliance-reviewer.agent.md` | Azure Compliance Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format` |
| 4 | `code-quality-reviewer.agent.md` | Code Quality Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format` |
| 5 | `deployer.agent.md` | Deployer | Phase Worker | 3+8 | No | — |
| 6 | `deployment-readiness-reviewer.agent.md` | Deployment Readiness Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-project-qa`, `sdlc-reviewer-output-format` |
| 7 | `documenter.agent.md` | Documenter | Phase Worker | 5 | No | — |
| 8 | `harness.agent.md` | Harness | Orchestrator | All (1–9) | — | — |
| 9 | `implementer.agent.md` | Implementer | Phase Worker | 4 | No | — |
| 10 | `llm-behavior-reviewer.agent.md` | LLM Behavior Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-project-qa`, `sdlc-security-review`, `sdlc-reviewer-output-format` |
| 11 | `qa-bug-checklist-reviewer.agent.md` | QA Bug Checklist Reviewer | Standalone | On-demand | Yes | `sdlc-qa-bug-checklist`, `sdlc-security-review`, `sdlc-azure-deployment` |
| 12 | `qa-coordinator.agent.md` | QA Coordinator | Orchestrator + Phase Worker | 6 | No | `sdlc-reviewer-output-format` |
| 13 | `rai-reviewer.agent.md` | RAI Reviewer | QA Reviewer | 7 | No | — |
| 14 | `release-manager.agent.md` | Release Manager | Phase Worker | 8-9 | No | — |
| 15 | `requirements-completeness-reviewer.agent.md` | Requirements Completeness Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format` |
| 16 | `scaffolder.agent.md` | Scaffolder | Phase Worker | 3 | No | — |
| 17 | `security-reviewer.agent.md` | Security Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format` |
| 18 | `test-coverage-reviewer.agent.md` | Test Coverage Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format` |
| 19 | `ux-accessibility-reviewer.agent.md` | UX & Accessibility Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-project-qa`, `sdlc-reviewer-output-format` |

## 2. Counts by Role

| Role | Count | Agents |
|---|---|---|
| Phase Worker | 6 | Analyst, Deployer, Documenter, Implementer, Release Manager, Scaffolder |
| QA Reviewer | 10 | Architecture Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Deployment Readiness Reviewer, LLM Behavior Reviewer, RAI Reviewer, Requirements Completeness Reviewer, Security Reviewer, Test Coverage Reviewer, UX & Accessibility Reviewer |
| Orchestrator | 1 | Harness |
| Standalone | 1 | QA Bug Checklist Reviewer |
| Orchestrator + Phase Worker | 1 | QA Coordinator |

## 3. Skill Inventory

| # | Skill Directory | Name | Description | Used By (frontmatter) |
|---|---|---|---|---|
| 1 | `sdlc-adr-authoring` | sdlc-adr-authoring | Create Architecture Decision Records following SDLC standards and application templates. Use when documenting design decisions, architect... | — |
| 2 | `sdlc-architecture-review` | sdlc-architecture-review | Review code for architecture and design consistency following SDLC layering rules and application project patterns. Use when reviewing PR... | — |
| 3 | `sdlc-azure-deployment` | sdlc-azure-deployment | Create Azure infrastructure with Bicep using Azure Verified Modules (AVM), configure azd orchestration, and manage deployment lifecycle. ... | QA Bug Checklist Reviewer |
| 4 | `sdlc-blob-storage` | sdlc-blob-storage | Implement Azure Blob Storage and Queue operations using the approved Storage library library. Use when uploading, downloading, listing, o... | — |
| 5 | `sdlc-canary-runner` | sdlc-canary-runner | Instructs the Harness agent how to run E2E canary tests against SDLC phase agents. Canary mode validates that the harness orchestration i... | — |
| 6 | `sdlc-code-quality` | sdlc-code-quality | Review and enforce code quality standards for Python, TypeScript, React, Java, C#, Go, and Rust following SDLC quality instruction files.... | — |
| 7 | `sdlc-cosmos-repository` | sdlc-cosmos-repository | Implement Azure Cosmos DB data access using the approved Cosmos DB library library with Repository Pattern. Use when creating entities, r... | — |
| 8 | `sdlc-project-manifest` | sdlc-project-manifest | Generate and read the project manifest that records which templates and patterns were chosen during scaffolding. This manifest is the sin... | — |
| 9 | `sdlc-project-qa` | sdlc-project-qa | Comprehensive product QA checklist for enterprise applications and AI agents, covering UX/accessibility, core functionality, LLM behavior... | Deployment Readiness Reviewer, LLM Behavior Reviewer, UX & Accessibility Reviewer |
| 10 | `sdlc-project-scaffolding` | sdlc-project-scaffolding | Scaffold new application project structures from templates with CI/CD pipelines, Dockerfiles, and devcontainers. Use when creating a new ... | — |
| 11 | `sdlc-qa-bug-checklist` | sdlc-qa-bug-checklist | Bug-driven QA checklist distilled from 338 real bugs across 9 CSACTOSOL ADO projects with detailed error patterns, Azure error codes, and... | QA Bug Checklist Reviewer |
| 12 | `sdlc-reference-catalog` | sdlc-reference-catalog | Manage the living reference catalog — research methodology, population rules, consumption rules, append-only enforcement, and review chec... | — |
| 13 | `sdlc-requirements-discovery` | sdlc-requirements-discovery | Guides the Analyst agent through collaborative requirements discovery with the user. Covers elicitation patterns, question strategies, re... | Analyst |
| 14 | `sdlc-reviewer-output-format` | sdlc-reviewer-output-format | Structured YAML output format for SDLC QA reviewer agents. Ensures consistent, parseable review output across all 9 reviewer domains. Use... | Architecture Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Deployment Readiness Reviewer, LLM Behavior Reviewer, QA Coordinator, Requirements Completeness Reviewer, Security Reviewer, Test Coverage Reviewer, UX & Accessibility Reviewer |
| 15 | `sdlc-security-review` | sdlc-security-review | Perform SDLC-aligned security review combining OWASP Top 10 with project-specific Azure patterns. Use when reviewing code for security vu... | LLM Behavior Reviewer, QA Bug Checklist Reviewer |
| 16 | `sdlc-workspace-init` | sdlc-workspace-init | Initialize a new repository with SDLC workspace files — MCP config, copilot-instructions.md, quality instructions, and prompt files. Use ... | — |

## 4. Phase-to-Agent Mapping

| Phase | Agent(s) |
|---|---|
| All (1–9) | Harness |
| 1-2 | Analyst |
| 3 | Scaffolder |
| 3+8 | Deployer |
| 4 | Implementer |
| 5 | Documenter |
| 6 | QA Coordinator |
| 6 (sub) | Architecture Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Deployment Readiness Reviewer, LLM Behavior Reviewer, Requirements Completeness Reviewer, Security Reviewer, Test Coverage Reviewer, UX & Accessibility Reviewer |
| 7 | RAI Reviewer |
| 8-9 | Release Manager |
| On-demand | QA Bug Checklist Reviewer |

## 5. Tool Requirements Matrix

| Tool / MCP Server | Agents Using It |
|---|---|
| `agent` | Harness, Implementer, QA Bug Checklist Reviewer, QA Coordinator |
| `awesome-copilot/*` | Analyst, Azure Compliance Reviewer, Code Quality Reviewer, Deployer, Harness, Implementer, QA Coordinator, RAI Reviewer, Scaffolder, Security Reviewer, Test Coverage Reviewer |
| `azure-devops/*` | Analyst, Deployer, Harness, Implementer, QA Coordinator, Scaffolder |
| `azure/*` | Harness |
| `azure/bicepschema` | Deployer |
| `azure/cosmos` | Implementer |
| `azure/deploy` | Deployer |
| `azure/group` | Deployer |
| `azure/keyvault` | Implementer |
| `azure/storage` | Implementer |
| `browser` | Harness, Implementer, QA Coordinator |
| `context7/*` | Analyst, Harness, Implementer, QA Coordinator, Scaffolder |
| `edit` | Deployer, Documenter, Harness, Implementer, Release Manager, Scaffolder |
| `execute` | Harness, Implementer |
| `fetch` | Analyst, Harness |
| `github/*` | Analyst, Architecture Reviewer, Azure Compliance Reviewer, Deployer, Documenter, Harness, Implementer, Release Manager, Scaffolder |
| `mermaidchart.vscode-mermaid-chart/get_syntax_docs` | QA Coordinator |
| `mermaidchart.vscode-mermaid-chart/mermaid-diagram-preview` | QA Coordinator |
| `mermaidchart.vscode-mermaid-chart/mermaid-diagram-validator` | QA Coordinator |
| `microsoft-learn/*` | Deployer, Documenter, Harness, Implementer, QA Coordinator, RAI Reviewer |
| `ms-python.python/configurePythonEnvironment` | Implementer |
| `ms-python.python/getPythonEnvironmentInfo` | Implementer |
| `ms-python.python/getPythonExecutableCommand` | Implementer |
| `ms-python.python/installPythonPackage` | Implementer |
| `playwright/*` | Harness, QA Coordinator, Test Coverage Reviewer, UX & Accessibility Reviewer |
| `read` | Analyst, Architecture Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Deployer, Deployment Readiness Reviewer, Documenter, Harness, Implementer, LLM Behavior Reviewer, QA Bug Checklist Reviewer, QA Coordinator, RAI Reviewer, Release Manager, Requirements Completeness Reviewer, Scaffolder, Security Reviewer, Test Coverage Reviewer, UX & Accessibility Reviewer |
| `search` | Analyst, Architecture Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Deployer, Deployment Readiness Reviewer, Documenter, Harness, Implementer, LLM Behavior Reviewer, QA Bug Checklist Reviewer, QA Coordinator, RAI Reviewer, Release Manager, Requirements Completeness Reviewer, Scaffolder, Security Reviewer, Test Coverage Reviewer, UX & Accessibility Reviewer |
| `terminal` | Deployer, Deployment Readiness Reviewer, Harness, Scaffolder, Test Coverage Reviewer |
| `todo` | Harness, Implementer |
| `web` | Harness, Implementer, QA Coordinator |

## 6. Delegation Graph

```
User
 └── Harness (master orchestrator)
      ├── Analyst
      ├── Architecture Reviewer
      ├── Azure Compliance Reviewer
      ├── Code Quality Reviewer
      ├── Deployer
      ├── Deployment Readiness Reviewer
      ├── Documenter
      ├── Implementer
      ├── LLM Behavior Reviewer
      ├── QA Coordinator
      │    ├── architecture-reviewer.agent.md
      │    ├── azure-compliance-reviewer.agent.md
      │    ├── code-quality-reviewer.agent.md
      │    ├── security-reviewer.agent.md
      │    ├── test-coverage-reviewer.agent.md
      │    ├── requirements-completeness-reviewer.agent.md
      │    ├── ux-accessibility-reviewer.agent.md
      │    ├── llm-behavior-reviewer.agent.md
      │    ├── deployment-readiness-reviewer.agent.md
      ├── RAI Reviewer
      ├── Release Manager
      ├── Requirements Completeness Reviewer
      ├── Scaffolder
      ├── Security Reviewer
      ├── Test Coverage Reviewer
      ├── UX & Accessibility Reviewer
 └── QA Bug Checklist Reviewer (standalone, user-invocable)
```

## 7. Cross-Reference Validation

✅ All skill references resolve to `skills/<name>/SKILL.md`.
✅ All Harness sub-agent references resolve to agent files.

## 8. Notes

- Agent counts and skill usage are derived from frontmatter, not prose —
  if a number here looks wrong, fix the agent file, not this document.
- `user-invocable: —` means the field is not declared in frontmatter.
- Run with `--check` in CI to fail when this document is stale.
