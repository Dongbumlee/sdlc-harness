---
name: sdlc-workspace-init
description: "Initialize a new repository with SDLC workspace files — MCP config, copilot-instructions.md, quality instructions, and prompt files. Use when setting up a new project, bootstrapping SDLC, onboarding a repo, or when Harness detects missing workspace files."
---

# SDLC Workspace Initialization

## When to use

- Setting up a new repository for SDLC-driven development
- After installing the SDLC Agent Template plugin into a repo that has no `.github/copilot-instructions.md`
- When Harness detects missing workspace files during first-run initialization

## What this skill does

Copies workspace-specific files from the skill's `assets/` folder into the target repo's
`.github/` and `.vscode/` directories. These files cannot be distributed via the plugin
system because they require per-project customization or live outside `.github/plugin/`.

> **This skill is the ONLY place that deploys `.vscode/mcp.json`.**
> No other agent or skill should deploy mcp.json to avoid duplicate writes.

## Files deployed

| Source (skill assets) | Target (workspace) | Customized? |
|---|---|---|
| `assets/mcp.template.json` | `.vscode/mcp.json` | No — copied as-is (MCP server definitions) |
| `assets/copilot-instructions.template.md` | `.github/copilot-instructions.md` | Yes — project name, domain, stack |
| `assets/instructions/*.instructions.md` | `.github/instructions/` | No — copied as-is |
| `assets/prompts/*.prompt.md` | `.github/prompts/` | No — copied as-is |
| *(generated at runtime)* | `.github/reference-catalog.md` | Yes — empty template with 5 fixed sections |

## Procedure

### Step 1: Check workspace state

Check what already exists in the workspace:

- `.vscode/mcp.json` — MCP server config
- `.github/copilot-instructions.md` — project-specific Copilot instructions
- `.github/instructions/` — quality instruction files (check if directory has files, not just exists)
- `.github/prompts/` — SDLC prompt files (check if directory has files, not just exists)

If ALL four are present and populated → Report: _"Workspace already initialized. Skipping."_ and stop.
If any are missing or empty → continue and deploy **only the missing pieces**.

### Step 2: Create directory structure

**Before writing any files**, create the required directories using the terminal.
These directories may not exist in a fresh workspace:

```bash
mkdir -p .github/instructions .github/prompts .vscode
```

**This step is mandatory** — do NOT skip it. File writes will fail silently in
directories that don't exist.

### Step 3: Deploy MCP server configuration

> **This is the ONLY place mcp.json should be deployed.** Do NOT deploy it anywhere else.
> **CRITICAL: Use the terminal to write this file — do NOT use create/edit tools.**
> LLM file tools sometimes append instead of overwrite, producing invalid JSON.

1. Check if `.vscode/mcp.json` exists in the workspace.
2. **If NOT found** → deploy using the terminal:
   a. Read [mcp.template.json](./assets/mcp.template.json) to get the content.
   b. **Delete any partial file** and write fresh using the terminal:
      ```bash
      rm -f .vscode/mcp.json
      ```
      Then write the content using a heredoc redirect (which ALWAYS overwrites):
      ```bash
      cat > .vscode/mcp.json << 'MCPEOF'
      <paste the exact content of mcp.template.json here>
      MCPEOF
      ```
   c. **Validate the file is valid JSON:**
      ```bash
      python3 -c "import json; json.load(open('.vscode/mcp.json')); print('✅ mcp.json is valid JSON')"
      ```
      If validation fails → `rm -f .vscode/mcp.json` and retry from step (b) once.
3. **If found** → validate it anyway:
   ```bash
   python3 -c "import json; json.load(open('.vscode/mcp.json')); print('✅ mcp.json is valid JSON')"
   ```
   If valid → Skip. Report: _"Existing `.vscode/mcp.json` found — keeping current config."_
   If invalid → `rm -f .vscode/mcp.json` and deploy fresh from step (b).

After deploying (or confirming it exists), tell the user:
> ✅ `.vscode/mcp.json` — 7 MCP server definitions ready.
> Please start all MCP servers: open `.vscode/mcp.json` and click **"Start"** on each.

### Step 4: Gather project information

