# SDLC End-to-End Test Script

> **Purpose:** Validate the entire 9-phase SDLC Agent pipeline using a realistic feature scenario.\
> **Scenario:** "Customer Feedback API" — a FastAPI service with Cosmos DB storage and React frontend.\
> **Duration:** ~60–90 minutes for a full run.\
> **Prerequisite:** VS Code with GitHub Copilot, MCP servers configured.

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │  🧪 E2E Test Flow                                                  │
 │                                                                    │
 │  Init → Analyze → Design → Scaffold → Deploy → Implement →        │
 │  Document → QA (9 reviewers) → RAI → Release                      │
 │                                                                    │
 │  19 agents · 16 skills · 7 MCP servers · 9 SDLC phases            │
 └──────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required software

- [ ] **VS Code** with GitHub Copilot + Copilot Chat extensions installed
- [ ] **Docker Desktop** — must be **running** before starting (required to host the `awesome-copilot` MCP server, which runs as a Docker container)
- [ ] **Node.js 20+** — required for MCP servers that use `npx` (`azure`, `azure-devops`, `context7`)
- [ ] **Python 3.12+** and **uv** package manager
- [ ] **Azure CLI** + **Azure Developer CLI (azd)** (for deployment tests)

### Start MCP servers

Before running any tests, you **must start all MCP servers** listed in `.vscode/mcp.json`:

1. Open `.vscode/mcp.json` in VS Code.
2. VS Code shows a **"Start"** button above each server definition — click **Start** on each one.
3. Verify all 6 servers are running (green status):

   | Server            | Requires                       | How to verify                                       |
   | ----------------- | ------------------------------ | --------------------------------------------------- |
   | `awesome-copilot` | Docker Desktop running         | Docker container `awesome-copilot:latest` is active |
   | `github`          | Copilot signed in              | GitHub MCP indicator in chat                        |
   | `azure`           | Node.js + `az login`           | No error in MCP output                              |
   | `azure-devops`    | Node.js (prompts for org name) | Browser login on first tool call                    |
   | `microsoft-learn` | (HTTP — always available)      | No action needed                                    |
   | `context7`        | Node.js                        | No error in MCP output                              |

4. If the `awesome-copilot` server fails to start, check that Docker Desktop is running:
   ```bash
   docker ps  # Should show the container if started manually
   docker run -i --rm ghcr.io/microsoft/mcp-dotnet-samples/awesome-copilot:latest  # Test manually
   ```

> **Important:** If MCP servers are not started, agents will fail silently when trying to load
> best practices (awesome-copilot), fetch reference patterns (github), or access documentation
> (microsoft-learn, context7). Always start servers before beginning the test.

---

## Pre-Flight Checklist

Before starting, verify these are in place:

- [ ] All **Prerequisites** above are met (Docker Desktop running, Node.js installed)
- [ ] All **6 MCP servers** are started in `.vscode/mcp.json` (see table above)
- [ ] VS Code is open with this repo as the workspace root
- [ ] GitHub Copilot extension is signed in
- [ ] `.github/copilot-instructions.md` still has unfilled placeholders (for first-run init test)
- [ ] `docs/adr/` folder is empty (clean slate)
- [ ] `docs/api/` folder is empty (clean slate)

---

## Test Overview

| Step | SDLC Phase     | Agent Chain                          | Duration |
| ---- | ------------- | ------------------------------------ | -------- |
| 0    | Pre-flight    | Harness (init)                         | 2 min    |
| 1    | Phase 1-2     | Harness → Analyst                      | 10 min   |
| 2    | Phase 2 (ADR) | Harness → Documenter                   | 5 min    |
| 3    | Phase 3       | Harness → Scaffolder                   | 10 min   |
| 4    | Phase 3+8     | Harness → Deployer                     | 10 min   |
| 5    | Phase 4       | Harness → Implementer                  | 15 min   |
| 6    | Phase 5       | Harness → Documenter                   | 5 min    |
| 7    | Phase 6       | Harness → QA Coordinator → 9 Reviewers | 10 min   |
| 8    | Phase 7       | Harness → RAI Reviewer                 | 5 min    |
| 9    | Phase 8-9     | Harness → Release Manager              | 5 min    |

---

## Step 0 — First-Run Initialization (Harness)

### Prompt to send to `@Harness`:

```
I want to build a Customer Feedback API for our team.
Users submit feedback with a rating (1-5), text comment, and category.
We need a REST API to store and query feedback.
```

### Expected behavior:

- [ ] **Workspace initialization** — Harness checks environment and probes MCP servers:
  - [ ] `awesome-copilot` — runs `mcp_awesome-copil_search_instructions(keywords: "security")` — **hard stop if unavailable**
  - [ ] `GitHub MCP` — probes reference repos if available — **optional, graceful degradation to reference-catalog.md**
  - [ ] `Context7` — runs `mcp_context7_resolve-library-id(libraryName: "fastapi")` — **warn if unavailable**
- [ ] **Status table reported** — Harness shows a table with ✅/⚠️/⛔ status for each server
- [ ] **Failure handling** — If awesome-copilot is down, Harness stops. If GitHub MCP unavailable, Harness continues with warning.
- [ ] **Placeholder detection** — Harness detects unfilled placeholders in `.github/copilot-instructions.md`
- [ ] **Questions asked** — Harness asks 2-3 quick questions:
  - Project name → answer: `"customer-feedback-service"`
  - Business domain → answer: `"Customer Experience"`
  - Tech stack preferences → answer: `"Python, FastAPI, React"`
