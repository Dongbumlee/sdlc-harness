# SDLC Full Pipeline E2E Test Script

End-to-end validation of all 18 agents and 11 skills across the complete
9-phase SDLC lifecycle. Each step sends a prompt to `@Harness`, validates
outputs, and feeds into the next step.

## Test Scenario

**Project**: "SmartDoc Analyzer" — a document analysis accelerator with:
- FastAPI backend with Cosmos DB for document storage
- React frontend for document upload and AI-powered chat
- Azure OpenAI for document Q&A with citations
- Blob Storage for uploaded files

This scenario exercises all agents and all skills in sequential order.

---

## Prerequisites

- VS Code with GitHub Copilot Chat and Harness agent available
- MCP servers configured in `.vscode/mcp.json`
- GitHub MCP authenticated with `your-org` org access
- awesome-copilot MCP running (Docker Desktop required)
- Clean working directory (no uncommitted changes)

---

## Step 0: MCP Readiness (Harness)

### Prompt
```
@Harness Hello, I want to build a new accelerator called SmartDoc Analyzer.
```

### Expected behavior
- [ ] Harness runs MCP server readiness check (Step 0)
- [ ] Reports status table for: awesome-copilot, GitHub MCP (libraries), GitHub MCP (templates), Context7
- [ ] Detects placeholders in `copilot-instructions.md` and asks for project details
- [ ] Fills `<PROJECT_NAME>` → "SmartDoc Analyzer"

### Agents validated
- [x] **Harness** — MCP readiness check, placeholder detection, progressive config

### Skills validated
- (none — orchestration only)

### Expected artifacts
- [ ] `.github/copilot-instructions.md` updated with project name

### Validation keywords
```
MCP Server Status|awesome-copilot|GitHub MCP|Context7|PROJECT_NAME|SmartDoc
```

---

## Step 1: Requirements & Design (Analyst)

### Prompt
```
@Harness Analyze requirements for SmartDoc Analyzer.
It needs:
- Upload PDF/DOCX documents to Azure Blob Storage
- Index documents with Azure AI Search for RAG
- Chat interface powered by Azure OpenAI GPT-4o with citations
- Store conversation history in Cosmos DB
- React frontend with dark/light mode
Target users: enterprise knowledge workers.
```

### Expected behavior
- [ ] Harness delegates to **Analyst**
- [ ] Analyst probes GitHub MCP, awesome-copilot, ADO MCP
- [ ] Loads planning best practices from awesome-copilot
- [ ] Fetches reference catalog from GitHub MCP
- [ ] Loads framework docs via Context7
- [ ] Produces structured design proposal with:
  - Architecture overview (API → Application → Domain)
  - Azure service mapping (your-cosmosdb-lib, your-storage-lib, Azure OpenAI, AI Search)
  - Template recommendation (python_api_application_template + React frontend)
  - Data model sketch (entities, repositories)

### Agents validated
- [x] **Analyst** — design proposal, MCP probes

### Skills validated
- [x] **sdlc-project-manifest** (if manifest creation is triggered)

### Expected artifacts
- [ ] Design proposal output with architecture, services, and template recommendation
- [ ] `<BUSINESS_DOMAIN>` filled in copilot-instructions.md (if recognized)

### Validation keywords
```
architecture|your-cosmosdb-lib|your-storage-lib|python_api_application_template|Azure OpenAI|AI Search|Cosmos DB|Repository Pattern|RAG|citations
```

---

## Step 2: ADR Creation (Documenter — auto-triggered by Harness)

### Expected behavior (no new prompt needed — Harness auto-delegates after Analyst)
- [ ] Harness auto-delegates to **Documenter** to create ADR from the design proposal
- [ ] Documenter reads `.design/ADR-TEMPLATE.md` template
- [ ] Creates ADR file at `docs/adr/ADR-001-smartdoc-analyzer-architecture.md`

### Agents validated
- [x] **Documenter** — ADR creation

