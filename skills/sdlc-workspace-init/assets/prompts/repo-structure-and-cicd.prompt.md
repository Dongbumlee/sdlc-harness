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

This prompt supports **SDLC Phase 3 – Repo Structure Configuration**. The exit criteria
for this phase are the ones listed in this prompt.

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
3. Generate CI pipeline stubs (build + test + deploy stages) for GitHub Actions:
   `.github/workflows/ci.yml`. GitHub is the only supported forge and CI system.
4. Include quality gates (linting/type-checking configs).
5. Ensure the structure supports the SDLC phases (implementation, testing, docs, release).

## Context loading (MCP resources)

Before starting, load these resources for authoritative patterns:

1. **Template structure** — the GitHub MCP server's file-contents tool → fetch the directory structure
   from the matching template repo (`the base app template repo`, `the API template repo`,
   or `the agent template repo`)
2. **Docker best practices** — fetch `instructions/containerization-docker-best-practices.instructions.md`
   from the `github/awesome-copilot` repository via the GitHub MCP server's file-contents
   tool or `fetch` (skip if unreachable)
   (multi-stage builds, layer caching, image security)
3. **Kubernetes best practices** — fetch `instructions/kubernetes-deployment-best-practices.instructions.md`
   from the `github/awesome-copilot` repository via the GitHub MCP server's file-contents
   tool or `fetch` (skip if unreachable)
   (when scaffolding for AKS: pod security, resource limits, health checks)
4. **CI/CD pipeline best practices** — fetch `instructions/github-actions-ci-cd-best-practices.instructions.md`
   from the `github/awesome-copilot` repository via the GitHub MCP server's file-contents
   tool or `fetch` (skip if unreachable)
5. **Package manager docs** — Use **Context7 MCP** to get current `uv` / `azd` / Docker documentation

## IMPORTANT: Scope boundary

This prompt is for **scaffolding only** — folder structure, configuration files, CI/CD pipeline stubs, and Dockerfiles.

**DO generate:**
- Folder structure with empty/stub files
- `pyproject.toml` / `package.json` with dependencies listed
- `Dockerfile` per project (multi-stage build template)
- CI pipeline stubs (GitHub Actions; build + test + deploy stages)
- `.gitignore`, `.dockerignore`, `.env.example`
- Per-project `.devcontainer/` and `.github/`
- Stub `main.py` or `App.tsx` with minimal boilerplate (imports + app initialization only)
- Empty test directories with `conftest.py` or test config
- Root-level compliance files (`TRANSPARENCY_FAQ.md`, `CODE_OF_CONDUCT.md`, etc.)

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
| API | `the API template repo` | REST endpoints (FastAPI + routers + DI) |
| Business | `the base app template repo` | Shared domain models, business services, repositories |
| Agent | `the agent template repo` | AI agent with Azure AI Foundry + MCP tools |
| Web | React + Vite | Frontend UI |

### 2. Create layered folder structure under `src/`

Follow the application project pattern.
Each layer is an **independent project** under `src/` with its own devcontainer, Dockerfile, and dependencies:

```
src/
├── <ProjectName>API/              ← API layer (FastAPI REST endpoints)
│   ├── .devcontainer/
│   ├── app/                       ← routers/, services/, models/
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml             ← Independent deps (fastapi, the approved Cosmos DB library, the approved Storage library)
│   ├── .gitignore, .dockerignore, .env.example
│   └── .python-version
├── <ProjectName>Business/         ← Business logic / domain services layer
│   ├── .devcontainer/
│   ├── app/                       ← domain models, business rules, repositories, shared services
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml             ← Independent deps (the approved Cosmos DB library, the approved Storage library, pydantic)
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

Generate the GitHub Actions pipeline files (GitHub is the only supported CI system).

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

### 4. Quality gates

Every pipeline MUST include these quality gates:

| Gate | GitHub Actions |
|---|---|
| **Lint / format** | `ruff check` / `npx eslint` |
| **Type check** | `mypy` / `npx tsc --noEmit` |
| **Unit tests** | `pytest --cov` / `npx vitest run --coverage` |
| **Coverage target** | Report coverage against the stack profile's target (e.g., 80%) — a shortfall is recorded as a deviation, never a pipeline failure (Class 2) |
| **Security scan** | CodeQL + dependency review |
| **Docker build** | Build + scan image |

### 5. Infrastructure as Code — delegate to Deployment prompt

If the project needs Azure resource provisioning (Bicep/AVM templates, `azd` configuration,
Codespaces/Dev Containers), this is handled by a separate SDLC Phase:

> **Use `.github/prompts/deployment.prompt.md`** for all infrastructure-as-code work.
> It covers Bicep templates with AVM modules, `azure.yaml` for `azd`,
> Landing Zone alignment, Dockerfiles, and Dev Container configurations.

**This prompt (Phase 3) should NOT generate Bicep templates or infrastructure code.**
The Scaffolder agent correctly delegates infrastructure to the Deployer agent.

If the user asks for infrastructure during scaffolding, acknowledge the need and recommend
running the deployment prompt as a follow-up step.

### 6. SDLC Exit Criteria check (Phase 3)

Verify the following exit criteria:

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
 the approved Cosmos DB library and Blob Storage via the approved Storage library. Deploy to Azure Container Apps.
 I need GitHub Actions pipelines. Use the the API template repo
 as the base structure."
-->
