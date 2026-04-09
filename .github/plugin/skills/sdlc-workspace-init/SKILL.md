---
name: sdlc-workspace-init
description: "Initialize a new repository with SDLC workspace files — copilot-instructions.md, quality instructions, and prompt files. Use when setting up a new project, bootstrapping SDLC, onboarding a repo, or when .github/copilot-instructions.md is missing."
---

# SDLC Workspace Initialization

## When to use

- Setting up a new repository for SDLC-driven development
- After installing the SDLC Agent Template plugin into a repo that has no `.github/copilot-instructions.md`
- When Harness detects missing workspace files during first-run initialization

## What this skill does

Copies workspace-specific files from the skill's `assets/` folder into the target repo's
`.github/` directory. These files cannot be distributed via the plugin system because they
require per-project customization.

## Files deployed

| Source (skill assets) | Target (workspace) | Customized? |
|---|---|---|
| `assets/copilot-instructions.template.md` | `.github/copilot-instructions.md` | Yes — project name, domain, stack |
| `assets/instructions/*.instructions.md` | `.github/instructions/` | No — copied as-is |
| `assets/prompts/*.prompt.md` | `.github/prompts/` | No — copied as-is |

## Procedure

### Step 1: Check if already initialized

Check if `.github/copilot-instructions.md` exists in the workspace.

- **If found** → Report: _"Workspace already initialized. Skipping."_ and stop.
- **If NOT found** → Continue to Step 2.

### Step 2: Gather project information

Ask the user for:
1. **Project name** (required) — e.g., "SmartDoc Analyzer"
2. **Business domain** (required) — e.g., "Intelligent document processing"
3. **Tech stack** (optional, default: "Python 3.12, FastAPI, React 18, TypeScript 5, Vite")

### Step 3: Deploy copilot-instructions.md

1. Read [copilot-instructions.template.md](./assets/copilot-instructions.template.md).
2. Replace these placeholders:
   - `{{PROJECT_NAME}}` → user's project name
   - `{{BUSINESS_DOMAIN}}` → user's business domain
   - `{{TECH_STACK}}` → user's tech stack (or default)
3. Write the result to `.github/copilot-instructions.md`.

### Step 4: Deploy instruction files

Copy each file from `assets/instructions/` to `.github/instructions/`:

- [code-quality-py.instructions.md](./assets/instructions/code-quality-py.instructions.md)
- [code-quality-ts.instructions.md](./assets/instructions/code-quality-ts.instructions.md)
- [code-quality-tsx.instructions.md](./assets/instructions/code-quality-tsx.instructions.md)
- [test-quality.instructions.md](./assets/instructions/test-quality.instructions.md)
- [test-quality-ts.instructions.md](./assets/instructions/test-quality-ts.instructions.md)
- [test-quality-tsx.instructions.md](./assets/instructions/test-quality-tsx.instructions.md)

Only copy instruction files matching the project's language stack:
- Python project → copy `code-quality-py` + `test-quality`
- TypeScript project → copy `code-quality-ts` + `test-quality-ts`
- React project → copy all TypeScript + TSX files
- Full stack → copy all 6 files

### Step 5: Deploy prompt files

Copy each file from `assets/prompts/` to `.github/prompts/`:

- [requirement-and-design.prompt.md](./assets/prompts/requirement-and-design.prompt.md)
- [repo-structure-and-cicd.prompt.md](./assets/prompts/repo-structure-and-cicd.prompt.md)
- [deployment.prompt.md](./assets/prompts/deployment.prompt.md)
- [implementation-and-tests.prompt.md](./assets/prompts/implementation-and-tests.prompt.md)
- [repo-documentation.prompt.md](./assets/prompts/repo-documentation.prompt.md)
- [qa-rai-release.prompt.md](./assets/prompts/qa-rai-release.prompt.md)

### Step 6: Report

```
## SDLC Workspace Initialized

- ✅ `.github/copilot-instructions.md` — customized for "{{PROJECT_NAME}}"
- ✅ `.github/instructions/` — X quality instruction files deployed
- ✅ `.github/prompts/` — 6 SDLC prompt files deployed

**Next steps:**
1. Review `.github/copilot-instructions.md` and adjust if needed.
2. Use `@Harness` to start your first SDLC task.
3. Use `/requirement-and-design` to begin Phase 1-2.
```