- [ ] **Config update** — Harness fills `<PROJECT_NAME>`, `<BUSINESS_DOMAIN>`, `<TECH_STACK>` in `copilot-instructions.md`
- [ ] **Phase identification** — Harness identifies this as Phase 1-2 and delegates to Analyst

### Verification:

```
Open .github/copilot-instructions.md and confirm:
- <PROJECT_NAME> → "customer-feedback-service"
- <BUSINESS_DOMAIN> → "Customer Experience"
- <TECH_STACK> → "Python 3.12, FastAPI, React, TypeScript" (or similar)
- <ARCH_STYLE>, <OTHER_AZURE_SERVICES>, <LOGGER_ABSTRACTION> → still placeholders (filled later)
```

### Result: [ ] PASS / [ ] FAIL

**Notes:**
___________________________________________________________________________

---

## Step 1 — Phase 1-2: Requirements & Design (Analyst)

### Prompt to send to `@Harness`:

```
Analyze requirements for the Customer Feedback API:

Functional requirements:
- Users submit feedback with: rating (1-5), text comment, category (bug, feature, general)
- API returns feedback by ID, by category, or all (paginated)
- Optional: aggregate ratings by category

Non-functional:
- Store in Azure Cosmos DB (SQL API)
- REST API via FastAPI
- React frontend for submission and viewing
- Deploy to Azure Container Apps

Please produce a design proposal.
```

### Expected behavior:

- [ ] **GitHub MCP (optional)** — Analyst probes reference repos if available; falls back to reference-catalog.md
- [ ] **awesome-copilot loaded** — `"project-planning"` collection + `"task-implementation"` instruction
- [ ] **Reference catalog fetched** — via GitHub MCP or local `.github/reference-catalog.md`
- [ ] **Context7 used** — FastAPI / Pydantic docs loaded
- [ ] **ADO wiki checked** — Attempts to fetch team standards (may fail gracefully if not configured)
- [ ] **Skills awareness** — Analyst output aligns with `sdlc-cosmos-repository` skill patterns (entity extends `RootEntityBase`, repo extends `RepositoryBase`)

### Expected output — ADR-ready design with these sections:

- [ ] **Context** — customer feedback collection system
- [ ] **Problem / Requirements** — functional + non-functional listed
- [ ] **Design / Implementation** — includes:
  - [ ] Layered architecture (API → Application → Domain → Infrastructure)
  - [ ] Azure services mapped: Cosmos DB → the approved Cosmos DB SDK wrapper, Container Apps
  - [ ] Data model: `Feedback` entity extending `RootEntityBase`
  - [ ] API endpoints: `POST /feedback`, `GET /feedback/{id}`, `GET /feedback?category=...`
  - [ ] Repository: `FeedbackRepository` extending `RepositoryBase`
- [ ] **Alternatives Considered** — e.g., Table Storage vs Cosmos DB
- [ ] **Testing Strategy** — unit tests for service, integration tests for API
- [ ] **RAI / Risk Considerations** — user text content moderation
- [ ] **SDLC Impact by Phase** — what each phase needs to do
- [ ] **Open Questions** — listed for human decision
- [ ] **Project Configuration** — `TECH_STACK`, `ARCH_STYLE`, `OTHER_AZURE_SERVICES` values for Harness
- [ ] **SDLC Exit Criteria** — checklist with ✅/⚠️/⛔ statuses

### Reference catalog checks:

- [ ] Analyst asks about preferred libraries before populating the reference catalog
- [ ] Analyst populates `.github/reference-catalog.md` with entries under the 5 fixed sections
- [ ] Each catalog entry includes source attribution
- [ ] Harness presents catalog summary and review checkpoint (if `catalog_review: true`)

### Red flags (should NOT happen):

- [ ] ~~Raw `CosmosClient` proposed instead of the approved Cosmos DB SDK wrapper~~
- [ ] ~~Raw `BlobServiceClient` proposed instead of the approved Storage SDK wrapper~~
- [ ] ~~New architectural pattern invented without checking existing code~~

### Result: [ ] PASS / [ ] FAIL

**Notes:**
___________________________________________________________________________

---

## Step 2 — Phase 2 (ADR): Auto-Documentation (Documenter)

### Expected behavior (automatic — no prompt needed):

Per Harness's ADR generation rule, after the Analyst returns a design, Harness MUST automatically
delegate to the Documenter to save it as an ADR.

- [ ] **Auto-delegation** — Harness delegates to Documenter without user prompt
- [ ] **`sdlc-adr-authoring` skill activated** — Documenter reads `.github/skills/sdlc-adr-authoring/SKILL.md`
- [ ] **awesome-copilot ADR skill loaded** — `create-architectural-decision-record/SKILL.md` via MCP
- [ ] **Template used** — Documenter reads `.design/ADR-TEMPLATE.md` (SDLC template takes precedence)
- [ ] **GitHub MCP (optional)** — Documenter probes reference repos if available; falls back to local patterns
- [ ] **ADR file created** — `docs/adr/ADR-001-customer-feedback-api.md` (or similar)
- [ ] **ADR structure correct** — matches SDLC template: Context, Problem, Design, Alternatives, Testing, RAI, SDLC Impact
- [ ] **Status set** — `Proposed`
- [ ] **Progressive config** — Harness fills `<ARCH_STYLE>` in `copilot-instructions.md`

### Verification:

```
1. Check docs/adr/ — should contain ADR-001-*.md
2. Open the ADR — verify it follows .design/ADR-TEMPLATE.md structure
3. Check .github/copilot-instructions.md — <ARCH_STYLE> should now be filled
```

### Result: [ ] PASS / [ ] FAIL

**Notes:**
___________________________________________________________________________

---

## Step 3 — Phase 3: Repo Structure & CI/CD (Scaffolder)

