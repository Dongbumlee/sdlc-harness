# ADR-0001: Pack Separation — Hybrid Model

> **Status:** Proposed
> **SDLC Phase:** 1-2 (Requirements & Design)
> **Date:** 2026-09-29
> **Author:** Dongbum(DB) Lee

---

## Context

The repo ships as a root Agent Plugins package (`plugin.json`, `skills/`, `com.github.copilot/`)
with a "Cloud Packs" concept for per-provider modules (README: Cloud Packs). Only the Azure
pack exists, and it is metadata-only: `packs/azure/` contains `pack.json` + `mcp-servers.json`
while its 3 skills live in root `skills/` mixed with 13 cloud-agnostic skills, and its agents
are referenced from the shared flat agent directories.

Related findings from the 2026-09-29 review:

- 19 agent files are byte-identical in `.github/agents/` and `com.github.copilot/agents/`
  with no declared canonical source (drift risk).
- `deployer.agent.md` is cloud-agnostic but claimed by the Azure pack; `azure-compliance-reviewer`
  is Azure-specific but lives in the core agent directories (blurry ownership).
- README promises a `packs/_template/` skeleton for new cloud packs — it does not exist.
  AWS/GCP packs are "Planned" with no mechanical path to add them.
- README acknowledges the flat `skills/` layout is a compatibility shim
  ("so current Agent Plugins clients discover them").

The design call: commit to packs as the unit of modularity without breaking existing
Agent Plugins / Copilot clients.

## Problem / Requirements

### Functional Requirements

- Each pack is self-contained: `pack.json`, `agents/`, `skills/`, `mcp-servers.json`
  under `packs/<name>/`.
- Adding a new cloud pack (AWS, GCP) is mechanical via a `packs/_template/` skeleton.
- Exactly one canonical source for every agent file; duplicates are generated, never edited.
- `pack.json` files validate against `schemas/cloud-pack.schema.json` in CI.

### Non-Functional Requirements

- Backward compatible: existing Agent Plugins installs (`skills/`, `com.github.copilot/agents/`,
  `.github/agents/` at root) keep working throughout the migration.
- No silent drift between duplicated agent directories.

### Constraints

- Agents are never merged/deployed by automation; all restructuring lands via human-reviewed PRs
  (harness operating principle).
- `schemas/cloud-pack.schema.json` currently requires `agents.deployer` and
  `cloud ∈ {azure, aws, gcp}` — the core pack does not fit this shape (see Open Questions).

## Design / Implementation

Chosen approach: **hybrid** — `packs/<name>/` becomes the single source of truth;
the root flat layout becomes a CI-assembled projection of the packs.

### Architecture

```
packs/
  _template/                 # skeleton for new cloud packs (pack.json, agents/, skills/, mcp-servers.json)
  core/
    pack.json                # cloud-agnostic agents + skills manifest
    agents/                  # 18 agents (all except azure-compliance-reviewer)
    skills/                  # 13 core skills
  azure/
    pack.json
    agents/                  # azure-compliance-reviewer (+ azure-specific deployer if it diverges)
    skills/                  # sdlc-azure-deployment, sdlc-cosmos-repository, sdlc-blob-storage
    mcp-servers.json
  aws/  (future)             # via _template
  gcp/  (future)             # via _template
```

Root `skills/`, `com.github.copilot/agents/`, `.github/agents/` are assembled by CI
from `packs/*/` (phase 3). Until then they remain checked in, with CI drift checks.

### Migration phases

**Phase 1 — contracts (no file moves):**
1. Declare `com.github.copilot/agents/` the canonical agent source (it is the documented
   Agent Plugins-compatible layout); add a CI job failing the PR when `.github/agents/`
   diverges.
2. Add `packs/_template/` skeleton.
3. Add CI validation of every `packs/*/pack.json` against `schemas/cloud-pack.schema.json`.
4. Add `packs/core/pack.json` manifest for the cloud-agnostic set.

**Phase 2 — physical separation:**
1. Move Azure-specific files into `packs/azure/{agents,skills}/`; update `pack.json`
   references to pack-relative paths.
2. Decide the `deployer` ownership: keep the generic deployer in core and let cloud packs
   reference or override it (schema already allows per-pack `agents.deployer`).

**Phase 3 — single source of truth:**
1. CI assembles the root flat layout from `packs/*/`; flat dirs become build artifacts.
2. AWS/GCP packs become copy-template + fill-in work.

### Azure Services

N/A — no runtime services in this decision.

### Data Model

N/A.

### API Endpoints

N/A.

## Alternatives Considered

### Alternative 1: Full physical separation, delete the flat layout

- **Pros:** Cleanest end state; one layout to maintain.
- **Cons:** Breaks every existing Agent Plugins install on upgrade; big-bang migration.
- **Rejected because:** backward compatibility is a hard constraint for a shipped 1.0.1 package.

### Alternative 2: Manifest-only (keep flat files, strengthen pack.json contracts)

- **Pros:** Minimal churn; clients untouched.
- **Cons:** Separation stays logical-only; the coupling that motivated this ADR
  (mixed skills dir, blurry agent ownership, duplication) remains.
- **Rejected because:** it does not resolve the drift/duplication problem, only documents it.

## Testing Strategy

- **Unit tests:** JSON-schema validation of `pack.json` files (CI).
- **Integration tests:** CI drift check (`.github/agents` vs canonical); CI assembly check
  (assembled flat layout matches checked-in flat layout) once phase 3 lands.
- **Manual testing:** install the plugin from the branch in VS Code / Copilot and verify
  agent + skill discovery is unchanged.

## RAI / Risk Considerations

- [x] Prompt injection risks assessed — N/A (packaging-only change, no prompt content changes).
- [x] Data privacy impact reviewed — none.
- [x] Bias considerations documented — N/A.

## SDLC Impact by Phase

| Phase | Impact |
|---|---|
| 1-2: Requirements & Design | This ADR |
| 3: Repo Structure & CI/CD | Phase 1 CI jobs (drift check, pack.json schema validation); phase 3 assembly job |
| 4: Implementation & Tests | Phase 2 file moves; `_template/` skeleton |
| 5: Documentation | README Cloud Packs section update (template exists, core pack documented) |
| 6: QA Activities | Canary specs unaffected (no agent/skill content changes in phase 1) |
| 7: RAI Review | N/A |
| 8-9: Release & Publish | Minor version bump when phase 3 lands (layout becomes generated) |

## Open Questions

- [ ] `schemas/cloud-pack.schema.json`: add `"core"` to the `cloud` enum, or make `cloud`
  optional / use a separate manifest shape for the core pack?
- [ ] Is generating `.github/agents/` from the canonical source acceptable to Copilot
  clients, or must both directories remain checked in during the transition?
- [ ] Phase 3 timing relative to AWS/GCP pack work — assemble first, or add AWS pack
  on the old layout?

## References

- README "Cloud Packs" section
- `schemas/cloud-pack.schema.json`
- `packs/azure/pack.json`
- Design discussion: 2026-09-29 pack-separation review (options A/B/C; hybrid selected)
