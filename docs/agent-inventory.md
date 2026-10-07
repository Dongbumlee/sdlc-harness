# SDLC Harness — Agent Inventory

> **Generated file — do not edit by hand.**
> Regenerate with `python3 tools/generate_agent_inventory.py`.

**Version:** 1.0.1
**Generated:** 2026-10-06
**Total agents:** 21 (21 agent files)
**Total skills:** 22

## 1. Agent Summary

| # | Agent File | Name | Role | Phase(s) | User-Invocable | Skills (frontmatter) |
|---|---|---|---|---|---|---|
| 1 | `analyst.agent.md` | Analyst | Phase Worker | 1-2 | No | `sdlc-requirements-discovery`, `sdlc-reference-catalog` |
| 2 | `architecture-reviewer.agent.md` | Architecture Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format`, `sdlc-architecture-review` |
| 3 | `aws-compliance-reviewer.agent.md` | AWS Compliance Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format` |
| 4 | `azure-compliance-reviewer.agent.md` | Azure Compliance Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format` |
| 5 | `code-quality-reviewer.agent.md` | Code Quality Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format`, `sdlc-code-quality` |
| 6 | `deployer.agent.md` | Deployer | Phase Worker | 3+8 | No | `sdlc-azure-deployment`, `sdlc-reference-catalog` |
| 7 | `deployment-readiness-reviewer.agent.md` | Deployment Readiness Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-project-qa`, `sdlc-reviewer-output-format` |
| 8 | `documenter.agent.md` | Documenter | Phase Worker | 5 | No | `sdlc-adr-authoring`, `sdlc-reference-catalog` |
| 9 | `gcp-compliance-reviewer.agent.md` | GCP Compliance Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format` |
| 10 | `harness.agent.md` | Harness | Orchestrator | All (1–9) | — | `sdlc-canary-runner`, `sdlc-requirements-discovery`, `sdlc-workspace-init` |
| 11 | `implementer.agent.md` | Implementer | Phase Worker | 4 | No | `sdlc-blob-storage`, `sdlc-cosmos-repository`, `sdlc-project-manifest`, `sdlc-reference-catalog` |
| 12 | `llm-behavior-reviewer.agent.md` | LLM Behavior Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-project-qa`, `sdlc-security-review`, `sdlc-reviewer-output-format` |
| 13 | `qa-bug-checklist-reviewer.agent.md` | QA Bug Checklist Reviewer | Standalone | On-demand | Yes | `sdlc-qa-bug-checklist`, `sdlc-security-review`, `sdlc-azure-deployment` |
| 14 | `qa-coordinator.agent.md` | QA Coordinator | Orchestrator + Phase Worker | 6 | No | `sdlc-reviewer-output-format`, `sdlc-project-qa` |
| 15 | `rai-reviewer.agent.md` | RAI Reviewer | QA Reviewer | 7 | No | — |
| 16 | `release-manager.agent.md` | Release Manager | Phase Worker | 8-9 | No | — |
| 17 | `requirements-completeness-reviewer.agent.md` | Requirements Completeness Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format` |
| 18 | `scaffolder.agent.md` | Scaffolder | Phase Worker | 3 | No | `sdlc-project-manifest`, `sdlc-project-scaffolding`, `sdlc-reference-catalog` |
| 19 | `security-reviewer.agent.md` | Security Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format`, `sdlc-security-review` |
| 20 | `test-coverage-reviewer.agent.md` | Test Coverage Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-reviewer-output-format`, `sdlc-project-qa` |
| 21 | `ux-accessibility-reviewer.agent.md` | UX & Accessibility Reviewer | QA Reviewer | 6 (sub) | No | `sdlc-project-qa`, `sdlc-reviewer-output-format` |

## 2. Counts by Role

| Role | Count | Agents |
|---|---|---|
| Phase Worker | 6 | Analyst, Deployer, Documenter, Implementer, Release Manager, Scaffolder |
| QA Reviewer | 12 | Architecture Reviewer, AWS Compliance Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Deployment Readiness Reviewer, GCP Compliance Reviewer, LLM Behavior Reviewer, RAI Reviewer, Requirements Completeness Reviewer, Security Reviewer, Test Coverage Reviewer, UX & Accessibility Reviewer |
| Orchestrator | 1 | Harness |
| Standalone | 1 | QA Bug Checklist Reviewer |
| Orchestrator + Phase Worker | 1 | QA Coordinator |

