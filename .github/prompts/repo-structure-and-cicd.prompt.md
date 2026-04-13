---
description: "Set up or restructure repository layout, CI/CD pipelines, Dockerfiles, and devcontainers following application scaffolding templates."
agent: "Scaffolder"
argument-hint: "Describe the project type and deployment target"
---
<!--
File: .github/prompts/repo-structure-and-cicd.prompt.md

How to use (VS Code):
1. Open this prompt file in VS Code.
2. In Copilot Chat, say:
   "Use `.github/prompts/repo-structure-and-cicd.prompt.md` to set up the repo structure
    for a new FastAPI service deploying to Azure Container Apps."
-->

# Repo Structure Prompt (SDLC Phase 3)

You are setting up or updating the repository structure for a project.

This repository uses Azure services, standard scaffolding templates, and the architecture rules defined
in the repository custom instructions. Follow the reference catalog at `.github/reference-catalog.md`
for template selection.

This prompt supports **SDLC Phase 3 – Repo Structure Configuration** as defined in
`.github/SDLC-with-Copilot-and-Azure.md`. Follow its exit criteria.

## Inputs from the user

Ask the user to provide:
- Project type (API, worker, CLI, AI agent, etc.).
- Language / framework (Python, TypeScript, React, etc.).
- Azure resources involved (Cosmos DB, Blob Storage, AI Foundry, etc.).
- Deployment target: **Azure Container Apps** (default).
- Whether this is a new repo or an update to an existing one.

If any of these are unclear, ask 1–2 focused questions before proceeding.

## Goals

1. Scaffold repo structure aligned with the matching template from the reference catalog.
2. Set up per-project devcontainer configurations.
3. Generate per-project `azure_cicd.yaml` pipeline stubs (build + test + deploy stages).
4. Include quality gates (linting/type-checking configs).
5. Ensure the structure supports the SDLC phases (implementation, testing, docs, release).

## Context loading (MCP resources)

Before starting, load these resources for authoritative patterns:

1. **Template structure** — `mcp_github_get_file_contents` → fetch the directory structure
   from the matching template repo (`python_application_template`, `python_api_application_template`,
   or `python_agent_framework_dev_template`)
2. **Docker best practices** — `mcp_awesome-copil_load_instruction` → `"containerization-docker-best-practices"`
   (multi-stage builds, layer caching, image security)
3. **Kubernetes best practices** — `mcp_awesome-copil_load_instruction` → `"kubernetes-deployment-best-practices"`
   (when scaffolding for AKS: pod security, resource limits, health checks)
4. **CI/CD pipeline best practices** — load the one matching your pipeline platform:
   - ADO: `mcp_awesome-copil_load_instruction` → `"azure-devops-pipelines"`
   - GitHub Actions: `mcp_awesome-copil_load_instruction` → `"github-actions-ci-cd-best-practices"`
5. **Package manager docs** — Use **Context7 MCP** to get current `uv` / `azd` / Docker documentation
6. **ADO wiki** — Search the team's Azure DevOps wiki for scaffolding standards:
   - Search: `mcp_ado_search_wiki(searchText: "scaffolding OR project structure", project: "CSA CTO Engineering")`
   - Fetch content: `mcp_ado_wiki_get_page_content(wikiIdentifier: "CSA-CTO-Engineering.wiki", project: "CSA CTO Engineering", path: "/<page-path>")`

## IMPORTANT: Scope boundary

This prompt is for **scaffolding only** — folder structure, configuration files, CI/CD pipeline stubs, and Dockerfiles.

**DO generate:**
- Folder structure with empty/stub files
- `pyproject.toml` / `package.json` with dependencies listed
- `Dockerfile` per project (multi-stage build template)
- Per-project `azure_cicd.yaml` pipeline stubs (build + test + deploy stages)
- `.gitignore`, `.dockerignore`, `.env.example`
- Per-project `.devcontainer/` and `.github/`
- Stub `main.py` or `App.tsx` with minimal boilerplate (imports + app initialization only)
- Empty test directories with `conftest.py` or test config
- Root-level compliance files (`TRANSPARENCY_FAQ.md`, `CODE_OF_CONDUCT.md`, etc.)
- Empty test directories with `conftest.py` or test config

**DO NOT generate:**
- Business logic, service classes, or domain models
- API endpoint implementations (routers/controllers)
- Agent implementations
- React components with real UI
- Unit tests with actual test cases
- Database schemas or seed data

