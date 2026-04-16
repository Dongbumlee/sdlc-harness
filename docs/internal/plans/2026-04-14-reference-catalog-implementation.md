# Living Reference Catalog Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Transform `.github/reference-catalog.md` from a static file into a living document that agents populate during the design phase, with optional user review and append-only downstream consumption.

**Architecture:** One new skill (`sdlc-reference-catalog`) becomes the single source of truth for catalog interaction. The `sdlc-workspace-init` skill creates an empty template at Step 0. The Analyst populates it during Phase 1-2. The Harness offers an optional review checkpoint. Downstream agents (Scaffolder, Implementer, Deployer, Documenter) consume and append.

**Tech Stack:** Markdown agent/skill instructions, YAML canary specs, no application code.

**Design doc:** `docs/specs/2026-04-14-reference-catalog-design.md`

---

## Codebase Orientation

Before you start, understand these conventions:

- **Agent files** live at `.github/plugin/agents/<name>.agent.md` — YAML frontmatter (`name`, `description`, `user-invocable`, `tools`, optionally `agents`) followed by a markdown body.
- **Skill files** live at `.github/plugin/skills/<skill-name>/SKILL.md` — YAML frontmatter (`name`, `description`) followed by a markdown body with numbered procedure steps.
- **Canary specs** live at `bench/canaries/<phase>/<id>.yaml` — YAML with `id`, `version`, `phase`, `title`, `description`, `prompt`, `expected` (containing `graders` array), `timeout_seconds`, `tags`. Validate with: `python tools/validate_canaries.py bench/canaries/`
- **Sync rule:** `.github/plugin/` must always mirror `vscode-extension/`. After all changes, sync with: `rsync -av --delete .github/plugin/ vscode-extension/ --exclude='.git'`
- **Git:** All work happens on the `evo` branch. Push with: `unset GITHUB_TOKEN && git push origin evo`
- **No Python app code** — all deliverables are markdown and YAML. "Tests" are canary schema validation and E2E checklists.

---

## Task 1: Create the `sdlc-reference-catalog` skill

This is the foundation — every other task references this skill.

**Files:**
- Create: `.github/plugin/skills/sdlc-reference-catalog/SKILL.md`

### Step 1: Create the skill directory

```bash
mkdir -p .github/plugin/skills/sdlc-reference-catalog
```

### Step 2: Create the skill file

Create `.github/plugin/skills/sdlc-reference-catalog/SKILL.md` with this exact content:

```markdown
---
name: sdlc-reference-catalog
description: "Manage the living reference catalog — research methodology, population rules, consumption rules, append-only enforcement, and review checkpoint behavior. Activated by the Analyst (population), Scaffolder/Implementer/Deployer/Documenter (consumption), and Harness (review checkpoint)."
---

# SDLC Reference Catalog

## When to use

- **Analyst (Phase 1-2):** After producing a design proposal, activate this skill to research and populate `.github/reference-catalog.md`.
- **Downstream agents (Phase 3+):** Before starting phase work, activate this skill to read the catalog and follow consumption rules.
- **Harness:** After Analyst completes, activate this skill to run the review checkpoint.

## Catalog file location

`.github/reference-catalog.md` — created by `sdlc-workspace-init` during Step 0 as an empty template.

## Catalog template structure

The catalog has 5 fixed top-level sections. The Analyst fills these during Phase 1-2. Downstream agents may add sub-sections and entries but must not modify existing content (after user approval).

```
# Reference Catalog

> This catalog is populated by the Analyst agent during the design phase.
> Downstream agents may append new entries but must not modify existing ones.
> Each entry includes the source agent that added it.

## Approved Libraries

<!-- Analyst: Research and list approved packages with versions, purpose, and installation -->

## Project Templates

<!-- Analyst: Document project structure patterns, scaffolding templates, starter repos -->

## API Patterns

<!-- Analyst: Document key design patterns (Repository Pattern, SDK abstractions, etc.) -->

## Code Examples

<!-- Analyst: Include representative code snippets showing approved usage patterns -->

## Documentation Links

