---
name: sdlc-stack-profiles
description: >-
  Per-stack profiles that declare everything language-specific in the harness —
  project files, layout, package manager, build/test/lint commands, Dockerfile
  and CI patterns — so the SDLC process itself stays stack-neutral. Use when
  scaffolding, implementing, testing, or reviewing a project in any supported
  stack (python, typescript, dotnet, java, go, rust), or when an organization adopts the
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

If the declared stack has an instruction pair but no profile, it is
not a supported stack (see "Adding a stack"): stop and
surface the gap to the user — never fall through to the python/typescript
defaults for it.

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
| Coverage target | The profile's coverage quality target — a Class 2 target: a shortfall is a recorded deviation, never a gate failure |
| Dockerfile | Base images and multi-stage outline |
| CI steps | Build-stage commands for the CI stub — GitHub Actions (`.github/workflows/ci.yml`) by default; ADO `azure_cicd.yaml` where the organization declares Azure DevOps |
| Devcontainer | Image |
| Template source | Org template repo (from copilot-instructions) if any; otherwise the bundled default template (below); the profile layout is the last-resort fallback |

---

## Bundled default templates

Every profile ships a **bundled default template** in this skill's assets:
`assets/templates/<profile>/<kind>/` — the service kinds (python/api,
dotnet/api, typescript/web, java/api, go/api, rust/api), the web
kind (the web kind for all six stacks; see the Web paragraph
below), the library
kind for all six stacks (see the library paragraph below), the
cli kind (all six stacks; see the CLI paragraph below), and the
worker kind for all six stacks (see the Worker paragraph below). A template is the profile expressed as files: project
files, layout, CI stub, and tests that prove the wiring; service
templates add a Dockerfile, devcontainer, a health endpoint, and one
sample vertical slice (an `items` resource), while library templates
ship a small sample public API instead and cli templates ship a
sample command tree over an importable library core. Every bundled template's test suite also includes **architecture
conformance tests** that enforce the profile's dependency direction
mechanically (layers may only depend in the declared direction) — they
run as part of the profile's Test command, so a layering violation fails
the build instead of waiting for a reviewer to notice it. Template
resolution mirrors profile resolution:

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
copyright line; a template may declare one more, `{{project_name}}` —
the snake_case import name, used by python/library); delete
`template.yaml`; generate lock files with the profile's install command
(lock files are never templated); then run the template's `verify` steps —
the profile's install, build, and test commands. The scaffold is not
complete until verification passes or an environment limitation is reported
per the harness's environment-failure rule.

**Editor baseline:** every bundled template ships an `.editorconfig`
at its root — the editor-level baseline (charset, line endings,
indentation) that the profile's toolchain formatters enforce in CI,
so a contributor's editor agrees with the gate before CI ever runs.

**Security baseline:** every bundled template ships `SECURITY.md`
(private vulnerability reporting, response expectations, and the
secret-handling rules) and a `renovate.json` — the pinned
dependency-update policy: weekly grouped updates, a 3-day minimum
release age, patch automerge for development-only dependencies,
major updates always human-reviewed. Every template CI workflow
declares top-level `permissions: contents: read` and a `security`
job — a gitleaks secret scan over the git history and an
OSV-Scanner scan of the project's dependency lock files, both
version-pinned in the workflow — and the deploy job requires the
security job as well as the build. Containers run as a non-root
user on an unprivileged port. A template whose sample fails its own
scans is a harness defect, like any other template/profile mismatch.

**Release baseline:** every bundled template versions by Semantic
Versioning and keeps a `CHANGELOG.md` in Keep a Changelog format.
A `vX.Y.Z` tag runs the template's release workflow: a verify job
re-runs the stack's full build-stage gate set (the CI build job
minus the Docker step) on the tagged tree, then the matching
CHANGELOG section becomes the GitHub Release notes — a tag whose
version has no CHANGELOG section fails the release rather than
publishing empty notes. Every template also ships a README stub at
its root (what it is, how to run it, links to SECURITY.md and the
changelog); the design phase expands the stub into the full
project README.

