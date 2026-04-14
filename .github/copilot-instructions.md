 # Repository Custom Instructions for GitHub Copilot

 > **📋 TEMPLATE:** This file ships with the SDLC harness as a generic default.
 > Replace `{{PLACEHOLDER}}` tokens with your project's actual values.
 > See `assets/copilot-instructions.template.md` in the workspace-init for the
 > token-based source that generates this file.

 You are GitHub Copilot assisting engineers working on the `{{PROJECT_NAME}}` repository.

 Your primary goals are:
 1. Reduce implementation time.
 2. Improve quality assurance.
 3. Enforce consistent patterns in code, architecture, and documentation.

 If a user asks you to do something that conflicts with these rules, explain the conflict and suggest a compliant alternative.

 ---

 ## 1. Project context

 - Project: `{{PROJECT_NAME}}`
 - Domain: `{{BUSINESS_DOMAIN}}`  <!-- e.g., Intelligent document processing -->
 - Tech stack: `{{TECH_STACK}}`  <!-- e.g., Python 3.12 / FastAPI, Java 21 / Spring Boot, C# / .NET 8, Go 1.22 -->
 - Cloud: Azure
 - Primary data stores and services:
   - Azure Cosmos DB
   - Azure Blob Storage
   - Azure AI Search, Azure OpenAI, Azure AI Document Intelligence, Azure Key Vault, Azure App Configuration, Azure Container Apps

 When you generate code or docs, use examples and terminology consistent with this context.

 ---

 ## 2. Architecture & layering

 **Architecture style**: `{{ARCH_STYLE}}`
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
   - Async methods: suffix with `Async` where idiomatic (C#, TypeScript). Python uses `async def` convention.
   - Avoid unexplained abbreviations.
 - **Error handling & logging**
   - Use the project's standard logging abstraction, not raw `print()`, `console.log()`, or `System.out`.
   - Include correlation IDs or request IDs from the existing context when useful.
 - **Security**
   - Never log secrets or credentials.
   - Prefer parameterized queries/ORM over string-concatenated SQL.
   - Use existing authentication/authorization patterns; don’t invent new ones.

 ### 3.2 Azure resource usage

 When generating or modifying code that interacts with Azure resources, follow these rules:

 1. **Consult `.github/reference-catalog.md`** for the approved SDK or wrapper library
    for your language and Azure service. The catalog lists approved libraries for each
    supported language (Python, Java, C#, Go, TypeScript, etc.).
 2. **Use the approved library** — do NOT create raw Azure SDK clients (e.g., raw
    `CosmosClient`, `BlobServiceClient`, `ServiceBusClient`) when an approved wrapper exists.
 3. **Follow the pattern documented in the catalog** (e.g., Repository Pattern for Cosmos DB,
    context-manager/disposable pattern for Storage).
 4. **Install using the project's package manager** (e.g., `uv add` / `pip install` for Python,
    `dotnet add package` for C#, `mvn dependency:add` for Java, `go get` for Go, `npm install` for TypeScript).

 If the user asks to use a different SDK than what the catalog prescribes, warn them and ask whether the deviation is intentional.

 ---

 ## 4. Reference implementations and scaffolding

 This repository maintains a **Reference Catalog** at `.github/reference-catalog.md`.
 That catalog is the authoritative registry of all reusable libraries and scaffolding templates.

 ### 4.1 Reusable libraries

 Consult `.github/reference-catalog.md` for the full multi-language catalog of approved
 libraries, their package coordinates, and API usage patterns. The catalog covers:
 - Data access (Cosmos DB, Storage, SQL)
 - Messaging (Service Bus, Event Hubs)
 - AI and search services
 - Cross-cutting concerns (logging, configuration, health checks)

 **Copilot behavior:**
 - When the user needs Azure data access, check the catalog and use the listed library for the project's language.
 - Do NOT introduce raw Azure SDK calls when an approved library covers the use case.

 ### 4.2 Scaffolding templates (clone to start a new project)

 Consult `.github/reference-catalog.md` for the full list of scaffolding templates.
 Templates are organized by language and project type. When the user asks to
 "create a new service/API/app/agent", use this decision tree:

 - **General app / worker / CLI** → use the base application template for the project's language.
 - **REST API / web service** → use the API template for the project's language.
 - **AI agent / chatbot / MCP** → use the agent framework template for the project's language.

 **Copilot behavior:**

 - **MANDATORY: All projects MUST be placed under `src/<ProjectName><Layer>/`.**
   The `src/` directory at the repo root is a PROJECT CONTAINER — never put source code
   files directly at the repo root or directly inside `src/`. Always create a named project folder first:
   - WRONG: `root/app/main.py` or `root/src/main.py` or `root/src/Program.cs`
   - CORRECT: `root/src/CustomerFeedbackAPI/app/main.py` or `root/src/CustomerFeedbackAPI/src/Program.cs`
 - Follow the template's folder layout INSIDE the project folder, not at the repo root.
 - See `.github/reference-catalog.md` for template details and project structure reference.
 - See `.github/plugin/skills/sdlc-project-scaffolding/SKILL.md` for the full scaffolding skill.

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
     - Java: JUnit 5 + Mockito
     - C#: xUnit / NUnit + Moq / NSubstitute
     - Go: standard `testing` package + testify
     - Rust: built-in `#[cfg(test)]` + mockall
   - Follow existing naming and folder structure (e.g., `tests/unit/`,
     co-located `*.test.ts` / `*.test.tsx`, or `*_test.go`).
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

 ## 8. GitHub MCP & reference repo access

 <!-- TEMPLATE: Replace {{ORG_NAME}} with your GitHub organization name -->

 Several agents and workflows use **GitHub MCP** (`mcp_github_get_file_contents`, `mcp_github_search_code`, etc.)
 to fetch live patterns from private reference repositories in the `{{ORG_NAME}}` organization.

 The specific repos are listed in `.github/reference-catalog.md`. They typically include
 approved SDK wrapper libraries and scaffolding templates.

 **GitHub MCP enhances workflows but is not mandatory.** When authenticated, agents fetch the
 latest SDK patterns, template structures, and API examples from reference repos. When
 unavailable, agents fall back to `.github/reference-catalog.md` and the patterns documented
 in agent/skill instructions — these are tested and valid.

 **Rules for Copilot and all agents:**

 1. **Prefer live patterns when GitHub MCP is available.** When authenticated with the
    `{{ORG_NAME}}` organization, use GitHub MCP to fetch the latest SDK versions, template
    updates, and cross-repo patterns. Live patterns are the most current source.

 2. **Degrade gracefully when GitHub MCP is unavailable.** If GitHub MCP is not authenticated
    or returns errors, fall back to:
    - `.github/reference-catalog.md` for approved libraries and patterns
    - Patterns documented in agent and skill instructions (e.g., `sdlc-cosmos-repository`)
    - Do NOT block the workflow — continue with available information and note the limitation.

 3. **Never fabricate API surfaces.** If you cannot determine the correct API from either
    GitHub MCP or local reference documentation, ask the user for clarification rather than
    guessing method signatures.

 **For best results:** Ensure GitHub Copilot is signed in with an account that has `{{ORG_NAME}}`
 org access, and confirm the GitHub MCP server is enabled in `.vscode/mcp.json`.

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