Business logic implementation belongs in **Phase 4** using `.github/prompts/implementation-and-tests.prompt.md`.
Agent implementation belongs in **Phase 4** using `.github/prompts/implementation-and-tests.prompt.md`.

## Steps

### 1. Select scaffolding template

Based on the project type, choose the matching template from `.github/reference-catalog.md`:

| Layer | Template | Use for |
|---|---|---|
| API | `python_api_application_template` | REST endpoints (FastAPI + routers + DI) |
| Business | `python_application_template` | Shared domain models, business services, repositories |
| Agent | `python_agent_framework_dev_template` | AI agent with Azure AI Foundry + MCP tools |
| Web | React + Vite | Frontend UI |

### 2. Create layered folder structure under `src/`

Each layer is an **independent project** under `src/` with its own devcontainer, Dockerfile, and dependencies:

```
src/
├── <ProjectName>API/              ← API layer (FastAPI REST endpoints)
│   ├── .devcontainer/
│   ├── app/                       ← routers/, services/, models/
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml             ← Independent deps (fastapi, your-cosmosdb-lib, your-storage-lib)
│   ├── .gitignore, .dockerignore, .env.example
│   └── .python-version
├── <ProjectName>Business/         ← Business logic / domain services layer
│   ├── .devcontainer/
│   ├── app/                       ← domain models, business rules, repositories, shared services
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml             ← Independent deps (your-cosmosdb-lib, your-storage-lib, pydantic)
│   └── .env.example
├── <ProjectName>Agent/            ← AI agent service (if applicable)
│   ├── .devcontainer/
│   ├── src/                       ← agents/, tools/, libs/agent_framework/
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml             ← Independent deps (agent framework, azure-ai)
│   └── .env.example
└── <ProjectName>Web/              ← Web frontend (React + TypeScript)
    ├── .devcontainer/
    ├── .github/                   ← Per-project copilot instructions
    ├── public/                    ← Static assets (favicon, index.html)
    ├── src/                       ← React source code
    │   ├── App.tsx
    │   ├── index.tsx
    │   ├── Components/            ← PascalCase folders (application convention)
    │   ├── Hooks/
    │   ├── Pages/
    │   ├── Services/              ← API client services
    │   ├── Styles/
    │   └── msal-auth/             ← Azure AD MSAL authentication
    ├── Dockerfile                 ← Multi-stage (node build → nginx serve)
    ├── nginx-custom.conf          ← Nginx reverse proxy config
    ├── package.json
    ├── tsconfig.json
    ├── eslint.config.mjs
    ├── .prettierrc
    ├── .pre-commit-config.yaml
    ├── .npmrc
    ├── .dockerignore
    ├── .gitignore
    ├── .env
    ├── README.md
    ├── azure_cicd.yaml            ← Per-project ADO CI/CD pipeline stub
    └── es-metadata.yml
```

**Naming convention:** `<ProjectName><Layer>` (e.g., `CustomerFeedbackAPI`, `CustomerFeedbackBusiness`).

**Layering rules:**
- **API** depends on **Business** (imports domain models, calls business services)
- **Agent** depends on **Business** (shares domain models, uses repositories)
- **Business** is the shared core — no dependency on API or Agent
- **Web** calls API via HTTP — no direct dependency on Python layers

### 3. Configure project files

Ensure these files exist per project and are correctly configured:

- **`pyproject.toml`** — dependencies, test config, coverage config
- **`.gitignore`** — language-appropriate exclusions
- **`.dockerignore`** — exclude tests, coverage artifacts, dev files
- **`Dockerfile`** per project — multi-stage build, production-optimized (mandatory)
- **`.env.example`** — document required environment variables (no secrets)
- **`.devcontainer/`** — per-project devcontainer (NOT at repo root)
- **`tests/`** directory — with `conftest.py` or test config
- **Quality instruction files** — select from `.github/instructions/*.instructions.md` for the language stack

### 3. Generate CI/CD pipelines

Based on the user's chosen platform, generate the appropriate pipeline files.

#### GitHub Actions

Create files under `.github/workflows/`:

**Build & Test** (`ci.yml`):
```yaml
# Triggers: push to main, pull_request
# Steps:
#   - Checkout
#   - Set up Python / Node.js
#   - Install dependencies (uv sync / npm ci)
#   - Lint / type-check
#   - Run tests with coverage
#   - Upload coverage report
```

