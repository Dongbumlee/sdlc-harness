# Living Reference Catalog Design

## Goal

Transform `.github/reference-catalog.md` from a static, pre-populated file into a living document that agents populate during the design phase, with an optional user review checkpoint and full self-driving mode.

## Background

The SDLC Harness orchestrates 18 specialized AI agents across 9 phases. Currently, `.github/reference-catalog.md` is a static fallback file used when GitHub MCP isn't available. This means every downstream agent — Scaffolder, Implementer, Deployer, Documenter, and 8 QA Reviewers — either discovers libraries and patterns independently or relies on stale pre-populated content.

A living catalog solves three problems:

1. **Duplication** — agents independently research the same libraries, wasting tokens and risking inconsistency
2. **Drift** — the static catalog falls out of date as projects evolve
3. **Discoverability** — agents that find useful patterns during their phase have no mechanism to share discoveries with later agents

## Approach

**Skill-Driven (Approach B)** — create one new skill (`sdlc-reference-catalog`) that codifies the research and population process. The skill is the single source of truth for how all agents interact with the catalog.

This was chosen over the instruction-only approach (editing agent files directly) because:

- The catalog is central enough to the pipeline that its rules should be codified in one place, not scattered across 10+ agent files
- A skill can be activated by multiple agents with consistent behavior
- Research methodology becomes a single maintainable artifact
- Matches the existing skill pattern (the project already has 10+ skills)

## Architecture

```
Step 0 (Init)                    Phase 1-2 (Design)              Phase 3+ (Downstream)
┌──────────────────┐            ┌──────────────────┐            ┌──────────────────┐
│  workspace-init   │            │     Analyst       │            │   Scaffolder     │
│                   │            │                   │            │   Implementer    │
│ • Create empty    │───────────▶│ • Activate skill  │───────────▶│   Deployer       │
│   catalog template│            │ • Research sources│            │   Documenter     │
│ • Ask review pref │            │ • Populate catalog│            │                  │
└──────────────────┘            └────────┬──────────┘            │ • Read catalog   │
                                         │                       │ • Append if new  │
                                         ▼                       └──────────────────┘
                                ┌──────────────────┐
                                │  Harness (review) │
                                │                   │
                                │ • Check config    │
                                │ • Present summary │
                                │ • Await approval  │
                                └──────────────────┘

                    ┌─────────────────────────────────┐
                    │  sdlc-reference-catalog (skill)  │
                    │                                   │
                    │  Single source of truth for:      │
                    │  • Research methodology            │
                    │  • Population rules                │
                    │  • Consumption rules               │
                    │  • Append-only rules               │
                    │  • Review checkpoint behavior      │
                    └─────────────────────────────────┘
```

## Components

### 1. Reference Catalog Template

The empty template is created by `sdlc-workspace-init` during Step 0 initialization. It has 5 fixed top-level sections with placeholder guidance. The Analyst fills these during Phase 1-2; downstream agents can append.