**Library type — reversed defaults:** a library's consumers are
other codebases' builds, so compatibility is the product and
several service defaults invert. Dependencies are declared as
abstract ranges, never exact versions, and **no lock file is
committed** (the CI security job generates one transiently for
scanning, and scans it with the scanner's ignore rules disabled —
the transient lock is git-ignored by design, and a scanner that
respects the ignore file silently scans nothing) — a library
declares what it can work with; an application records what it
did work with. The public surface is explicit, small, and
machine-checked: python declares `__all__` and CI diffs the API
against the last release with griffe; .NET declares
`PublicAPI.Shipped/Unshipped.txt` and the PublicApiAnalyzers fail
the build when code and declaration disagree; typescript exposes
only the entry point through the package `exports` map, keeps
the api-extractor report of the surface committed, and CI fails
when the report and the built declarations disagree (exports
carry `@public` release tags); java pins the declared surface
with a reflection test in the build and CI diffs the compiled jar
against the last release with japicmp, failing on binary- or
source-incompatible changes; go diffs the exported API of its
packages against the last release with apidiff, failing on
incompatible changes; rust checks the crate against the last
release with cargo-semver-checks, failing on breaking changes.
Tests are black-box against the public API only, the README
quickstart is executed in CI (a runnable example file; doctests
in python and rust; Go examples, which `go test` runs and
verifies), and CI tests
the declared support range — every supported runtime version,
and for python also the lowest allowed dependency resolution.
There is no Dockerfile, no app configuration, and no deploy job.
Publishing happens only from a release tag, through registry
trusted publishing (OIDC — no stored registry token), and only
after the built artefact passes a consumer smoke test in a clean
project; the tag is the version (python, typescript, and rust
also require the tag to match the manifest version). Go is the
limiting case: the tag is the entire publication — the module
proxy serves the library from the repository, so there is no
registry account or credential at all. Maven Central is
the one documented exception to trusted publishing: it has no
OIDC exchange, so the java template publishes with a dedicated
Central Portal token and a dedicated GPG key held as release
environment secrets. Deprecation is a written policy in the
template README: mark in one release (a runtime warning,
`[Obsolete]`, a `@deprecated` tag, `@Deprecated`, a
`// Deprecated:` doc paragraph, or `#[deprecated]`), remove no
earlier than the next major. The library kind ships for all six
stacks: python, dotnet, typescript, java, go, and rust.

