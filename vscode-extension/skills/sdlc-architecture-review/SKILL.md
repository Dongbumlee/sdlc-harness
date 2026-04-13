---
name: sdlc-architecture-review
description: >-
  Review code for architecture and design consistency following SDLC layering rules
  and application project patterns. Use when reviewing PRs, checking dependency
  boundaries, or validating pattern reuse. Triggers on architecture review,
  layering check, design review, or pattern compliance requests.
---

# SDLC Architecture Review

Review code for structural alignment with SDLC architecture rules and application patterns.

## Step 1: Load architecture guidance

Load blueprint generation guidance from awesome-copilot:

```
mcp_awesome-copil_load_instruction(
  filename: "architecture-blueprint-generator/SKILL.md",
  mode: "skills"
)
```

For cross-repo pattern consistency, search via GitHub MCP:

```
mcp_github_search_code(
  q: "RepositoryBase RootEntityBase org:the project's GitHub org",
  per_page: 5
)
```

## Step 2: Verify layering rules

The application project uses a strict layered architecture:

```
┌─────────────────────────────────────────┐
│  API Layer (src/<Name>API/app/)          │ ← HTTP controllers, routers
│    ↓ depends on                         │
│  Application Layer (services/)          │ ← Orchestrates use cases
│    ↓ depends on                         │
│  Domain Layer (Business/src/libs/)      │ ← Models, business rules
│    ↑ depended on by                     │
│  Infrastructure (repositories, storage) │ ← Data access, external APIs
└─────────────────────────────────────────┘
```

**Check each violation:**

| Rule | Violation Example | Fix |
|---|---|---|
| API → Application → Domain | Router imports `CosmosClient` directly | Route through service layer |
| Infrastructure depends on Domain | Entity imports from `routers/` | Move shared types to Business |
| No God services | Service class with 20+ methods | Split by domain area |
| No cross-layer shortcuts | Controller calls repository directly | Add a service method |

## Step 3: Validate project structure

Each layer should be an independent project under `src/`:

| Layer | Project | Code Root | Template |
|---|---|---|---|
| API | `src/<Name>API/` | `app/` | `the API template repo` |
| Business | `src/<Name>Business/` | `src/` | `the base app template repo` |
| Agent | `src/<Name>Agent/` | `src/` | `the agent template repo` |
| Web | `src/<Name>Web/` | `src/` | React + TypeScript |

**Check:**
- API depends on Business (imports domain models, calls services)
- Agent depends on Business (shares models, uses repositories)
- Business is the shared core — NO dependency on API or Agent
- Web calls API via HTTP — no direct dependency on Python layers

## Step 4: Pattern reuse check

Before new code introduces a new pattern, verify:

1. Does a similar pattern already exist in this repo? Search for it.
2. Does the reference catalog (`.github/reference-catalog.md`) prescribe a pattern?
3. Do other application repos use a different approach? Check via GitHub MCP.

**Prefer extending existing patterns over inventing new ones.**

## Step 5: Template alignment

Verify the project follows the correct scaffolding template:

- API template uses `app/` as code root (NOT `src/`)
- Base app and agent template use `src/` as code root (NOT `app/`)
- Tests are at `tests/` in the project root (NOT inside `app/` or `src/`)
- `pyproject.toml` uses `[project]` format (NOT `[tool.poetry]`)
- `Dockerfile` uses `uv sync --frozen` (NOT `pip install`)

## Output format

Return findings as:
- **Critical**: Layering violations, architectural shortcuts
- **Important**: Pattern deviations, inconsistencies with other applications
- **Suggestion**: Minor structural improvements
- **Positive**: Architecture aspects done well