### Prompt to send to `@Harness`:

```
Scaffold the project structure for the Customer Feedback API based on the design.
We need a layered architecture following the application pattern:
- CustomerFeedbackAPI — FastAPI backend (API layer)
- CustomerFeedbackBusiness — shared domain models, repositories, services (Business layer)
- CustomerFeedbackWeb — React frontend (Web layer)
Use the API application template for API, base application template for Business.
```

### Expected behavior:

- [ ] **GitHub MCP (optional)** — Scaffolder probes template repos if available; falls back to reference-catalog.md
- [ ] **`sdlc-project-scaffolding` skill activated** — reads `.github/skills/sdlc-project-scaffolding/SKILL.md`
- [ ] **Template fetched** — `API application template` structure retrieved via GitHub MCP
- [ ] **awesome-copilot loaded (via skill)** — `multi-stage-dockerfile` + `containerization-docker-best-practices`
- [ ] **Context7 used** — `uv` / Docker docs loaded

### Expected output — layered project structure created:

- [ ] `src/CustomerFeedbackAPI/` — API layer with:
  - [ ] `app/routers/` — API route handlers
  - [ ] `app/services/` — application services (orchestration)
  - [ ] `tests/` — API-level tests
  - [ ] `pyproject.toml` — with the approved Cosmos DB SDK wrapper, `fastapi` dependencies
  - [ ] `Dockerfile` — multi-stage build
  - [ ] `.devcontainer/` — per-project devcontainer
  - [ ] `.gitignore`, `.dockerignore`, `.env.example`
- [ ] `src/CustomerFeedbackBusiness/` — Business layer with:
  - [ ] `app/models/` or `app/entities/` — domain models (Feedback entity)
  - [ ] `app/repositories/` — data access (FeedbackRepository)
  - [ ] `app/services/` — shared business logic
  - [ ] `tests/` — unit tests
  - [ ] `pyproject.toml` — with the approved Cosmos DB SDK wrapper, the approved Storage SDK wrapper, `pydantic` dependencies
  - [ ] `Dockerfile`, `.devcontainer/`
- [ ] `src/CustomerFeedbackWeb/` — Web layer with:
  - [ ] `src/` — React source (components, hooks, pages)
  - [ ] `package.json` — dependencies
  - [ ] `Dockerfile` — multi-stage build
  - [ ] `.devcontainer/`
- [ ] Quality instruction files confirmed for Python + TypeScript stack
- [ ] Root-level compliance files created (`TRANSPARENCY_FAQ.md`, `CODE_OF_CONDUCT.md`, etc.)

### Reference catalog checks:

- [ ] Scaffolder reads `.github/reference-catalog.md` before starting
- [ ] Scaffolder uses catalog entries for library selection (not independent research)
- [ ] Scaffolder appends new discoveries with `Source: Scaffolder (Phase 3)`

### Red flags:

- [ ] ~~Project folders created directly at repo root instead of under `src/` — e.g., `root/app/` instead of `root/src/<Name>API/app/`~~
- [ ] ~~Single root-level devcontainer instead of per-project~~
- [ ] ~~`pip` or `poetry` used instead of `uv`~~
- [ ] ~~Flat `src/api/`, `src/web/` naming instead of `<ProjectName><Layer>` convention~~
- [ ] ~~No Business layer — domain models mixed into API project~~
- [ ] ~~CI/CD pipeline files generated (not in Scaffolder scope — belongs to Deployer)~~

### SDLC Exit Criteria reported by Scaffolder:

- [ ] Repository folders match template: ✅/⚠️/⛔
- [ ] `pyproject.toml` configured correctly: ✅/⚠️/⛔
- [ ] Quality instruction files in place: ✅/⚠️/⛔
- [ ] Dockerfile per project with multi-stage build: ✅/⚠️/⛔
- [ ] Per-project devcontainer configured: ✅/⚠️/⛔

### Result: [ ] PASS / [ ] FAIL

**Notes:**
___________________________________________________________________________

---

## Step 4 — Phase 3+8: Deployment & Infrastructure (Deployer)

### Prompt to send to `@Harness`:

```
Set up Azure infrastructure for the Customer Feedback API:
- Azure Cosmos DB (SQL API) for feedback storage
- Azure Container Apps for the API and web frontend
- Azure Container Registry for images
- Use Bicep with AVM modules
- Configure azd for orchestration
```

### Expected behavior:

- [ ] **`sdlc-azure-deployment` skill activated** — reads `.github/plugin/packs/azure/skills/sdlc-azure-deployment/SKILL.md`
- [ ] **ADO wiki fetched FIRST** — all 7 Bicep-development subsections (Bicep-standards, WAF-configuration-by-resource, AVM-publishing-process, Reusable-Network-Module-for-AVM-WAF, network, network_subnet_design)
- [ ] **AVM registry checked** — `#fetch https://azure.github.io/Azure-Verified-Modules/indexes/bicep/bicep-resource-modules/` for module availability and latest versions
- [ ] **GitHub MCP (optional)** — Deployer probes reference repos if available; falls back to local Bicep patterns
- [ ] **awesome-copilot loaded (via skill)** — `azure-deployment-preflight` + `update-avm-modules-in-bicep` + `bicep-code-best-practices`
- [ ] **Azure MCP Bicep tools used** — AVM module discovery, resource type schemas
- [ ] **Existing Bicep patterns fetched** — from application repos via GitHub MCP
- [ ] **Azure MCP used** — resource validation (if configured)
- [ ] **MS Learn MCP used** — AVM module documentation

### Expected output:

