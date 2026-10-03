---
name: sdlc-gcp-deployment
description: >-
  Create GCP infrastructure with Terraform using the google provider, deploy
  containerized APIs to Cloud Run (HTTPS, scale-to-zero) and long-running
  workers to Cloud Run Jobs, and manage deployment lifecycle. Use when writing
  Terraform configs, configuring Cloud Run services/jobs, setting up Pub/Sub
  queues, Secret Manager, Artifact Registry, or preparing deployments. Triggers
  on Terraform, Cloud Run, Pub/Sub, Secret Manager, Artifact Registry,
  infrastructure, or deployment requests. Never use raw REST/gcloud
  imperative commands for infrastructure — always declare it in Terraform.
version: "1.0"
author: sdlc-harness
user-invocable: false
---

# SDLC GCP Deployment — Terraform + Cloud Run + Cloud Run Jobs

## When to use

- Creating or updating Terraform configs (google provider)
- Deploying containerized HTTP APIs to Cloud Run
- Running background workers as Cloud Run Jobs
- Wiring Pub/Sub topics/subscriptions, Secret Manager, Artifact Registry, IAM
- Reviewing infrastructure-as-code for compliance
- Preparing environment promotion (dev → staging → production)

## Paved-road architecture

One Terraform root, two compute targets — this is the pack's core opinion:

```
             ┌──────────────────────┐
             │ Cloud Run service    │  HTTP API — same Artifact Registry repo
             │ (api, min 0)         │  as the worker ($0 idle: scale-to-zero);
             └──────────┬───────────┘  two tagged images, api-<tag>/worker-<tag>
                        │ publish message
             ┌──────────▼───────────┐      ┌──────────────┐
             │ Pub/Sub topic        ├─────►│ DLQ topic    │  poison messages,
             │ (jobs)               │      │              │  max_delivery_attempts
             └──────────┬───────────┘      └──────────────┘
                        │ API triggers one Job execution per message
          ┌─────────────▼──────────────┐
          │ Cloud Run Job              │  background worker (run-to-completion,
          │ (worker)                   │  up to 25 min per deep-research job)
          └─────────────┬──────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   Firestore       Cloud Storage   Secret Manager
   (one design)    (private only)  (LLM + search API keys)
```

**Why this split:** Cloud Run services are request-driven (max 60 min per
request, but billed per request) — the API scales to zero and costs $0 idle.
The worker (planner → researchers → critic → writer pipeline, up to 25 min/job)
is run-to-completion batch work, which is exactly what Cloud Run Jobs is for.
Pub/Sub sits between them as the durable work queue: the API publishes one
message per job and triggers a Job execution; the Job pulls the message,
processes it, and acks. Poison messages exhaust `max_delivery_attempts` and
land on the DLQ topic instead of retrying forever.

**No VPC needed for v1.** Cloud Run and Cloud Run Jobs reach Google APIs
(Firestore, Pub/Sub, Storage, Secret Manager) over the internet without a VPC
connector. Do not add Serverless VPC Access or Private Service Connect unless
a compliance requirement says so — each adds idle cost for zero v1 benefit.

**Scale-up path:** when the API outgrows a single Cloud Run service (traffic
needing min-instances, websockets/SSE fan-out), raise `min_instance_count`
or split the worker trigger into Eventarc — same image contract (one Artifact
Registry repo, `api-`/`worker-` tags), same Pub/Sub contract, no API redesign.

## Step 1: Terraform layout

```
infra/
├── main.tf               # provider, terraform block, GCS backend, locals
├── variables.tf          # project_id, region (default us-west1), image_tag
├── artifact_registry.tf  # Docker repo (created FIRST — see image pipeline)
├── secrets.tf            # Secret Manager secrets (values added post-deploy)
├── firestore.tf          # database + TTL + composite indexes
├── storage.tf            # private GCS bucket + lifecycle
├── pubsub.tf             # topic, subscription (+DLQ), ack deadline
├── cloudrun.tf           # API service, worker job, IAM bindings
└── outputs.tf            # api_url, bucket name, topic names
```