### Skills validated
- [x] **sdlc-adr-authoring** — ADR template + awesome-copilot ADR skill

### Expected artifacts
- [ ] `docs/adr/ADR-001-*.md` exists
- [ ] ADR contains: Context, Decision, Consequences sections
- [ ] ADR references approved libraries (your-cosmosdb-lib, your-storage-lib)

### Validation keywords
```
ADR|Architecture Decision Record|Context|Decision|Consequences|your-cosmosdb-lib|Accepted
```

---

## Step 3: Project Scaffolding (Scaffolder)

### Prompt
```
@Harness Scaffold the SmartDoc Analyzer project based on ADR-001.
It needs a FastAPI backend, React frontend, and shared infrastructure.
```

### Expected behavior
- [ ] Harness delegates to **Scaffolder**
- [ ] Scaffolder probes GitHub MCP for template structure
- [ ] Loads Docker/CI-CD best practices from awesome-copilot
- [ ] Fetches template structure from `your-org/your-api-template`
- [ ] Creates project under `src/SmartDocAnalyzerAPI/` (mandatory `src/` prefix)
- [ ] Creates Dockerfile, pyproject.toml, app structure
- [ ] Creates `.sdlc/project-manifest.md` with template choices

### Agents validated
- [x] **Scaffolder** — project structure, template fetching

### Skills validated
- [x] **sdlc-project-scaffolding** — folder layout, Dockerfile, devcontainer
- [x] **sdlc-project-manifest** — manifest creation

### Expected artifacts
- [ ] `src/SmartDocAnalyzerAPI/` directory exists
- [ ] `src/SmartDocAnalyzerAPI/pyproject.toml` exists
- [ ] `src/SmartDocAnalyzerAPI/Dockerfile` exists
- [ ] `src/SmartDocAnalyzerAPI/app/` directory exists
- [ ] `.sdlc/project-manifest.md` exists

### Validation keywords
```
src/SmartDocAnalyzer|pyproject.toml|Dockerfile|project-manifest|python_api_application_template
```

---

## Step 4: Infrastructure (Deployer)

### Prompt
```
@Harness Create Azure infrastructure for SmartDoc Analyzer.
We need: Cosmos DB, Blob Storage, Azure OpenAI, AI Search, Container Apps.
Use AVM modules with WAF toggles.
```

### Expected behavior
- [ ] Harness delegates to **Deployer**
- [ ] Deployer probes GitHub MCP, awesome-copilot, ADO MCP
- [ ] Loads Bicep best practices from awesome-copilot
- [ ] Fetches AVM patterns from GitHub MCP (existing application repos)
- [ ] Creates `infra/main.bicep` with AVM modules (`br/public:avm/res/...`)
- [ ] Includes WAF parameters (`enablePrivateNetworking`, `enableMonitoring`)
- [ ] Creates `azure.yaml` for azd orchestration
- [ ] All resources have standard tags

### Agents validated
- [x] **Deployer** — Bicep generation, AVM modules, azd config

### Skills validated
- [x] **sdlc-azure-deployment** — AVM, Bicep patterns, azd orchestration

### Expected artifacts
- [ ] `infra/main.bicep` exists with `br/public:avm/res/` references
- [ ] `infra/main.parameters.json` exists
- [ ] `azure.yaml` exists
- [ ] WAF toggle parameters present in Bicep
- [ ] Standard tags on all resources

### Validation keywords
```
br/public:avm/res|enablePrivateNetworking|enableMonitoring|azure.yaml|Cosmos|OpenAI|Container Apps|tags
```

---

## Step 5: Implementation (Implementer)

### Prompt
```
@Harness Implement the document upload and chat features for SmartDoc Analyzer.
Follow the patterns from ADR-001 and the project manifest.
Use your-cosmosdb-lib for Cosmos DB and your-storage-lib for Blob Storage.
Include unit tests for all new code.
```