- [ ] `infra/main.bicep` — orchestrator template
- [ ] `infra/modules/` — Bicep modules using AVM (`br/public:avm/res/...`)
  - [ ] Cosmos DB account + database + container
  - [ ] Container Apps Environment + Container Apps
  - [ ] Container Registry
  - [ ] Log Analytics workspace
- [ ] `infra/main.parameters.json` — non-WAF parameters
- [ ] `infra/main.waf.parameters.json` — WAF-aligned parameters
- [ ] WAF toggle parameters: `enablePrivateNetworking`, `enableMonitoring`, `enableRedundancy`, `enableScalability`
- [ ] `azure.yaml` — `azd` configuration with service mappings
- [ ] Standard tags on all resources: `azd-env-name`, `TemplateName`, `CreatedBy`
- [ ] **Progressive config** — Harness fills `<OTHER_AZURE_SERVICES>` in `copilot-instructions.md`

### Verification:

```
1. Check infra/ folder — Bicep files should exist
2. Verify AVM module references (br/public:avm/res/...)
3. Check azure.yaml — service mappings correct
4. Check .github/copilot-instructions.md — <OTHER_AZURE_SERVICES> should be filled
```

### Result: [ ] PASS / [ ] FAIL

**Notes:**
___________________________________________________________________________

---

## Step 5 — Phase 4: Implementation & Tests (Implementer)

### Prompt to send to `@Harness`:

```
Implement the Customer Feedback API according to the design.
Follow the strict code → unit test → next step sequence:

1. Domain layer: Feedback entity using the approved Cosmos DB SDK wrapper RootEntityBase → unit test for validation
2. Infrastructure layer: FeedbackRepository using the approved Cosmos DB SDK wrapper RepositoryBase → unit test with mocked DB
3. Application layer: FeedbackService with business logic → unit test with mocked repository
4. API layer: FastAPI routes (POST /feedback, GET /feedback/{id}, GET /feedback?category=...) → unit test for routes
5. Integration tests for API endpoints (after all code + unit tests)
6. Run all tests: uv run pytest --cov
```

### Expected behavior:

- [ ] **GitHub MCP (optional)** — Implementer probes SDK repos if available; falls back to reference-catalog.md patterns
- [ ] **`sdlc-cosmos-repository` skill activated** — Implementer reads `.github/plugin/packs/azure/skills/sdlc-cosmos-repository/SKILL.md` for entity/repo patterns
- [ ] **`sdlc-blob-storage` skill activated** — (if blob operations needed) reads `.github/plugin/packs/azure/skills/sdlc-blob-storage/SKILL.md`
- [ ] **awesome-copilot Cosmos skill loaded** — `cosmosdb-datamodeling/SKILL.md` via MCP (loaded by skill)
- [ ] **Live SDK patterns fetched** — `HANDS_ON_GUIDE.md` from `Cosmos DB library repo` via GitHub MCP
- [ ] **Context7 used** — FastAPI + Pydantic docs loaded

### Expected output — code files created (with tests per step):

#### Step 1: Domain Layer → Unit Test
- [ ] `Feedback` entity extending `RootEntityBase["Feedback", str]`
  - Fields: `id`, `rating` (1-5), `text`, `category` (enum: bug/feature/general), `created_at`
  - Pydantic validation on rating range
- [ ] **Unit test** for entity validation in `tests/`

#### Step 2: Infrastructure Layer → Unit Test
- [ ] `FeedbackRepository` extending `RepositoryBase[Feedback, str]`
  - Constructor with `connection_string`, `database_name`, `container_name`
  - Uses `async with` pattern
- [ ] **Unit test** with mocked Cosmos DB in `tests/`

#### Step 3: Application Layer → Unit Test
- [ ] `FeedbackService` — orchestrates repository calls
  - `create_feedback_async()`, `get_feedback_async()`, `list_feedback_async()`
  - Business validation (e.g., text length limits)
- [ ] **Unit test** with mocked repository in `tests/`
  - Happy path: create, get, list
  - Edge cases: invalid rating, empty text, not found
  - Arrange–Act–Assert structure

#### Step 4: API Layer → Unit Test
- [ ] `POST /feedback` — creates feedback, returns 201
- [ ] `GET /feedback/{id}` — returns feedback by ID, 404 if not found
- [ ] `GET /feedback?category=bug&page=1&size=10` — paginated query
- [ ] Pydantic request/response models
- [ ] **Unit test** for route handlers in `tests/`

#### Step 5: Integration Tests (after all code + unit tests)
- [ ] HTTP-level integration tests using test client
- [ ] All endpoint scenarios covered
- [ ] Tests in `tests/integration/`

#### Step 6: Run All Tests
- [ ] `uv run pytest --cov` passes with all tests green
- [ ] Dockerfile uses `uv sync --frozen` (NOT `pip install`)

### Red flags:

- [ ] ~~Raw `CosmosClient` used instead of the approved Cosmos DB SDK wrapper RepositoryBase~~
- [ ] ~~`os.getenv()` used instead of Pydantic `BaseSettings`~~
- [ ] ~~No tests generated alongside code (tests batched at end)~~
- [ ] ~~Infrastructure called directly from router (skip Application layer)~~
- [ ] ~~`pip install` used instead of `uv sync` in Dockerfile~~
- [ ] ~~Tests placed inside `app/` or `src/` instead of project-root `tests/`~~

### SDLC Exit Criteria reported by Implementer:

- [ ] Feature follows architecture layering rules: ✅/⚠️/⛔
- [ ] Unit tests with Arrange-Act-Assert: ✅/⚠️/⛔
- [ ] Integration tests for API/data access: ✅/⚠️/⛔
- [ ] All tests pass: ✅/⚠️/⛔
- [ ] Quality instruction files respected: ✅/⚠️/⛔
- [ ] Approved SDK abstractions used: ✅/⚠️/⛔