Conventions:
- Terraform >= 1.9, `hashicorp/google` provider `~> 6.x` (pin minor).
- Remote state in a GCS bucket (`terraform { backend "gcs" {} }`) — never
  local state for shared work.
- Default region `us-west1` (v1); make it a variable, not hardcoded.
- Standard labels on all resources: `project`, `environment`, `managed-by=terraform`.

## Step 2: The image pipeline — registry BEFORE images, images BEFORE deploy

**⛔ NEVER reference an image tag that has not been pushed yet.**
Container image references in Terraform are resolved at apply time — if the
image does not exist in Artifact Registry, the Cloud Run deployment fails.

The order is fixed:

```
1. terraform apply -target=google_artifact_registry_repository.images
   (or apply the whole infra minus cloudrun.tf on first run)
2. docker buildx build --platform linux/amd64 -t <repo>/api:<tag> ./src/api
   docker buildx build --platform linux/amd64 -t <repo>/worker:<tag> ./src/worker
   docker push <repo>/api:<tag> && docker push <repo>/worker:<tag>
3. terraform apply -var image_tag=<tag>     # full deploy, images now exist
```

- Tag images by git SHA (`api-<sha>`, `worker-<sha>`), never redeploy `:latest`
  and assume it moved. The `image_tag` variable carries the SHA.
- **Architecture MUST match the image** — build `linux/amd64` and set the
  Cloud Run execution environment accordingly. Add a CI check
  (`docker inspect --format '{{.Architecture}}'`) — the pack does not trust
  humans to remember this.
- **One `image_tag` variable means TWO images.** The paved road tags images
  as `api-<tag>` / `worker-<tag>` off a single `var.image_tag` — both images
  must be built and pushed with that tag before `terraform apply`, or one
  target deploys a revision that never starts (real-deploy finding
  2026-10-03). CI should check both tags exist in Artifact Registry
  before apply.

### Dockerfile rules (non-root + gunicorn)

```dockerfile
FROM --platform=linux/amd64 python:3.12-slim

# World-readable source: container runtimes run as non-root and must be able
# to read the code. Capital X = +x on directories ONLY (traversal), so a
# non-root user can stat/read files inside. Plain `a+r` is NOT enough —
# directories need +x for traversal (real-deploy bug 2026-10-03:
# ModuleNotFoundError despite correct PYTHONPATH).
COPY src/ /app/src/
RUN chmod -R a+rX /app && useradd -m appuser
WORKDIR /app/src
# gunicorn does not reliably add cwd to sys.path — set PYTHONPATH explicitly
# (real-deploy bug 2026-10-03: ModuleNotFoundError: No module named 'api.app').
ENV PYTHONPATH=/app/src
RUN pip install --no-cache-dir -r /app/src/api/requirements.txt

USER appuser
ENV PORT=8080
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "api.app:create_app()"]
```

Rules:
- **Always `chmod -R a+rX`, never `a+r`** when the image runs as non-root.
- **Always `ENV PYTHONPATH`** for gunicorn/WSGI entrypoints — never assume
  the working directory is on `sys.path`.

## Step 3: IAM — least privilege via google_*_iam_member, one SA per target

**⛔ NEVER use primitive roles (`roles/owner`, `roles/editor`) and NEVER
hand-write IAM policy JSON when a purpose-built binding exists.**

```hcl
# ✅ CORRECT: one service account per compute target, least-privilege roles
resource "google_service_account" "api" { account_id = "deep-research-api" }
resource "google_service_account" "worker" { account_id = "deep-research-worker" }

resource "google_project_iam_member" "worker_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"      # Firestore read/write, no admin
  member  = "serviceAccount:${google_service_account.worker.email}"
}
```

Rules:
- One service account per compute target (API SA, worker SA) — never a shared
  god-identity.
- Workload identity / attached SAs for GCP API access from containers. If you
  see a service-account JSON key in code, env files, or images, that is a
  critical finding.
- Secret access: `roles/secretmanager.secretAccessor` on each secret,
  per-service-account — never project-wide.
- **API → Cloud Run Jobs trigger (verified 2026-10-03):** the API SA gets
  `roles/run.developer` scoped to the worker job to call the Run API
  (`run.projects.locations.jobs.run`). No extra `iam.serviceAccount.actAs`
  binding was needed in the slice.