```markdown
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

**Entry format** (used by any agent when appending):

```markdown
### [Entry Name]
- **Source:** [agent-name] (Phase [N])
- **Package/Pattern:** [name@version or pattern name]
- **Purpose:** [what it's for]
- **Usage:** [code example or description]
- **Links:** [documentation URLs]
```

Fixed top-level sections give downstream agents predictable anchors to scan by heading. Flexible sub-sections let the Analyst adapt to the project domain (e.g., `### Device SDK Patterns` under `## API Patterns` for an IoT project).

### 2. New Skill — `sdlc-reference-catalog`

Lives at `.github/plugin/skills/sdlc-reference-catalog/SKILL.md`. Single source of truth for catalog interaction across all agents.

The skill codifies five areas:

**Research methodology** — where to look and in what priority order:

1. User-specified libraries/templates (from the init question)
2. GitHub MCP (org reference repos, when available)
3. Context7 (official documentation for chosen tech stack)
4. awesome-copilot (best practice patterns)
5. Web research (community patterns, comparison articles)

**Population rules** — how the Analyst writes entries:

- Use the fixed top-level headings (`## Approved Libraries`, etc.)
- Add sub-sections freely under each heading as needed
- Every entry must include: source agent, package/version, purpose, usage example, links
- Mark user-specified libraries as `Source: user-provided`

**Consumption rules** — how downstream agents read the catalog:

- Read `.github/reference-catalog.md` before starting any phase work
- Prefer catalog entries over independent research
- If a needed pattern isn't in the catalog, do the work and append the discovery

**Append-only rules** — how downstream agents add entries:

- Add new entries under the appropriate top-level section
- Include `Source: [agent-name] (Phase [N])` to distinguish from Analyst entries
- Never modify or remove existing entries

**Review checkpoint behavior** — what happens after population:

- Check `catalog_review` setting in `harness-config.yml`
- If `true` (or unset): Harness presents catalog summary to user, asks for approval/modifications
- If `false`: Harness proceeds automatically, logs that catalog was populated

**Activating agents:**

| Agent | Mode | Phase |
|-------|------|-------|
| Analyst | Population | Phase 1-2 |
| Scaffolder | Consumption | Phase 3 |
| Implementer | Consumption | Phase 5 |
| Deployer | Consumption | Phase 7 |
| Documenter | Consumption | Phase 8 |
| QA Reviewers (×8) | Reference (optional) | Varies |

### 3. Agent Modifications

**3a. Analyst agent** (`analyst.agent.md`):

- After producing the design proposal, activate the `sdlc-reference-catalog` skill
- Research libraries, templates, and patterns using the priority order defined in the skill
- Ask the user: "Are there any specific libraries, templates, or frameworks you'd like me to include?"
- Populate `.github/reference-catalog.md` with findings plus user-specified entries
- Catalog population is a natural output of the research the Analyst already does — no new phase, just structured output

**3b. Harness agent** (`harness.agent.md`):

- **Step 0 addition:** Ask "Would you like to review the reference catalog before development begins, or proceed automatically? (review/auto) [default: review]" — store in `harness-config.yml` as `catalog_review: true|false`
- **Post-Analyst checkpoint:** After the Analyst completes Phase 1-2, check `catalog_review`. If `true`, present catalog summary and ask for approval. If `false`, log and continue.

**3c. Downstream agents** (Scaffolder, Implementer, Deployer, Documenter):

- Each gets a consumption instruction: "Before starting work, read `.github/reference-catalog.md` and activate the `sdlc-reference-catalog` skill. Use catalog entries as primary reference. If you discover a new pattern not in the catalog, append it."

**3d. QA Reviewers** (all 8):

- No mandatory changes. Optional reference for compliance checking (e.g., verifying that implemented libraries match catalog-approved ones). Not a new gate.

### 4. Workspace Init & Config Changes

**4a. `sdlc-workspace-init` skill update:**

- Create the empty catalog template during Step 0, alongside `copilot-instructions.md` generation
- Add the catalog review preference question after existing project questions

**4b. `harness-config.yml` schema update:**

- New field: `catalog_review: true` (default: `true` if unset)

## Data Flow

### User Experience Flow

**Step 0 — Initialization:**
User sends first message → Harness does normal init → creates empty catalog template → asks review preference → stores in config → delegates to Analyst.

**Phase 1-2 — Design:**
Analyst does design work → asks user about preferred libraries → researches all sources in priority order → populates catalog → returns to Harness.

**Review Checkpoint:**
If `catalog_review: true` — Harness presents summary (N entries across 5 sections, bulleted) → user can review, edit, or proceed.
If `catalog_review: false` — Harness logs that catalog was populated and auto-proceeds.

**Phase 3+ — Downstream:**
Agents silently consume catalog. If they discover new patterns, they append with their agent name and phase number. The user sees normal agent output, not catalog-append notifications.

## Files Affected

| File | Change |
|------|--------|
| `.github/plugin/skills/sdlc-reference-catalog/SKILL.md` | **New file** — the skill from Section 2 |
| `.github/plugin/skills/sdlc-workspace-init/SKILL.md` | Add catalog template creation + review preference question |
| `.github/plugin/agents/harness.agent.md` | Add review checkpoint logic + `catalog_review` config handling |
| `.github/plugin/agents/analyst.agent.md` | Add catalog population responsibility + user library question |
| `.github/plugin/agents/scaffolder.agent.md` | Add catalog consumption instruction |
| `.github/plugin/agents/implementer.agent.md` | Add catalog consumption instruction |
| `.github/plugin/agents/deployer.agent.md` | Add catalog consumption instruction |
| `.github/plugin/agents/documenter.agent.md` | Add catalog consumption instruction |
| `.github/reference-catalog.md` | Replaced by empty template (created by workspace-init at runtime) |

> **Sync note:** `.github/plugin/` files auto-sync to `vscode-extension/` via the existing sync workflow. `.github/reference-catalog.md` is project-level and does not need syncing.

## Error Handling

- **Missing catalog file:** If `.github/reference-catalog.md` doesn't exist when a downstream agent tries to read it (e.g., workspace-init was skipped), the agent proceeds without catalog guidance and logs a warning. No hard failure.
- **Empty catalog:** If the Analyst fails to populate the catalog (e.g., no relevant libraries found), the template remains with placeholder comments. Downstream agents treat missing entries as "not yet researched" and do their own research, appending discoveries.
- **Merge conflicts in catalog:** Since entries are append-only and each agent writes to distinct sub-sections, conflicts are unlikely. If they occur, the later agent's entry wins (append at bottom).
- **Review mode interruption:** If the user dismisses the review checkpoint without explicit approval, the Harness treats it as approved and proceeds (fail-open, not fail-closed).

## Testing Strategy

### Canary Spec Updates

- `phase-1-analysis.canary.yaml` — verify the Analyst populates the catalog with entries under `## Approved Libraries` and `## API Patterns`
- `phase-3-scaffolding.canary.yaml` — verify the Scaffolder reads the catalog before generating project structure

### E2E Test Script Updates (`SDLC-END-TO-END-TEST-SCRIPT.md`)

- **Step 0:** Catalog template created, review preference question asked
- **Step 1 (Analyst):** User asked about preferred libraries, catalog populated, entries have correct format
- **Post-Step 1 checkpoint:** Harness presents catalog summary (review mode), user can approve/edit/proceed
- **Step 3 (Scaffolder):** Verify references catalog entries
- **Step 5 (Implementer):** Verify uses catalog-approved libraries

### Test Scenario Updates (`tests/e2e-pipeline-test/test-scenario.md`)

- Step 0 validation keywords include catalog template
- Step 1 expected behaviors include catalog population
- New validation checkpoint between Step 1 and Step 3

## Open Questions

None — all design decisions have been validated.