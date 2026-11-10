# Design Document: [Feature / Component Name]

> **SDLC Phase:** 2 (Design)
> **Date:** YYYY-MM-DD
> **Author:** [Name or @Harness → Analyst agent]

---

## Overview

<!-- One paragraph summary of what this designs -->

## Goals

1. 
2. 
3. 

## Non-Goals

- 

## Architecture

<!-- High-level architecture diagram (mermaid or text) -->

```mermaid
flowchart TD
    A[Component A] --> B[Component B]
```

## Detailed Design

### Component 1: [Name]

**Responsibility:**

**Pattern:** (e.g., Repository Pattern via `the approved Cosmos DB library`)

**Key interfaces:**

```python
# Example interface
```

### Component 2: [Name]

**Responsibility:**

**Pattern:**

## Data Model

### Entities

| Entity | Base Class | Key Type | Container |
|---|---|---|---|
| | (base class from the project's data library, if it defines one) | `str` | |

### Relationships

## Platform Services

<!-- The services THIS design uses, on the project's own cloud — example
     rows below are one Azure project's; replace them. -->

| Service | Library | Configuration |
|---|---|---|
| (e.g., Cosmos DB) | (e.g., `the approved Cosmos DB library`) | |
| (e.g., Blob Storage) | (e.g., `the approved Storage library`) | |

## Error Handling & Logging

- 

## Security Considerations

- [ ] Authentication method defined
- [ ] Authorization model specified
- [ ] Data encryption at rest and in transit
- [ ] Secrets management via the cloud's secret manager

## Testing Approach

| Test Type | Scope | Framework |
|---|---|---|
| Unit | Service logic | (the stack profile's test framework — e.g., pytest) |
| Integration | API endpoints | (the stack profile's HTTP test tooling) |
| E2E | Full flow | Playwright (if applicable) |

## Dependencies

| Dependency | Version | Source |
|---|---|---|
| (the project's approved data libraries) | | Reference catalog |

## Open Questions

- [ ] 
