---
name: sdlc-adr-authoring
description: >-
  Create Architecture Decision Records following SDLC standards and application templates.
  Use when documenting design decisions, architecture choices, or technology
  selections. Triggers on ADR, architecture decision, design proposal, or
  design document requests. Combines awesome-copilot ADR skill with SDLC-specific
  ADR template from .design/ADR-TEMPLATE.md.
---

# ADR Authoring — SDLC Phase 5

Create Architecture Decision Records that satisfy SDLC Phase 5 exit criteria.

## Step 1: Load ADR best practices

Load the generic ADR creation skill from awesome-copilot:

```
mcp_awesome-copil_load_instruction(
  filename: "create-architectural-decision-record/SKILL.md",
  mode: "skills"
)
```

Then read the project's ADR template for SDLC-specific format:

```
Read file: .design/ADR-TEMPLATE.md
```

**The SDLC template takes precedence** over the awesome-copilot format when they differ.

## Step 2: Assign the next ADR number

Check existing files in `docs/adr/` and assign the next sequential number:

```
List directory: docs/adr/
```

Convention: `ADR-XXX-<topic-slug>.md` (e.g., `ADR-001-cosmos-db-for-order-data.md`)

## Step 3: Write the ADR

Follow the SDLC ADR template structure (from `.design/ADR-TEMPLATE.md`):

```markdown
# ADR-XXX: <Title>

## Metadata
- **Status:** Proposed | Accepted | Deprecated | Superseded
- **SDLC Phase:** Phase 2 — Design
- **Date:** YYYY-MM-DD
- **Author:** <author>

## Context
What prompted this decision? Business need, technical constraint, or opportunity.

## Problem / Requirements
### Functional Requirements
- FR-1: ...

### Non-Functional Requirements
- NFR-1: ...

### Constraints
- ...

## Design / Implementation
### Architecture
High-level description of the chosen approach.

### Azure Services
| Service | Library | Purpose |
|---|---|---|
| Cosmos DB | the approved Cosmos DB library | Order data storage |
| Blob Storage | the approved Storage library | Invoice PDF storage |

### Data Model
| Entity | Base Class | Key Type | Container |
|---|---|---|---|
| Order | RootEntityBase["Order", str] | str | orders |

### API Endpoints (if applicable)
| Method | Path | Description |
|---|---|---|
| POST | /api/v1/orders | Create order |

## Alternatives Considered
### Alternative 1: <Name>
- **Description:** ...
- **Pros:** ...
- **Cons:** ...
- **Rejected because:** ...

## Testing Strategy
- **Unit:** pytest with mocked repositories
- **Integration:** HTTP-level API tests
- **E2E:** Playwright (if applicable)

## RAI / Risk Considerations
- [ ] Prompt injection risks assessed (if LLM involved)
- [ ] Data privacy evaluated
- [ ] Bias assessment completed (if AI involved)

## SDLC Impact by Phase
| Phase | Impact |
|---|---|
| 3 (Scaffolding) | New container config in Cosmos DB Bicep module |
| 4 (Implementation) | New entity + repository + API route |
| 5 (Documentation) | This ADR + API docs |

## Open Questions
- OQ-1: ...

## References
- [Reference Catalog](/.github/reference-catalog.md)
```

## Step 4: Validate the ADR

Before saving, verify:

- [ ] Status is set to "Proposed" for new decisions
- [ ] Azure services use approved libraries from reference catalog
- [ ] No placeholder text remains
- [ ] Entity definitions use `RootEntityBase` (not raw Pydantic)
- [ ] At least one alternative is documented with rejection rationale
- [ ] Testing strategy specifies frameworks (pytest, Vitest, Playwright)
- [ ] SDLC Impact table maps to specific phases

## Step 5: Save and link

1. Save to `docs/adr/ADR-XXX-<topic>.md`
2. If a README index exists in `docs/adr/`, update it
3. If this ADR results from an Analyst design proposal, carry forward all technical
   details — do not summarize or lose specificity

## Gotchas

- **Always use the SDLC template from `.design/ADR-TEMPLATE.md`** — the awesome-copilot
  ADR format is a useful reference but our template has SDLC-specific sections
  (SDLC Impact, RAI Considerations) that are mandatory.
- **Azure services table must specify the library** (the approved Cosmos DB library, the approved Storage library) —
  not just the service name.
- **Data model entities must specify `RootEntityBase` base class** — this ensures
  the Implementer knows the exact pattern to follow.
- **Status "Proposed"** means it needs team review; "Accepted" means approved to implement.

## Where files go

| Artifact | Location |
|---|---|
| ADR document | `docs/adr/ADR-XXX-<topic>.md` |
| ADR template | `.design/ADR-TEMPLATE.md` (read-only reference) |
