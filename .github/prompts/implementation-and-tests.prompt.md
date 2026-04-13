---
description: "Implement features with test-driven development following SDLC Phase 4. Generates production code, unit tests, and integration tests with acceptance criteria."
agent: "Implementer"
argument-hint: "Describe the feature to implement"
---
<!--
File: .github/prompts/implementation-and-tests.prompt.md

How to use (VS Code):
1. After design is agreed, open this prompt file.
2. In Copilot Chat, say:
   "Use `.github/prompts/implementation-and-tests.prompt.md` for implementing:
    'Order history API using the approved Cosmos DB library repository pattern and the approved Storage library blob helper.'"
-->

# Implementation and Tests Prompt (SDLC Phase 4)

You are implementing a feature or change that already has an approved design.

This repository uses Azure services and standard patterns for Cosmos DB and Blob Storage. Prefer existing abstractions and
repositories over new ad-hoc code.

This prompt supports **SDLC Phase 4 – Implementation with Test Strategy** as defined in
`.github/SDLC-with-Copilot-and-Azure.md`. Follow its exit criteria.

## Inputs from the user

The user will provide:
- A short description of the feature/change.
- The relevant design/requirements or a summary.
- Any constraints (backward compatibility, performance, deadlines).

## Goals

1. Implement the change following this repo's architecture, Azure usage, and coding standards.
2. Generate or extend tests (unit and, where appropriate, integration tests).
3. Keep changes small, reviewable, and aligned with existing patterns.
4. Ensure the code-quality and test-quality standards in `.github/*.instructions.md` are respected.

## Context loading (MCP resources)

Before starting, load these resources for accurate implementation:

1. **Cosmos DB patterns** — `mcp_github_get_file_contents` → fetch `README.md` and
   `HANDS_ON_GUIDE.md` from `the project's Cosmos DB library repo (from copilot-instructions.md)`
   (Repository Pattern, entity definitions, query patterns)
2. **Blob/Queue patterns** — `mcp_github_get_file_contents` → fetch `README.md` from
   `the project's Storage library repo (from copilot-instructions.md)`
   (AsyncStorageBlobHelper, context manager usage)
3. **Framework docs** — Use **Context7 MCP** to load current documentation for:
   - FastAPI + Pydantic (for API services)
   - React + Vite (for web frontend)
   - Azure AI Agent Framework (for agent services)
4. **Language-specific best practices** — from awesome-copilot (load conditionally):
   - React frontend: `mcp_awesome-copil_load_instruction` → `"reactjs"`
   - MCP tools: `mcp_awesome-copil_load_instruction` → `"python-mcp-server"`
   - TypeScript tests: `mcp_awesome-copil_load_instruction` → `"nodejs-javascript-vitest"`

## Steps

0. **Define acceptance criteria (sprint contract)**

   Before writing any code, create testable acceptance criteria that define what "done"
   looks like for this feature. This bridges the gap between high-level design and
   testable implementation:

   - List specific behaviors the feature must exhibit when complete.
   - For each behavior, define: expected input, expected output, verification method.
   - Include edge cases and error paths — not just happy paths.
   - Present the criteria to the user for approval before proceeding.

   Example:
   ```
   | # | Criterion | Verification |
   |---|---|---|
   | 1 | POST /orders accepts valid order JSON | Integration test |
   | 2 | POST /orders rejects missing customerId with 422 | Unit test |
   | 3 | GET /orders/{id} returns 404 for non-existent order | Unit test |
   | 4 | Order entity saved to Cosmos DB with correct partition key | Unit test (mocked) |
   ```

1. **Locate relevant code**
   - Identify the modules/classes/functions that should be changed or created.
   - All layers live under `src/` as independent projects:
     - API: `src/<Name>API/app/` (FastAPI routers, services), `src/<Name>API/tests/`, `src/<Name>API/pyproject.toml`
     - Business: `src/<Name>Business/src/` (domain models, repositories, shared services), `src/<Name>Business/tests/`
     - Agent: `src/<Name>Agent/src/` (agents, MCP tools, middleware), `src/<Name>Agent/tests/`
     - Web: `src/<Name>Web/src/` (React components, hooks), `src/<Name>Web/package.json`
   - **Layering rules:**
     - API depends on Business (imports domain models, calls business services)
     - Agent depends on Business (shares domain models, uses repositories)
     - Business is the shared core — no dependency on API or Agent
     - Web calls API via HTTP — no direct dependency on Python layers\n   - For data access (lives in the **Business** layer):
     - Cosmos DB: look for existing `RepositoryBase` subclasses using `the approved Cosmos DB library`.
     - Blob/Queue: look for existing `AsyncStorageBlobHelper` / `AsyncStorageQueueHelper` usage via `the approved Storage library`.
   - For APIs and services (varies by template):
     - `the API template repo`: `app/main.py`, `app/routers/`, `app/services/`, DI via `app_context`
     - `the base app template repo`: `src/main.py`, `src/libs/` (AppContext, config, Azure)
     - `the agent template repo`: `src/libs/agent_framework/`, `src/samples/`