```hcl
# ✅ CORRECT: API SA can trigger the worker job (verified at real deploy)
resource "google_cloud_run_v2_job_iam_member" "api_triggers_worker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.worker.name
  role     = "roles/run.developer"
  member   = "serviceAccount:${google_service_account.api.email}"
}
```

## Step 4: Secrets — Secret Manager, mounted by Cloud Run at runtime

All secrets (LLM API key, search API key, API keys list) live in Secret
Manager and are mounted as environment variables by Cloud Run — never
plaintext, never baked into the image, never in Terraform variables or state:

```hcl
# ✅ CORRECT: secret referenced, value never in config
resource "google_cloud_run_v2_service" "api" {
  # ...
  template {
    containers {
      # ...
      env {
        name = "LLM_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.llm_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }
}
```

Secret *values* are added post-deploy (`gcloud secrets versions add`) or via
CI — Terraform creates the secret containers only. Values in `.tfvars` or
`terraform.tfstate` are a critical finding.

**Name vs value — pick the right one (real-deploy bug 2026-10-03):**
`value_source.secret_key_ref` injects the secret **value** into the env var.
If the app constructs the secret resource path from the **name** itself
(e.g. builds `projects/<p>/secrets/<name>/versions/latest` in code), pass the
name as a plain value instead:

```hcl
# ✅ CORRECT when the app expects the NAME and builds the path itself
env {
  name  = "API_KEYS_SECRET_NAME"
  value = google_secret_manager_secret.api_keys.secret_id
}

# ❌ WRONG here: this injects the VALUE, and the app chokes building a
#    resource path out of it ("Secret ID ... does not match format")
env {
  name = "API_KEYS_SECRET_NAME"
  value_source { secret_key_ref {
    secret  = google_secret_manager_secret.api_keys.secret_id
    version = "latest"
  } }
}
```

Rule: read the app's expectation first. App reads by name → plain `value`
with the secret ID. App reads the env var as the secret itself →
`value_source.secret_key_ref`.

## Step 5: Pub/Sub queue contract

```hcl
resource "google_pubsub_topic" "jobs" { name = "jobs" }
resource "google_pubsub_topic" "jobs_dlq" { name = "jobs-dlq" }

resource "google_pubsub_subscription" "jobs_worker" {
  name  = "jobs-worker"
  topic = google_pubsub_topic.jobs.name

  # Ack deadline MUST exceed the longest single pull-process cycle of the
  # worker, or messages redeliver mid-processing. Formula:
  #   ack_deadline = max_job_seconds + polling_skew
  # Example: 25-min jobs -> 1800s (600s is the max; use 600 and extend
  # the deadline from the worker if a job runs longer).
  ack_deadline_seconds = 600

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.jobs_dlq.id
    max_delivery_attempts = 5
  }
  retry_policy { minimum_backoff = "10s" }

  # Message retention caps storage cost of an idle backlog.
  message_retention_duration = "86400s"  # 24h
}
```

Rules:
- Every work topic gets a DLQ topic — no exceptions.
- The worker extends the ack deadline (`modify_ack_deadline`) while a long
  job runs; a job that crashes without ack redelivers (at-least-once).
- Terminal outcomes (done/failed/cancelled) ack the message. A failed job is
  not new work — do not let it redeliver as if it were.

**Worker pull pattern — `timeout` is a method argument, not a request field**
(real-deploy bug 2026-10-03: `ValueError: Unknown field for PullRequest:
timeout` crashed the worker):

```python
# ✅ CORRECT
resp = subscriber.pull(
    request={"subscription": sub_path, "max_messages": 1},
    timeout=20,
)

# ❌ WRONG: timeout inside the request dict
resp = subscriber.pull(
    request={"subscription": sub_path, "max_messages": 1, "timeout": 20}
)
```

## Step 6: Cost guardrails (enforced, not advisory)

- **Cloud Run services scale to zero by default** — keep `min_instance_count = 0`
  and say so explicitly. Never claim "$0 at test scale" for anything with a
  nonzero minimum.
