# Quick Reference

The numbers and rules people look up most, on one page. This page
**restates** the canonical standard — where this page and
[Base Definitions](base-definitions.md) disagree, Base Definitions wins.

## QA panel — scores and thresholds

Canon: [§4](base-definitions.md#4-severity--one-scale-explicit-translations)

| Domain | Pass bar |
|---|---|
| Security | ≥ 8 |
| Every other domain | ≥ 7 |
| Composite | ≥ 7 |

Composite = `(security × 1.5 + sum of other active domains) / (1.5 + active domains)` —
the denominator follows the active panel; 9.5 is only the full-panel value.

The verdict is ⛔ (CRITICAL_FAIL) when **any** of these holds:

1. Any reviewer returns CRITICAL_FAIL.
2. Security score < 8.
3. Any domain score < 5.
4. Composite < 7.
5. Any Critical finding exists.
6. Two or more Important findings within a single reviewer domain.

## Rounds and escalation

Canon: [§6](base-definitions.md#6-rounds-convergence-and-escalation)

| Cap | Small | Medium | Large |
|---|---|---|---|
| Phase 6 QA rounds | 2 | 3 | 3 |
| Phase-exit fix loops | 1 full + 1 delta | 2 | 3 |

On a FAIL verdict the escalation runs: **tier 1** auto-route the fixes and
re-review the failed domains only (tier 1 requires at least one Critical
or Important finding — a fail on composite alone goes straight to the
user) → **tier 2** retry with the user's confirmation → **tier 3** the
user decides (override, manual fix, or abandon). A CRITICAL_FAIL stops the run for a user decision immediately.
Suggestions never consume a round.

## Pit-stops — when a run stops itself

Canon: [§7](base-definitions.md#7-pit-stop-counting-failure-ledger)

The Harness counts failures in `.SDLC/failure-ledger.md` at every phase
transition. A pit-stop review runs before the next phase when:

- **T1** — the same failure signature reaches its 3rd line
- **T2** — the same rework reason-class reaches its 2nd line
- **T3** — a claim is contradicted by what is on disk
- **T4** — no progress (no artifact change for ~30 minutes)
- **T5** — a delegation signature would be issued a 3rd time

At most **3 pit-stop reviews per run**; at the cap the run stops and the
evidence goes to the user.

## Run envelopes

Canon: [§8](base-definitions.md#8-records-and-contracts)

| Grade | Spend | Active run time |
|---|---|---|
| Small | ≤ $20 | ≤ 4 hours |
| Medium | ≤ $75 | ≤ 2 days |
| Large | ≤ $250 | ≤ 5 days |

Operational defaults, set at intake — the user may set a different
envelope for a run, and the recorded value is the run's.

## Records a run leaves behind

Canon: [§8](base-definitions.md#8-records-and-contracts)

| Record | Where |
|---|---|
| Project manifest | `.SDLC/project-manifest.md` |
| Design brief | `.SDLC/design-brief.md` |
| Failure ledger | `.SDLC/failure-ledger.md` |
| Pattern register | `.SDLC/pattern-register.md` |
| Run guidance | `.SDLC/run-guidance.md` |
| Reference catalog | `.github/reference-catalog.md` |
| Requirements spec (REQ) | project docs, from the Analyst |
| ADR set + index | `docs/adr/` |
| Design proposal | `.SDLC/design-proposal-<topic>.md` |
| QA evidence pack | `.SDLC/qa-evidence/` |
| Run retrospective | `.SDLC/run-retrospective.md` |
| Run tracking Issue | GitHub — one per run, labelled `sdlc:run` |

## Phases and their agents

Canon: [§2](base-definitions.md#2-phase-model) ·
[§3](base-definitions.md#3-exit-definitions--one-per-phase)

| Phase | Agent |
|---|---|
| 1 Requirements | Analyst (Discovery + Spec modes) |
| 2 Design | Analyst (Design mode) |
| 3 Repo structure & CI/CD | Scaffolder |
| 3 + 8 Deployment & infrastructure | Deployer |
| 4 Implementation & tests | Implementer |
| 5 Documentation | Documenter |
| 6 QA activities | QA Coordinator |
| 7 RAI review | RAI Reviewer |
| 8–9 Release & publish | Release Manager |

## The package, in numbers

22 agents · 25 skills · 30 bundled templates · 57 canary specs ·
6 prompt files · 3 core MCP servers (GitHub, Context7, Playwright) plus
the vendor servers in your cloud pack. Full generated listing:
[Agent Inventory](agent-inventory.md).
