# SDLC Harness — Skill Inventory

**Version:** 1.0.0
**Date:** 2026-04-11
**Source branch:** `evo`
**Total skills:** 12

---

## Summary Table

| # | Skill ID | Scope | Phase(s) | Consuming Agents | Stack-Specific |
|---|---|---|---|---|---|
| 1 | sdlc-workspace-init | Project bootstrap & first-run setup | 0 (Init) | Harness | No |
| 2 | sdlc-project-scaffolding | Project structure generation | 3 (Scaffold) | Scaffolder | Partial |
| 3 | sdlc-project-manifest | Project manifest tracking | 3-4 | Scaffolder, Implementer, Documenter | No |
| 4 | sdlc-azure-deployment | Azure IaC deployment | 3+8 (Deploy) | Deployer | Yes (Azure) |
| 5 | sdlc-adr-authoring | Architecture Decision Records | 5 (Document) | Documenter | No |
| 6 | sdlc-code-quality | Code quality review | 6 (QA) | Code Quality Reviewer, QA Coordinator | Partial |
| 7 | sdlc-security-review | Security vulnerability scanning | 6 (QA) | Security Reviewer, LLM Behavior Reviewer, QA Bug Checklist | No |
| 8 | sdlc-architecture-review | Architecture pattern validation | 6 (QA) | Architecture Reviewer | No |
| 9 | sdlc-project-qa | Project QA checklist | 6 (QA) | UX/Accessibility, LLM Behavior, Deployment Readiness | No |
| 10 | sdlc-qa-bug-checklist | QA bug tracking checklist | 6 (QA) | QA Bug Checklist Reviewer, QA Coordinator | No |
| 11 | sdlc-cosmos-repository | CosmosDB repository pattern | 4 (Implement) | Implementer | Yes (Azure) |
| 12 | sdlc-blob-storage | Azure Blob Storage integration | 4 (Implement) | Implementer | Yes (Azure) |

---

## Skill-to-Agent Cross-Reference

| Agent | Skills Used |
|---|---|
| Harness | sdlc-workspace-init |
| Analyst | sdlc-workspace-init |
| Scaffolder | sdlc-project-scaffolding, sdlc-project-manifest |
| Deployer | sdlc-azure-deployment |
| Implementer | sdlc-project-manifest, sdlc-cosmos-repository, sdlc-blob-storage |
| Documenter | sdlc-adr-authoring, sdlc-project-manifest |
| QA Coordinator | sdlc-code-quality, sdlc-security-review, sdlc-project-qa, sdlc-qa-bug-checklist |
| Architecture Reviewer | sdlc-architecture-review |
| Code Quality Reviewer | sdlc-code-quality |
| Security Reviewer | sdlc-security-review |
| UX & Accessibility Reviewer | sdlc-project-qa |
| LLM Behavior Reviewer | sdlc-project-qa, sdlc-security-review |
| Deployment Readiness Reviewer | sdlc-project-qa |
| QA Bug Checklist Reviewer | sdlc-qa-bug-checklist, sdlc-security-review, sdlc-azure-deployment |
| RAI Reviewer | _(external: awesome-copilot MCP)_ |
| Release Manager | _(none — uses GitHub MCP)_ |
| Test Coverage Reviewer | _(none — uses instruction files)_ |
| Azure Compliance Reviewer | _(none — uses awesome-copilot MCP)_ |

---

## Stack-Specific Skill Packs

### Azure (Implemented)
- sdlc-azure-deployment
- sdlc-cosmos-repository
- sdlc-blob-storage

### AWS (Planned)
- sdlc-aws-deployment (CDK/CloudFormation)
- sdlc-dynamodb-repository
- sdlc-s3-storage

### GCP (Planned)
- sdlc-gcp-deployment (Terraform)
- sdlc-firestore-repository
- sdlc-gcs-storage
