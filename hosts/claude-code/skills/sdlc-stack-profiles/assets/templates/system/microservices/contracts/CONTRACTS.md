# Inter-service contracts — the rules of every boundary

A boundary between two services is a **published contract**, not a
shared understanding. This directory holds one pact per boundary
declared in `system.json`; the system E2E checker fails when a
declared boundary has no pact file here.

## How contracts flow

1. The **consumer's** CI writes and publishes its pact to the Pact
   Broker. The pact in this directory is the shape of that file —
   the broker is the living registry; this copy documents the
   boundary in the system repository.
2. The **provider's** CI verifies itself against every consumer
   pact from the broker and publishes the verification result.
3. **Deploy gate:** no service deploys unless
   `pact-broker can-i-deploy --to-environment production` passes
   for its version — the consumer and provider versions that would
   meet in production must be a verified pair.

## Compatibility policy

- **Additive only within a version.** New optional fields and new
  endpoints are fine; removing or renaming a field, tightening a
  type, or changing a status code is breaking.
- **N−1 compatibility.** A provider supports the current and the
  previous consumer contract version, so consumers and providers
  deploy independently — a coordinated release is a defect.
- **Deprecation window.** A breaking change is announced in the
  system map and this file at least one release before it lands,
  with the removal version named.
- **Events follow the same rules.** An event schema is a contract
  like any other: versioned, additive within a version, verified
  before deploy.

## What is never shared

- **No shared database, no shared tables.** Each service owns its
  datastore (declared per service in `system.json`). Cross-service
  data flows through contracts; durable cross-service effects use
  the worker type's transactional outbox pattern in the owning
  service.
- **No fat shared `commons`.** Shared libraries are thin and
  versioned like any library: wire types generated from the
  contracts, client/resilience starters, test utilities. Domain
  logic in a shared library recreates the distributed monolith —
  services that cannot deploy independently.
