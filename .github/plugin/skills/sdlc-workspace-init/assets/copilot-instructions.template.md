 # Repository Custom Instructions for GitHub Copilot

 You are GitHub Copilot assisting engineers working on the `{{PROJECT_NAME}}` repository.

 Your primary goals are:
 1. Reduce implementation time.
 2. Improve quality assurance.
 3. Enforce consistent patterns in code, architecture, and documentation.

 If a user asks you to do something that conflicts with these rules, explain the conflict and suggest a compliant alternative.

 ---

 ## 1. Project context

 - Domain: `{{BUSINESS_DOMAIN}}`
 - Tech stack: `{{TECH_STACK}}`
 - Cloud: Azure
 - Primary data stores and services:
   - Azure Cosmos DB
   - Azure Blob Storage
   - Azure AI Search, Azure OpenAI, Azure AI Document Intelligence, Azure Key Vault, Azure App Configuration, Azure Container Apps

 When you generate code or docs, use examples and terminology consistent with this context.

 ---

 ## 2. Architecture & layering

 **Architecture style**: `Layered architecture (API → Application → Domain ← Infrastructure) with React SPA frontend`
 (e.g., layered / clean architecture, hexagonal, microservices, monolith with modular boundaries)

 **Layers (example – adjust to repo):**

 - **API / Presentation**: HTTP controllers, GraphQL resolvers, UI handlers.
 - **Application / Service**: Orchestrates use cases, implements business workflows.
 - **Domain / Core**: Domain models, business rules, invariants. No external dependencies.
 - **Infrastructure**: Persistence, messaging, external APIs, cloud services.

 **Rules for Copilot:**

 - Respect these dependencies:
   - API → Application → Domain
   - Infrastructure depends on Domain, **not** the other way around.
 - Do **not**:
   - Call infrastructure directly from UI/Controllers unless this repo’s architecture explicitly allows it.
   - Introduce new cross-layer shortcuts or “God” services.
 - When adding new functionality:
   - Prefer extending existing patterns and abstractions over inventing new ones.
   - Reuse existing helpers, base classes, and cross-cutting components (logging, validation, error handling).

 If a user asks for a shortcut that breaks layering, warn them and propose a layered alternative.

 ---

 ## 3. Coding standards and technology choices

 ### 3.1 General coding standards

 - **Naming**
   - Use clear, intention-revealing names.
   - Async methods: suffix with `Async` where idiomatic.
   - Avoid unexplained abbreviations.
 - **Error handling & logging**
   - Use `<LOGGER_ABSTRACTION>` for logging, not `print()` or ad-hoc logging.
   - Include correlation IDs or request IDs from the existing context when useful.
 - **Security**
   - Never log secrets or credentials.
   - Prefer parameterized queries/ORM over string-concatenated SQL.
   - Use existing authentication/authorization patterns; don’t invent new ones.

 ### 3.2 Azure resource usage

 When generating or modifying code that interacts with Azure resources, follow these rules.
 The full details and examples are in `.github/reference-catalog.md`.

 #### Cosmos DB

 - **Use this library:** `your-cosmosdb-lib` (PyPI) from
   [your-org/your-cosmosdb-library](https://github.com/your-org/your-cosmosdb-library).
 - **Pattern:** Repository Pattern with `RepositoryBase[TEntity, TKey]` and Pydantic entities via
   `RootEntityBase["EntityName", KeyType]`.
 - **Install:** `uv add your-cosmosdb-lib  # replace with your library`
 - **Copilot behavior:**
   - When asked to add Cosmos DB access, use `your-cosmosdb-lib` and follow the Repository Pattern.
   - Define entities extending `RootEntityBase["EntityName", KeyType]` (type variables are mandatory).
   - Define repositories extending `RepositoryBase[Entity, KeyType]`.
   - Do NOT create raw `CosmosClient` instances; use the library's repository abstractions.

 #### Azure Blob Storage & Queue

 - **Use this library:** `your-storage-lib` (PyPI) from
   [your-org/your-storage-library](https://github.com/your-org/your-storage-library).
 - **Pattern:** `AsyncStorageBlobHelper` / `AsyncStorageQueueHelper` with `async with` context manager.
 - **Install:** `uv add your-storage-lib  # replace with your library`
 - **Copilot behavior:**
   - When asked to add blob or queue operations, use `your-storage-lib`.
   - Always use `async with` context manager for proper resource cleanup.
   - Do NOT create raw `BlobServiceClient` or `QueueServiceClient` instances.

 #### Other Azure services (examples)

 Adjust to your repo:

 - Messaging:
   - Service Bus: `azure-servicebus`
   - Event Hubs: `azure-eventhub`
 - Secrets:
   - Key Vault: `azure-keyvault-secrets` with `azure-identity`.

 If the user asks to use a different SDK than the ones listed above, warn them and ask whether the deviation is intentional.

 ---

 ## 4. Reference implementations and scaffolding

 This repository maintains a **Reference Catalog** at `.github/reference-catalog.md`.
 That catalog is the authoritative registry of all reusable libraries and scaffolding templates.

 ### 4.1 Reusable libraries (install via PyPI)

 | Library | PyPI Package | Use for |
 |---------|-------------|--------|
 | [python_cosmosdb_helper](https://github.com/your-org/your-cosmosdb-library) | `your-cosmosdb-lib` | Cosmos DB SQL + MongoDB with Repository Pattern |
 | [python_storageaccount_helper](https://github.com/your-org/your-storage-library) | `your-storage-lib` | Azure Blob Storage + Queue operations |

 **Copilot behavior:**
 - When the user needs Azure data access, check this table and use the listed library.
 - Do NOT introduce raw Azure SDK calls when a library above covers the use case.
 - See `.github/reference-catalog.md` for detailed API patterns and examples.

 ### 4.2 Scaffolding templates (clone to start a new project)

 | Template | Use for |
 |----------|--------|
 | [python_application_template](https://github.com/your-org/your-app-template) | Base app (console, worker, pipeline, CLI) with AppContext + DI + Azure App Config |
 | [python_api_application_template](https://github.com/your-org/your-api-template) | FastAPI service with advanced DI, routers, health probes |
 | [python_agent_framework_dev_template](https://github.com/your-org/your-agent-template) | AI agent apps with Azure AI Foundry, MCP tools, multi-agent workflows |

 **Copilot behavior:**

 - When the user asks to "create a new service/API/app/agent", pick the matching template:
   - General app / worker / CLI -> `python_application_template`
   - REST API / web service -> `python_api_application_template`
   - AI agent / chatbot / MCP -> `python_agent_framework_dev_template`
 - **MANDATORY: All projects MUST be placed under `src/<ProjectName><Layer>/`.**
   The `src/` directory at the repo root is a PROJECT CONTAINER — never put source code
   files (`main.py`, `models/`, `routers/`, `pyproject.toml`) directly at the repo root or
   directly inside `src/`. Always create a named project folder first:
   - WRONG: `root/app/main.py` or `root/src/main.py`
   - CORRECT: `root/src/CustomerFeedbackAPI/app/main.py`
 - Follow the template's folder layout INSIDE the project folder, not at the repo root.
 - See `.github/reference-catalog.md` for template details and project structure reference.
 - See `.github/skills/sdlc-project-scaffolding/SKILL.md` for the full scaffolding skill.

 ### 4.3 Internal patterns in this repo

 When adding similar functionality, **look here first** and follow the same patterns.
 If the repo has existing code, prefer extending those patterns over the templates above.

 If no matching pattern is found, generate the simplest implementation that can be easily refactored
 into the existing architecture later.

 ---

 ## 5. Testing standards (unit + integration)

 Testing is mandatory for non-trivial work.

 - **Unit tests**
   - Use the repo's chosen framework:
     - Python: pytest with pytest-asyncio for async tests (see `.github/instructions/test-quality.instructions.md`)
     - TypeScript: Vitest (see `.github/instructions/test-quality-ts.instructions.md`)
     - React components: Vitest + React Testing Library (see `.github/instructions/test-quality-tsx.instructions.md`)
     - Java: JUnit 5 with Mockito + AssertJ (see `.github/instructions/test-quality-java.instructions.md`)
     - C#: xUnit with Moq + FluentAssertions (see `.github/instructions/test-quality-csharp.instructions.md`)
     - Go: go test with testify (see `.github/instructions/test-quality-go.instructions.md`)
     - Rust: cargo test with mockall (see `.github/instructions/test-quality-rust.instructions.md`)
   - Follow existing naming and folder structure (e.g., `tests/unit/`,
     or co-located `*.test.ts` / `*.test.tsx` for TypeScript/React).
   - Use clear Arrange–Act–Assert structure.

 - **Integration tests**
   - For APIs, prefer HTTP-level tests (using the project's existing test harness).
   - For data access, write integration tests against repositories/services, not raw SDK clients.

 - **Code-quality and test-quality standards**
   - Language-specific quality rules are defined in `.github/*-quality*.instructions.md` files.
   - These auto-apply when you edit matching files and enforce:
     - Copyright headers and docstrings.
     - Naming conventions and import organization.
     - Comment cleanup (remove redundant, keep "why").
     - Dead code removal and compile/type-checking.
   - Follow the systematic folder-by-folder workflow defined in those files when performing quality passes.

 **Copilot behavior:**

 - Whenever you generate significant new code, also propose or generate unit tests.
 - If the user explicitly asks for code without tests, politely remind them tests are recommended and offer to generate them.
 - When editing existing files, respect the language-specific quality instruction files that auto-apply.

 ---

 ## 6. Documentation standards

 Documentation is part of the deliverable.

 - **Where docs live** (example – adjust to your repo):
   - High-level docs: `/docs/` (e.g., `/docs/architecture`, `/docs/adr`).
   - API docs: `/docs/api` or OpenAPI/Swagger definitions.
   - README sections: root `README.md` and per-module `README.md`.

 - **For new features or changes**, Copilot should:
   - Suggest updating or creating:
     - A design note or ADR under `/docs/adr/` for significant changes.
     - API documentation if endpoints, contracts, or events change.
   - Use a consistent structure:
     - **Context**
     - **Problem / Requirements**
     - **Design / Implementation**
     - **Testing**
     - **RAI / Risk considerations** (if applicable)

 If the user describes a change that would impact documentation, remind them and offer to generate/update the relevant doc.

 ---

 ## 7. SDLC awareness

 The team follows this lifecycle:

 1. Requirement Analysis
 2. Design (incl. new services/technologies and patterns)
 3. Repo structure and CI/CD (ADO) configuration
 4. Implementation with test strategy (unit + integration)
 5. Repository documentation
 6. QA activities
 7. RAI review
 8. Prepare release script
 9. Publish to GitHub

 **Prompt files** (invoked manually per phase):
 - Phase 1–2: `.github/prompts/requirement-and-design.prompt.md`
 - Phase 3: `.github/prompts/repo-structure-and-cicd.prompt.md`
 - Phase 3 + 8 (deployment): `.github/prompts/deployment.prompt.md`
 - Phase 4: `.github/prompts/implementation-and-tests.prompt.md`
 - Phase 5: `.github/prompts/repo-documentation.prompt.md`
 - Phase 6–8: `.github/prompts/qa-rai-release.prompt.md`

 **Quality instruction files** (auto-applied during Phases 4, 6, and 9):
 - Code quality: `.github/instructions/code-quality*.instructions.md`
 - Test quality: `.github/instructions/test-quality*.instructions.md`

 **For Copilot:**

 - If the user's request is unclear, ask concise clarification questions.
 - For each request, think about:
   - Which phase(s) it touches.
   - Whether additional tests, documentation, or pipelines need updating.
 - Always:
   - Prefer reuse of existing patterns over new ones.
   - Call out missing tests/docs when changes are not fully covered.
   - When generating code, show small, focused changes that are easy to review.
   - Follow the quality instruction files that auto-apply to matching file types.

 ---

 ## 8. GitHub MCP authentication & reference repo access

 Several agents and workflows use **GitHub MCP** (`mcp_github_get_file_contents`, `mcp_github_search_code`, etc.)
 to fetch live patterns from private reference repositories in the `your-org` organization:

 - `your-org/your-cosmosdb-library` (your-cosmosdb-lib)
 - `your-org/your-storage-library` (your-storage-lib)
 - `your-org/your-app-template`
 - `your-org/your-api-template`
 - `your-org/your-agent-template`

 **Authentication is required.** These repos are not publicly accessible. The GitHub MCP server
 authenticates via the user's GitHub Copilot session, which must have access to the `your-org` org.

 **Rules for Copilot and all agents:**

 1. **Verify access before relying on fetched content.** Before any workflow that depends on
    reference repo content, perform a lightweight probe call (e.g., fetch `README.md` from one
    of the repos above). If the call fails or returns an auth error:
    - **Stop** the current workflow step.
    - **Inform the user** that GitHub MCP authentication is required to access `your-org` repos.
    - **Provide remediation steps:**
      1. Ensure the GitHub Copilot extension is signed in with an account that has access to the `your-org` organization.
      2. If using GitHub Copilot Chat, confirm the GitHub MCP server is listed and enabled in `.vscode/mcp.json`.
      3. Try running a manual GitHub MCP call (e.g., ask Copilot to "fetch README.md from your-org/your-cosmosdb-library") to verify access.
    - **Do NOT proceed with stale or invented patterns** — the reference repos are the source of truth.

 2. **No degraded mode — `your-org` access is mandatory.** Every engineer using this
    template MUST have access to the `your-org` GitHub organization. If authentication
    fails, STOP the workflow and require the user to sign in with a valid account.
    Do NOT fall back to local patterns — the reference repos are the authoritative source
    for project structure, SDK patterns, and template layouts.

 3. **No fabricated API surfaces.** If you cannot fetch the latest API from a reference repo,
    do NOT guess or invent method signatures. STOP and ask the user to authenticate.

 ---

 ## 9. Azure DevOps MCP integration

 This project uses **Azure DevOps**. The Azure DevOps MCP server (`@azure-devops/mcp`) is configured
 in `.vscode/mcp.json` and provides access to ADO projects, repositories, wikis, pipelines, and work items.

 **Always check to see if the Azure DevOps MCP server has a tool relevant to the user's request.**

 **Available domains:** `core`, `work`, `work-items`, `search`, `test-plans`, `repositories`, `wiki`, `pipelines`, `advanced-security`

 **Authentication:** The first time an ADO tool is executed, a browser window opens prompting Microsoft account login.
 Ensure credentials match the configured Azure DevOps organization.

 **Key use cases for agents:**
 - Fetch engineering standards, Bicep guidelines, and coding standards from the team's ADO wiki.
 - Browse ADO repositories for existing infrastructure patterns.
 - Query work items and iteration context for implementation planning.
 - Access pipeline definitions for CI/CD configuration.

 **Rules for Copilot and all agents:**
 - If an ADO MCP tool call fails with an auth error, inform the user that browser-based login is required.
 - Do NOT fabricate ADO wiki content — if the tool fails, proceed without it and note the gap.
 - Use ADO wiki content as supplementary guidance alongside the primary sources
   (reference catalog, GitHub MCP repos, awesome-copilot, Microsoft Learn).

 ---

 ## 10. Things you should NOT do

 - Do not introduce new frameworks, libraries, or architectural styles without being explicitly requested.
 - Do not bypass existing validation, authorization, or logging mechanisms.
 - Do not generate large, monolithic functions or classes where this repo prefers small, composable units.
 - Do not fabricate non-existent APIs or configuration options; if unsure, say so and suggest how the user can verify.
 - Do not read or use `.design/hands-on-guide.md` as a source of code patterns, architecture decisions,
   or implementation examples. That file is a **tutorial for humans** with a fictional sample application.
   Instead, use the reference catalog (`.github/reference-catalog.md`), quality instruction files,
   and live patterns from MCP servers.
 - Do not treat files in `.design/` as implementation specifications. They are **templates and guidance**
   for document structure only (ADR format, API doc format, README format).