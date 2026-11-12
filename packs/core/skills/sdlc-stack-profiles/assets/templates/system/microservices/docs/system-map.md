# {{SystemName}} — system map

The human view of `system.json`. The JSON is the source of truth
(the E2E checker validates it; the scaffolder renders
`docker-compose.yaml` from the same list) — keep this page in sync
when the JSON changes.

## Services

| Service | Kind | Port | Owns |
| --- | --- | --- | --- |
| items-api | api | 8081 | items-db — its items and their storage |
| catalog-api | api | 8082 | catalog-db — its catalog views; reads items only through the items-api contract |

Each service is instantiated from its stack's api template under
`services/<name>/` (or lives in its own repository — the layout
rule is in the system README), deploys independently, and is built
by the one reusable workflow, `service-ci.yml`.

## Boundaries

| Boundary | Consumer | Provider | Contract |
| --- | --- | --- | --- |
| catalog-reads-items | catalog-api | items-api | `contracts/items-api.pact.json` |

Boundary rules — additive-only changes, N−1 compatibility,
can-i-deploy as the deploy gate, no shared tables, no fat shared
libraries — live in `contracts/CONTRACTS.md`.

## Cross-service behaviour

- Correlation IDs and tracing propagate across every boundary
  (each service template's observability baseline carries them).
- A service that needs another service's *effect*, not just its
  data, uses the worker type's transactional outbox in the owning
  service — never a distributed transaction, never a shared table.
- Independent deployability is part of done: if a change needs two
  services released together, the boundary is wrong — fix the
  contract, not the release calendar.
