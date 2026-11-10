---
name: sdlc-project-manifest
description: >-
  Generate and read the project manifest that records which templates and patterns
  were chosen during scaffolding. This manifest is the single source of truth for
  ALL agents — the Harness creates its skeleton at intake, the Scaffolder
  completes it during Phase 3, and every other agent reads it before working.
  Triggers on any scaffolding, implementation, review, or documentation task.
  Ensures cross-agent consistency for template patterns across the entire SDLC lifecycle.
version: "1.0"
author: sdlc-harness
user-invocable: false
---

# SDLC Project Manifest — Cross-Agent Pattern Persistence

## What is the project manifest?

The file `.SDLC/project-manifest.md` is created by the **Harness** at intake
(skeleton: run basis, provisional Task Grade, empty ledger), completed by the
**Scaffolder** during Phase 3, and maintained by the Harness at every phase
transition (base definitions §8.1). No other agent creates it.
It records which templates were chosen and the exact code patterns that ALL agents must follow.
This ensures the Implementer, QA Reviewers, Deployer, and Documenter all work consistently
with the same patterns the Scaffolder established.

## For the SCAFFOLDER (write mode)

After scaffolding, complete the body of the `.SDLC/project-manifest.md` the
Harness created at intake, using this exact format and preserving the Task
Grade section and the ledger's existing rows.
The worked example below is one project's manifest (a Python/Azure
multi-project build): the **section structure** is the format — the values
(patterns, libraries, base images, route shapes) are that project's.
Record your own project's values from its stack profile and templates;
never copy the example's stack values into a different stack's manifest:

```markdown
# Project Manifest — <ProjectName>

> Skeleton created by the Harness at intake; body completed by the Scaffolder (Phase 3). All agents MUST follow these patterns.
> Last updated: YYYY-MM-DD

## Projects

| Project Folder | Template Used | Code Root | Language |
|---|---|---|---|
| src/<Name>API/ | the API template repo | app/ | python (Python 3.12) |
| src/<Name>Business/ | the base app template repo | src/ | python (Python 3.12) |
| src/<Name>Web/ | React + TypeScript | src/ | typescript |

The **Language** column records the project's **stack profile id** (from the
`sdlc-stack-profiles` skill: `python`, `typescript`, `dotnet`, …) plus the
runtime version. Downstream agents resolve every stack-specific command,
layout, and pattern from that profile — a .NET project records `dotnet`,
and its build/test/CI commands come from the dotnet profile, never from
python defaults.

## Template Patterns (fetched from the project's GitHub org repos)

### API Project: <Name>API

**Template:** `the project's API template (from copilot-instructions.md)`

**Entry point pattern:**
- `app/main.py` uses `Application()` factory (from `application.py`)
- `Application` extends `Application_Base` from `app/libs/base/`
- NEVER use bare `app = FastAPI()`

**DI container pattern:**
- Register services: `self.application_context.add_singleton(IService, Implementation)`
- Resolve in routers via `TypedFastAPI` app context
- Use Protocol interfaces in `app/services/interfaces.py`

**Framework directories:**
- `app/libs/base/` — Application_Base, TypedFastAPI
- `app/libs/application/` — AppContext, Configuration
- `app/libs/azure/` — Azure App Configuration helpers

**Router pattern:**
- Routers in `app/routers/` — one file per domain area
- Health probes in `app/routers/http_probes.py`
- Routers registered in `Application._config_routers()`

**Service pattern:**
- Interfaces: `app/services/interfaces.py` (Protocol classes)
- Implementations: `app/services/<name>_service.py`
- Registered via DI in `Application._register_dependencies()`

**Data access pattern:**
- Entities: `RootEntityBase["EntityName", KeyType]` (from `the approved Cosmos DB library`)
- Repositories: `RepositoryBase[Entity, KeyType]` (from `the approved Cosmos DB library`)
- Location: `app/domain/` or `app/business_component/`

**Dockerfile pattern:**
- Base: `mcr.microsoft.com/azurelinux/base/python:3.12`
- UV: `COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/`
- Install: `uv sync --frozen --no-cache`
- Run: `.venv/bin/uvicorn app.main:app --port 80 --host 0.0.0.0 --workers 4`

**Dependencies pattern:**
- `pyproject.toml` uses `[dependency-groups] dev` (not optional-dependencies)
- `[tool.pytest.ini_options]` with `pythonpath = ["."]`

### Business Project: <Name>Business

**Template:** `the project's app template (from copilot-instructions.md)`
[Fill with patterns from that template]

### Web Project: <Name>Web

**Template:** React + TypeScript
[Fill with patterns]

## Azure SDK Libraries

| Library | Package | Used For | Pattern |
|---|---|---|---|
| the approved Cosmos DB library | `the approved Cosmos DB library` | Cosmos DB | `RootEntityBase` + `RepositoryBase` |
| the approved Storage library | `the approved Storage library` | Blob/Queue | `AsyncStorageBlobHelper` with `async with` |

## Naming Conventions