### Expected behavior
- [ ] Harness delegates to **Implementer**
- [ ] Implementer reads `.sdlc/project-manifest.md` for template patterns
- [ ] Probes GitHub MCP for live SDK patterns
- [ ] Fetches your-cosmosdb-lib README + HANDS_ON_GUIDE for Repository Pattern
- [ ] Fetches your-storage-lib README for Blob patterns
- [ ] Loads framework docs via Context7 (FastAPI, Pydantic)
- [ ] Creates entities extending `RootEntityBase`
- [ ] Creates repositories extending `RepositoryBase`
- [ ] Creates service layer with business logic
- [ ] Creates API routes with proper auth
- [ ] Creates unit tests alongside code

### Agents validated
- [x] **Implementer** — code generation, SDK patterns, test writing

### Skills validated
- [x] **sdlc-cosmos-repository** — RootEntityBase, RepositoryBase, Repository Pattern
- [x] **sdlc-blob-storage** — AsyncStorageBlobHelper, async with

### Expected artifacts
- [ ] Entity files with `RootEntityBase` inheritance
- [ ] Repository files with `RepositoryBase` inheritance
- [ ] Service layer files
- [ ] Router files with endpoints
- [ ] `tests/` directory with unit tests
- [ ] Tests follow Arrange-Act-Assert pattern

### Validation keywords
```
RootEntityBase|RepositoryBase|your-cosmosdb-lib|your-storage-lib|async with|AsyncStorageBlobHelper|pytest|test_|DefaultAzureCredential
```

---

## Step 6: Documentation (Documenter)

### Prompt
```
@Harness Update documentation for SmartDoc Analyzer.
Create API docs for the document upload and chat endpoints.
Update the README with deployment and usage instructions.
```

### Expected behavior
- [ ] Harness delegates to **Documenter**
- [ ] Documenter reads `.design/API-DOC-TEMPLATE.md` and `.design/README.template.md`
- [ ] Creates API docs at `docs/api/`
- [ ] Updates project README with proper sections

### Agents validated
- [x] **Documenter** — API docs, README update

### Skills validated
- [x] **sdlc-adr-authoring** (template reading)

### Expected artifacts
- [ ] `docs/api/*.md` files exist
- [ ] README contains: overview, prerequisites, deployment, usage, configuration, troubleshooting, known issues, license

### Validation keywords
```
docs/api|Prerequisites|Deployment|Usage|Configuration|Troubleshooting|Known Issues|License|POST /api/documents|POST /api/chat
```

---

## Step 7: QA Review (QA Coordinator + 8 Reviewers)

### Prompt
```
@Harness Run a full QA review on the SmartDoc Analyzer implementation.
Review all code, tests, infrastructure, and documentation.
```

### Expected behavior
- [ ] Harness delegates to **QA Coordinator**
- [ ] QA Coordinator runs MCP readiness check (Step 0)
- [ ] Launches 8 reviewers IN PARALLEL
- [ ] Synthesizes findings from all 8 perspectives
- [ ] Presents Manual QA Checklist
- [ ] Offers to create ADO bugs (if ADO available)

### Agents validated (9 agents)
- [x] **QA Coordinator** — MCP probes, orchestration, synthesis, manual QA checklist
- [x] **Architecture Reviewer** — layering, dependency direction
- [x] **Azure Compliance Reviewer** — your-cosmosdb-lib/your-storage-lib usage, AVM patterns
- [x] **Code Quality Reviewer** — copyright, docstrings, naming, debug code
- [x] **Security Reviewer** — OWASP, secrets, auth, XSS, input validation
- [x] **Test Coverage Reviewer** — test existence, coverage, Playwright checks
- [x] **UX & Accessibility Reviewer** — ARIA, alt text, keyboard, responsive
- [x] **LLM Behavior Reviewer** — prompt safety, grounding, citations, retry
- [x] **Deployment Readiness Reviewer** — health endpoint, logging, README, timeouts

### Skills validated (4 skills)
- [x] **sdlc-accelerator-qa** — 10-category product QA checklist
- [x] **sdlc-security-review** — OWASP Top 10 + team Azure patterns
- [x] **sdlc-code-quality** — naming, docstrings, commenting patterns
- [x] **sdlc-architecture-review** — layering rules, pattern reuse