**CLI type — the interface is the contract:** a CLI's consumers are
scripts and agents, so its flags, stdout schema, and exit codes are
an API surface and are tested like one (the canonical source is
clig.dev). Arguments are parsed by the ecosystem library, never
hand-rolled (cobra for go, clap for rust, Click/Typer for python,
System.CommandLine for dotnet, Commander for typescript), with a
`tool <noun> <verb>` command structure and a thin entry point over
an importable library core — the testable logic never lives in the
entry point. Primary data goes to stdout, diagnostics to stderr;
exit codes follow a small documented map (0 success, 1 failure,
2 usage error) printed in the help text and the README. Data
commands offer `--format plain|json` (plus a `--json` shorthand);
color is decided from TTY detection, the `NO_COLOR` environment
variable, and `--no-color`, and never touches piped output.
Destructive actions carry `--dry-run`, overwriting requires
`--force`, and prompting never happens when stdin is not a TTY
(`--no-input` makes that explicit); secrets are read from the
environment, never from a flag. Configuration precedence is stated
in the help: flags, then environment, then defaults. Tests pin the
contract: golden files for help and primary output, exit-code
tests per failure mode, argument-parsing tables. Distribution is
this type's biggest delta and is tag-driven in the GoReleaser
shape for every stack: cross-compiled binaries for linux, darwin,
and windows on amd64 and arm64, archives with a SHA-256 checksums
file, GitHub Releases plus the package channels users actually
use (Homebrew, deb/rpm, the language channel), shell completions
and a man page generated from the parser — never hand-written —
and the release version derived from the tag — GoReleaser injects
it into the binary (an untagged build reports `dev`), cargo-dist
takes it from Cargo.toml and refuses a mismatched tag; `--version`
keeps the parser's canonical, stable shape (the tool name plus the
version), which scripts parse and which never changes within a
major version. Changes to the `--json` schema, the exit
codes, or flag names are breaking changes and ship only in a
major release. The cli kind ships for go (cobra + GoReleaser),
rust (clap + cargo-dist), python (Click + PyInstaller binaries
and a PyPI package, man pages rendered from the built tool's help),
dotnet (System.CommandLine + single-file publish and a NuGet tool
package, man pages rendered the same way), typescript
(Commander + Node SEA binaries and an npm package, completions
generated from the command tree, man pages rendered the same way),
and java (picocli + a shaded executable jar and jpackage app
images and a Maven Central artifact, completions generated by
picocli from the command model — bash/zsh only, picocli has no
fish generator); the contract is fully shipped for every stack.

**Web type — the browser is untrusted:** A web app renders for a
client the server cannot trust, and its signature security defect
is a server secret reaching that client — so the environment
split is structural, not a naming habit: configuration lives in
two separate objects (a Public config templates and client code
may read, and a Server config that is never rendered, logged, or
serialized to a response), and every web template's test suite
pins a sentinel server secret out of every response while
asserting the public values do render. Pages are server-rendered
first — client scripts enhance, they are not the only path to
the content — and form posts answer with post/redirect/get so a
refresh never resubmits. The markup floor is WCAG 2.2 AA: a
language attribute, a skip link, landmark regions, exactly one
h1 per page, labelled form controls, and visible focus, asserted
by the page tests so a new page cannot silently drop it; bundle
and performance budgets (where the stack has a bundle) are
reported in CI rather than hard gates, because lab scores vary
by runner. The web kind ships for typescript (Next.js), python
(FastAPI + Jinja2 server-rendered), go (net/http +
html/template server-rendered, assets embedded in the binary),
dotnet (ASP.NET Core Razor Pages), rust (axum + MiniJinja),
and java (Spring Boot + Thymeleaf) — the contract is fully
shipped for every stack. On typescript the split rides the
framework's own mechanism: only NEXT_PUBLIC_-prefixed variables
reach the bundle, the two configuration modules sit on that
line (lib/config and lib/server-config), and the architecture
test — not convention — keeps client code from importing the
server module.

**Worker type — correctness under redelivery:** A worker is
designed for at-least-once delivery: the same job can arrive
twice, a worker can die mid-job, and a poison job can arrive at
any time, so correctness lives in the store's transactions, not
in careful handlers. Every job carries a producer-chosen
idempotency key with a UNIQUE constraint; the effect row is
inserted in the same transaction that marks the job done, so a
redelivery is acked without re-applying the effect (the effect
exists exactly once) and completion events go through a
transactional outbox written in that same transaction (published
afterwards, at-least-once, keyed for consumer dedupe). Failures
are classified by the handler: a permanent error (bad payload,
unknown job type) dead-letters at once; anything else is retryable
with exponential backoff and full jitter until the attempt budget
runs out, then it dead-letters too. Claims are leases, not locks:
a claimed job whose lease expires is claimable again, which is
how a crash mid-job recovers. The dead-letter queue is part of
the shipped surface from day one: dead jobs are queryable, an
alarm fires whenever the dead depth is above zero, and a replay
operation returns a dead job to pending with its budget restored
— a DLQ without replay is a write-only graveyard. Job scope is
per job: a handler receives exactly one job's payload and returns
its result. The pinned store is SQLite through the stack's
canonical driver: it makes every guarantee testable with no
external services, and the schema and claim protocol map onto any
transactional store in production — the guarantees live in the
protocol, not in SQLite. The defining tests ship in every worker
template: duplicate delivery applies the effect once, a poison
message dead-letters, a crash mid-job recovers through the lease,
plus backoff scheduling, outbox single-drain, and replay — all
against a fake clock, no sleeping. The worker kind ships for
every stack, each on its canonical SQLite driver: python
(standard-library sqlite3, no runtime dependencies), dotnet
(Microsoft.Data.Sqlite), typescript (Node's built-in node:sqlite,
no third-party driver), java (xerial sqlite-jdbc), go
(modernc.org/sqlite, pure Go), and rust (rusqlite, bundled
engine); the contract is fully shipped for every stack.

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
- **Domain errors:** service-layer failures live in
  `app/services/errors.py` (`DomainError` + NotFound/Forbidden/
  Conflict/Validation). Services raise them; the composition root
  maps them to HTTP status codes. Routers never translate failures,
  and a project adds its own failures as `DomainError` subclasses in
  that module — never ad-hoc exceptions inside a service.
- **Shared test helpers:** pytest runs with `--import-mode=importlib`
  (pyproject), under which test modules cannot import `conftest`. The
  template's conftest puts `tests/` on `sys.path`: shared fixture
  factories and scenario builders go in a plain module under `tests/`
  (e.g. `tests/rig.py`), imported by name; conftest itself holds only
  fixture definitions.
- **Coverage target:** 80% (Class 2 — a shortfall is a recorded deviation, never a gate failure)
- **Lint / format:** `uv run ruff check .` and `uv run ruff format --check .`
  — Ruff is the pinned formatter + linter for every Python project,
  configured in the project's `pyproject.toml` (`[tool.ruff]`). There is
  no second formatter and no per-project rule shopping.
- **Dockerfile:** multi-stage per `sdlc-project-scaffolding` — Azure Linux
  Python base, `COPY --from=ghcr.io/astral-sh/uv:latest`, `uv sync --frozen`
- **CI steps:** `uv sync --frozen` → `uv run ruff check .` → `uv run ruff format --check .` → `uv run pytest --cov --junitxml=results.xml` → `docker build`
- **Template source:** the org's base / API / agent template repos from
  copilot-instructions; otherwise the bundled default template
  (`assets/templates/python/api`); the profile layout above is the
  last-resort fallback.

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
- **Coverage target:** 80% (Class 2 — a shortfall is a recorded deviation, never a gate failure)
- **Lint / format:** `pnpm lint` (ESLint flat config, `eslint.config.mjs`)
  and `pnpm format:check` (Prettier, `.prettierrc.json`) — both configs
  ship in the template at the project root; CI runs both. The
  template's `.prettierignore` excludes the files Next.js manages
  itself (`next-env.d.ts`, `tsconfig.json` — Next rewrites the
  latter in its own format on build, so formatting it by hand only
  creates churn).
- **Dockerfile:** multi-stage — Node build stage → nginx serve stage
- **CI steps:** `pnpm install --frozen-lockfile` → `pnpm lint` → `pnpm format:check` → `pnpm test` → `pnpm build` → `docker build`
- **Template source:** an org template repo overrides when declared;
  otherwise the bundled default template (`assets/templates/typescript/web`),
  which follows the React + TypeScript structure in
  `sdlc-project-scaffolding`.

Defaults that belong to this profile: TypeScript 6, React + Next.js,
shadcn/ui components, Tailwind CSS. TypeScript is held at 6.x: the
profile's pinned lint toolchain (typescript-eslint, loaded by
eslint-config-next) does not support TypeScript 7 yet, and a standard
whose lint gate cannot run is not a standard (measured 2026-11-11:
TS 7.0.2 makes `eslint .` fail while loading its config; TS 6 runs
lint, format check, tests, and build green). The Next.js pin (16.2.11
or later) already satisfies the floor TypeScript 7 will need, so
moving to 7 is a one-line change when typescript-eslint support lands.