### Result: [ ] PASS / [ ] FAIL

**Notes:**
___________________________________________________________________________

---

## Step 6 — Phase 5: Documentation (Documenter)

### Prompt to send to `@Harness`:

```
Update documentation for the Customer Feedback API:
1. API documentation for all feedback endpoints
2. Update the project README
```

### Expected behavior:

- [ ] **GitHub MCP (optional)** — Documenter probes reference repos if available; falls back to local patterns
- [ ] **API doc template used** — reads `.design/API-DOC-TEMPLATE.md`
- [ ] **README template used** — reads `.design/README.template.md`
- [ ] **MS Learn MCP used** — for Azure service documentation references

### Expected output:

- [ ] `docs/api/feedback-api.md` — API documentation with:
  - [ ] All endpoints listed (POST, GET by ID, GET with query)
  - [ ] Request/response schemas
  - [ ] Error codes and examples
  - [ ] Authentication requirements
- [ ] `README.md` updated — or new project README with:
  - [ ] Project overview
  - [ ] Architecture summary
  - [ ] Getting started / setup instructions
  - [ ] Azure resources required

### Result: [ ] PASS / [ ] FAIL

**Notes:**
___________________________________________________________________________

---

## Step 7 — Phase 6: QA Activities (QA Coordinator + 9 Reviewers)

### Prompt to send to `@Harness`:

```
Run a full QA review on the Customer Feedback API implementation.
Review all code, tests, infrastructure, and documentation.
```

### Expected behavior:

- [ ] **Harness delegates to QA Coordinator**
- [ ] **QA Coordinator launches 9 reviewers IN PARALLEL** (not sequentially)

### 9 Parallel Reviewers — what each should do:

#### 1. Architecture Reviewer
- [ ] **`sdlc-architecture-review` skill activated** — reads `.github/skills/sdlc-architecture-review/SKILL.md`
- [ ] awesome-copilot loaded (via skill): `architecture-blueprint-generator/SKILL.md`
- [ ] GitHub MCP (optional) — probes reference repos if available; falls back to reference-catalog.md
- [ ] `mcp_github_search_code` for `RepositoryBase` patterns (if GitHub MCP available)
- [ ] Reads `.github/reference-catalog.md`
- [ ] Checks: layering, dependency direction, pattern reuse, no God services, template alignment
- [ ] Output: Critical / Important / Suggestion / Positive findings

#### 2. Azure Compliance Reviewer
- [ ] GitHub MCP (optional) — probes SDK repos if available; falls back to reference-catalog.md
- [ ] Fetches latest SDK APIs from `Cosmos DB library repo` + `Storage library repo`
- [ ] awesome-copilot: `"bicep-code-best-practices"` loaded
- [ ] Checks: the approved Cosmos DB SDK wrapper usage, `RepositoryBase` pattern, `async with`, AVM modules, tags, diagnostics
- [ ] Output: Critical / Important / Suggestion / Positive findings

#### 3. Code Quality Reviewer
- [ ] **`sdlc-code-quality` skill activated** — reads `.github/skills/sdlc-code-quality/SKILL.md`
- [ ] awesome-copilot loaded (via skill): `"self-explanatory-code-commenting"`, `"performance-optimization"`, `"object-calisthenics"`
- [ ] Reads `.github/instructions/code-quality-py.instructions.md`
- [ ] Checks: copyright headers, docstrings, naming, dead code, comments, type safety, imports, DRY
- [ ] Output: Critical / Important / Suggestion / Positive findings

#### 4. Security Reviewer
- [ ] **`sdlc-security-review` skill activated** — reads `.github/skills/sdlc-security-review/SKILL.md`
- [ ] awesome-copilot loaded (via skill): `"security-and-owasp"` (fresh every review)
- [ ] Project-specific Azure checks applied: Managed Identity, Key Vault, the approved Cosmos DB SDK wrapper/the approved Storage SDK wrapper auth
- [ ] Checks: OWASP Top 10 mapped, secrets, credentials, CORS, headers, input validation, dependencies
- [ ] Output: Critical / Important / Suggestion / Positive findings

#### 5. Test Coverage Reviewer
- [ ] awesome-copilot loaded: `"playwright-typescript"` / `"playwright-python"`
- [ ] Reads `.github/instructions/test-quality.instructions.md`
- [ ] Runs `pytest --cov` (if possible)
- [ ] Checks: test existence, AAA structure, naming, isolation, mocking, edge cases, assertions, coverage
- [ ] Output: Critical / Important / Suggestion / Positive findings

#### 6. Requirements Completeness Reviewer
- [ ] **`sdlc-requirements-discovery` skill activated** — reads `.github/skills/sdlc-requirements-discovery/SKILL.md`
- [ ] Cross-references implementation against design requirements from ADR
- [ ] Checks: all functional requirements addressed, NFRs covered, edge cases identified
- [ ] Checks: acceptance criteria mapped to tests, no requirement gaps
- [ ] Output: Critical / Important / Suggestion / Positive findings

#### 7. UX & Accessibility Reviewer
- [ ] **`sdlc-project-qa` skill activated** — reads `.github/skills/sdlc-project-qa/SKILL.md`
- [ ] Categories 1-2 applied (UX & Accessibility, Core Functionality & State)
- [ ] Checks: ARIA labels, alt text, keyboard nav, focus indicators, dark mode CSS, error boundaries
- [ ] Emits manual QA items: cross-browser, screen reader, high-DPI, golden path
- [ ] Output: Critical / Important / Suggestion / Positive + Manual QA Required

