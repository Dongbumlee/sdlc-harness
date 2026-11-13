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
 - Cloud: `{{CLOUD_PROVIDER}}`
 - Primary data stores and services: `{{PRIMARY_SERVICES}}`
   <!-- Filling agent: replace {{CLOUD_PROVIDER}} and {{PRIMARY_SERVICES}} with
        THIS project's cloud and its actual services from the approved design
        (e.g., "Azure — Cosmos DB, Blob Storage, Key Vault" or "AWS — DynamoDB,
        S3, Secrets Manager"). Do not leave another project's service list here. -->

 When you generate code or docs, use examples and terminology consistent with this context.

 ---

 ## 2. Architecture & layering

 **Architecture style**: `{{ARCH_STYLE}}`
 <!-- Filling agent: set {{ARCH_STYLE}} from the approved design (Phase 2) —
      e.g., "Layered architecture (API → Application → Domain ← Infrastructure)
      with React SPA frontend", hexagonal, microservices, or modular monolith.
      The Layers list and rules below describe the layered example; adjust
      them to the recorded style. -->

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

 <!-- Filling agent: this section ships with the Azure variant filled in.
      If the project's cloud (Section 1) is AWS or GCP, replace this whole
      section with the installed cloud pack's equivalent resource-usage
      rules — do not leave Azure rules in a non-Azure project. -->

 When generating or modifying code that interacts with Azure resources, follow these rules.
 The full details and examples are in `.github/reference-catalog.md`.

 #### Cosmos DB

 - **Use this library:** `{{COSMOSDB_LIB_PACKAGE}}` (PyPI) from
   [{{ORG_NAME}}/{{COSMOSDB_LIB_REPO}}](https://github.com/{{ORG_NAME}}/{{COSMOSDB_LIB_REPO}}).
 - **Pattern:** Repository Pattern with `RepositoryBase[TEntity, TKey]` and Pydantic entities via
   `RootEntityBase["EntityName", KeyType]`.
 - **Install:** `uv add {{COSMOSDB_LIB_PACKAGE}}  # replace with your library`
 - **Copilot behavior:**
   - When asked to add Cosmos DB access, use `{{COSMOSDB_LIB_PACKAGE}}` and follow the Repository Pattern.
   - Define entities extending `RootEntityBase["EntityName", KeyType]` (type variables are mandatory).
   - Define repositories extending `RepositoryBase[Entity, KeyType]`.
   - Do NOT create raw `CosmosClient` instances; use the library's repository abstractions.

 #### Azure Blob Storage & Queue

 - **Use this library:** `{{STORAGE_LIB_PACKAGE}}` (PyPI) from
   [{{ORG_NAME}}/{{STORAGE_LIB_REPO}}](https://github.com/{{ORG_NAME}}/{{STORAGE_LIB_REPO}}).
 - **Pattern:** `AsyncStorageBlobHelper` / `AsyncStorageQueueHelper` with `async with` context manager.
 - **Install:** `uv add {{STORAGE_LIB_PACKAGE}}  # replace with your library`
 - **Copilot behavior:**
   - When asked to add blob or queue operations, use `{{STORAGE_LIB_PACKAGE}}`.
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
 | [{{COSMOSDB_LIB_REPO}}](https://github.com/{{ORG_NAME}}/{{COSMOSDB_LIB_REPO}}) | `{{COSMOSDB_LIB_PACKAGE}}` | Cosmos DB SQL + MongoDB with Repository Pattern |
 | [{{STORAGE_LIB_REPO}}](https://github.com/{{ORG_NAME}}/{{STORAGE_LIB_REPO}}) | `{{STORAGE_LIB_PACKAGE}}` | Azure Blob Storage + Queue operations |

 **Copilot behavior:**
 - When the user needs Azure data access, check this table and use the listed library.
 - Do NOT introduce raw Azure SDK calls when a library above covers the use case.
 - See `.github/reference-catalog.md` for detailed API patterns and examples.

 ### 4.2 Scaffolding templates (clone to start a new project)

 | Template | Use for |
 |----------|--------|
 | [{{APP_TEMPLATE_REPO}}](https://github.com/{{ORG_NAME}}/{{APP_TEMPLATE_REPO}}) | Base app (console, worker, pipeline, CLI) with AppContext + DI + Azure App Config |
 | [{{API_TEMPLATE_REPO}}](https://github.com/{{ORG_NAME}}/{{API_TEMPLATE_REPO}}) | FastAPI service with advanced DI, routers, health probes |
 | [{{AGENT_TEMPLATE_REPO}}](https://github.com/{{ORG_NAME}}/{{AGENT_TEMPLATE_REPO}}) | AI agent apps with Azure AI Foundry, MCP tools, multi-agent workflows |

 **Copilot behavior:**

 - When the user asks to "create a new service/API/app/agent", pick the matching template:
   - General app / worker / CLI -> `{{APP_TEMPLATE_REPO}}`
   - REST API / web service -> `{{API_TEMPLATE_REPO}}`
   - AI agent / chatbot / MCP -> `{{AGENT_TEMPLATE_REPO}}`
 - **MANDATORY: All projects MUST be placed under `src/<ProjectName><Layer>/`.**
   The `src/` directory at the repo root is a PROJECT CONTAINER — never put source code
   files (`main.py`, `models/`, `routers/`, `pyproject.toml`) directly at the repo root or
   directly inside `src/`. Always create a named project folder first:
   - WRONG: `root/app/main.py` or `root/src/main.py`
   - CORRECT: `root/src/CustomerFeedbackAPI/app/main.py`
 - Follow the template's folder layout INSIDE the project folder, not at the repo root.
 - See `.github/reference-catalog.md` for template details and project structure reference.
 - Use the `sdlc-project-scaffolding` skill for the full scaffolding procedure.

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
     - C#: xUnit with the bundled template's test stack (see `.github/instructions/test-quality-csharp.instructions.md`); assertion/mocking libraries only as recorded in the reference catalog
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
     - Docstrings and documentation comments. No copyright or license headers unless the org standard recorded in the project manifest mandates one.
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
 3. Repo structure and CI/CD (GitHub Actions) configuration
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

 Several agents and workflows use **GitHub MCP** (its file-contents and code-search tools, among others)
 to fetch live patterns from private reference repositories in the `{{ORG_NAME}}` organization:

 - `{{ORG_NAME}}/{{COSMOSDB_LIB_REPO}}` ({{COSMOSDB_LIB_PACKAGE}})
 - `{{ORG_NAME}}/{{STORAGE_LIB_REPO}}` ({{STORAGE_LIB_PACKAGE}})
 - `{{ORG_NAME}}/{{APP_TEMPLATE_REPO}}`
 - `{{ORG_NAME}}/{{API_TEMPLATE_REPO}}`
 - `{{ORG_NAME}}/{{AGENT_TEMPLATE_REPO}}`

 **Authentication is required.** These repos are not publicly accessible. The GitHub MCP server
 authenticates via the user's GitHub Copilot session, which must have access to the `{{ORG_NAME}}` org.

 **Rules for Copilot and all agents:**

 1. **Verify access before relying on fetched content.** Before any workflow that depends on
    reference repo content, perform a lightweight probe call (e.g., fetch `README.md` from one
    of the repos above). If the call fails or returns an auth error:
    - **Warn the user** that GitHub MCP authentication failed and live reference
      content from `{{ORG_NAME}}` repos is unavailable.
    - **Fall back to local patterns** in `.github/reference-catalog.md` and note in
      your output that live verification was not possible.
    - **Do NOT invent patterns** — where no local pattern covers the case, say so in
      your output rather than fabricating one.

 2. **Degraded mode is the defined fallback.** If `{{ORG_NAME}}` access is unavailable,
    work continues on local patterns (`.github/reference-catalog.md`). Only steps that
    themselves create or modify a GitHub repository (repo creation, PR creation) wait
    for access — no other workflow stops.

 3. **No fabricated API surfaces.** If you cannot fetch the latest API from a reference repo,
    use the local catalog. If neither live nor local patterns cover the API, flag it as
    unverified in your output — do NOT guess or invent method signatures.

 ---

 ## 9. Public guidance sources

 GitHub is this project's only forge — issues, pull requests, and GitHub Actions
 are the work medium, and there is no Azure DevOps (or other tracker) integration.
 Team standards live in this repository's own instruction files, not an external wiki.

 When no project-local pattern covers a question, agents consult the public sources
 below — and note the gap rather than fabricating guidance:

 - Best-practice instructions and collections fetched from the `github/awesome-copilot`
   repository via the GitHub MCP server's file-contents tool or `fetch`. This is a
   discovery-time source, not a configured MCP server; skip a load if it is unreachable.
 - **Microsoft Learn MCP** (Azure pack) and **Context7 MCP** for current vendor and
   framework documentation.
 - The **AVM module registry** for Azure Verified Modules.

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