Two dependency pins in the template's `package.json` are security
holds, verified against the template's own OSV-Scanner gate
(2026-11-11): Vitest is at 4.x because the 3.x tree carried critical
vulnerabilities (tinypool), and a pnpm override lifts `minimatch@10`
to ^11 — typescript-eslint's estree resolves minimatch 10, whose
only fixed line is 11. Remove the override when eslint-config-next's
typescript-eslint no longer resolves minimatch 10. The Vitest 4 move
also retired the `esbuild.jsx` setting in `vitest.config.ts`:
Vitest 4 transforms JSX via oxc, and the stale key failed
`next build`'s type check against Vitest 4's bundled Vite types.

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
- **Stack facts (mechanical):** version facts live in the bundled
  template's project files (target framework + package pins) — the
  single source of truth, never restated in prose. The Phase 1–2
  gate verifies REQ/ADR stack claims against them with
  `scripts/check_stack_conformance.py` (this skill's scripts
  folder); a spec claim that contradicts a template pin fails the
  gate mechanically.
- **Package manager:** NuGet via the `dotnet` CLI — restore:
  `dotnet restore <Name>.sln` (add `--locked-mode` when lock files are used).
- **Build:** `dotnet build <Name>.sln -c Release`
- **Test:** `dotnet test <Name>.sln -c Release`; coverage:
  `dotnet test <Name>.sln -c Release --collect "XPlat Code Coverage"`
  (coverlet). Test framework: xUnit with `Microsoft.NET.Test.Sdk`.
- **Errors:** the web layer owns HTTP translation — endpoints return
  `Results.*` and services signal absence with `null`. When a service
  needs richer failures, declare exception types in the service layer
  and map them in one middleware; never per-endpoint catch blocks.