### Expected artifacts
- [ ] QA Review Summary with Critical/Important/Suggestions sections
- [ ] Source attribution on each finding
- [ ] Overall Verdict (✅/⚠️/⛔)
- [ ] SDLC Exit Criteria Check (9 items)
- [ ] Manual QA Checklist (5 categories)

### Validation keywords
```
QA Review Summary|Critical Issues|Important Issues|Suggestions|Overall Verdict|SDLC Exit Criteria|Manual QA Checklist|Architecture Reviewer|Security Reviewer|UX.*Accessibility|LLM Behavior|Deployment Readiness
```

---

## Step 8: RAI Review (RAI Reviewer)

### Prompt
```
@Harness Run an RAI review on SmartDoc Analyzer.
The system uses Azure OpenAI for document Q&A — assess AI risks,
prompt injection, data leakage, and bias.
```

### Expected behavior
- [ ] Harness delegates to **RAI Reviewer**
- [ ] RAI Reviewer probes awesome-copilot for AI safety review
- [ ] Loads `ai-prompt-engineering-safety-review` instruction
- [ ] Assesses: prompt injection, data leakage, bias, transparency, human oversight, data retention, hallucination
- [ ] Produces structured RAI assessment with risk level

### Agents validated
- [x] **RAI Reviewer** — AI risk assessment, safety review

### Skills validated
- (loads awesome-copilot AI safety review)

### Expected artifacts
- [ ] RAI assessment with Risk Level (Low/Medium/High/Critical)
- [ ] Findings with severity
- [ ] Mitigations for each finding
- [ ] SDLC Exit Criteria Check (Phase 7)

### Validation keywords
```
RAI|Responsible AI|Risk Level|prompt injection|data leakage|bias|transparency|hallucination|mitigation|Phase 7
```

---

## Step 9: Release Preparation (Release Manager)

### Prompt
```
@Harness Prepare a release for SmartDoc Analyzer v1.0.
Create a changelog, verify exit criteria, and prepare the PR.
```

### Expected behavior
- [ ] Harness delegates to **Release Manager**
- [ ] Release Manager probes GitHub MCP
- [ ] Gathers commit history
- [ ] Generates changelog
- [ ] Verifies all SDLC exit criteria across phases
- [ ] Prepares PR body following `.github/PULL_REQUEST_TEMPLATE.md`

### Agents validated
- [x] **Release Manager** — changelog, PR preparation, exit criteria

### Skills validated
- (no skill — orchestration-focused)

### Expected artifacts
- [ ] Changelog content with categorized commits
- [ ] PR body matching PULL_REQUEST_TEMPLATE.md format
- [ ] Release checklist with all phases verified

### Validation keywords
```
Changelog|CHANGELOG|v1.0|Release|PR|Pull Request|SDLC Phase|exit criteria|feat:|fix:
```

---

## Step 10: QA Bug Checklist (QA Bug Checklist Reviewer — standalone)

### Prompt
```
@QA Bug Checklist Reviewer Run a bug checklist review on
the SmartDoc Analyzer project. Focus on deployment readiness.
```

### Expected behavior
- [ ] QA Bug Checklist Reviewer loads `sdlc-qa-bug-checklist` skill
- [ ] Runs applicable checklists (Deployment, AI/ML, Frontend, API, Identity)
- [ ] Cross-references with `sdlc-security-review` skill
- [ ] Reports findings with bug count sourcing

### Agents validated
- [x] **QA Bug Checklist Reviewer** — 338-bug pattern validation

### Skills validated
- [x] **sdlc-qa-bug-checklist** — 7 checklists from 338 ADO bugs

### Expected artifacts
- [ ] Bug checklist report with Blocker/Warning/Info/Pass items
- [ ] Bug count citations (e.g., "sourced from 38 bugs")
- [ ] Verdict: Ready / Ready with caveats / Not ready