**Security Scanning** (`security.yml`):
```yaml
# Triggers: push to main, pull_request, schedule (weekly)
# Steps:
#   - CodeQL analysis (if supported)
#   - Dependency review (for PRs)
#   - Secret scanning (built-in)
```

**Deployment** (`deploy.yml`):
```yaml
# Triggers: push to main (after CI passes), manual dispatch
# Steps:
#   - Build container image
#   - Push to Azure Container Registry
#   - Deploy to Azure Container Apps
#   - Run post-deploy health checks
# Environments: staging → production (with approval gate)
```

#### Azure DevOps (ADO)

Create pipeline files at the repo root or under `/ado/`:

**Build & Test** (`azure-pipelines.yml` or `ado/ci.yml`):
```yaml
# Trigger: main branch, PR validation
# Stages:
#   - Build: install deps, lint, type-check
#   - Test: run pytest/vitest with coverage, publish results
#   - Security: run security scanning tasks
```

**Deployment** (`ado/deploy.yml` or stages in main pipeline):
```yaml
# Stages:
#   - Build: produce artifact (container image or package)
#   - Deploy-Staging: deploy to staging, run smoke tests
#   - Approve: manual approval gate
#   - Deploy-Production: deploy to production, health check
#   - Post-Deploy: verify metrics (error rates, latency, Cosmos RU)
```

### 4. Quality gates

Every pipeline MUST include these quality gates:

| Gate | GitHub Actions | ADO |
|---|---|---|
| **Lint / format** | `ruff check` / `npx eslint` | Same commands in script tasks |
| **Type check** | `mypy` / `npx tsc --noEmit` | Same commands in script tasks |
| **Unit tests** | `pytest --cov` / `npx vitest run --coverage` | Same with test result publishing |
| **Coverage threshold** | Fail if below threshold (e.g., 80%) | Same with coverage gates |
| **Security scan** | CodeQL + dependency review | Built-in security tasks or third-party |
| **Docker build** | Build + scan image | Build + scan image |

### 5. Infrastructure as Code — delegate to Deployment prompt

If the project needs Azure resource provisioning (Bicep/AVM templates, `azd` configuration,
Codespaces/Dev Containers), this is handled by a separate SDLC Phase:

> **Use `.github/prompts/deployment.prompt.md`** for all infrastructure-as-code work.
> It covers Bicep templates with AVM modules, `azure.yaml` for `azd`, WAF toggle parameters,
> Landing Zone alignment, Dockerfiles, and Dev Container configurations.

**This prompt (Phase 3) should NOT generate Bicep templates or infrastructure code.**
The Scaffolder agent correctly delegates infrastructure to the Deployer agent.

If the user asks for infrastructure during scaffolding, acknowledge the need and recommend
running the deployment prompt as a follow-up step.

### 6. SDLC Exit Criteria check (Phase 3)

Verify the following exit criteria from `.github/SDLC-with-Copilot-and-Azure.md`:

- Repository folders and projects are created or updated to match architecture and templates.
- Pipeline definitions are updated or confirmed to:
  - Build and test the new code.
  - Run existing checks without regressions.
- Quality instruction files are in place for the repo's language stack.
- `.gitignore` and `.dockerignore` are properly configured.
- For each criterion, mark it as:
  - ✅ satisfied
  - ⚠️ partially satisfied (explain what remains)
  - ⛔ not satisfied (explain what is missing)

## Output format

Return a single markdown response with these sections:

- **Template Selection** — which template and why
- **Repo Structure** — proposed folder tree with explanations
- **Project Configuration** — `pyproject.toml`, `.gitignore`, `Dockerfile`, etc.
- **CI/CD Pipeline Files** — full YAML content, ready to paste
- **Quality Gates** — summary of gates and thresholds
- **Infrastructure** (if applicable) — Bicep templates, `azure.yaml`
- **Follow-up Tasks** — what needs manual setup (secrets, service connections, environments)
- **SDLC Exit Criteria Check (Phase 3)** with ✅/⚠️/⛔

<!--
Example invocation for engineers:

"Copilot, use `.github/prompts/repo-structure-and-cicd.prompt.md` to:
 Set up a new FastAPI service for order processing. It uses Cosmos DB via
 your-cosmosdb-lib and Blob Storage via your-storage-lib. Deploy to Azure Container Apps.
 I need both GitHub Actions and ADO pipelines. Use the python_api_application_template
 as the base structure."
-->