- **Coverage target:** 80% (Class 2 — a shortfall is a recorded deviation, never a gate failure)
- **Lint / format:** `dotnet format --verify-no-changes`; analyzers and
  code style run as part of `dotnet build` — the template's
  `Directory.Build.props` at the solution root pins `AnalysisLevel`
  latest-recommended, `EnforceCodeStyleInBuild`, and
  `TreatWarningsAsErrors`, so warnings fail the build rather than
  scrolling past. The one recorded exception: test projects carry
  their own `.editorconfig` exempting CA1707, because test method
  names use the Unit_Scenario_Expectation convention.
- **Dockerfile:** multi-stage — build stage
  `mcr.microsoft.com/dotnet/sdk:10.0` (restore → `dotnet publish -c Release`),
  runtime stage `mcr.microsoft.com/dotnet/aspnet:10.0`, non-root `APP_UID`
  user, `EXPOSE 8080`, `ENTRYPOINT ["dotnet", "<Name>API.dll"]`.
- **CI steps (GitHub Actions, default):** `actions/setup-dotnet` →
  `dotnet restore` → `dotnet format --verify-no-changes` →
  `dotnet build -c Release` → `dotnet test -c Release`.
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

## Profile: java

- **Project files:** `pom.xml` per project, plus the committed Maven wrapper
  (`mvnw`, `mvnw.cmd`, `.mvn/wrapper/`) — the wrapper pins the Maven version,
  so there is no lock file and no system-Maven dependency.
- **Layout:**
  ```
  src/
  └── <Name>API/
      ├── pom.xml
      ├── mvnw                        ← committed wrapper (pins Maven)
      ├── Dockerfile
      └── src/
          ├── main/java/com/example/<packagename>/
          │   ├── <Name>Application.java   ← composition root (wiring only)
          │   ├── web/                     ← controllers (HTTP boundary)
          │   ├── service/                 ← interfaces + implementations + repositories
          │   └── model/                   ← records / DTOs
          ├── main/resources/application.properties
          └── test/java/com/example/<packagename>/   ← mirrors the main tree
  ```
  Layers are **packages**, and the dependency direction is web → service →
  model. The Application class in the base package is the composition root —
  the only place implementations are wired. Tests mirror the main packages
  under `src/test/java` (Maven convention), they are not a separate project.
- **Runtime:** Java 21 LTS (this profile's default; the organization may pin
  a newer LTS).
- **Package manager / build tool:** **Maven via the committed wrapper** —
  restore: `./mvnw -B dependency:resolve`. **Decision rule:** Maven is the
  bundled default because its build is declarative and convention-fixed, so
  the profile can pin it exactly and every project builds the same way.
  Gradle is used only when the organization declares it — its build scripts
  are code, and code drifts. Never the system `mvn`: the wrapper is the pin.
- **Build:** `./mvnw -B package -DskipTests`
- **Test:** `./mvnw -B test`; coverage: `./mvnw -B verify` (JaCoCo report
  under `target/site/jacoco/`).
- **Errors:** the web layer owns HTTP translation — controllers throw
  `ResponseStatusException` and services return `Optional`. When a
  service needs richer failures, declare domain exceptions in the
  service layer and map them in one `@RestControllerAdvice`; never
  per-controller catch blocks.
- **Coverage target:** 80% (Class 2 — a shortfall is a recorded deviation, never a gate failure)
- **Lint / format:** `./mvnw -B spotless:check` (googleJavaFormat), bound to
  the `verify` phase in the template's pom.
- **Dockerfile:** multi-stage — build stage `maven:3.9-eclipse-temurin-21`
  (`mvn package`), runtime stage `eclipse-temurin:21-jre`, non-root user,
  `EXPOSE 8080`, `ENTRYPOINT ["java", "-jar", "app.jar"]`.
- **CI steps (GitHub Actions, default):** `actions/setup-java` (temurin 21,
  maven cache) → `./mvnw -B verify` → `docker build`.
- **Devcontainer:** `mcr.microsoft.com/devcontainers/base:ubuntu` with the
  `java` feature (version 21).