#### 8. LLM Behavior Reviewer
- [ ] **`sdlc-project-qa` skill activated** — reads `.github/skills/sdlc-project-qa/SKILL.md`
- [ ] Categories 3-4 applied (LLM & Agent Behavior, Data & File Handling)
- [ ] Checks: system prompt protection, content filters, prompt injection guards, citations, grounding, retry logic
- [ ] Checks: file type validation, size limits, filename sanitization, encoding handling
- [ ] Emits manual QA items: grounding accuracy, citation verification, prompt brittleness
- [ ] Output: Critical / Important / Suggestion / Positive + Manual QA Required

#### 9. Deployment Readiness Reviewer
- [ ] **`sdlc-project-qa` skill activated** — reads `.github/skills/sdlc-project-qa/SKILL.md`
- [ ] Categories 5, 7-9 applied (Error Handling, Performance, Repo Hygiene, Observability)
- [ ] Checks: error exposure, rate limits, global exception handler, timeouts, unbounded queries, pagination
- [ ] Checks: README completeness, hyperlink integrity, stale refs, debug code, dependency health
- [ ] Checks: structured logging, health endpoint, correlation IDs, known issues doc
- [ ] Emits manual QA items: clean-environment deploy, response time benchmarks
- [ ] Output: Critical / Important / Suggestion / Positive + Manual QA Required

### Expected synthesized output from QA Coordinator:

- [ ] **Prioritized summary** with sections:
  - Critical Issues (must fix before merge)
  - Important Issues (should fix)
  - Suggestions (nice to have)
  - What the code does well
- [ ] **Source attribution** — each finding tagged with its reviewer
- [ ] **Overall Verdict** — ✅ Approve / ⚠️ Approve with conditions / ⛔ Request changes
- [ ] **Manual QA Checklist** appended with human-required test items from reviewers 6-8
- [ ] **ADO bug filing offer** — asks user to confirm before creating Bug work items

### SDLC Exit Criteria reported by QA Coordinator:

- [ ] All 9 review perspectives completed: ✅/⚠️/⛔
- [ ] No critical issues remaining: ✅/⚠️/⛔
- [ ] Automated tests pass: ✅/⚠️/⛔
- [ ] Code quality standards met: ✅/⚠️/⛔
- [ ] Security review passed: ✅/⚠️/⛔
- [ ] Azure compliance verified: ✅/⚠️/⛔
- [ ] UX & accessibility checks passed: ✅/⚠️/⛔
- [ ] LLM behavior & safety verified: ✅/⚠️/⛔
- [ ] Deployment readiness confirmed: ✅/⚠️/⛔

### Result: [ ] PASS / [ ] FAIL

**Notes:**
___________________________________________________________________________

---

## Step 8 — Phase 7: RAI Review (RAI Reviewer)

### Prompt to send to `@Harness`:

```
Run an RAI (Responsible AI) review on the Customer Feedback API.
The system collects user-submitted text feedback — assess data handling and privacy risks.
```

### Expected behavior:

- [ ] **awesome-copilot loaded** — `"ai-prompt-engineering-safety-review"` instruction
- [ ] **MS Learn MCP used** — RAI guidelines fetched (optional)

### Expected output:

- [ ] **Risk Level assigned** — likely Low or Medium (no AI models, but user text data)
- [ ] **Checklist assessed:**
  - [ ] Data leakage — feedback text exposure risks?
  - [ ] Bias — category classification fairness?
  - [ ] Transparency — clear what data is collected?
  - [ ] Data retention — how long feedback stored? Deletion policy?
  - [ ] Privacy — PII in free-text feedback?
- [ ] **Mitigations recommended:**
  - [ ] Input sanitization for text field
  - [ ] Data retention policy documentation
  - [ ] No PII logging of feedback text
  - [ ] Rate limiting to prevent abuse
- [ ] **Approval Status** — ✅ Approved / ⚠️ Approved with conditions / ⛔ Requires changes

### Result: [ ] PASS / [ ] FAIL

**Notes:**
___________________________________________________________________________

---

## Step 9 — Phase 8-9: Release & Publish (Release Manager)

### Prompt to send to `@Harness`:

```
Prepare the release for the Customer Feedback API.
Create a release checklist, changelog, and prepare the PR.
```

### Expected behavior:

- [ ] **GitHub MCP (recommended)** — Release Manager uses GitHub MCP for PR creation; other release tasks work without it
- [ ] **Commit history gathered** — via `mcp_github_list_commits`
- [ ] **PR body follows template** — uses `.github/PULL_REQUEST_TEMPLATE.md` structure

### Expected output:

- [ ] **Release checklist** with:
  - [ ] All unit tests pass
  - [ ] All integration tests pass
  - [ ] Code quality standards met (verified by QA)
  - [ ] Documentation updated (verified by Documenter)
  - [ ] RAI review completed
  - [ ] PR form filled completely
- [ ] **Changelog** — categorized by type (feature, infra, docs)
- [ ] **PR body** containing:
  - [ ] Description of the feedback API feature
  - [ ] SDLC Phases checked: 1-2, 3, 3+8, 4, 5, 6, 7, 8, 9
  - [ ] Copilot Prompts Used listed
  - [ ] Changes listed
  - [ ] Azure Resources Affected: Cosmos DB, Container Apps, ACR
  - [ ] Testing summary
  - [ ] Quality checklist
  - [ ] Documentation artifacts listed
- [ ] **Progressive config** — Harness fills any remaining placeholders (`<LOGGER_ABSTRACTION>`)

### Final verification:

