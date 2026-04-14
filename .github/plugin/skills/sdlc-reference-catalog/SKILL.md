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

## Entry format

Every entry appended by any agent must use this format:

```
### [Entry Name]
- **Source:** [agent-name] (Phase [N])
- **Package/Pattern:** [name@version or pattern name]
- **Purpose:** [what it's for]
- **Usage:** [code example or description]
- **Links:** [documentation URLs]
- **Research Notes:** [optional — note if any research source was unavailable, e.g., "GitHub MCP unavailable — verified via web research only"]
```

Mark user-specified entries as `Source: user-provided`.

## Research methodology (Analyst only)

When populating the catalog, research sources in this priority order:

1. **User-specified libraries/templates** — ask the user: "Are there any specific libraries, templates, or frameworks you'd like me to include in the reference catalog?" Mark these as `Source: user-provided`.
2. **GitHub MCP** — fetch patterns from org reference repos (when available). Use `mcp_github_get_file_contents` to read README files and example code from template repos referenced in `copilot-instructions.md`.
3. **Context7 MCP** — load official documentation for the chosen tech stack. Use `mcp_context7_resolve-library-id` and `mcp_context7_get-library-docs` for framework docs.
4. **awesome-copilot MCP** — load best practice patterns. Use `mcp_awesome-copil_search_instructions` to find relevant instructions for the project's tech stack.
5. **Web research** — community patterns, comparison articles, and ecosystem guidance for libraries not covered by the above sources.

For each source that is unavailable (MCP not running, auth failure), skip it gracefully and use the `Research Notes` field in the catalog entry to record which source was unavailable (e.g., `Research Notes: GitHub MCP unavailable — verified via web research only`).

## Population rules (Analyst only)

- Use the 5 fixed top-level headings (`## Approved Libraries`, `## Project Templates`, `## API Patterns`, `## Code Examples`, `## Documentation Links`).
- Add sub-sections freely under each heading as needed for the project domain (e.g., `### Device SDK Patterns` under `## API Patterns` for an IoT project).
- Every entry must include: source agent, package/version, purpose, usage example, and links; and optionally research notes (when a research source was unavailable).
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
