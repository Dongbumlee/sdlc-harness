# ADR-0002: Bundled Default Templates

> **Status:** Proposed
> **SDLC Phase:** 1-2 (Requirements & Design)
> **Date:** 2026-10-18
> **Author:** Dongbum(DB) Lee

---

## Context

The harness's north star is consistency: one adopted standard, applied the
same way across languages and implementation solutions, so that any engineer
who knows the standard can work in any project that follows it — minimizing
dependence on individual engineers, the way an FDE brings a client's own code
standards to every engagement.

Two layers of that standard already ship:

- **Process** (phases, requirements, ADRs, manifest, reviews) — stack-neutral.
- **Stack profiles** (v1.1.0, `sdlc-stack-profiles` skill) — each profile
  declares a stack's project files, layout, package manager, build/test/lint
  commands, Dockerfile, and CI steps as prose an agent can follow.

The third layer — the actual template files a project is scaffolded from —
does **not** ship. By a 2026-10-07 design decision, templates are fetched at
scaffold time from template repositories in the project's GitHub organization
(base app, API, agent templates), with `.github/reference-catalog.md` patterns
as the fallback. That decision assumed an enterprise organization that already
maintains template repos. Individual users and small teams — and enterprise
teams piloting the harness before investing in their own templates — have
none.

Measured consequence (2026-10-18, .NET greenfield E2E): with no organization
template declared, the Scaffolder improvised the entire scaffold from the
dotnet profile's prose. The run's manifest recorded the provenance honestly
("dotnet profile fallback layout (no org template declared)"). The result was
good — but it was one model's interpretation of a description, not the
application of a standard. The fallback path is the de-facto product for
every user without organization templates, and today that path is
improvisation.

A prose standard still depends on the executing agent's interpretation.
A file standard does not.

## Problem / Requirements

### Functional Requirements

- **FR1 — Ship default templates.** The harness bundles a default template
  for each stack profile it ships, versioned with the harness release.
- **FR2 — Override, never replace.** Template resolution mirrors profile
  resolution: an organization template (declared in
  `.github/copilot-instructions.md`) wins over the bundled default. The
  bundled template is a floor, never a ceiling.
- **FR3 — Golden path.** Instantiating a bundled template (token
  substitution, then the profile's install command) produces a project whose
  profile Build and Test commands pass immediately. Every bundled template
  carries a health endpoint, one sample vertical slice, and at least one
  passing test proving the wiring.
- **FR4 — Provenance.** The Scaffolder records the template source in
  `.SDLC/project-manifest.md`: `bundled <profile>/<kind>@<harness version>`
  or `org <repo>@<ref>`. Deviations from the template are recorded with
  reasons, as the manifest already records pattern deviations.
- **FR5 — Full obligation set.** A bundled template carries everything the
  Scaffolder's checklist demands per project: project files, Dockerfile,
  CI stub, devcontainer, `.gitignore` / `.dockerignore`, and the
  language quality-instruction wiring from `sdlc-workspace-init`.

### Non-Functional Requirements

- **No network dependency** for the bundled tier: scaffolding from a bundled
  template works offline once the plugin is installed.
- **Small skeletons, not frameworks.** Templates are starting points an
  organization is expected to outgrow or fork, not a runtime library.
- **Backward compatible.** Projects and organizations already using org
  template repos are unaffected; resolution order preserves their flow.
- **No silent mutation.** A scaffolded project records the harness version
  it came from. Later template updates never rewrite existing projects;
  upgrading a project's scaffold is a deliberate, separate act (out of
  scope here).

### Constraints

- `packs/` remains the single source of truth; the flat layout stays
  generated (ADR-0001). Bundled templates must ride a distribution mechanism
  that already exists — skill assets are shipped by the assembler today
  (`sdlc-workspace-init` assets are the precedent).
- Templates contain no secrets, no concrete model names, and no
  organization-internal package references that a public user cannot resolve.
- All harness artifacts are written in English.

## Design / Implementation

Chosen approach: **bundle default templates as assets of the
`sdlc-stack-profiles` skill**, one directory per profile/kind, instantiated
by the Scaffolder with literal token substitution.

### Architecture

```
packs/core/skills/sdlc-stack-profiles/
  SKILL.md                     # profiles (standards) — exists since v1.1.0
  assets/
    templates/
      python/
        api/
          template.yaml        # id, profile, kind, tokens, verify commands
          src/{{ProjectName}}API/
            app/...
            tests/...
            pyproject.toml
            Dockerfile
            .github/workflows/ci.yml
            .devcontainer/devcontainer.json
      dotnet/
        api/
          template.yaml
          {{ProjectName}}.sln
          src/{{ProjectName}}API/...
          src/{{ProjectName}}API.Tests/...
          Dockerfile
          .github/workflows/ci.yml
      typescript/
        web/
          template.yaml
          src/{{ProjectName}}Web/...
```