Ask the user for:
1. **Project name** (required) — e.g., "SmartDoc Analyzer"
2. **Business domain** (required) — e.g., "Intelligent document processing"
3. **Tech stack** (required) — e.g., "Python, FastAPI, React, TypeScript"
4. **Primary language(s)** (derived from tech stack) — used to filter instruction files and reference catalog

### Step 5: Deploy copilot-instructions.md

1. Read [copilot-instructions.template.md](./assets/copilot-instructions.template.md).
2. Replace these placeholders:
   - `{{PROJECT_NAME}}` → user's project name
   - `{{BUSINESS_DOMAIN}}` → user's business domain
   - `{{TECH_STACK}}` → user's tech stack
3. Write the result to `.github/copilot-instructions.md`.

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

### Step 7: Deploy instruction files

Copy each file from `assets/instructions/` to `.github/instructions/`:

- [code-quality-py.instructions.md](./assets/instructions/code-quality-py.instructions.md)
- [code-quality-ts.instructions.md](./assets/instructions/code-quality-ts.instructions.md)
- [code-quality-tsx.instructions.md](./assets/instructions/code-quality-tsx.instructions.md)
- [code-quality-java.instructions.md](./assets/instructions/code-quality-java.instructions.md)
- [code-quality-csharp.instructions.md](./assets/instructions/code-quality-csharp.instructions.md)
- [code-quality-go.instructions.md](./assets/instructions/code-quality-go.instructions.md)
- [code-quality-rust.instructions.md](./assets/instructions/code-quality-rust.instructions.md)
- [test-quality.instructions.md](./assets/instructions/test-quality.instructions.md)
- [test-quality-ts.instructions.md](./assets/instructions/test-quality-ts.instructions.md)
- [test-quality-tsx.instructions.md](./assets/instructions/test-quality-tsx.instructions.md)
- [test-quality-java.instructions.md](./assets/instructions/test-quality-java.instructions.md)
- [test-quality-csharp.instructions.md](./assets/instructions/test-quality-csharp.instructions.md)
- [test-quality-go.instructions.md](./assets/instructions/test-quality-go.instructions.md)
- [test-quality-rust.instructions.md](./assets/instructions/test-quality-rust.instructions.md)

Only copy instruction files matching the project's language stack:
- Python project → copy `code-quality-py` + `test-quality`
- TypeScript project → copy `code-quality-ts` + `test-quality-ts`
- React project → copy all TypeScript + TSX files
- Java project → copy `code-quality-java` + `test-quality-java`
- C# project → copy `code-quality-csharp` + `test-quality-csharp`
- Go project → copy `code-quality-go` + `test-quality-go`
- Rust project → copy `code-quality-rust` + `test-quality-rust`
- Full stack → copy all applicable files

### Step 8: Deploy prompt files

Copy each file from `assets/prompts/` to `.github/prompts/`:

- [requirement-and-design.prompt.md](./assets/prompts/requirement-and-design.prompt.md)
- [repo-structure-and-cicd.prompt.md](./assets/prompts/repo-structure-and-cicd.prompt.md)
- [deployment.prompt.md](./assets/prompts/deployment.prompt.md)
- [implementation-and-tests.prompt.md](./assets/prompts/implementation-and-tests.prompt.md)
- [repo-documentation.prompt.md](./assets/prompts/repo-documentation.prompt.md)
- [qa-rai-release.prompt.md](./assets/prompts/qa-rai-release.prompt.md)

### Step 9: Report

```
## ✅ SDLC Workspace Initialized

- ✅ `.vscode/mcp.json` — 7 MCP server definitions deployed
- ✅ `.github/copilot-instructions.md` — customized for "{{PROJECT_NAME}}"
- ✅ `.github/instructions/` — X quality instruction files deployed
- ✅ `.github/prompts/` — 6 SDLC prompt files deployed
- ✅ `.github/reference-catalog.md` — empty catalog template created (Analyst will populate during Phase 1-2)

**Next steps:**
1. **Start MCP servers** — open `.vscode/mcp.json` and click "Start" on each server.
   All 7 servers are required.
2. Review `.github/copilot-instructions.md` and adjust if needed.
3. Use `@Harness` to start your first SDLC task.
4. Use `/requirement-and-design` to begin Phase 1-2.
```