<!-- Analyst: Link to official docs, internal wikis, and reference guides -->
```

### Entry format

Every entry appended by any agent must use this format:

```
### [Entry Name]
- **Source:** [agent-name] (Phase [N])
- **Package/Pattern:** [name@version or pattern name]
- **Purpose:** [what it's for]
- **Usage:** [code example or description]
- **Links:** [documentation URLs]
```

Mark user-specified entries as `Source: user-provided`.

## Research methodology (Analyst only)

When populating the catalog, research sources in this priority order:

1. **User-specified libraries/templates** — ask the user: "Are there any specific libraries, templates, or frameworks you'd like me to include in the reference catalog?" Mark these as `Source: user-provided`.
2. **GitHub MCP** — fetch patterns from org reference repos (when available). Use `mcp_github_get_file_contents` to read README files and example code from template repos referenced in `copilot-instructions.md`.
3. **Context7 MCP** — load official documentation for the chosen tech stack. Use `mcp_context7_resolve-library-id` and `mcp_context7_get-library-docs` for framework docs.
4. **awesome-copilot MCP** — load best practice patterns. Use `mcp_awesome-copil_search_instructions` to find relevant instructions for the project's tech stack.
5. **Web research** — community patterns, comparison articles, and ecosystem guidance for libraries not covered by the above sources.

For each source that is unavailable (MCP not running, auth failure), skip it gracefully and note in the catalog entry that the source was unavailable.

## Population rules (Analyst only)

- Use the 5 fixed top-level headings (`## Approved Libraries`, `## Project Templates`, `## API Patterns`, `## Code Examples`, `## Documentation Links`).
- Add sub-sections freely under each heading as needed for the project domain (e.g., `### Device SDK Patterns` under `## API Patterns` for an IoT project).
- Every entry must include: source agent, package/version, purpose, usage example, and links.
- Mark user-specified libraries as `Source: user-provided`.
- Replace the HTML comment placeholders with actual content as you populate each section.

## Consumption rules (downstream agents)

- **Read first:** Before starting any phase work, read `.github/reference-catalog.md`.
- **Prefer catalog:** Use catalog entries as the primary reference for libraries, patterns, and templates. Do not independently research what is already documented in the catalog.
- **Append if new:** If you discover a pattern or library not in the catalog during your phase work, append it under the appropriate top-level section using the entry format above. Include `Source: [your-agent-name] (Phase [N])`.
- **Never modify:** After the catalog has been approved (or auto-approved), never modify or remove existing entries. Append only.

## Append-only rules

- The append-only rule activates **after user approval** of the catalog (or after auto-approval in self-driving mode).
- Before approval, the Analyst may freely modify any entry during revision cycles.
- After approval, all agents (including the Analyst) may only append new entries.
- Add new entries at the bottom of the appropriate top-level section.
- Include `Source: [agent-name] (Phase [N])` on every appended entry.
- Never modify or remove existing entries.

## Review checkpoint behavior (Harness only)

After the Analyst completes catalog population:

1. Check `catalog_review` setting in `harness-config.yml`.
2. **If `true` (or field is missing/unset — default is review):**
   - Present a summary to the user: count of entries per section (e.g., "Catalog populated: 5 libraries, 2 templates, 3 API patterns, 4 code examples, 6 doc links").
   - Ask the user: "Would you like to review the catalog, request changes, or proceed?"
   - **If user requests changes:** Route the revision back to the Analyst. The Analyst may modify any entry freely (append-only has not activated yet). After revision, re-present the summary.
   - **If user says "proceed":** Append-only mode activates. Continue to the next phase.
   - **If user dismisses without explicit response:** Treat as approved. Append-only activates.
3. **If `false`:**
   - Log that the catalog was populated and auto-proceed. Append-only activates immediately.

## Error handling

- **Missing catalog file:** If `.github/reference-catalog.md` doesn't exist when a downstream agent tries to read it, proceed without catalog guidance and log a warning. No hard failure.
- **Empty catalog:** If the Analyst fails to populate the catalog, the template remains with placeholder comments. Downstream agents treat missing entries as "not yet researched" and do their own research, appending discoveries.
- **Review mode interruption:** If the user dismisses the review checkpoint without explicit approval, treat as approved. Append-only activates.
```

### Step 3: Verify the skill file exists and has correct structure

```bash
head -5 .github/plugin/skills/sdlc-reference-catalog/SKILL.md
```

Expected output — the YAML frontmatter:
```
---
name: sdlc-reference-catalog
description: "Manage the living reference catalog — research methodology, population rules, consumption rules, append-only enforcement, and review checkpoint behavior. Activated by the Analyst (population), Scaffolder/Implementer/Deployer/Documenter (consumption), and Harness (review checkpoint)."
---
```

Also verify the key sections exist:

```bash
grep -c "^## " .github/plugin/skills/sdlc-reference-catalog/SKILL.md
```

Expected: `10` (or more — the 5 catalog template headings inside the code block plus the skill's own sections).

### Step 4: Commit

```bash
git add .github/plugin/skills/sdlc-reference-catalog/SKILL.md
git commit -m "feat: add sdlc-reference-catalog skill for living catalog management"
```

---

## Task 2: Update `sdlc-workspace-init` skill

Add catalog template creation and the review preference question.

**Files:**
- Modify: `.github/plugin/skills/sdlc-workspace-init/SKILL.md`

### Step 1: Read the current file

Read `.github/plugin/skills/sdlc-workspace-init/SKILL.md` to confirm the current content.

### Step 2: Update the "Files deployed" table

In the `## Files deployed` table (around line 25), add a new row for the catalog template. Find this table:

```markdown
| `assets/prompts/*.prompt.md` | `.github/prompts/` | No — copied as-is |
```

Add a new row after it:

```markdown
| `assets/prompts/*.prompt.md` | `.github/prompts/` | No — copied as-is |
| *(generated at runtime)* | `.github/reference-catalog.md` | Yes — empty template with 5 fixed sections |
```

### Step 3: Replace Step 6 content

Find the current Step 6 (lines 110-121):

```markdown
### Step 6: Deploy filtered reference catalog

1. Read `.github/reference-catalog.md` from the skill assets.
2. Based on the **primary language(s)** from Step 4, generate a **project-specific** version:
   - Keep all language-agnostic sections (intro, how to use, adding entries).
   - In SDK tables (§1.1–1.4), **highlight the project's language rows** and keep others as reference.
   - In the Template Matrix, **bold the row(s)** matching the project's language.
   - In detailed templates (§2.1–2.4), include only the language-specific entries that apply.
3. Write the filtered catalog to `.github/reference-catalog.md`.

> **Why filter?** A Java team doesn't need to read through Python/Rust/Go details on every lookup.
> The full catalog stays in the skill assets; the deployed version is focused on the project's stack.
```

Replace the entire Step 6 with:

```markdown
### Step 6: Create empty reference catalog template

Create `.github/reference-catalog.md` with the empty catalog template. This template will be populated
by the Analyst agent during Phase 1-2 using the `sdlc-reference-catalog` skill.

Write this content to `.github/reference-catalog.md`:

```
# Reference Catalog

> This catalog is populated by the Analyst agent during the design phase.
> Downstream agents may append new entries but must not modify existing ones.
> Each entry includes the source agent that added it.

## Approved Libraries

<!-- Analyst: Research and list approved packages with versions, purpose, and installation -->

## Project Templates

<!-- Analyst: Document project structure patterns, scaffolding templates, starter repos -->

## API Patterns

<!-- Analyst: Document key design patterns (Repository Pattern, SDK abstractions, etc.) -->

## Code Examples

<!-- Analyst: Include representative code snippets showing approved usage patterns -->

## Documentation Links

<!-- Analyst: Link to official docs, internal wikis, and reference guides -->
```

> **Why an empty template?** The Analyst populates this during the design phase using live research
> from GitHub MCP, Context7, awesome-copilot, and web sources. A static pre-populated catalog
> falls out of date; a living catalog stays current with each project's actual tech stack.
```

### Step 4: Add the catalog review preference question

After Step 6 and before Step 7 (Deploy instruction files), insert a new step. Find:

```markdown
### Step 7: Deploy instruction files
```

Insert this new step before it:

```markdown
### Step 6b: Ask catalog review preference

Ask the user:

> **Catalog review preference:** Would you like to review the reference catalog before
> development begins, or proceed automatically?
>
> - **review** (default) — Harness will show you the catalog summary after the Analyst
>   populates it, and you can approve, edit, or proceed.
> - **auto** — Harness proceeds automatically after catalog population.

Store the answer in `harness-config.yml` as:

```yaml
catalog_review: true   # "review" → true (default)
catalog_review: false  # "auto" → false
```

If the user doesn't answer or skips the question, default to `catalog_review: true`.

```

### Step 5: Update Step 9 (Report) to mention catalog

Find the report section (around line 165). In the report template, find:

```markdown
- ✅ `.github/prompts/` — 6 SDLC prompt files deployed
```

Add a line after it:

```markdown
- ✅ `.github/prompts/` — 6 SDLC prompt files deployed
- ✅ `.github/reference-catalog.md` — empty catalog template created (Analyst will populate during Phase 1-2)
```

### Step 6: Verify changes

```bash
grep -n "reference-catalog" .github/plugin/skills/sdlc-workspace-init/SKILL.md
```

Expected: Multiple matches showing the new Step 6, Step 6b, and report line.

```bash
grep -n "catalog_review" .github/plugin/skills/sdlc-workspace-init/SKILL.md
```

Expected: At least 2 matches (the question and the YAML examples).

### Step 7: Commit

```bash
git add .github/plugin/skills/sdlc-workspace-init/SKILL.md
git commit -m "feat: update workspace-init to create catalog template and ask review preference"
```

---

## Task 3: Update Analyst agent

Add catalog population responsibility after design work is complete.

**Files:**
- Modify: `.github/plugin/agents/analyst.agent.md`

### Step 1: Read the current file

Read `.github/plugin/agents/analyst.agent.md` to confirm the current content.

### Step 2: Add catalog population to the responsibilities list

Find the responsibilities section (around line 14):

```markdown
## Your responsibilities

1. Clarify requirements from user descriptions or GitHub issues.
2. Research existing patterns in the codebase and reference repos.
3. Propose architecture and design decisions.
4. Map features to Azure services following the reference catalog.
5. Produce a structured design output (ADR-ready format).
```

Replace it with:

```markdown
## Your responsibilities

1. Clarify requirements from user descriptions or GitHub issues.
2. Research existing patterns in the codebase and reference repos.
3. Propose architecture and design decisions.
4. Map features to Azure services following the reference catalog.
5. Produce a structured design output (ADR-ready format).
6. Populate the living reference catalog with researched libraries, patterns, and templates.
```

### Step 3: Add catalog population section before "Output format"

Find the section header (around line 67):

```markdown
## Output format
```

Insert the following new section **before** it:

```markdown
## Reference catalog population

After completing your design proposal, populate the living reference catalog.

1. **Activate the `sdlc-reference-catalog` skill** — read its research methodology, population rules, and entry format.

2. **Ask the user about preferred libraries:**
   > "Are there any specific libraries, templates, or frameworks you'd like me to include in the reference catalog?"
   
   Record any user-specified items as `Source: user-provided` entries.

3. **Research and populate** `.github/reference-catalog.md` using the priority order from the skill:
   - User-specified libraries/templates (from the question above)
   - GitHub MCP (org reference repos, when available)
   - Context7 (official documentation for chosen tech stack)
   - awesome-copilot (best practice patterns)
   - Web research (community patterns, comparison articles)

4. **Write entries** under the 5 fixed top-level sections using the entry format defined in the skill. Add domain-specific sub-sections as needed (e.g., `### Device SDK Patterns` under `## API Patterns` for an IoT project).

5. **Report completion** to Harness with a summary: number of entries per section.

> **This is a natural extension of your existing research work.** You already research libraries,
> templates, and patterns during the design phase. This step structures that research into a
> shared catalog that downstream agents consume.

```

### Step 4: Verify changes

```bash
grep -n "reference catalog" .github/plugin/agents/analyst.agent.md
```

Expected: Multiple matches showing the new responsibility (#6) and the new section.

```bash
grep -n "sdlc-reference-catalog" .github/plugin/agents/analyst.agent.md
```

Expected: At least 1 match (the skill activation instruction).

### Step 5: Commit

```bash
git add .github/plugin/agents/analyst.agent.md
git commit -m "feat: add catalog population responsibility to Analyst agent"
```

---

## Task 4: Update Harness agent

Add the review checkpoint and catalog review preference to the orchestration flow.

**Files:**
- Modify: `.github/plugin/agents/harness.agent.md`

### Step 1: Read the current file

Read `.github/plugin/agents/harness.agent.md` to confirm the current content.

### Step 2: Add catalog review preference to Step 2

Find the end of Step 2 (around line 116-118):

```markdown
This ensures zero friction at project start — engineers describe their task and Harness
handles configuration progressively as design decisions are made.
```

Insert the following after that paragraph, before `## Your responsibilities`:

```markdown

### Step 2b: Catalog review preference

If `harness-config.yml` does not already contain a `catalog_review` field, ask the user:

> **Catalog review preference:** Would you like to review the reference catalog before
> development begins, or proceed automatically? (review/auto) [default: review]

Store in `harness-config.yml` as `catalog_review: true` (review) or `catalog_review: false` (auto).
Default to `true` if the user skips the question or the field is missing.

```

### Step 3: Add the post-Analyst review checkpoint

Find the design feedback loop section (around line 182-189):

```markdown
#### Phase 1-2: Design feedback loop (Analyst)

When the Analyst's design proposal has gaps (missing NFRs, untestable requirements,
over-specified implementation details):

1. Point out the specific gaps to the Analyst.
2. Ask the Analyst to revise the affected sections.
3. Review the revised proposal before proceeding to ADR creation.
```

Replace it with:

```markdown
#### Phase 1-2: Design feedback loop (Analyst)

When the Analyst's design proposal has gaps (missing NFRs, untestable requirements,
over-specified implementation details):

1. Point out the specific gaps to the Analyst.
2. Ask the Analyst to revise the affected sections.
3. Review the revised proposal before proceeding to ADR creation.

#### Phase 1-2: Reference catalog review checkpoint

After the Analyst completes Phase 1-2 (design proposal + catalog population):

1. **Check `catalog_review`** in `harness-config.yml`.
2. **If `true` (or unset):**
   - Present a catalog summary to the user: count of entries per section (e.g., "Catalog populated: 5 libraries, 2 templates, 3 API patterns, 4 code examples, 6 doc links").
   - Ask: "Would you like to review the catalog, request changes, or proceed?"
   - **If the user requests changes:** Route the revision back to the Analyst. The Analyst may modify entries freely — append-only has not activated yet. After revision, re-present the summary.
   - **If the user says "proceed":** Append-only mode activates. Continue to ADR creation.
   - **If the user dismisses without responding:** Treat as approved. Append-only activates.
3. **If `false`:** Log that the catalog was populated and auto-proceed. Append-only activates immediately.

After this checkpoint, downstream agents follow the `sdlc-reference-catalog` skill's append-only rules.

```

### Step 4: Update the workflow rules to mention catalog consultation

Find the workflow rules section (around line 162-169):

```markdown
## Workflow rules

- **Always check the reference catalog** before allowing new dependencies. Use GitHub MCP to fetch
  `.github/reference-catalog.md` if needed.
```

Replace that bullet with:

```markdown
## Workflow rules

- **Always consult the reference catalog** before allowing new dependencies. Read `.github/reference-catalog.md`
  directly — it is populated by the Analyst during Phase 1-2 and kept current by downstream agents.
```

### Step 5: Verify changes

```bash
grep -n "catalog_review" .github/plugin/agents/harness.agent.md
```

Expected: At least 3 matches (Step 2b, checkpoint logic).

```bash
grep -n "Reference catalog review checkpoint" .github/plugin/agents/harness.agent.md
```

Expected: 1 match.

### Step 6: Commit

```bash
git add .github/plugin/agents/harness.agent.md
git commit -m "feat: add catalog review checkpoint and preference to Harness agent"
```

---

## Task 5: Update downstream agents (4 files)

Add catalog consumption instructions to Scaffolder, Implementer, Deployer, and Documenter.

**Files:**
- Modify: `.github/plugin/agents/scaffolder.agent.md`
- Modify: `.github/plugin/agents/implementer.agent.md`
- Modify: `.github/plugin/agents/deployer.agent.md`
- Modify: `.github/plugin/agents/documenter.agent.md`

### Step 1: Read all four files

Read all four agent files to confirm their current content and find the right insertion points.

### Step 2: Update Scaffolder

In `.github/plugin/agents/scaffolder.agent.md`, find the "Before scaffolding" section (around line 57). Right before the existing step `0. **Verify GitHub MCP authentication (required):**`, insert:

```markdown
## Reference catalog

Before starting scaffolding work, read `.github/reference-catalog.md` and activate the
`sdlc-reference-catalog` skill. Use catalog entries under `## Project Templates` and
`## Approved Libraries` as your primary reference for project structure and dependencies.

If you discover a new template pattern or library not in the catalog during scaffolding,
append it under the appropriate section using the entry format from the skill.
Include `Source: Scaffolder (Phase 3)` on your entries.

```

### Step 3: Update Implementer

In `.github/plugin/agents/implementer.agent.md`, find the "Before implementing" section (around line 72). Right before the existing step `0. **Read the project manifest**`, insert:

```markdown
## Reference catalog

Before starting implementation work, read `.github/reference-catalog.md` and activate the
`sdlc-reference-catalog` skill. Use catalog entries under `## Approved Libraries`,
`## API Patterns`, and `## Code Examples` as your primary reference for SDK usage and patterns.

If you discover a new pattern or library not in the catalog during implementation,
append it under the appropriate section using the entry format from the skill.
Include `Source: Implementer (Phase 5)` on your entries.

```

### Step 4: Update Deployer

In `.github/plugin/agents/deployer.agent.md`, find the "Before creating infrastructure" section (around line 22). Right before the existing step `0. **Verify GitHub MCP authentication (required):**`, insert:

```markdown
## Reference catalog

Before creating infrastructure, read `.github/reference-catalog.md` and activate the
`sdlc-reference-catalog` skill. Use catalog entries under `## Approved Libraries` and
`## Documentation Links` as your reference for Azure service patterns and AVM module versions.

If you discover a new infrastructure pattern not in the catalog during deployment work,
append it under the appropriate section using the entry format from the skill.
Include `Source: Deployer (Phase 7)` on your entries.

```

### Step 5: Update Documenter

In `.github/plugin/agents/documenter.agent.md`, find the "Before writing documentation" section (around line 43). Right before the existing step `0. **Verify GitHub MCP authentication (required):**`, insert:

```markdown
## Reference catalog

Before writing documentation, read `.github/reference-catalog.md` and activate the
`sdlc-reference-catalog` skill. Use catalog entries as your reference for accurate library names,
version numbers, and API patterns when writing ADRs, API docs, and READMEs.

If you discover documentation links or patterns not in the catalog during documentation work,
append them under `## Documentation Links` using the entry format from the skill.
Include `Source: Documenter (Phase 8)` on your entries.

```

### Step 6: Verify changes across all four files

```bash
grep -l "sdlc-reference-catalog" .github/plugin/agents/scaffolder.agent.md .github/plugin/agents/implementer.agent.md .github/plugin/agents/deployer.agent.md .github/plugin/agents/documenter.agent.md
```

Expected: All 4 files listed.

```bash
grep -c "Reference catalog" .github/plugin/agents/scaffolder.agent.md .github/plugin/agents/implementer.agent.md .github/plugin/agents/deployer.agent.md .github/plugin/agents/documenter.agent.md
```

Expected: Each file shows at least 1 match.

### Step 7: Commit

```bash
git add .github/plugin/agents/scaffolder.agent.md .github/plugin/agents/implementer.agent.md .github/plugin/agents/deployer.agent.md .github/plugin/agents/documenter.agent.md
git commit -m "feat: add catalog consumption instructions to 4 downstream agents"
```

---

## Task 6: Update tests and canaries

Add canary specs for catalog behavior and update E2E test checklists.

**Files:**
- Create: `bench/canaries/design/des-002-catalog-population.yaml`
- Create: `bench/canaries/scaffold/scf-002-catalog-consumption.yaml`
- Modify: `SDLC-END-TO-END-TEST-SCRIPT.md`
- Modify: `tests/e2e-pipeline-test/test-scenario.md`

### Step 1: Create the design-phase canary spec for catalog population

Create `bench/canaries/design/des-002-catalog-population.yaml` with this content:

```yaml
# Canary: Reference Catalog Population During Design
id: des-002-catalog-population
version: "1.0"
phase: design
title: "Reference Catalog Population During Design"
description: >
  Tests that the Analyst agent populates the living reference catalog during
  the design phase, including asking the user about preferred libraries,
  researching sources in priority order, and writing entries in the correct
  format under the 5 fixed top-level sections.

prompt: |
  You are the Analyst agent. You have just completed a design proposal for a
  FastAPI + Cosmos DB + React project called "TaskTracker". The user specified
  they want to use "azure-cosmos" and "pydantic v2".

  Now populate the reference catalog at `.github/reference-catalog.md` following
  the sdlc-reference-catalog skill. The catalog template already exists with
  5 empty sections: Approved Libraries, Project Templates, API Patterns,
  Code Examples, Documentation Links.

  Research and populate entries for the project's tech stack. Include the
  user-specified libraries as `Source: user-provided` entries.

expected:
  keywords:
    - Approved Libraries
    - API Patterns
    - Code Examples
    - Documentation Links
    - Source
    - user-provided
    - azure-cosmos
    - pydantic
  graders:
    - type: keyword
      weight: 0.3
      config:
        required:
          - Approved Libraries
          - API Patterns
          - Code Examples
          - Documentation Links
          - "Source:"
          - user-provided
          - azure-cosmos
          - pydantic
          - FastAPI
        forbidden: ["TODO", "placeholder", "TBD"]
    - type: structural
      weight: 0.3
      config:
        required_sections:
          - Approved Libraries
          - Project Templates
          - API Patterns
          - Code Examples
          - Documentation Links
    - type: llm-judge
      weight: 0.4
      config:
        criteria:
          - catalog_entry_format_compliance
          - source_attribution_present
          - user_specified_libraries_included
          - research_breadth

timeout_seconds: 120
tags:
  - design
  - reference-catalog
  - analyst
  - living-catalog
```

### Step 2: Create the scaffold-phase canary spec for catalog consumption

Create `bench/canaries/scaffold/scf-002-catalog-consumption.yaml` with this content:

```yaml
# Canary: Reference Catalog Consumption During Scaffolding
id: scf-002-catalog-consumption
version: "1.0"
phase: scaffold
title: "Reference Catalog Consumption During Scaffolding"
description: >
  Tests that the Scaffolder agent reads the reference catalog before
  generating project structure, uses catalog entries for dependency
  selection, and appends any new discoveries.

prompt: |
  You are the Scaffolder agent. Before scaffolding a FastAPI project called
  "TaskTrackerAPI", you must read the reference catalog at
  `.github/reference-catalog.md`.

  The catalog contains these entries under Approved Libraries:
  - azure-cosmos v4.7.0 (Source: Analyst, Phase 1-2)
  - FastAPI v0.115.0 (Source: Analyst, Phase 1-2)
  - pydantic v2.9.0 (Source: user-provided)

  And under Project Templates:
  - API application template with app/ code root (Source: Analyst, Phase 1-2)

  Scaffold the project structure following the catalog entries. Use the
  approved library versions in pyproject.toml. If you identify a new
  dependency not in the catalog (e.g., uvicorn), append it.

expected:
  keywords:
    - reference-catalog
    - azure-cosmos
    - FastAPI
    - pydantic
    - pyproject.toml
    - Scaffolder
  graders:
    - type: keyword
      weight: 0.3
      config:
        required:
          - reference-catalog
          - azure-cosmos
          - FastAPI
          - pydantic
          - pyproject.toml
          - "4.7.0"
        forbidden: ["TODO", "placeholder"]
    - type: structural
      weight: 0.3
      config:
        required_sections:
          - project structure
          - dependencies
    - type: llm-judge
      weight: 0.4
      config:
        criteria:
          - catalog_entries_used_in_dependencies
          - catalog_referenced_before_scaffolding
          - new_discoveries_appended

timeout_seconds: 120
tags:
  - scaffold
  - reference-catalog
  - consumption
  - living-catalog
```

### Step 3: Validate canary specs

```bash
python tools/validate_canaries.py bench/canaries/
```

Expected: All canaries pass validation (0 errors). If there are errors, fix the YAML structure to match the schema at `schemas/canary-spec.schema.json`.

### Step 4: Update `SDLC-END-TO-END-TEST-SCRIPT.md`

Read `SDLC-END-TO-END-TEST-SCRIPT.md` and make these additions:

**In Step 0 (around line 97-104)**, after the existing checklist items, find:

```markdown
- [ ] **Phase identification** — Harness identifies this as Phase 1-2 and delegates to Analyst
```

Add after it:

```markdown
- [ ] **Catalog template created** — `.github/reference-catalog.md` exists with 5 empty sections (Approved Libraries, Project Templates, API Patterns, Code Examples, Documentation Links)
- [ ] **Catalog review preference asked** — Harness asks "review/auto" and stores `catalog_review` in `harness-config.yml`
```

**In Step 1 (around line 144-169)**, after the existing expected output items, find:

```markdown
- [ ] **SDLC Exit Criteria** — checklist with ✅/⚠️/⛔ statuses
```

Add after it:

```markdown
- [ ] **User asked about libraries** — Analyst asks: "Are there any specific libraries, templates, or frameworks you'd like me to include in the reference catalog?"
- [ ] **Catalog populated** — `.github/reference-catalog.md` has entries under `## Approved Libraries` and `## API Patterns` with correct entry format (Source, Package/Pattern, Purpose, Usage, Links)
- [ ] **Catalog summary reported** — Analyst reports entry counts per section to Harness
```

**Between Step 1 and Step 2**, after the Step 1 result section (around line 181), insert a new section:

```markdown

---

## Step 1b — Post-Analyst Catalog Review Checkpoint (Harness)

### Expected behavior (automatic — no prompt needed):

After the Analyst completes Phase 1-2 and reports catalog population:

- [ ] **Checkpoint triggered** — Harness checks `catalog_review` in `harness-config.yml`
- [ ] **Summary presented** — Harness shows: "Catalog populated: N libraries, N templates, N API patterns, N code examples, N doc links"
- [ ] **User prompted** — Harness asks: "Would you like to review the catalog, request changes, or proceed?"
- [ ] **Proceed accepted** — When user says "proceed", Harness activates append-only mode and continues to ADR creation

### Verification:

```
1. Check .github/reference-catalog.md — should have populated entries (not just empty template)
2. Verify entries have Source attribution (e.g., "Source: Analyst (Phase 1-2)")
3. Verify user-specified libraries are marked "Source: user-provided"
```

### Result: [ ] PASS / [ ] FAIL

**Notes:**
___________________________________________________________________________

```

**In Step 3 (around line 229-260)**, in the expected behavior section, find:

```markdown
- [ ] **Context7 used** — `uv` / Docker docs loaded
```

Add after it:

```markdown
- [ ] **Reference catalog read** — Scaffolder reads `.github/reference-catalog.md` before scaffolding and uses catalog entries for dependencies
```

**In Step 5 (around line 360-365)**, in the expected behavior section, find:

```markdown
- [ ] **Context7 used** — FastAPI + Pydantic docs loaded
```

Add after it:

```markdown
- [ ] **Reference catalog read** — Implementer reads `.github/reference-catalog.md` and uses catalog-approved libraries and patterns
```

**In the Skills Activation table (around line 729-738)**, add a new row:

```markdown
| `sdlc-reference-catalog` | Step 1 (Analyst — population), Steps 3/5 (consumption) | [ ] |
```

### Step 5: Update `tests/e2e-pipeline-test/test-scenario.md`

Read `tests/e2e-pipeline-test/test-scenario.md` and make these additions:

**In Step 0 (around line 36-55)**, add to the expected behavior list:

Find:

```markdown
- [ ] Detects placeholders in `copilot-instructions.md` and asks for project details
- [ ] Fills `<PROJECT_NAME>` → "SmartDoc Analyzer"
```

Add after:

```markdown
- [ ] Creates empty reference catalog template at `.github/reference-catalog.md`
- [ ] Asks catalog review preference (review/auto), stores in `harness-config.yml`
```

Also update the "Validation keywords" section for Step 0. Find:

```markdown
awesome-copilot|GitHub MCP|Context7|PROJECT_NAME|SmartDoc
```

Replace with:

```markdown
awesome-copilot|GitHub MCP|Context7|PROJECT_NAME|SmartDoc|reference-catalog|catalog_review
```

**In Step 1 (around line 72-97)**, add to the expected behavior list:

Find:

```markdown
  - Data model sketch (entities, repositories)
```

Add after:

```markdown
- [ ] Asks user about preferred libraries for the reference catalog
- [ ] Populates `.github/reference-catalog.md` with researched entries (libraries, patterns, templates)
- [ ] Catalog entries include Source attribution and follow the standard entry format
```

Also update the "Validation keywords" section for Step 1. Find:

```markdown
architecture|approved Cosmos DB library|approved Storage library|API application template|Azure OpenAI|AI Search|Cosmos DB|Repository Pattern|RAG|citations
```

Replace with:

```markdown
architecture|approved Cosmos DB library|approved Storage library|API application template|Azure OpenAI|AI Search|Cosmos DB|Repository Pattern|RAG|citations|reference-catalog|Approved Libraries|API Patterns
```

**In the Skill Coverage table (around line 469-481)**, add a new row:

Find the last row of the skill coverage table:

```markdown
| sdlc-qa-bug-checklist | 10 | [ ] |
```

Add after it:

```markdown
| sdlc-reference-catalog | 1, 3, 5 | [ ] |
```

### Step 6: Validate canary specs again (after any edits)

```bash
python tools/validate_canaries.py bench/canaries/
```

Expected: All canaries pass validation (0 errors).

### Step 7: Commit

```bash
git add bench/canaries/design/des-002-catalog-population.yaml bench/canaries/scaffold/scf-002-catalog-consumption.yaml SDLC-END-TO-END-TEST-SCRIPT.md tests/e2e-pipeline-test/test-scenario.md
git commit -m "feat: add catalog canary specs and update E2E test checklists"
```

---

## Task 7: Sync, update AGENTS.md, and push

Sync the plugin directory to the VS Code extension mirror, update the project documentation, and push.

**Files:**
- Modify: `AGENTS.md`
- Sync: `.github/plugin/` → `vscode-extension/`

### Step 1: Sync plugin directory to vscode-extension

```bash
rsync -av --delete .github/plugin/ vscode-extension/ --exclude='.git'
```

### Step 2: Verify sync

```bash
diff -rq .github/plugin/ vscode-extension/ --exclude='.git'
```

Expected: No output (directories are identical).

### Step 3: Update AGENTS.md — Skills Inventory table

Read `AGENTS.md` and find the Skills Inventory table (around line 37-49):

```markdown
### Skills Inventory

| Skill | Purpose |
|-------|---------|
```

Add a new row to the table. Find:

```markdown
| `sdlc-workspace-init` | Workspace initialization (contains prompt assets) |
```

Add after it:

```markdown
| `sdlc-reference-catalog` | Living reference catalog — research, population, consumption, and append-only rules |
```

### Step 4: Update AGENTS.md — Implementation History

Find the Implementation History section (around line 154). In the commits list or history table, add a new entry for the reference catalog work. Find the last entry in the history table (or the section header if adding a new subsection):

```markdown
| — | Docs: align all markdown with MCP gate changes | `9e332da` | Done |
```

Add after it:

```markdown
| — | Living Reference Catalog (skill + agent updates + canaries) | *(current)* | Done |
```

### Step 5: Verify AGENTS.md changes

```bash
grep "sdlc-reference-catalog" AGENTS.md
```

Expected: At least 1 match in the Skills Inventory table.

### Step 6: Commit and push everything

```bash
git add vscode-extension/ AGENTS.md
git commit -m "feat: sync plugin to vscode-extension and update AGENTS.md for reference catalog"
```

Now push all commits:

```bash
unset GITHUB_TOKEN && git push origin evo
```

### Step 7: Verify push

```bash
gh api repos/Dongbumlee/sdlc-harness/commits?sha=evo --jq '.[0] | "\(.sha[0:7]) \(.commit.message | split("\n")[0])"'
```

Expected: The latest commit message should be `feat: sync plugin to vscode-extension and update AGENTS.md for reference catalog`.

---

## Summary of all changes

| File | Action | Task |
|------|--------|------|
| `.github/plugin/skills/sdlc-reference-catalog/SKILL.md` | **Create** | 1 |
| `.github/plugin/skills/sdlc-workspace-init/SKILL.md` | Modify | 2 |
| `.github/plugin/agents/analyst.agent.md` | Modify | 3 |
| `.github/plugin/agents/harness.agent.md` | Modify | 4 |
| `.github/plugin/agents/scaffolder.agent.md` | Modify | 5 |
| `.github/plugin/agents/implementer.agent.md` | Modify | 5 |
| `.github/plugin/agents/deployer.agent.md` | Modify | 5 |
| `.github/plugin/agents/documenter.agent.md` | Modify | 5 |
| `bench/canaries/design/des-002-catalog-population.yaml` | **Create** | 6 |
| `bench/canaries/scaffold/scf-002-catalog-consumption.yaml` | **Create** | 6 |
| `SDLC-END-TO-END-TEST-SCRIPT.md` | Modify | 6 |
| `tests/e2e-pipeline-test/test-scenario.md` | Modify | 6 |
| `vscode-extension/` (mirror sync) | Sync | 7 |
| `AGENTS.md` | Modify | 7 |

**Total commits:** 7 (one per task)
**Total new files:** 3
**Total modified files:** 10
**Total sync operations:** 1
