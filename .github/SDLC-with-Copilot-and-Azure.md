# Software Development Lifecycle (SDLC) with GitHub Copilot, Azure Standards, and Reference Repos

 ## 0. Scope and Preconditions

 This SDLC applies to all engineering work in this project, from initial requirements through release to GitHub. It assumes:

 - Engineers use **VS Code** with **GitHub Copilot** (Chat + coding agents).
 - **Copilot CLI** is available for terminal-based workflows.
 - The repository defines:
   - A **Copilot instructions file**: `.github/copilot-instructions.md`.
   - **Language-specific quality instruction files** in `.github/instructions/` (auto-applied by file type):
     - `.github/instructions/code-quality-py.instructions.md` — Python code quality (`**.py`)
     - `.github/instructions/code-quality-ts.instructions.md` — TypeScript code quality (`**/*.ts`)
     - `.github/instructions/code-quality-tsx.instructions.md` — React component quality (`**/*.tsx`)
     - `.github/instructions/test-quality.instructions.md` — Python test quality (`tests/**`)
     - `.github/instructions/test-quality-ts.instructions.md` — TypeScript test quality (`**/*.test.ts`)
     - `.github/instructions/test-quality-tsx.instructions.md` — React test quality (`**/*.test.tsx`)
   - **Prompt files** in `.github/prompts/` (invoked manually per phase):
     - `.github/prompts/requirement-and-design.prompt.md` — Phase 1–2
     - `.github/prompts/repo-structure-and-cicd.prompt.md` — Phase 3
     - `.github/prompts/deployment.prompt.md` — Phase 3 + 8 (Bicep/AVM/azd)
     - `.github/prompts/implementation-and-tests.prompt.md` — Phase 4
     - `.github/prompts/repo-documentation.prompt.md` — Phase 5
     - `.github/prompts/qa-rai-release.prompt.md` — Phase 6–8
 - CI/CD is implemented in **Azure DevOps (ADO)** or **GitHub Actions**, and code is published to **GitHub**.

 ---

 ## 1. Global Technology and Reference Rules

 These rules apply across all phases. Copilot MUST follow them unless the team explicitly agrees to deviate.

 ### 1.1 Azure library standards

 **Cosmos DB**

 - Use **`your-cosmosdb-lib`** (PyPI) for all Cosmos DB access (SQL API and MongoDB API).
   - Install: `uv add your-cosmosdb-lib  # replace with your library`
   - Source: [your-org/your-cosmosdb-library](https://github.com/your-org/your-cosmosdb-library)
 - Pattern: Repository Pattern with `RepositoryBase[TEntity, TKey]` and Pydantic entities via
   `RootEntityBase["EntityName", KeyType]`.
 - Do **NOT** use raw `azure-cosmos` SDK or `pymongo` directly when `your-cosmosdb-lib` covers the use case.
 - Namespace: `from your_org.cosmosdb.sql import RootEntityBase, RepositoryBase`

 **Azure Blob Storage & Queue**

 - Use **`your-storage-lib`** (PyPI) for all blob and queue operations.
   - Install: `uv add your-storage-lib  # replace with your library`
   - Source: [your-org/your-storage-library](https://github.com/your-org/your-storage-library)
 - Pattern: `AsyncStorageBlobHelper` / `AsyncStorageQueueHelper` with `async with` context manager.
 - Do **NOT** use raw `azure-storage-blob` or `azure-storage-queue` SDK directly.
 - Namespace: `from your_org.storage.blob import AsyncStorageBlobHelper`

 **Other Azure services** (examples, tailor as needed):

 - Service Bus: `azure-servicebus`
 - Event Hubs: `azure-eventhub`
 - Key Vault: `azure-keyvault-secrets` / `azure-identity`
 - App Configuration: `azure-appconfiguration` (used by scaffolding templates)

 **Rule:** New code MUST use the `your-cosmosdb-lib` and `your-storage-lib` libraries and their patterns rather than
 raw Azure SDK clients. See `.github/reference-catalog.md` for detailed API examples.

 ---

 ### 1.2 Reference implementation and scaffolding sources

 The team maintains a **Reference Catalog** at `.github/reference-catalog.md`.
 That catalog is the authoritative registry of all reusable libraries and scaffolding templates.

 **Reusable libraries (install via PyPI)**

 | Library                                                                                         | PyPI Package   | Use for                                         |
 | ----------------------------------------------------------------------------------------------- | -------------- | ----------------------------------------------- |
 | [python_cosmosdb_helper](https://github.com/your-org/your-cosmosdb-library)             | `your-cosmosdb-lib` | Cosmos DB SQL + MongoDB with Repository Pattern |
 | [python_storageaccount_helper](https://github.com/your-org/your-storage-library) | `your-storage-lib`  | Azure Blob Storage + Queue operations           |

 **Scaffolding templates (clone to start a new project)**

 | Template                                                                                                      | Use for                                                                           |
 | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
 | [python_application_template](https://github.com/your-org/your-app-template)                 | Base app (console, worker, pipeline, CLI) with AppContext + DI + Azure App Config |
 | [python_api_application_template](https://github.com/your-org/your-api-template)         | FastAPI service with advanced DI, routers, health probes                          |
 | [python_agent_framework_dev_template](https://github.com/your-org/your-agent-template) | AI agent apps with Azure AI Foundry, MCP tools, multi-agent workflows             |

 **Internal patterns in this repo**

 When adding similar functionality, look at existing code first and follow the same patterns.
 If the repo has existing code, prefer extending those patterns over the templates above.

 **Rule:**
 If you need a new service or module, follow the structure of these templates and the internal patterns; do not invent a new
 structure in isolation. See `.github/reference-catalog.md` for detailed API patterns, examples, and Copilot behavior rules.

 ---

 ### 1.3 Copilot prompts: required vs. recommended

 **Required prompt usage**

 - For each new or significantly changed feature:
   - Requirements & design:
     - `.github/prompts/requirement-and-design.prompt.md` (Phase 1–2)
   - Implementation & tests:
     - `.github/prompts/implementation-and-tests.prompt.md` (Phase 4)
   - QA & release:
     - `.github/prompts/qa-rai-release.prompt.md` (Phase 6–8) for medium/high-risk work, new services, or visible changes.

 **Recommended prompt usage**

 - Documentation:
   - `.github/prompts/repo-documentation.prompt.md` whenever docs are created/updated (Phase 5).
 - For small changes, prompts may be used at engineer’s discretion, but standards (Azure, architecture, tests) still apply.

 ---

 ## 2. SDLC Phases

 The SDLC consists of nine phases:

 1. Requirement Analysis
 2. Design (incl. new services/technologies and patterns)
 3. Repo Structure & CI/CD (ADO)
 4. Implementation & Tests (unit + integration)
 5. Repository Documentation
 6. QA Activities
 7. RAI (Responsible AI) Review
 8. Release Script Preparation
 9. Publish to GitHub

 Each phase below defines: objectives, activities, Copilot usage, and exit criteria.

 ---

 ### Phase 1 – Requirement Analysis

 **Objective**

 Understand the business problem and constraints well enough to design a solution aligned with architecture, Azure standards,
 and SDLC.

 **Activities**

 - Clarify:
   - Business needs and users.
   - Functional and non-functional requirements (performance, security, data residency, compliance).
   - Dependencies and integration points.
 - Identify whether the change:
   - Touches data (Cosmos/Blob/other Azure).
   - Introduces or modifies APIs, services, or background processes.
   - Involves AI/ML or RAI-sensitive behavior.

 **Copilot usage**

 - **Required:** Use `.github/prompts/requirement-and-design.prompt.md` in VS Code Copilot Chat:
   - Provide the feature description and constraints.
   - Let Copilot:
     - Ask clarifying questions.
     - Restate the requirements.
 - Copilot CLI (optional):
   - Use Copilot CLI research commands to quickly summarize relevant code, docs, and issues if needed.

 **Exit criteria**

 - Requirements are clarified and documented (even briefly):
   - Problem statement, goals, non-goals.
   - Known constraints (tech, security, RAI).
 - Agreement on scope and success criteria.

 ---

 ### Phase 2 – Design (services, technologies, patterns)

 **Objective**

 Design a solution following the repository’s architecture and Azure usage rules, reusing existing patterns and reference repos.

 **Activities**

 - Decide:
   - Which layers are involved (API, Application, Domain, Infrastructure, UI).
   - Which Azure services are needed (Cosmos DB, Blob, Service Bus, etc.).
 - Map:
   - Which existing patterns will be reused (e.g., `your-cosmosdb-lib` repositories, `your-storage-lib` helpers).
   - When a new service/module is required, align it with internal patterns and/or template repositories.

 - Produce:
   - A design or ADR describing:
     - Architecture (components and relationships).
     - Data flows and Azure resource interactions (Cosmos containers, blob containers, etc.).
     - Error handling, logging, and security boundaries.
     - Test strategy (unit, integration).

 **Copilot usage**

 - **Required:**
   - Continue using `.github/prompts/requirement-and-design.prompt.md` to:
     - Generate a recommended design and alternatives.
     - Map tasks to SDLC phases.
 - **Recommended:**
   - If a new service repo is needed, explicitly tell Copilot:
     - Which **template repo** to follow (e.g. `python_api_application_template`).
     - It should mirror that template's layout and patterns.

 **Exit criteria**

 - Design is documented (ADR/design doc) and agreed by the team.
 - Azure library choices are explicit and compliant:
   - Cosmos: `your-cosmosdb-lib` (PyPI).
   - Blob/Queue: `your-storage-lib` (PyPI).
 - Reuse of internal patterns and/or external templates is identified, not left to chance.

 ---

 ### Phase 3 – Repo Structure & CI/CD Configuration (ADO)

 **Objective**

 Ensure the repository structure and pipelines support the new design, including Azure resources and tests.

 **Activities**

 - For new services:
   - Create repo structure aligned with template repos and internal patterns.
   - Establish standard folders:
     - `src/Presentation`, `src/Application`, `src/Domain`, `src/Infrastructure`, `tests`, `docs`, etc.
 - Configure or update **ADO pipelines**:
   - Build and test stages.
   - Static analysis / security scanning.
   - Integration test stages if applicable.
   - Deployment stages (if this repo owns deployment).
 - Select and copy the appropriate `.github/instructions/*.instructions.md` files for the repo's language stack:
   - Python → `.github/instructions/code-quality-py.instructions.md` + `.github/instructions/test-quality.instructions.md`
   - TypeScript → `.github/instructions/code-quality-ts.instructions.md` + `.github/instructions/test-quality-ts.instructions.md`
   - React → `.github/instructions/code-quality-tsx.instructions.md` + `.github/instructions/test-quality-tsx.instructions.md`

 **Copilot usage**

 - **Recommended:** Use `.github/prompts/repo-structure-and-cicd.prompt.md`:
   - To scaffold repo structure aligned with reference catalog templates.
   - To generate CI/CD pipelines (GitHub Actions and/or ADO) with quality gates.
   - To configure project files (`pyproject.toml`, `.gitignore`, `Dockerfile`, etc.).
 - Copilot CLI:
   - Plan mode to draft pipeline changes and file layout.
   - Autopilot to apply straightforward scaffolding (with human review via git diff).

 **Exit criteria**

 - Repository folders and projects are created or updated to match architecture and templates.
 - ADO pipeline definitions are updated or confirmed to:
   - Build and test the new code.
   - Run existing checks without regressions.

 ---

 ### Phase 4 – Implementation with Test Strategy (Unit & Integration)

 **Objective**

 Implement the feature/change correctly and safely, with appropriate unit and integration tests, using Azure and patterns
 correctly.

 **Activities**

 - Implement feature in small, reviewable increments:
   - Routers/endpoints, services, domain logic.
   - Data access using `your-cosmosdb-lib` repository pattern and `your-storage-lib` helpers.
 - For Cosmos DB:
   - Use `your-cosmosdb-lib` with `RepositoryBase[Entity, KeyType]`.
   - Follow the patterns in the reference catalog and `python_cosmosdb_helper` repo for:
     - Partition keys and entity definitions.
     - Predicate-based queries.
     - Error handling and async patterns.

 - For Blob Storage / Queue:
   - Use `your-storage-lib` with `AsyncStorageBlobHelper` / `AsyncStorageQueueHelper`.
   - Always use `async with` context manager for proper resource cleanup.
 - Implement tests:
   - Unit tests for core logic and services.
   - Integration tests for critical API flows and data access.
 - Run a **code-quality and test-quality pass** on new/modified files:
   - Copilot auto-applies the relevant `.github/*-quality*.instructions.md` files by file type.
   - These enforce copyright headers, docstrings, naming conventions, comment cleanup,
     dead code removal, and test structure standards.
   - See the quality instruction files for the systematic folder-by-folder workflow.

 **Copilot usage**

 - **Required:** Use `.github/prompts/implementation-and-tests.prompt.md`:
   - To generate a step-by-step implementation plan with associated tests.
   - To ensure each step includes a test update.
 - **Auto-applied:** Language-specific quality instruction files:
   - Python: `.github/instructions/code-quality-py.instructions.md`, `.github/instructions/test-quality.instructions.md`
   - TypeScript: `.github/instructions/code-quality-ts.instructions.md`, `.github/instructions/test-quality-ts.instructions.md`
   - React: `.github/instructions/code-quality-tsx.instructions.md`, `.github/instructions/test-quality-tsx.instructions.md`
 - **Recommended:**
   - Smart Actions (VS Code) for **Generate Tests** on selected functions.
   - Copilot CLI Plan/Autopilot for repetitive refactors or broad pattern application (e.g., adding logging across multiple
 services).

 **Exit criteria**

 - All new code:
   - Uses the correct Azure libraries and established infrastructure patterns.
   - Compiles / type-checks and passes local tests.
   - Meets code-quality standards (copyright headers, docstrings, naming, no dead code).
 - Tests:
   - Unit tests cover key logic including edge cases.
   - Integration tests exist for high-risk flows.
   - Test files meet test-quality standards (structure, naming, assertions, mocking patterns).
 - No new TODOs left in critical paths without tracking issues.

 ---

 ### Phase 5 – Repository Documentation

 **Objective**

 Document the change so future engineers and stakeholders can understand design, usage, and implications.

 **Activities**

 - Create or update documentation:
   - Design doc / ADR in `/docs/adr/` or similar.
   - API documentation in `/docs/api/` or README.
   - Operational or runbook docs if necessary.
 - Reflect:
   - Architecture and Azure usage (Cosmos containers, Blob containers, etc.).
   - Testing strategy and coverage.
   - Any constraints or known limitations.

 **Copilot usage**

 - **Recommended:** Use `.github/prompts/repo-documentation.prompt.md`:
   - To generate the ADR/design doc.
   - To create or update API docs based on implemented endpoints.
 - Copilot should:
   - Reference actual types and files (repositories, services, controllers).
   - Align structure with existing docs.

 **Exit criteria**

 - At least:
   - One documentation artifact updated/created for the feature (ADR/design or API doc).
   - Links from index/README updated if necessary.

 ---

 ### Phase 6 – QA Activities

 **Objective**

 Verify that the system behaves as expected and no regressions are introduced.

 **Activities**

 - Plan and execute:
   - Automated regression suite (unit, integration, E2E as available).
   - Targeted manual QA (especially around UI/UX, performance, or complex flows).
 - If needed, create additional tests based on discovered gaps.
 - Run a **systematic code-quality and test-quality pass** across all modified folders:
   - Use the workflow defined in `.github/*-quality*.instructions.md`:
     list folder → read files → edit → compile/type-check → next folder.
   - This ensures code and test hygiene is verified before declaring QA complete.

 **Copilot usage**

 - **Required for medium/high-risk changes:** Use `.github/prompts/qa-rai-release.prompt.md`:
   - To generate a focused QA plan:
     - Automated tests to run/add.
     - Manual scenarios.
     - Regression areas.
 - **Auto-applied:** Quality instruction files activate when Copilot edits or reviews matching files.
 - Copilot CLI:
   - Plan and run test commands; in some cases, use Autopilot to fix failing tests with human review.

 **Exit criteria**

 - All targeted automated tests for this change pass.
 - QA plan executed; key manual scenarios verified.
 - Code-quality and test-quality passes completed on all modified files.
 - No unresolved critical or high-severity defects remain.

 ---

 ### Phase 7 – RAI (Responsible AI) Review

 **Objective**

 Ensure AI-related features and data handling meet RAI, privacy, and compliance expectations.

 > If a change does **not** involve AI or sensitive user data, this phase is a short confirmation; if it does, this phase is
 mandatory and more detailed.

 **Activities**

 - Identify:
   - AI components, models, or prompts touched.
   - Data types involved (PII, financial, health, etc.).
 - Assess:
   - Potential harms (e.g., unfair outcomes, harmful content, hallucinations).
   - Misuse or abuse scenarios.
 - Define mitigations:
   - Guardrails (validation, limits).
   - Monitoring (logging, metrics).
   - Documentation/disclosures.

 **Copilot usage**

 - **Recommended:** Reuse `.github/prompts/qa-rai-release.prompt.md`:
   - Emphasize RAI in the inputs.
   - Let Copilot propose:
     - Risks.
     - Mitigations.
     - Documentation updates needed (e.g., RAI notes in docs).

 **Exit criteria**

 - RAI risks documented and reviewed (if AI involved).
 - Mitigations identified and (for this release) either implemented or tracked as work items.
 - RAI doc updated or confirmed not applicable.

 ---

 ### Phase 8 – Prepare Release Script

 **Objective**

 Create or update a repeatable, safe release process for this change.

 **Activities**

 - Create or update release scripts (e.g., `/scripts/release/release-<service>.sh`):
   - Tagging/version bump.
   - Triggering ADO pipeline.
   - Environment selection.
   - Post-deploy checks (health/info endpoints, logs, metrics).
 - Ensure scripts are idempotent and safe to re-run where practical.

 **Copilot usage**

 - **Recommended:** Use `.github/prompts/qa-rai-release.prompt.md` to:
   - Generate a release checklist and script outline.
 - Copilot CLI:
   - Plan and scaffold basic script content.
   - Suggest integration with ADO or other automation.

 **Exit criteria**

 - Release script exists or is updated.
 - Release checklist is clear and documented (often in the same doc or a `/docs/release` file).

 ---

 ### Phase 9 – Publish to GitHub

 **Objective**

 Safely merge and publish changes to GitHub with traceability.

 **Activities**

 - Ensure:
   - All previous phases are complete (requirements, design, implementation, tests, docs, QA, RAI, release prep).
 - Create or update:
   - Pull request with:
     - Design/ADR reference.
     - Link to relevant work items.
     - Summary of QA and RAI results.
 - Leverage:
   - **Copilot code review** on the PR (GitHub).
   - Human code review.

 **Copilot usage**

 - GitHub PR:
   - Enable Copilot PR review to comment on potential issues.
 - VS Code + Copilot:
   - Apply suggested changes from code review.
   - Ensure final diffs still comply with Azure and architecture standards.
   - Quality instruction files auto-apply during any last-minute edits, ensuring
     code and test quality standards are maintained through final changes.

 **Exit criteria**

 - PR approved by:
   - At least one human reviewer.
   - Copilot code review (no unresolved critical concerns).
 - ADO pipeline green for the PR branch.
 - Code-quality and test-quality standards verified (no regressions from final edits).
 - Changes merged and available on the appropriate branch (main/develop).
 - Release executed according to the release script (Phase 8) when appropriate.

 ---

 ## 3. Summary of Required Copilot Integrations

 - **Copilot Instructions** (repo-level)
   - `.github/copilot-instructions.md` — MUST encode Azure library rules and reference repo patterns.
   - Always active when Copilot assists in this repo.

 - **Quality Instruction Files** (auto-applied by file type)
   - Code quality: `code-quality-py.instructions.md`, `code-quality-ts.instructions.md`, `code-quality-tsx.instructions.md`
   - Test quality: `test-quality.instructions.md`, `test-quality-ts.instructions.md`, `test-quality-tsx.instructions.md`
   - Auto-applied during Phase 4 (implementation), Phase 6 (QA), and Phase 9 (final PR edits).
   - No manual invocation needed.

 - **Prompt files** (VS Code Copilot — invoked manually per phase)
   - Requirements & Design:
     - `.github/prompts/requirement-and-design.prompt.md` – required — SDLC Phase 1–2
   - Repo Structure & CI/CD:
     - `.github/prompts/repo-structure-and-cicd.prompt.md` – recommended — SDLC Phase 3
   - Deployment & Infrastructure:
     - `.github/prompts/deployment.prompt.md` – recommended — SDLC Phase 3 + 8 (Bicep/AVM/azd)
   - Implementation & Tests:
     - `.github/prompts/implementation-and-tests.prompt.md` – required — SDLC Phase 4
   - Documentation:
     - `.github/prompts/repo-documentation.prompt.md` – recommended — SDLC Phase 5
   - QA, RAI, Release:
     - `.github/prompts/qa-rai-release.prompt.md` – required for medium/high-risk changes, recommended otherwise — SDLC Phase 6–8

 - **Copilot CLI**
   - Recommended for:
     - Large refactors and pattern-enforcement tasks.
     - Running and iterating on test suites.
     - Planning and applying bulk changes consistent with this SDLC.

 Adhering to this SDLC ensures that Copilot is used deliberately to:

 - **Accelerate** implementation, not replace design or review.
 - **Strengthen** QA through systematic test generation, quality passes, and targeted plans.
 - **Standardize** code, architecture, documentation, and Azure usage across the codebase.