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
`assets/templates/<profile>/<kind>/` (python/api, dotnet/api,
typescript/web, java/api, go/api, rust/api). A template is the profile expressed as files: project
files, layout, Dockerfile, CI stub, devcontainer, a health endpoint, one
sample vertical slice (an `items` resource), and tests that prove the
wiring. Every bundled template's test suite also includes **architecture
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
- **Shared test helpers:** pytest runs with `--import-mode=importlib`
  (pyproject), under which test modules cannot import `conftest`. The
  template's conftest puts `tests/` on `sys.path`: shared fixture
  factories and scenario builders go in a plain module under `tests/`
  (e.g. `tests/rig.py`), imported by name; conftest itself holds only
  fixture definitions.
- **Coverage target:** 80% (Class 2 — a shortfall is a recorded deviation, never a gate failure)
- **Lint / format:** per the repo's `code-quality-py` instructions and root
  linter config (e.g. `.flake8`)
- **Dockerfile:** multi-stage per `sdlc-project-scaffolding` — Azure Linux
  Python base, `COPY --from=ghcr.io/astral-sh/uv:latest`, `uv sync --frozen`
- **CI steps:** `uv sync --frozen` → `uv run pytest --cov --junitxml=results.xml` → `docker build`
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
- **Coverage target:** 80% (Class 2 — a shortfall is a recorded deviation, never a gate failure)
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
- **Coverage target:** 80% (Class 2 — a shortfall is a recorded deviation, never a gate failure)
- **Lint / format:** `gofmt -l .` (must print nothing) and
  `go vet ./...`.
- **Dockerfile:** multi-stage — build stage `golang:1.27`
  (`CGO_ENABLED=0 go build`), runtime stage
  `gcr.io/distroless/static-debian12:nonroot` (static binary running as
  the distroless non-root user), `EXPOSE 8080`,
  `ENTRYPOINT ["/server"]`.
- **CI steps (GitHub Actions, default):** `actions/setup-go` (1.27) →
  `gofmt` check → `go vet ./...` → `go test ./...` → `docker build`.
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
- **Coverage target:** 80% (Class 2 — a shortfall is a recorded deviation, never a gate failure)
- **Lint / format:** `cargo fmt --check` and
  `cargo clippy --all-targets -- -D warnings`.
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