## 3. Skill Inventory

| # | Skill Directory | Name | Description | Used By (frontmatter) |
|---|---|---|---|---|
| 1 | `sdlc-adr-authoring` | sdlc-adr-authoring | Create Architecture Decision Records following SDLC standards and application templates. Use when documenting design decisions, architect... | Documenter |
| 2 | `sdlc-architecture-review` | sdlc-architecture-review | Review code for architecture and design consistency following SDLC layering rules and application project patterns. Use when reviewing PR... | Architecture Reviewer |
| 3 | `sdlc-aws-deployment` | sdlc-aws-deployment | Create AWS infrastructure with CDK (TypeScript) using L2/L3 constructs, deploy containerized APIs to Lambda (container image + Function U... | — |
| 4 | `sdlc-azure-deployment` | sdlc-azure-deployment | Create Azure infrastructure with Bicep using Azure Verified Modules (AVM), configure azd orchestration, and manage deployment lifecycle. ... | Deployer, QA Bug Checklist Reviewer |
| 5 | `sdlc-blob-storage` | sdlc-blob-storage | Implement Azure Blob Storage and Queue operations using the approved Storage library. Use when uploading, downloading, listing, or managi... | Implementer |
| 6 | `sdlc-canary-runner` | sdlc-canary-runner | Instructs the Harness agent how to run E2E canary tests against SDLC phase agents. Canary mode validates that the harness orchestration i... | Harness |
| 7 | `sdlc-code-quality` | sdlc-code-quality | Review and enforce code quality standards for Python, TypeScript, React, Java, C#, Go, and Rust following SDLC quality instruction files.... | Code Quality Reviewer |
| 8 | `sdlc-cosmos-repository` | sdlc-cosmos-repository | Implement Azure Cosmos DB data access using the approved Cosmos DB library with Repository Pattern. Use when creating entities, repositor... | Implementer |
| 9 | `sdlc-dynamodb-repository` | sdlc-dynamodb-repository | Implement DynamoDB data access with single-table design and the Repository Pattern over boto3. Use when creating entities, repositories, ... | — |
| 10 | `sdlc-firestore-repository` | sdlc-firestore-repository | Implement Firestore data access with an explicit collection design and the Repository Pattern over the google-cloud-firestore client. Use... | — |
| 11 | `sdlc-gcp-deployment` | sdlc-gcp-deployment | Create GCP infrastructure with Terraform using the google provider, deploy containerized APIs to Cloud Run (HTTPS, scale-to-zero) and lon... | — |
| 12 | `sdlc-gcs-storage` | sdlc-gcs-storage | Implement Cloud Storage with private buckets, uniform bucket-level access, and V4 signed URLs. Use when creating buckets, generating sign... | — |
| 13 | `sdlc-project-manifest` | sdlc-project-manifest | Generate and read the project manifest that records which templates and patterns were chosen during scaffolding. This manifest is the sin... | Implementer, Scaffolder |
| 14 | `sdlc-project-qa` | sdlc-project-qa | Comprehensive product QA checklist for enterprise applications and AI agents, covering UX/accessibility, core functionality, LLM behavior... | Deployment Readiness Reviewer, LLM Behavior Reviewer, QA Coordinator, Test Coverage Reviewer, UX & Accessibility Reviewer |
| 15 | `sdlc-project-scaffolding` | sdlc-project-scaffolding | Scaffold new application project structures from templates with CI/CD pipelines, Dockerfiles, and devcontainers. Use when creating a new ... | Scaffolder |
| 16 | `sdlc-qa-bug-checklist` | sdlc-qa-bug-checklist | Bug-driven QA checklist distilled from 338 real bugs across 9 production Azure DevOps projects with detailed error patterns, Azure error ... | QA Bug Checklist Reviewer |
| 17 | `sdlc-reference-catalog` | sdlc-reference-catalog | Manage the living reference catalog — research methodology, population rules, consumption rules, append-only enforcement, and review chec... | Analyst, Deployer, Documenter, Implementer, Scaffolder |
| 18 | `sdlc-requirements-discovery` | sdlc-requirements-discovery | Guides the Analyst agent through collaborative requirements discovery with the user. Covers elicitation patterns, question strategies, re... | Analyst, Harness |
| 19 | `sdlc-reviewer-output-format` | sdlc-reviewer-output-format | Structured YAML output format for SDLC QA reviewer agents. Ensures consistent, parseable review output across all 9 reviewer domains. Use... | Architecture Reviewer, AWS Compliance Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Deployment Readiness Reviewer, GCP Compliance Reviewer, LLM Behavior Reviewer, QA Coordinator, Requirements Completeness Reviewer, Security Reviewer, Test Coverage Reviewer, UX & Accessibility Reviewer |
| 20 | `sdlc-s3-storage` | sdlc-s3-storage | Implement Amazon S3 object storage with private buckets, presigned URLs, and lifecycle rules. Use when uploading, downloading, listing, o... | — |
| 21 | `sdlc-security-review` | sdlc-security-review | Perform SDLC-aligned security review combining OWASP Top 10 with project-specific Azure patterns. Use when reviewing code for security vu... | LLM Behavior Reviewer, QA Bug Checklist Reviewer, Security Reviewer |
| 22 | `sdlc-workspace-init` | sdlc-workspace-init | Initialize a new repository with SDLC workspace files — MCP config, copilot-instructions.md, quality instructions, and prompt files. Use ... | Harness |

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
| 6 (sub) | Architecture Reviewer, AWS Compliance Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Deployment Readiness Reviewer, GCP Compliance Reviewer, LLM Behavior Reviewer, Requirements Completeness Reviewer, Security Reviewer, Test Coverage Reviewer, UX & Accessibility Reviewer |
| 7 | RAI Reviewer |
| 8-9 | Release Manager |
| On-demand | QA Bug Checklist Reviewer |

## 5. Tool Requirements Matrix

| Tool / MCP Server | Agents Using It |
|---|---|
| `agent` | Harness, Implementer, QA Bug Checklist Reviewer, QA Coordinator |
| `awesome-copilot/*` | Analyst, AWS Compliance Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Deployer, GCP Compliance Reviewer, Harness, Implementer, QA Coordinator, RAI Reviewer, Scaffolder, Security Reviewer, Test Coverage Reviewer |
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
| `github/*` | Analyst, Architecture Reviewer, AWS Compliance Reviewer, Azure Compliance Reviewer, Deployer, Documenter, GCP Compliance Reviewer, Harness, Implementer, Release Manager, Scaffolder |
| `microsoft-learn/*` | Azure Compliance Reviewer, Deployer, Documenter, Harness, Implementer, QA Coordinator, RAI Reviewer |
| `ms-python.python/configurePythonEnvironment` | Implementer |
| `ms-python.python/getPythonEnvironmentInfo` | Implementer |
| `ms-python.python/getPythonExecutableCommand` | Implementer |
| `ms-python.python/installPythonPackage` | Implementer |
| `playwright/*` | Harness, QA Coordinator, Test Coverage Reviewer, UX & Accessibility Reviewer |
| `read` | Analyst, Architecture Reviewer, AWS Compliance Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Deployer, Deployment Readiness Reviewer, Documenter, GCP Compliance Reviewer, Harness, Implementer, LLM Behavior Reviewer, QA Bug Checklist Reviewer, QA Coordinator, RAI Reviewer, Release Manager, Requirements Completeness Reviewer, Scaffolder, Security Reviewer, Test Coverage Reviewer, UX & Accessibility Reviewer |
| `search` | Analyst, Architecture Reviewer, AWS Compliance Reviewer, Azure Compliance Reviewer, Code Quality Reviewer, Deployer, Deployment Readiness Reviewer, Documenter, GCP Compliance Reviewer, Harness, Implementer, LLM Behavior Reviewer, QA Bug Checklist Reviewer, QA Coordinator, RAI Reviewer, Release Manager, Requirements Completeness Reviewer, Scaffolder, Security Reviewer, Test Coverage Reviewer, UX & Accessibility Reviewer |
| `terminal` | Deployer, Deployment Readiness Reviewer, Harness, Scaffolder, Test Coverage Reviewer |
| `todo` | Harness, Implementer |
| `web` | Harness, Implementer, QA Coordinator |

## 6. Delegation Graph

```
User
 └── Harness (master orchestrator)
      ├── Analyst
      ├── Architecture Reviewer
      ├── AWS Compliance Reviewer
      ├── Azure Compliance Reviewer
      ├── Code Quality Reviewer
      ├── Deployer
      ├── Deployment Readiness Reviewer
      ├── Documenter
      ├── GCP Compliance Reviewer
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
