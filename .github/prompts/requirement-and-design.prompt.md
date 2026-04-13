---
description: "Analyze requirements and design solutions for new features. Produces ADR-ready design proposals with Azure service mapping, architecture decisions, and test strategy."
agent: "Analyst"
argument-hint: "Describe the feature or requirement to analyze"
---
<!--
 File: .github/prompts/requirement-and-design.prompt.md

 How to use (VS Code):
 1. Open this file in VS Code.
 2. Open GitHub Copilot Chat.
 3. Type something like:
    "Use the prompt file `.github/prompts/requirement-and-design.prompt.md` for this feature:
     'Add order history API using Cosmos DB and Azure Blob for attachments.'"
 4. Paste your feature description when Copilot asks for inputs.
 -->

 # Requirement Analysis and Design Prompt (SDLC Phases 1–2)

 You are helping analyze requirements and design a solution inside this repository.

 This repo uses Azure (Cosmos DB, Blob Storage, etc.) and the architecture and technology rules defined in the repository custom
 instructions.

 This prompt supports **SDLC Phases 1–2 (Requirement Analysis and Design)** as defined in
 `.github/SDLC-with-Copilot-and-Azure.md`. Follow their exit criteria.

 ## Inputs from the user

 The user will provide:
 - Business problem or feature idea.
 - High-level constraints (time, tech stack, performance, compliance/RAI).
 - Any known dependencies or integration points.

 ## Goals

 1. Clarify requirements.
 2. Propose a design consistent with this repo’s architecture and patterns, including Azure usage.
 3. Identify which phases of the SDLC will be impacted and which artifacts are needed.
 ## Context loading (MCP resources)

 Before starting, load these resources for enriched analysis:

 1. **Planning tools** — `mcp_awesome-copil_load_collection` → `"project-planning"`
    (structured planning patterns and feature breakdown guidance)
 2. **Task breakdown** — `mcp_awesome-copil_load_instruction` → `"task-implementation"`
    (feature decomposition into implementable steps)
 3. **Reference catalog** — `mcp_github_get_file_contents` → fetch `reference-catalog.md`
    from the SDLC template repo (verify Azure service choices match approved libraries)
 4. **Template patterns** — `mcp_github_get_file_contents` → fetch project structure from
    the matching template repo (`the base app template repo`, `the API template repo`,
    or `the agent template repo`)
 5. **Framework docs** — Use **Context7 MCP** to get current documentation for frameworks
    being evaluated (FastAPI, Pydantic, Azure AI Agent Framework, etc.)
 6. **ADO wiki** — Search the team's Azure DevOps wiki for engineering guidelines:
    - Search: `mcp_ado_search_wiki(searchText: "architecture", project: "CSA CTO Engineering")`
    - Fetch content: `mcp_ado_wiki_get_page_content(wikiIdentifier: "CSA-CTO-Engineering.wiki", project: "CSA CTO Engineering", path: "/<page-path>")`
 ## Steps

 1. **Clarify requirements**
    - Ask up to 3–5 focused questions if needed.
    - Restate the requirements in your own words as:
      - Problem statement
      - Goals
      - Non-goals / out of scope
      - Constraints (tech, performance, security, RAI, data residency, etc.)

 2. **Align with architecture and Azure conventions**
    - Based on repo instructions and existing code:
      - Identify which layers are involved (routers/endpoints, services, domain logic, data access).
      - Identify which Azure services are relevant (Cosmos DB, Blob Storage, etc.).
      - Point to existing patterns/components that should be reused:
        - Cosmos DB: `the approved Cosmos DB library` with `RepositoryBase[Entity, KeyType]` pattern.
        - Blob/Queue: `the approved Storage library` with `AsyncStorageBlobHelper` / `AsyncStorageQueueHelper`.
        - Scaffolding templates from `.github/reference-catalog.md`.

 3. **Propose a design**
    - Propose one **recommended design** and optionally 1–2 alternatives with trade-offs.
    - For the recommended design, provide:
      - High-level architecture diagram in text (components and relationships).
      - Main data flows (request → processing → persistence → external calls).
      - Where Cosmos DB and Blob Storage fit in (which entities, which containers, etc.).
      - Error handling and logging strategy using the standard abstractions.
      - Testing approach (unit/integration & test boundaries).
      - Any RAI / security/privacy considerations if applicable.

 4. **Map to the SDLC**
    - For each SDLC Phase, specify what needs to be done:
      1. Requirement Analysis – what is now clear or still open.
      2. Design – what artifacts should be created (e.g., ADR, design doc).
      3. Repo structure / CI–CD – new folders, pipelines, or configs needed (especially for new Azure resources).
      4. Implementation – modules/files/classes to create or modify.
      5. Tests – which test suites to add or extend (unit, integration).
      6. Documentation – which docs to update/create.
      7. QA – manual/exploratory testing, performance checks, etc.
      8. RAI review – any model/AI/data concerns to review.
      9. Release – any special release or migration steps.


 5. **SDLC Exit Criteria check (Phases 1-2)**
    - Requirements are clarified and documented:
      - Problem statement, goals, non-goals.
      - Known constraints (tech, security, RAI).
    - Agreement on scope and success criteria.
    - Design is documented (ADR/design doc) and agreed by the team.
    - Azure library choices are explicit and compliant.
    - Reuse of internal patterns and/or external templates is identified.
    - For each criterion, mark it as:
      - Satisfied
      - Partially satisfied (explain what remains)
      - Not satisfied (explain what is missing)

 6. **Output format**

 Return your answer in this structure:

 - Summary
 - Requirements (clarified)
 - Recommended Design
 - Alternatives (if any)
 - SDLC Impact by Phase
 - Open Questions / Risks
 - **SDLC Exit Criteria Check (Phases 1-2)**

 <!--
 Example invocation for engineers:

 "Copilot, use the requirement-and-design prompt file to design a feature:
 Allow customers to download their order history. Orders should be stored in Cosmos DB
 using the approved Cosmos DB library repository pattern, and PDF invoices should be stored in Azure Blob
 Storage using the approved Storage library AsyncStorageBlobHelper."
 -->