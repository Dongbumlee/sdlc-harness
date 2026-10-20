---
name: sdlc-stack-profiles
description: >-
  Per-stack profiles that declare everything language-specific in the harness —
  project files, layout, package manager, build/test/lint commands, Dockerfile
  and CI patterns — so the SDLC process itself stays stack-neutral. Use when
  scaffolding, implementing, testing, or reviewing a project in any supported
  stack (python, typescript, dotnet), or when an organization adopts the
  harness with its own stack standards.
version: "1.0"
author: sdlc-harness
user-invocable: false
---

# SDLC Stack Profiles

The harness process (phases, requirements, ADRs, manifest, reviews) is
**stack-neutral**. Everything that is NOT neutral — project file names,
folder layout inside a project, package manager, build/test/lint commands,
Dockerfile base images, CI steps — is declared in exactly one place: the
project's **stack profile** in this skill.

**Rule: no agent hardcodes a stack-specific command or layout from memory.**
Before scaffolding, running tests, or verifying a build, resolve the
project's profile and use its declared values.

## Resolving a project's stack

In order:

1. An explicit instruction from the user or the organization for this project.
2. The stack declared in `.github/copilot-instructions.md`.
3. For an existing project, the **Stack** recorded in that project's row of
   `.SDLC/project-manifest.md`.
4. Defaults when nothing declares a stack: API / business / agent projects
   use the **python** profile; web frontends use the **typescript** profile.

The Scaffolder records the resolved stack in the manifest's Projects table.
Every later phase reads it from there.

## Adopting an organization's standard

A profile's pinned values (runtime version, base images, approved libraries,
CI system) are the organization's standard in executable form. An organization
adopts the harness by overriding those values in its own copy of the profile —
the process, gates, and artifact contracts do not change. This is deliberate:
engineers who know the standard can work in any project that follows it,
regardless of stack.

## Profile format

Every profile declares the same fields:

| Field | Meaning |
|---|---|
| Project files | The files that define a project in this stack |
| Layout | Folder structure inside `src/<ProjectName><Layer>/` |
| Package manager | Tool + lock file + install/restore command |
| Build | Exact build command |
| Test | Exact test command (+ coverage variant) |
| Lint / format | Exact check commands |
| Dockerfile | Base images and multi-stage outline |
| CI steps | Build-stage commands for the CI stub — GitHub Actions (`.github/workflows/ci.yml`) by default; ADO `azure_cicd.yaml` where the organization declares Azure DevOps |
| Devcontainer | Image |
| Template source | Org template repo (from copilot-instructions) if any; otherwise the bundled default template (below); the profile layout is the last-resort fallback |

---

## Bundled default templates

Every profile ships a **bundled default template** in this skill's assets:
`assets/templates/<profile>/<kind>/` (python/api, dotnet/api,
typescript/web). A template is the profile expressed as files: project
files, layout, Dockerfile, CI stub, devcontainer, a health endpoint, one
sample vertical slice (an `items` resource), and tests that prove the
wiring. Template resolution mirrors profile resolution:

1. An explicit instruction from the user or the organization.
2. The organization template repo named in `.github/copilot-instructions.md`
   (fetched via GitHub MCP).
3. **The bundled default template** for the resolved profile.
4. This profile's prose layout, as the last-resort fallback.

**Instantiation contract** (performed by the Scaffolder): copy the template
tree to the repository root; substitute the tokens declared in its
`template.yaml` in file names and contents (`{{ProjectName}}` — PascalCase
base name; `{{project-name}}` — the kebab-case name derived from it;
`{{Year}}` — the current four-digit year, written into the `LICENSE`
copyright line); delete
`template.yaml`; generate lock files with the profile's install command
(lock files are never templated); then run the template's `verify` steps —
the profile's install, build, and test commands. The scaffold is not
complete until verification passes or an environment limitation is reported
per the harness's environment-failure rule.

**License:** every bundled template ships an MIT `LICENSE` at its root
(ADR-0003). An organization template or an explicit user decision overrides
the license text; the Scaffolder records the license actually shipped next
to the template provenance in the manifest. Never ship a project without a
`LICENSE` file because a checklist mentioned one — the file comes from the
template.

**Provenance:** the Scaffolder records the template source in the project's
manifest row: `bundled <profile>/<kind>@<harness version>`,
`org <repo>@<ref>`, or `prose fallback`. Deviations from the template are
recorded in the manifest with reasons, like any pattern deviation.

**Template content is copied verbatim** — including its sample slice and
tests. They are the template's golden-path fixture, not Phase 3 output: the
Implementer replaces or extends the sample slice in Phase 4. The
Scaffolder's no-business-logic rule governs what it creates *beyond* the
resolved template.

If a bundled template and its profile ever disagree, that is a harness
defect: follow the profile (the declared standard) and report the mismatch.

## Profile: python

- **Project files:** `pyproject.toml` (`[project]` format), `uv.lock`, `.python-version`
- **Layout:** per the `sdlc-project-scaffolding` skill — API projects use
  `app/` as code root (Application factory + `libs/` + Protocol services);
  business/agent projects use `src/` as code root; tests in `tests/` at the
  project root.
- **Package manager:** `uv` — install/restore: `uv sync --frozen`. Never pip
  or poetry unless the user explicitly requests it.
- **Build:** `uv sync --frozen` (no separate compile step)
- **Test:** `uv run pytest --cov`
- **Lint / format:** per the repo's `code-quality-py` instructions and root
  linter config (e.g. `.flake8`)
- **Dockerfile:** multi-stage per `sdlc-project-scaffolding` — Azure Linux
  Python base, `COPY --from=ghcr.io/astral-sh/uv:latest`, `uv sync --frozen`