- **No VPC connector, no load balancer, no NAT** for v1 — serverless egress to
  Google APIs is free and needs no network plumbing.
- **Cloud Run Jobs** cost only while executing. The worker has no idle cost
  because there is no always-on worker to idle.
- **Cloud Storage lifecycle**: reports expire (e.g. 90 days). Forgotten objects
  with no lifecycle are a classic money leak.
- **Firestore TTL**: ephemeral docs (rate counters, findings) self-expire via
  a TTL field — no cleanup cron.
- Run `checkov` or `tfsec` on every Terraform root; suppressions require a
  written justification.

**Free-tier honesty (not "$0" hand-waving):** at test scale the slice sits
inside GCP's free tier — Cloud Run (2M requests + 360k GB-s/mo), Firestore
(1 GiB + 50k reads/day), Pub/Sub (10 GB/mo), Cloud Storage (5 GB-mo),
Secret Manager (6 active versions), Artifact Registry (0.5 GB). Anything
beyond that burns trial credits; say which, per service.

## Step 7: Offline fallback

If the Google Cloud docs MCP server (or any MCP server) is unavailable in the
environment, do not block the build — proceed from provider knowledge plus
this skill, and note the limitation in the build log. The pack's guidance
must stand on its own; MCP servers are accelerators, not prerequisites.

## Gotchas

- **Cloud Run Jobs ≠ Pub/Sub push target.** Jobs are triggered via the Run
  API (or Scheduler/Eventarc). The paved road is: API publishes to Pub/Sub
  *and* triggers one Job execution per message — the queue is the durable
  record + DLQ story, not the trigger.
- **Signed URLs need signing permission — on the SA itself.** The signer
  needs `iam.serviceAccounts.signBlob` on the runtime service account, granted
  via `google_service_account_iam_member` where the member is the SA's own
  email (self-impersonation). Do NOT grant `roles/iam.serviceAccountTokenCreator`
  on the bucket via `google_storage_bucket_iam_member` — that fails with
  Error 400 (real-deploy finding 2026-10-03). Test signed-URL generation in
  the deployed environment, not just locally.
- **Cloud Run Jobs block destroy by default.** The provider defaults
  `deletion_protection = true`, which blocks `terraform destroy` and job
  replacement on config change. Test slices must set
  `deletion_protection = false` on the job; production keeps it true and
  replaces explicitly.
- **A Job in error state needs a force update to clear.** New executions use
  the job template captured at creation time — if a bad template went out,
  update the job (or destroy/recreate) before re-triggering; re-running the
  same execution reuses the broken template.
- **`gcloud builds submit` has no `--dockerfile` flag.** To build with a
  non-default Dockerfile, pass a `--config cloudbuild.yaml` whose build step
  uses `args: ["build", "-f", "path/to/Dockerfile", ...]` — and watch the
  context path: the `-f` path is relative to the build context you submit.
- **GCS buckets block destroy when non-empty.** Either set
  `force_destroy = true` on test buckets or empty them before
  `terraform destroy` — otherwise destroy fails partway and leaves a stale
  state lock (force-unlock with `terraform force-unlock`, then re-run).
- **Firestore composite indexes** are required for `where(status) +
  orderBy(createdAt)` listings — declare them in Terraform
  (`google_firestore_index`), never click them into existence in the console.
- **Artifact Registry repo must exist before `docker push`** — same
  chicken-and-egg as ECR (AWS lesson). Terraform creates the repo; the
  pipeline pushes; then the full apply runs.
- **Secret values in state** — `terraform plan` output and `.tfstate` must
  never contain secret values. Create secret containers in Terraform; add
  versions via `gcloud` or CI.
- **`terraform apply -auto-approve` in CI** is convenient and dangerous —
  keep manual approval for IAM-changing applies.

## Where files go

| Artifact | Location |
|---|---|
| Terraform root | `infra/` |
| Per-concern configs | `infra/*.tf` |
| Container images | Artifact Registry (created by Terraform) |
| API service code | `src/<Name>API/` (Flask/WSGI) |
| Worker job code | `src/<Name>Worker/` (run-to-completion entrypoint) |
