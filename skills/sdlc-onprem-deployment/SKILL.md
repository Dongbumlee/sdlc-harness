---
name: sdlc-onprem-deployment
description: >-
  Deploy to on-premises infrastructure the project owns: Kubernetes
  clusters, container hosts, or VMs. Use when the recorded deployment
  target is on-premises — manifests, Helm, Compose, or host scripts
  through the terminal, with the project's own recorded deploy path.
  Triggers on on-premises, bare metal, self-hosted, Kubernetes, Helm,
  or Compose deployment requests.
version: "1.0"
author: sdlc-harness
user-invocable: false
---

# SDLC On-Premises Deployment — Recorded Path, Project Tooling

## When to use

- The manifest's recorded deployment target is on-premises
- Writing or updating Kubernetes manifests, Helm charts, or Compose files
- Preparing host-level deployments (systemd services, install scripts)
- Setting up environment promotion across the project's own environments
- Reviewing an on-premises deployment for operational compliance

There is **no cloud control plane and no cloud MCP server** for this
target. Everything runs through the terminal and the tooling the project
already owns. What a cloud would provide by default — identity, secrets,
logging, patching, backup — the deployment must provide explicitly; that
is what most of this skill is about.

## Paved-road shapes (pick the one the project already runs)

| Shape | When | Deploy path |
|---|---|---|
| **Kubernetes** (self-managed or managed-on-prem distribution) | The project already operates a cluster | `kubectl apply -k <env>` or `helm upgrade --install` with per-environment values |
| **Compose on a host** | One or a few hosts, containerized services | `docker compose -f compose.yaml -f compose.<env>.yaml up -d` |
| **VM / bare-metal services** | Non-containerized workloads | The recorded install/upgrade script + systemd units in the repo |

Do not introduce a new shape to a project that already runs one. The
manifest records the shape and the deploy path; both are the contract.

## Step 1: Record the deploy path before deploying anything

The manifest's recorded deploy path names: the shape, the exact commands,
the target hosts/cluster, the configuration source per environment, and
the rollback procedure. If any of these is missing, record it first —
an unrecorded path is tribal knowledge, and tribal knowledge does not
survive the operator's vacation.

## Step 2: Images come from a registry the project controls

- Push images to the project's own registry (self-hosted registry,
  Harbor, or the cluster's internal registry) **before** the deploy
  step references them — the registry-before-images order is the same
  chicken-and-egg rule as the cloud packs.
- Tag images immutably (commit SHA or version), never `latest` — rollback
  is "redeploy the previous tag," which only works if tags are stable.
- Hosts pull by digest or tag from the internal registry; no building
  images on production hosts.

## Step 3: Configuration and secrets

- Configuration per environment lives in the repo as manifests, values
  files, or env templates — parameterized by host names, ports, and
  paths; nothing environment-specific is baked into images.
- Secrets live in a real store: Vault, SOPS/age-encrypted files in the
  repo, or the platform's sealed-secrets mechanism. File permissions
  `0600`, owned by the service account. **Never** plaintext secrets in
  the repo, in images, or in world-readable env files.
- External dependency URLs and endpoints are env-overridable — a
  hardcoded address makes failover and failure drills impossible.

## Step 4: Health, logging, and rollback are part of the deploy

- Every service exposes the health/readiness probes its shape supports
  (Kubernetes probes, Compose healthchecks, a `/health` endpoint behind
  the service manager) and the deploy verifies them before reporting
  success — a started process is not a healthy service.
- Logs go to the recorded surface: the cluster's log stack, journald with
  forwarding, or files with rotation and retention configured. A service
  whose logs die with its host is unobservable.
- Rollback = run the recorded procedure (previous image tag, previous
  manifest revision, previous release). Test it in the lowest
  environment before the first production deploy.

## Infrastructure rules

- **Idempotent deploys** — running the deploy path twice produces the
  same state; scripts check before they mutate.
- **One recorded entry point** — ingress (Kubernetes Ingress, a reverse
  proxy, or the load balancer the project owns) is the only public
  surface; data services are never directly exposed.
- **Time sync everywhere** — NTP on every host; TLS validation and log
  correlation silently break without it.
- **Patch cadence is recorded** — OS patching runs on the recorded
  schedule via the recorded mechanism; the deploy does not assume hosts
  are current, it checks the recorded patch state.
- **Backups before destructive steps** — any deploy step that migrates
  or mutates state runs after the recorded backup for that data exists.

## Gotchas

- **Certificate renewal is the classic on-prem outage** — certificates
  from the internal CA or ACME with automated renewal and expiry
  alerting; a hand-renewed certificate is a scheduled incident.
- **`kubectl apply` without a namespace discipline** — always deploy
  into the project's recorded namespace; the default namespace is how
  environments collide.
- **Compose `depends_on` is not readiness** — pair it with healthchecks
  and `condition: service_healthy`, or services race their dependencies
  on every host reboot.
- **Host firewalls drift** — firewall rules belong in the recorded
  configuration tooling, not in commands an operator ran once.
- **The deploy host is a single point of knowledge** — if the deploy
  only works from one operator's machine, the deploy path is not
  recorded well enough. It must run from a clean checkout.

## Infrastructure quality checklist (self-evaluation)

Run this on top of the Deployer's generic self-review before
reporting on-premises infrastructure as complete:

1. **Recorded path completeness** — Does the manifest record the
   shape, commands, targets, configuration source, and rollback?
2. **Repeatability** — Would the deploy path succeed from a clean
   checkout on a freshly provisioned host/cluster of the recorded
   shape?
3. **No hardcoded values** — Host names, IPs, ports, paths, and
   secrets all parameterized or in the secret store?
4. **Image discipline** — Immutable tags, internal registry,
   registry-before-images order respected?
5. **Health verified** — Probes/healthchecks defined and checked by
   the deploy before success is reported?
6. **Observability** — Logs reach the recorded surface with rotation
   or forwarding; a dead host is noticed without a user report?
7. **Secrets** — In the store, `0600`, referenced — never plaintext
   in repo, images, or env files?
8. **Rollback tested** — The recorded rollback procedure has run at
   least once in the lowest environment?

## Exit criteria (on-premises targets)

Include these rows in the Deployer's SDLC Exit Criteria Check for an
on-premises target:

- Deployment runs the recorded deploy path (shape + commands in the manifest): ✅/⚠️/⛔
- Images in the project's registry with immutable tags: ✅/⚠️/⛔
- Secrets in the store with restricted permissions (no plaintext): ✅/⚠️/⛔
- Health checks defined and verified by the deploy: ✅/⚠️/⛔
- Logs reach the recorded surface (rotation/forwarding configured): ✅/⚠️/⛔
- Rollback procedure documented and tested in the lowest environment: ✅/⚠️/⛔

## Where files go

| Artifact | Location |
|---|---|
| Kubernetes manifests / overlays | `infra/k8s/` |
| Helm chart / values | `infra/chart/`, `infra/values-<env>.yaml` |
| Compose files | `infra/compose.yaml`, `infra/compose.<env>.yaml` |
| Host install/upgrade scripts | `infra/scripts/` |
| systemd units | `infra/systemd/` |
| API service code | `src/<Name>API/` |
| Worker service code | `src/<Name>Worker/` |