```
Check .github/copilot-instructions.md — ALL placeholders should now be filled:
- <PROJECT_NAME> → filled in Step 0
- <BUSINESS_DOMAIN> → filled in Step 0
- <TECH_STACK> → filled in Step 0
- <ARCH_STYLE> → filled in Step 2
- <OTHER_AZURE_SERVICES> → filled in Step 4
- <LOGGER_ABSTRACTION> → filled in Step 5 or 9
```

### Result: [ ] PASS / [ ] FAIL

**Notes:**
___________________________________________________________________________

---

## Summary Scorecard

| Step | Phase   | Agent(s)           | Result              | Notes |
| ---- | ------- | ------------------ | ------------------- | ----- |
| 0    | Init    | Harness              | [ ] PASS / [ ] FAIL |       |
| 1    | 1-2     | Analyst            | [ ] PASS / [ ] FAIL |       |
| 2    | 2 (ADR) | Documenter (auto)  | [ ] PASS / [ ] FAIL |       |
| 3    | 3       | Scaffolder         | [ ] PASS / [ ] FAIL |       |
| 4    | 3+8     | Deployer           | [ ] PASS / [ ] FAIL |       |
| 5    | 4       | Implementer        | [ ] PASS / [ ] FAIL |       |
| 6    | 5       | Documenter         | [ ] PASS / [ ] FAIL |       |
| 7    | 6       | QA Coordinator + 9 | [ ] PASS / [ ] FAIL |       |
| 8    | 7       | RAI Reviewer       | [ ] PASS / [ ] FAIL |       |
| 9    | 8-9     | Release Manager    | [ ] PASS / [ ] FAIL |       |

### Agent Coverage

| Agent                     | Tested | MCP Integrations Verified                                 | Skills Activated                                            |
| ------------------------- | ------ | --------------------------------------------------------- | ----------------------------------------------------------- |
| Harness (Coordinator)       | [ ]    | awesome-copilot (required), GitHub MCP (optional), progressive config | (orchestrator — delegates to skill-enabled agents)          |
| Analyst                   | [ ]    | GitHub MCP, awesome-copilot, Context7, ADO MCP            | (reads skill-aligned patterns in design output)             |
| Scaffolder                | [ ]    | GitHub MCP, awesome-copilot, Context7, ADO MCP            | `sdlc-project-scaffolding`                                   |
| Deployer                  | [ ]    | GitHub MCP, awesome-copilot, Azure MCP, MS Learn, ADO MCP | `sdlc-azure-deployment`                                      |
| Implementer               | [ ]    | GitHub MCP, Context7, awesome-copilot                     | `sdlc-cosmos-repository`, `sdlc-blob-storage`                 |
| Documenter                | [ ]    | GitHub MCP, MS Learn                                      | `sdlc-adr-authoring`                                         |
| QA Coordinator            | [ ]    | (orchestrates 9 reviewers)                                | (delegates to skill-enabled reviewers)                      |
| Architecture Reviewer     | [ ]    | GitHub MCP                                                | `sdlc-architecture-review`                                  |
| Azure Compliance Reviewer | [ ]    | GitHub MCP, awesome-copilot                               | (references `sdlc-cosmos-repository`, `sdlc-blob-storage`)  |
| Code Quality Reviewer     | [ ]    | awesome-copilot                                           | `sdlc-code-quality`                                         |
| Security Reviewer         | [ ]    | awesome-copilot                                           | `sdlc-security-review`                                      |
| Test Coverage Reviewer    | [ ]    | awesome-copilot                                           | (references test-quality instruction files)                 |
| Req. Completeness Rev.    | [ ]    | —                                                         | `sdlc-requirements-discovery`                               |
| UX & Accessibility Rev.   | [ ]    | —                                                         | `sdlc-project-qa` (Categories 1-2)                      |
| LLM Behavior Reviewer     | [ ]    | —                                                         | `sdlc-project-qa` (Cat 3-4) + `sdlc-security-review`   |
| Deployment Readiness Rev. | [ ]    | —                                                         | `sdlc-project-qa` (Categories 5, 7-9)                   |
| QA Bug Checklist Reviewer | [ ]    | —                                                         | `sdlc-qa-bug-checklist`                                     |
| RAI Reviewer              | [ ]    | awesome-copilot, MS Learn                                 | (loads `ai-prompt-engineering-safety-review` via MCP)       |
| Release Manager           | [ ]    | GitHub MCP                                                | (no skill — orchestration-focused)                          |

### MCP Server Coverage

| MCP Server      | Used By                                                                                                         | Verified |
| --------------- | --------------------------------------------------------------------------------------------------------------- | -------- |
| GitHub MCP      | Harness, Analyst, Scaffolder, Deployer, Implementer, Documenter, Arch Reviewer, Azure Compliance, Release Manager | [ ]      |
| awesome-copilot | Analyst, Scaffolder, Deployer, Implementer, Code Quality, Security, Test Coverage, RAI, Azure Compliance        | [ ]      |
| Context7        | Analyst, Scaffolder, Implementer                                                                                | [ ]      |
| Azure MCP       | Deployer                                                                                                        | [ ]      |
| MS Learn MCP    | Deployer, Documenter, RAI Reviewer                                                                              | [ ]      |
| ADO MCP         | Analyst, Scaffolder, Deployer                                                                                   | [ ]      |

---

## Cross-Cutting Validation Points

These should be verified across all steps:

### Skills Activation (NEW)
- [ ] Agents reference skills from `.github/skills/` when performing domain-specific tasks
- [ ] Skills load awesome-copilot best practices at runtime via MCP (not hardcoded)
- [ ] SDLC-specific procedures in skills (gotchas, checklists) are followed
- [ ] Skills use progressive disclosure: metadata at startup, body on activation, references on demand