- **CI steps:** `uv sync --frozen` → `uv run pytest --cov --junitxml=results.xml` → `docker build`
- **Template source:** the org's base / API / agent template repos from
  copilot-instructions; otherwise the bundled default template
  (`assets/templates/python/api`); `.github/reference-catalog.md` patterns
  are the last-resort fallback.

Defaults that belong to this profile: FastAPI is the default API framework;
Python 3.12 is the default runtime version.

## Profile: typescript (web frontend)

- **Project files:** `package.json`, `pnpm-lock.yaml`, `tsconfig.json`
- **Layout:** React + Next.js application under the project folder; `src/`
  code root with PascalCase component folders (application convention);
  ESLint + Prettier configs at the project root.
- **Package manager:** `pnpm` — install: `pnpm install --frozen-lockfile`.
  Never npm or yarn unless the user explicitly requests it.
- **Build:** `pnpm build`
- **Test:** `pnpm test` (Vitest); direct equivalent: `npx vitest run`
- **Lint / format:** `npx eslint .` and `npx prettier --check src`
- **Dockerfile:** multi-stage — Node build stage → nginx serve stage
- **CI steps:** `pnpm install --frozen-lockfile` → `pnpm test` → `pnpm build` → `docker build`
- **Template source:** an org template repo overrides when declared;
  otherwise the bundled default template (`assets/templates/typescript/web`),
  which follows the React + TypeScript structure in
  `sdlc-project-scaffolding`.

Defaults that belong to this profile: TypeScript 7, React + Next.js,
shadcn/ui components, Tailwind CSS. TypeScript 7 requires Next.js 16.2.11
or later — Next 15's TypeScript integration cannot use the TS 7 native
compiler API (measured 2026-10-18 building the bundled template).

## Profile: dotnet

- **Project files:** one solution file `<Name>.sln` at the repository root;
  per project, `<ProjectName><Layer>.csproj`
  (`Microsoft.NET.Sdk.Web` for APIs, `Microsoft.NET.Sdk` for libraries,
  `Microsoft.NET.Sdk.Worker` for workers). `packages.lock.json` per project
  when the org enables locked restore.
- **Layout:**
  ```
  src/
  ├── <Name>API/
  │   ├── <Name>API.csproj
  │   ├── Program.cs              ← host builder + DI registration
  │   ├── appsettings.json
  │   ├── Endpoints/              ← minimal-API endpoint groups (or Controllers/)
  │   └── Services/               ← I<Name>Service interfaces + implementations
  ├── <Name>Business/
  │   └── <Name>Business.csproj   ← domain models, repositories
  └── <Name>API.Tests/
      └── <Name>API.Tests.csproj ← xUnit test project (its own project folder)
  ```
  In .NET, tests are a **separate project**, not a subfolder — the test
  project is a sibling project folder under `src/` and references the project
  under test. The `src/` container rule and `<ProjectName><Layer>` naming
  are unchanged.
- **Runtime:** the current .NET LTS as pinned by the organization
  (this profile's default: .NET 10, target framework `net10.0`).
- **Package manager:** NuGet via the `dotnet` CLI — restore:
  `dotnet restore <Name>.sln` (add `--locked-mode` when lock files are used).
- **Build:** `dotnet build <Name>.sln -c Release`
- **Test:** `dotnet test <Name>.sln -c Release`; coverage:
  `dotnet test <Name>.sln -c Release --collect "XPlat Code Coverage"`
  (coverlet). Test framework: xUnit with `Microsoft.NET.Test.Sdk`.
- **Lint / format:** `dotnet format --verify-no-changes`; analyzers run as
  part of `dotnet build` (the org may set `TreatWarningsAsErrors` in CI).
- **Dockerfile:** multi-stage — build stage
  `mcr.microsoft.com/dotnet/sdk:10.0` (restore → `dotnet publish -c Release`),
  runtime stage `mcr.microsoft.com/dotnet/aspnet:10.0`, non-root `APP_UID`
  user, `EXPOSE 8080`, `ENTRYPOINT ["dotnet", "<Name>API.dll"]`.
- **CI steps (GitHub Actions, default):** `actions/setup-dotnet` →
  `dotnet restore` → `dotnet build -c Release` → `dotnet test -c Release`.
  **ADO variant** (organization declares Azure DevOps): `DotNetCoreCLI@2`
  restore → build → test with `PublishTestResults@2` in `azure_cicd.yaml`.
- **Devcontainer:** `mcr.microsoft.com/devcontainers/dotnet` (org-pinned tag).
- **Patterns:** dependency injection uses the built-in
  `Microsoft.Extensions.DependencyInjection` container — register services in
  `Program.cs` (`builder.Services.AddScoped<IOrderService, OrderService>()`),
  interface-first like the python profile's Protocol convention.
  Configuration uses the Options pattern (`IOptions<T>`). Every API exposes
  health endpoints via `AddHealthChecks()` mapped at `/health` (the .NET
  counterpart of the python template's http_probes).
- **Template source:** the org's .NET template repo from copilot-instructions
  when declared; otherwise the bundled default template
  (`assets/templates/dotnet/api`); this profile's layout is the last-resort
  fallback.

---

## Adding a stack

A new stack is **data, not code**: add one profile section above (all fields),
confirm a matching instruction pair exists in `sdlc-workspace-init` assets
(`code-quality-<stack>` / `test-quality-<stack>` — go, java, and rust already
have theirs), add a bundled default template under `assets/templates/` whose
`verify` steps pass, and the Scaffolder, Implementer, and QA agents pick the
stack up through profile resolution. No agent file changes. A stack counts
as fully supported only when profile, instruction pair, bundled template,
and a passing greenfield run all exist.