- Project folders: `<ProjectName><Layer>` (e.g., CustomerFeedbackAPI)
- Async methods: suffix with `Async`
- Test files: `test_<module_name>.py` mirroring source structure
- API routes: `/api/v1/<resource>`

## Task Grade

- Provisional grade (intake, size axis only): <Small | Medium | Large | ungraded> — basis: <counts per signal, or "not countable from the task statement">
- Size signals (verified by the Analyst from the approved spec): functional units <n>, components <n>, external integrations <n>
- Complexity signals (fixed by the Analyst at design): <the strong signals found, citing requirement lines; or "none">
- Sensitivity correction: <+1 — personal/payment/health data | none>
- **Final grade: <Small | Medium | Large>** — basis: <one line>, set by <Harness at intake | Analyst at design | user override>, <date>

## Phase-State Ledger

**Run basis** — Task: <one line naming the task> (user instruction, <date>).
Approved artifacts:
- <path> — approved by <approver>, <date>, sha256:<first 12 characters>

| Phase | Status | Artifacts | Updated | Notes |
|---|---|---|---|---|
| 0 Workspace Init | Pending | — | — | |
| 1 Requirements | Pending | — | — | |
| 2 Design | Pending | — | — | |
| 3 Scaffold | Pending | — | — | |
| 4 Implementation | Pending | — | — | |
| 5 Documentation | Pending | — | — | |
| 6 QA | Pending | — | — | |
| 7 RAI | Pending | — | — | |
| 8-9 Release | Pending | — | — | |
```

**The Task Grade section** is created by the Harness in the intake
skeleton (provisional, size axis only), verified by the Analyst against
the approved spec (Phase 1B counts; Phase 2 complexity and the final
grade), and preserved by the Scaffolder when it generates the full
manifest. Reviewer counts and round caps read the final grade.

**The Phase-State Ledger** is maintained by the **Harness** directly
at every phase transition — mechanical record upkeep is the Harness's
own work, never a Documenter delegation: Status (`Pending` / `In Progress` /
`Complete`, plus `Blocked` and `N/A` — N/A always carries its reason in
Notes; base definitions §2.2), the artifact paths the phase produced, and
the date. It is the
single source of truth for run state — an interrupted run resumes from it
(Harness Step 0.5), and the Release Manager refuses to release while a phase
the ledger covers is not Complete or N/A-with-reason. The **Run basis** block above the table is
maintained on a different rhythm: the task line is written when the manifest
skeleton is created, and an approved-artifact line is added or updated **when
an approval lands**, with the artifact's short hash (`sha256sum`, first 12
characters) recorded at that moment. Step 0.5 recomputes those hashes before
resuming; a mismatch means the approved artifact changed after approval and
the run stops for the user instead of continuing on a stale approval. For feature work on an existing project,
add one ledger row-set (or a dated section) per task so the state of each
feature stays visible.

**CRITICAL: Read the actual template files from the resolved template source when generating this manifest** — the bundled template assets in this plugin when the provenance is a bundled template, or the organization's template repository (via GitHub MCP) when an org template was resolved.
Do NOT invent patterns — read and record what the templates actually contain.

## For ALL OTHER AGENTS (read mode)

**Before doing any work, read `.SDLC/project-manifest.md` if it exists.**

This tells you:
- Which template each project uses → follow its patterns exactly
- What DI pattern to use → `Application_Base` + `add_singleton` or plain FastAPI
- Where files go → code root, test location, service location
- What Dockerfile pattern → base image, uv installation, CMD
- What SDK patterns → `RootEntityBase`, `AsyncStorageBlobHelper`

### For the IMPLEMENTER

1. Read `.SDLC/project-manifest.md` FIRST.
2. Check which project you're working in → find its template section.
3. Follow the exact pattern listed — entry point, DI, services, data access.
4. When adding a new service: use the Protocol interface pattern from the manifest.
5. When adding a new entity: use the data access pattern from the manifest.

### For QA REVIEWERS

1. Read `.SDLC/project-manifest.md` FIRST.
2. Verify code matches the patterns recorded in the manifest.
3. Flag any deviation at finding level `high` (synthesis term: **Important**):
   - "Code uses bare `FastAPI()` but manifest specifies `Application_Base` pattern"
   - "Service registered directly but manifest requires Protocol interface"

### For the DEPLOYER

1. Read `.SDLC/project-manifest.md` to know which projects exist and their Dockerfile patterns.
2. Use the recorded Dockerfile pattern for `azure.yaml` service mappings.

### For the DOCUMENTER

1. Read `.SDLC/project-manifest.md` to understand the architecture.
2. Reference the correct template names and patterns in ADRs and API docs.

## If the manifest doesn't exist

Only the Harness creates a manifest (base definitions §8.1). If
`.SDLC/project-manifest.md` doesn't exist yet (e.g., working on an existing
project that predates this skill):

1. Report the missing manifest to the Harness — do NOT generate one yourself.
2. Proceed with the task without manifest pattern guidance, and note the gap
   in your output.

At the next intake, the Harness creates the skeleton from what exists on
disk, which restores pattern guidance without a reader inventing a record.