### Template anatomy

- **`template.yaml`** declares: template id (`<profile>/<kind>`), the token
  list with per-stack defaults, and the verify commands (the profile's Build
  and Test commands) used by the canary in Testing Strategy.
- **File tree** is literal: what is in the template is what lands in the
  project, after token substitution in file names and file contents.
- **Tokens** are deliberately few and stack-scoped, e.g. `{{ProjectName}}`
  (PascalCase base), `{{project-name}}` (kebab, for package names),
  `{{RootNamespace}}` (dotnet), `{{PackageName}}` (python), `{{Port}}`.
  Substitution is literal string replacement performed by the Scaffolder —
  no templating engine is introduced.
- **Lock files are never templated.** `uv.lock`, `pnpm-lock.yaml`, and
  `packages.lock.json` are generated by the profile's install command during
  instantiation (FR3 sequences: copy → substitute → install → verify).

### CI default: GitHub Actions

Bundled templates ship **GitHub Actions** CI (`.github/workflows/ci.yml`) as
the default. Azure DevOps (`azure_cicd.yaml`) remains a profile-declared
variant, selected by organization override — it is not removed. Rationale:
the harness is distributed and operated in the GitHub ecosystem (Copilot
plugin, GitHub MCP template fetch), the bundled tier targets users with no
organization platform commitments, and the 2026-10-18 .NET E2E independently
chose the GitHub Actions variant when scaffolding into a GitHub repo. This
inverts the v1.1.0 profile default (ADO first, GitHub Actions "where
given"); aligning the shipped `sdlc-stack-profiles` /
`sdlc-project-scaffolding` defaults is a follow-up content change, tracked
separately from this ADR.

### Resolution order (extends profile resolution)

1. An explicit instruction from the user or the organization.
2. The organization template repo named in `.github/copilot-instructions.md`,
   fetched via GitHub MCP (the existing flow — unchanged).
3. **The bundled default template for the resolved stack profile** (new).
4. The profile's prose layout as the last-resort fallback, recorded as such
   in the manifest (today's behavior, demoted to tier 4).

### Scaffolder changes

- The template-fetch step gains tier 3: read the bundled template from the
  installed `sdlc-stack-profiles` skill assets and instantiate it.
- The manifest's Projects table gains the provenance from FR4.
- The Phase 3 exit criteria gain one item: scaffold source recorded
  (org repo / bundled template id + harness version / prose fallback).

### First template set (scope of the implementing change)

| Template | Source of truth for its content |
|---|---|
| `python/api` | The application patterns already documented in `sdlc-project-scaffolding` (Application factory, `libs/`, Protocol services), with org-internal library references replaced by dependency-free equivalents — see Open Questions |
| `dotnet/api` | The layout proven in the 2026-10-18 .NET greenfield E2E, adjusted to the profile (test project as a sibling under `src/`) |
| `typescript/web` | The React + Next.js structure in `sdlc-project-scaffolding` |

Business/agent kinds and the go/java/rust profiles follow through the same
mechanism when their profiles are written; adding a template is data, not
code, once the mechanism exists.

### Organization adoption paths

1. **Use the bundled defaults as-is** — the cold-start path; zero setup.
2. **Override pinned values** in the organization's copy of the profile
   (runtime version, base images, approved libraries) — the v1.1.0 mechanism.
3. **Point copilot-instructions at an organization template repo** — the
   pre-existing enterprise flow; wins over the bundle (FR2).
4. **Fork the bundle** — copy a bundled template into an organization repo
   and customize it there. This is the expected enterprise path: the harness
   hands the organization a working standard to make its own.

### Versioning

Templates version with the harness (single version number, as aligned in
v1.1.0). Template changes are called out in release notes. The manifest
provenance record (FR4) is what makes a project's template vintage auditable
after the fact.

## Alternatives Considered

### Alternative 1: Status quo — prose profiles only, org repos assumed

- **Pros:** No new artifacts to maintain; templates stay the organization's
  problem.
- **Cons:** The fallback path remains per-run improvisation; cold start for
  individuals and pilots stays broken; the standard cannot be tested because
  it does not exist as files.
- **Rejected because:** it leaves the measured 2026-10-18 behavior — a good
  outcome by luck rather than by standard — as the designed behavior.

### Alternative 2: Separate template repositories under the project org

- **Pros:** Templates are independently forkable and versioned; matches the
  existing GitHub-MCP fetch design; organizations can watch/star/fork them.
- **Cons:** Network dependency at scaffold time; version skew between
  harness releases and template repos; N more repositories to maintain,
  release, and keep consistent with the profiles.
- **Deferred, not rejected:** the resolution contract (tier 2) already
  treats repos as first-class. Bundled templates can be mirrored to repos
  later without changing the design; bundling first keeps one version story.

### Alternative 3: Generate with native scaffolding CLIs at runtime

(`dotnet new`, `uv init`, `create-next-app`, …)

- **Pros:** Always current with the platform; no template files to maintain.
- **Cons:** CLI output is the vendor's convention, not the organization's
  standard — the 2026-10-18 run showed template-CLI output diverging from
  profile conventions (test-project location, project naming) and needing
  corrective edits; requires each toolchain installed at scaffold time;
  output drifts with CLI versions outside the harness's control.
- **Rejected as the primary mechanism.** Native CLIs remain available inside
  an organization's own template (tier 2), where the organization owns the
  consequences.

## Testing Strategy

- **Canary per bundled template** (extends `bench/canaries`): instantiate
  the template with a canary project name into a temporary directory, run
  the profile's install, Build, and Test commands, assert exit code 0 and
  the presence of the FR5 obligation files. A template that does not pass
  its own golden path does not ship.
- **Contract checks:** extend `tools/check_pack_contracts.py` — every
  profile that declares a bundled template has a matching template
  directory; every template directory has a `template.yaml`; every token
  used in template files is declared in its `template.yaml`.
- **E2E verification:** repeat the .NET greenfield scenario after
  implementation with pre-registered expectations: provenance recorded as
  `bundled dotnet/api@<version>`, zero layout improvisations, and an empty
  deviation list in the manifest.
- **Environment note:** canary Test steps require a working test runner.
  Where a runner is environment-blocked (repeated identical infrastructure
  failure), the v1.1.0 environment-failure rule applies: the canary degrades
  to Build + live smoke and reports the limitation rather than failing the
  template or claiming a pass.

## RAI / Risk Considerations

- [x] Templates are code shipped to every user — they are reviewed like
      code, carry the repo's license/compliance files, and contain no
      secrets, credentials, or external calls in sample code (in-memory
      storage only).
- [x] Prompt injection risks assessed — templates are data files copied by
      the Scaffolder; they contain no instructions addressed to agents.
- [x] Data privacy impact reviewed — none; templates process no user data.

## SDLC Impact by Phase

| Phase | Impact |
|---|---|
| 1-2: Requirements & Design | This ADR |
| 3: Repo Structure & CI/CD | Scaffolder gains tier-3 (bundled) instantiation; canary CI job for templates |
| 4: Implementation & Tests | Template file trees for python/api, dotnet/api, typescript/web; contract-check extensions |
| 5: Documentation | README: bundled templates + adoption paths; agent inventory unchanged |
| 6: QA Activities | Template canaries join the canary suite; E2E re-run for dotnet |
| 7: RAI Review | Sample-code review per template (no secrets, no external calls) |
| 8-9: Release & Publish | Minor version bump; release notes call out template additions/changes |

## Open Questions

- [ ] **python/api framework surface:** the documented application patterns
  reference organization-internal libraries (e.g. "the approved Cosmos DB
  library", `Application_Base` in `app/libs/`). The bundled template needs
  dependency-free equivalents that preserve the *shape* (factory + DI +
  Protocol services) without unresolvable packages — plain FastAPI with
  `Depends`-based DI is the leading candidate. Decide before implementing
  `python/api`.
- [ ] **`template.yaml` schema:** add `schemas/template.schema.json` and
  CI validation in the first implementation, or start with contract-check
  assertions only?
- [ ] **First-set kinds:** are `python/business` and `python/agent` in the
  first set, or do they follow once `python/api` proves the mechanism?
- [ ] **dotnet naming:** bundled template uses the profile's
  `<ProjectName><Layer>` convention (`TaskTrackerAPI`) rather than the
  `dotnet new` default (`TaskTracker.Api`) — confirm this is the standard
  the bundle should teach.

## References

- ADR-0001: Pack Separation — Hybrid Model (`docs/adr/ADR-0001-pack-separation.md`)
- `sdlc-stack-profiles` skill (stack profiles, resolution order) — v1.1.0
- `sdlc-project-scaffolding` skill (documented application patterns)
- v1.1.0 release notes — https://github.com/Dongbumlee/sdlc-harness/releases/tag/v1.1.0
- Design discussions: 2026-10-07 (templates live in org repos; defaults fill
  unspecified choices), 2026-10-18 (north star: cross-stack consistency via
  adopted standards; .NET greenfield E2E findings)