| Skill | Expected Activation Point | Verified |
| --- | --- | --- |
| `sdlc-security-review` | Step 7 (Security Reviewer) | [ ] |
| `sdlc-cosmos-repository` | Step 5 (Implementer — entity/repo creation) | [ ] |
| `sdlc-blob-storage` | Step 5 (Implementer — if blob ops needed) | [ ] |
| `sdlc-adr-authoring` | Step 2 (Documenter — ADR creation) | [ ] |
| `sdlc-architecture-review` | Step 7 (Architecture Reviewer) | [ ] |
| `sdlc-azure-deployment` | Step 4 (Deployer — Bicep/AVM) | [ ] |
| `sdlc-project-scaffolding` | Step 3 (Scaffolder — folder structure) | [ ] |
| `sdlc-code-quality` | Step 7 (Code Quality Reviewer) | [ ] |\n| `sdlc-requirements-discovery` | Step 7 (Requirements Completeness Reviewer) | [ ] |

### Progressive Configuration
- [ ] Placeholders are filled incrementally (not all at once)
- [ ] Each phase fills only what it can determine
- [ ] No placeholder is filled with a guessed value

### MCP Integration Consistency
- [ ] awesome-copilot is hard-required — agents stop if unavailable
- [ ] GitHub MCP is optional — agents probe if available and fall back to reference-catalog.md with warning
- [ ] Auth failures produce clear error messages with remediation steps
- [ ] Graceful degradation uses `.github/reference-catalog.md` patterns when GitHub MCP unavailable

### SDLC Exit Criteria
- [ ] Every agent includes its SDLC Exit Criteria checklist
- [ ] Statuses use ✅/⚠️/⛔ notation
- [ ] No phase is skipped without explicit justification

### Quality Standards
- [ ] Code quality instructions auto-applied for `.py` files
- [ ] Test quality instructions auto-applied for `tests/` files
- [ ] Copyright headers present on all new files
- [ ] Docstrings on all public functions/classes

### Reference Catalog Compliance
- [ ] the approved Cosmos DB SDK wrapper used for Cosmos DB (never raw SDK)
- [ ] the approved Storage SDK wrapper used for Blob/Queue (if applicable)
- [ ] No unauthorized dependencies introduced

---

## Troubleshooting

| Problem                            | Likely Cause                                        | Fix                                                    |
| ---------------------------------- | --------------------------------------------------- | ------------------------------------------------------ |
| Harness doesn't detect placeholders  | `copilot-instructions.md` already filled            | Reset placeholders to `<PROJECT_NAME>` etc.            |
| GitHub MCP not available            | Copilot not signed in with org access, or MCP not configured | Sign in with correct account, check `.vscode/mcp.json`. Agents fall back to reference-catalog.md |
| Agent doesn't use awesome-copilot  | MCP server not configured or not responding         | Verify `awesome-copilot` in `.vscode/mcp.json`         |
| ADR not auto-created after Analyst | Harness didn't follow ADR generation rule             | Manually ask: "Create an ADR from this design"         |
| QA reviewers run sequentially      | QA Coordinator not parallelizing                    | Check if subagent tool supports parallel calls         |
| Deployer doesn't use AVM           | awesome-copilot Bicep practices not loaded          | Verify the instruction loaded; check Bicep output      |
| Implementer uses raw CosmosClient  | Live patterns not fetched from GitHub MCP           | Check auth, fallback to reference-catalog.md patterns  |
| Context7 not loading docs          | MCP server misconfigured                            | Verify Context7 in `.vscode/mcp.json`                  |

---

## Post-Test Artifacts Inventory

After a successful full run, the workspace should contain:

```
.devcontainer/                                    ← Root devcontainer (for azd + Codespaces)
docs/
├── adr/
│   └── ADR-001-customer-feedback-api.md     ← Step 2
├── api/
│   └── feedback-api.md                       ← Step 6
src/
├── CustomerFeedbackAPI/                     ← Step 3
│   ├── .devcontainer/
│   ├── .github/
│   ├── app/
│   │   ├── routers/feedback.py               ← Step 5
│   │   ├── services/
│   │   ├── libs/
│   │   ├── application.py
│   │   └── main.py                           ← Step 3
│   ├── tests/                                ← Tests at project root
│   │   ├── test_feedback_routes.py           ← Step 5
│   │   └── integration/
│   ├── pyproject.toml
│   ├── Dockerfile                            ← Uses uv sync --frozen
│   ├── .python-version
│   ├── .gitignore, .dockerignore, .env.example
├── CustomerFeedbackBusiness/                ← Step 3
│   ├── .devcontainer/
│   ├── .github/
│   ├── src/                                  ← Code root (NOT app/)
│   │   ├── libs/
│   │   │   ├── models/feedback.py            ← Step 5 (domain model)
│   │   │   ├── repositories/feedback_repository.py ← Step 5
│   │   │   └── services/feedback_service.py  ← Step 5
│   │   └── main.py
│   ├── tests/                                ← Tests at project root
│   │   └── test_feedback_service.py          ← Step 5
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile
│   └── .env.example
├── CustomerFeedbackWeb/                     ← Step 3
│   ├── .devcontainer/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
tests/
└── e2e-test/                                ← Root-level E2E tests
infra/
├── main.bicep                                ← Step 4
├── modules/                                  ← Step 4
├── scripts/
├── main.parameters.json                      ← Step 4
└── main.waf.parameters.json                  ← Step 4
azure.yaml                                    ← Step 4
.github/copilot-instructions.md               ← All placeholders filled
TRANSPARENCY_FAQ.md                           ← application compliance
CODE_OF_CONDUCT.md, CONTRIBUTING.md, SECURITY.md, SUPPORT.md, LICENSE
```