### Validation keywords
```
Bug Checklist|Blocker|Warning|sourced from|bugs|Deployment|Identity|RBAC|post-deploy
```

---

## Summary Scorecard

| Step | Phase | Agent(s) | Skills Validated | Result |
|---|---|---|---|---|
| 0 | Init | Harness | — | [ ] PASS / [ ] FAIL |
| 1 | 1-2 | Analyst | sdlc-project-manifest | [ ] PASS / [ ] FAIL |
| 2 | 2 (auto) | Documenter | sdlc-adr-authoring | [ ] PASS / [ ] FAIL |
| 3 | 3 | Scaffolder | sdlc-project-scaffolding, sdlc-project-manifest | [ ] PASS / [ ] FAIL |
| 4 | 3+8 | Deployer | sdlc-azure-deployment | [ ] PASS / [ ] FAIL |
| 5 | 4 | Implementer | sdlc-cosmos-repository, sdlc-blob-storage | [ ] PASS / [ ] FAIL |
| 6 | 5 | Documenter | sdlc-adr-authoring | [ ] PASS / [ ] FAIL |
| 7 | 6 | QA Coordinator + 8 | sdlc-accelerator-qa, sdlc-security-review, sdlc-code-quality, sdlc-architecture-review | [ ] PASS / [ ] FAIL |
| 8 | 7 | RAI Reviewer | (awesome-copilot AI safety) | [ ] PASS / [ ] FAIL |
| 9 | 8-9 | Release Manager | — | [ ] PASS / [ ] FAIL |
| 10 | 6 (standalone) | QA Bug Checklist Reviewer | sdlc-qa-bug-checklist | [ ] PASS / [ ] FAIL |

### Agent Coverage

| Agent | Step | Tested |
|---|---|---|
| Harness (Coordinator) | 0-9 | [ ] |
| Analyst | 1 | [ ] |
| Documenter | 2, 6 | [ ] |
| Scaffolder | 3 | [ ] |
| Deployer | 4 | [ ] |
| Implementer | 5 | [ ] |
| QA Coordinator | 7 | [ ] |
| Architecture Reviewer | 7 | [ ] |
| Azure Compliance Reviewer | 7 | [ ] |
| Code Quality Reviewer | 7 | [ ] |
| Security Reviewer | 7 | [ ] |
| Test Coverage Reviewer | 7 | [ ] |
| UX & Accessibility Reviewer | 7 | [ ] |
| LLM Behavior Reviewer | 7 | [ ] |
| Deployment Readiness Reviewer | 7 | [ ] |
| QA Bug Checklist Reviewer | 10 | [ ] |
| RAI Reviewer | 8 | [ ] |
| Release Manager | 9 | [ ] |

### Skill Coverage

| Skill | Step(s) | Tested |
|---|---|---|
| sdlc-project-manifest | 1, 3 | [ ] |
| sdlc-adr-authoring | 2, 6 | [ ] |
| sdlc-project-scaffolding | 3 | [ ] |
| sdlc-azure-deployment | 4 | [ ] |
| sdlc-cosmos-repository | 5 | [ ] |
| sdlc-blob-storage | 5 | [ ] |
| sdlc-accelerator-qa | 7 | [ ] |
| sdlc-security-review | 7, 10 | [ ] |
| sdlc-code-quality | 7 | [ ] |
| sdlc-architecture-review | 7 | [ ] |
| sdlc-qa-bug-checklist | 10 | [ ] |

### MCP Server Coverage

| MCP Server | Tested in Step(s) |
|---|---|
| GitHub MCP | 0, 1, 2, 3, 4, 5, 7, 9 |
| awesome-copilot | 0, 1, 3, 4, 5, 7, 8, 10 |
| Context7 | 0, 1, 5 |
| Azure MCP | 4 |
| Microsoft Learn MCP | 4, 6, 8 |
| Azure DevOps MCP | 1, 4, 7 |
| Playwright MCP | 7 |
