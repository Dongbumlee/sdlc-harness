# {{SystemName}} System

<!-- One line: what this system does and who it serves. The design
phase expands this stub into the full project README. -->

This repository is the **composition layer** of the system: no
service code lives here. It holds the pieces no single service
owns — the system map, the local composition, the contract
registry, the one CI definition every service calls, and the thin
system E2E suite.

## Layout

- `system.json` — the system map: every service, its port, health
  path, and owned datastore; every boundary and its pact. The
  source of truth the scaffolder and the checker both read.
- `docs/system-map.md` — the human view of the map.
- `docker-compose.yaml` — local development composition: brings
  up every service with its own environment and datastore.
- `services/` — one directory per service, each instantiated from
  its stack's api template (see `services/README.md` for the
  rules; a service may move to its own repository unchanged).
- `contracts/` — one pact per boundary, plus `CONTRACTS.md`: the
  compatibility policy (additive-only, N−1) and the can-i-deploy
  deploy gate.
- `.github/workflows/service-ci.yml` — **the one definition of
  service CI.** Every service calls it at a pinned ref; copied
  pipeline YAML is the failure mode this exists to prevent.
- `tools/system-e2e/` — the thin system smoke suite: validates the
  map and pacts (`--check`, what this repo's CI runs) and probes
  deployed services' health (the scheduled `system-e2e.yml`
  pipeline — never a per-service PR gate).

## The rules that make it a system

1. **Independent deployability.** No system-wide version, no
   lockstep releases; a change that needs two services deployed
   together means the boundary is wrong.
2. **Contracts before code at every boundary.** Consumer-driven
   pacts, broker-verified, with `can-i-deploy` gating deploys.
3. **A database per service.** Cross-service data flows through
   contracts; cross-service effects use the owning service's
   transactional outbox.
4. **Thin shared libraries only.** Wire types generated from the
   contracts, observability/resilience starters, test utilities —
   versioned like any library. No shared domain `commons`.

## Getting started

```bash
docker compose up --build          # the whole system, locally
python3 tools/system-e2e/system_e2e.py --map system.json --check
python3 tools/system-e2e/system_e2e.py --map system.json \
    --base items-api=http://localhost:8081 \
    --base catalog-api=http://localhost:8082
```

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability.

## Changelog

See [CHANGELOG.md](CHANGELOG.md). System releases are cut from
version tags (`vX.Y.Z`) and version the composition only — the
map, the contracts, and the E2E runner image.