2. **Plan small steps (code → unit test → integration test)**
   - Break the implementation into 3–7 steps, following this strict order:
     1. Domain model / entity → unit test for validation
     2. Repository / data access → unit test with mocked DB
     3. Business service → unit test with mocked repository
     4. API route / controller → unit test for route handler
     5. Integration tests → HTTP-level tests for API endpoints
     6. Run all tests → `uv run pytest --cov`
   - **Never move to the next step without writing the unit test for the current step.**
   - For each step, specify:
     - Files to create/edit.
     - What behavior will be added or changed.
     - Which unit test will be written immediately after.
   - When Cosmos DB or Blob is used, explicitly state which repository or service you will extend or create.

3. **Implement code + unit tests (per step)**
   - For each step in the plan:
     - **First:** implement the production code.
     - **Immediately after:** write the unit test for that code.
     - Do NOT batch all tests at the end — test each step as you go.
   - Use these Python libraries (do NOT use raw Azure SDKs):
     - `the approved Cosmos DB library` via `RepositoryBase[Entity, KeyType]` pattern.
     - `the approved Storage library` via `AsyncStorageBlobHelper` / `AsyncStorageQueueHelper` with `async with`.
   - Unit tests go in `tests/` at the project root (match existing folder structure).
   - Follow the language-specific quality standards:
     - **Python**: `.github/instructions/code-quality-py.instructions.md` and `.github/instructions/test-quality.instructions.md`
     - **TypeScript**: `.github/instructions/code-quality-ts.instructions.md` and `.github/instructions/test-quality-ts.instructions.md`
     - **React (TSX)**: `.github/instructions/code-quality-tsx.instructions.md` and `.github/instructions/test-quality-tsx.instructions.md`

4. **Write/update integration tests (after all code + unit tests)**
   - After all implementation steps are complete with unit tests:
     - Write **API-level integration tests** for new endpoints (HTTP tests using test client).
     - Write **data access integration tests** that exercise Cosmos DB/Blob via the library abstractions.
   - Integration tests go in `tests/integration/` or `tests/` alongside unit tests.

5. **Run all tests and verify**
   - Run `uv run pytest --cov` (Python) or `npx vitest run` (TypeScript/React).
   - Verify all tests pass and coverage meets thresholds.

6. **Check for cross-cutting concerns**
   - Logging:
     - Use the project's logging configuration (Python `logging` module or structured logger).
   - Error handling:
     - Use consistent exception types and error responses as existing services.
   - Security:
     - Use existing authentication patterns (DefaultAzureCredential, Pydantic settings); do not bypass them.
   - Performance:
     - Be cautious about cross-partition queries or large blob downloads; highlight any potential performance concerns.

7. **Map to CI/CD**
   - If the change requires new build or test steps (e.g., new test project, new integration test stage):
     - Suggest updates to Azure DevOps pipelines (e.g., `azure-pipelines.yml` or `/ado/*.yml`).
     - Keep the pipeline structure consistent with existing stages.

8. **Self-evaluation before completion**

   Before reporting work as done, perform a deliberate self-review:

   - Re-read the acceptance criteria from Step 0. Is every criterion verified by a passing test?
   - Review your own code as if you didn't write it. Look for edge cases, hardcoded values,
     missing validation, and functions that grew too large.
   - Generate an acceptance criteria coverage table showing status of each criterion.
   - Fix any gaps found before marking work complete.

   > **Warning:** Generators tend to be overly positive about their own work.
   > Be deliberately critical. Look for what is WRONG, not for confirmation you did well.

9. **SDLC Exit Criteria check (Phase 4)**
   - Acceptance criteria defined and approved before coding.
   - All new code uses the correct Azure libraries and established infrastructure patterns.
   - Code compiles / type-checks and passes local tests.
   - Unit tests cover key logic including edge cases.
   - Integration tests exist for high-risk flows.
   - No new TODOs left in critical paths without tracking issues.
   - Code-quality and test-quality standards are met (copyright headers, docstrings,
     naming conventions, comment cleanup, import order).
   - Self-evaluation completed with acceptance criteria coverage table.
   - All acceptance criteria have corresponding passing tests.
   - For each criterion, mark it as:
     - ✅ satisfied
     - ⚠️ partially satisfied (explain what remains)
     - ⛔ not satisfied (explain what is missing)

9. **Output format**

Return your answer in this structure:

- Acceptance Criteria (sprint contract)
- Step-by-step Implementation Plan (with test for each step)
- Code Changes + Unit Tests (grouped by step — test immediately follows code)
- Integration Tests (after all code + unit tests)
- Self-Evaluation: Acceptance Criteria Coverage Table
- CI/CD Impact (if any)
- Follow-up Tasks (docs, QA, feature flags)
- **SDLC Exit Criteria Check (Phase 4)** with ✅/⚠️/⛔

<!--
Example invocation for engineers:

"Copilot, use `.github/prompts/implementation-and-tests.prompt.md` to implement:
 Add an /orders/{customerId}/history endpoint. Data comes from Cosmos DB using
 the approved Cosmos DB library with a CustomerOrderRepository extending RepositoryBase.
 PDF invoices should be retrieved via the approved Storage library AsyncStorageBlobHelper.
 Make sure we have unit tests for the service and router,
 and an integration test for the API endpoint."
-->