- **Patterns:** interface-first services, mirroring the other profiles —
  controllers depend on service interfaces, services on repository
  interfaces, and the Application class wires the implementations as
  `@Bean` methods (explicit composition root, the counterpart of the
  python template's app context). Constructor injection only. Every API
  exposes `/health` and `/health/ready` with the same response shape as
  the other templates.
- **Template source:** the org's Java template repo from
  copilot-instructions when declared; otherwise the bundled default
  template (`assets/templates/java/api`); this profile's layout is the
  last-resort fallback.

Defaults that belong to this profile: Spring Boot 3.5 is the default
framework (its parent POM manages dependency versions); Java 21 LTS is
the default runtime.

---

## Profile: go

- **Project files:** `go.mod` per project (Go modules) — the `go`
  directive in `go.mod` pins the language version. `go.sum` appears when
  the first external dependency is added; the bundled template uses only
  the standard library, so a fresh scaffold has no dependencies and no
  `go.sum`.
- **Layout:**
  ```
  src/
  └── <Name>API/
      ├── go.mod                     ← module example.com/<project-name>
      ├── Dockerfile
      ├── cmd/
      │   └── <project-name>/
      │       └── main.go            ← composition root (wiring only)
      └── internal/
          ├── web/                   ← handlers (HTTP boundary)
          ├── service/               ← interfaces + implementations + repositories
          ├── model/                 ← structs / DTOs
          └── architecture/          ← the architecture test (test-only package)
  ```
  Layers are **packages** under `internal/`, and the dependency
  direction is web → service → model. `cmd/<project-name>/main.go` is
  the composition root — the only place implementations are wired.
  Tests live beside the code they test as `*_test.go` files (Go
  convention); they are not a separate tree.
- **Runtime:** Go 1.27 (this profile's default; the organization may
  pin a newer release — the `go` directive in `go.mod` is the pin).
- **Package manager / build tool:** **Go modules** — restore:
  `go mod download`. **Decision rule:** the standard library
  (`net/http`, with `http.ServeMux` method-and-pattern routing) is the
  bundled default web stack because it ships with the toolchain, so the
  profile can pin it exactly and every project builds the same way with
  zero dependency decisions. A framework (chi, gin, echo) is used only
  when the organization declares it — a framework is a dependency
  decision, and dependency decisions belong to the organization.
- **Build:** `go build ./...`
- **Test:** `go test ./...`; coverage:
  `go test -coverprofile=coverage.out ./...`.
- **Errors:** the web layer owns HTTP translation (`writeError`) and
  services signal absence with `nil`. When a service needs richer
  failures, declare sentinel errors in the service package
  (`var Err…`) and map them in the web layer in one place; never
  string-match error text in handlers.
- **Coverage target:** 80% (Class 2 — a shortfall is a recorded deviation, never a gate failure)
- **Lint / format:** `gofmt -l .` (must print nothing), `go vet ./...`,
  and `golangci-lint run` — the standard linter set (errcheck, govet,
  ineffassign, staticcheck, unused) pinned in the project's
  `.golangci.yml`; CI runs all three.
- **Dockerfile:** multi-stage — build stage `golang:1.27`
  (`CGO_ENABLED=0 go build`), runtime stage
  `gcr.io/distroless/static-debian12:nonroot` (static binary running as
  the distroless non-root user), `EXPOSE 8080`,
  `ENTRYPOINT ["/server"]`.
- **CI steps (GitHub Actions, default):** `actions/setup-go` (1.27) →
  `gofmt` check → `go vet ./...` → `golangci-lint run` →
  `go test ./...` → `docker build`.
- **Devcontainer:** `mcr.microsoft.com/devcontainers/base:ubuntu` with
  the `go` feature (version 1.27).
- **Patterns:** interface-first services, mirroring the other profiles —
  handlers depend on service interfaces, services on repository
  interfaces, and `main` wires the implementations (explicit composition
  root, the counterpart of the python template's app context).
  Constructor injection only — plain constructors, no DI container.
  Configuration comes from environment variables (`PORT`, default
  8080). Every API exposes `/health` and `/health/ready` with the same
  response shape as the other templates.
- **Template source:** the org's Go template repo from
  copilot-instructions when declared; otherwise the bundled default
  template (`assets/templates/go/api`); this profile's layout is the
  last-resort fallback.

Defaults that belong to this profile: Go 1.27 is the default runtime;
the standard library is the default web stack (frameworks are an
organization declaration, per the decision rule above).

---

## Profile: rust

- **Project files:** `Cargo.toml` per project (Cargo) — its
  `rust-version` and `edition` fields pin the language baseline.
  `Cargo.lock` is generated by the install step, never templated.
- **Layout:**
  ```
  src/
  └── <Name>API/
      ├── Cargo.toml               ← package <project-name>, lib <crate_name>
      ├── Dockerfile
      ├── src/
      │   ├── main.rs              ← composition root (wiring only)
      │   ├── lib.rs               ← module declarations only
      │   ├── web.rs               ← handlers (HTTP boundary)
      │   ├── service.rs           ← traits + implementations + repositories
      │   └── model.rs             ← structs / DTOs
      └── tests/                   ← integration tests (handlers, architecture)
  ```
  Layers are **modules** in one crate, and the dependency direction is
  web → service → model. `main.rs` is the composition root — the only
  place implementations are wired; `lib.rs` only declares modules, so
  integration tests exercise the same library the binary serves. Tests
  live under `tests/` (Cargo convention) as integration tests.
- **Runtime:** Rust 1.99, edition 2024 (this profile's defaults; the
  organization may pin a newer stable — `rust-version` in `Cargo.toml`
  is the pin).
- **Package manager / build tool:** **Cargo** — restore: `cargo fetch`
  (generates `Cargo.lock`). **Decision rule:** unlike Go, Rust's
  standard library has no HTTP server, so a web framework is required;
  **axum** is the bundled default because it is the tokio-ecosystem
  standard — small, extractor-based, and composed from tower
  middleware, so the profile can pin one framework exactly. Another
  framework (actix-web, rocket) is used only when the organization
  declares it.
- **Build:** `cargo build`
- **Test:** `cargo test`; coverage: `cargo llvm-cov` (requires the
  `cargo-llvm-cov` tool — install it once per environment).
- **Shared test helpers:** integration tests under `tests/` are
  separate crates. Shared helpers live in `tests/common/mod.rs` and
  are pulled in with `mod common;` — a `.rs` file placed directly
  under `tests/` becomes its own test crate instead of a library.
- **Errors:** handlers own HTTP translation, returning
  `(StatusCode, Json)`; services signal absence with `Option`. When
  a service needs richer failures, declare one error enum in the
  service module implementing `IntoResponse` and let handlers return
  it; never hand-map the same failure in several handlers.
- **Coverage target:** 80% (Class 2 — a shortfall is a recorded deviation, never a gate failure)
- **Lint / format:** `cargo fmt --check` and
  `cargo clippy --all-targets -- -D warnings` — the pins live in the
  project's `rustfmt.toml` (edition, width) and `clippy.toml` (MSRV,
  so clippy never suggests an API newer than `rust-version`).
- **Dockerfile:** multi-stage — build stage `rust:1.99`
  (`cargo build --release`), runtime stage
  `gcr.io/distroless/cc-debian12:nonroot` (the binary links libc,
  hence the cc variant), `EXPOSE 8080`, `ENTRYPOINT ["/server"]`.
- **CI steps (GitHub Actions, default):**
  `actions-rust-lang/setup-rust-toolchain` (rustfmt, clippy) →
  `cargo fmt --check` → `cargo clippy` → `cargo test` → `docker build`.
- **Devcontainer:** `mcr.microsoft.com/devcontainers/base:ubuntu` with
  the `rust` feature (version 1.99).
- **Patterns:** trait-first services, mirroring the other profiles —
  handlers depend on service traits, services on repository traits,
  shared through `Arc<dyn Trait>`, and `main` wires the implementations
  (explicit composition root, the counterpart of the python template's
  app context). Configuration comes from environment variables
  (`PORT`, default 8080). Every API exposes `/health` and
  `/health/ready` with the same response shape as the other templates.
- **Template source:** the org's Rust template repo from
  copilot-instructions when declared; otherwise the bundled default
  template (`assets/templates/rust/api`); this profile's layout is the
  last-resort fallback.

Defaults that belong to this profile: Rust 1.99 / edition 2024 is the
default baseline; axum is the default web framework (other frameworks
are an organization declaration, per the decision rule above).

---

## Adding a stack

A new stack is **data, not code**: add one profile section above (all fields),
confirm a matching instruction pair exists in `sdlc-workspace-init` assets
(`code-quality-<stack>` / `test-quality-<stack>`), add a bundled
default template under `assets/templates/` whose
`verify` steps pass, and the Scaffolder, Implementer, and QA agents pick the
stack up through profile resolution. No agent file changes. A stack counts
as fully supported only when profile, instruction pair, bundled template,
and a passing greenfield run all exist.
