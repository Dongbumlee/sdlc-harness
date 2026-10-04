---
name: sdlc-firestore-repository
description: >-
  Implement Firestore data access with an explicit collection design and the
  Repository Pattern over the google-cloud-firestore client. Use when creating
  collections, repositories, document layouts, or any Firestore CRUD
  operations. Triggers on Firestore, database, collection, document, data
  model, or data access requests. Never substitute client-side filtering for
  document/index design — always model access patterns as documents,
  subcollections, and composite indexes first.
version: "1.0"
author: sdlc-harness
user-invocable: false
---

# GCP Firestore — Explicit Collection Design with Repository Pattern

## When to use

- Designing a Firestore layout for a new domain (design comes first)
- Adding CRUD operations for any domain object
- Implementing queries, filtering, or pagination against Firestore
- Reviewing code that accesses Firestore

## Step 1: List access patterns BEFORE designing documents

Write down every query the application needs, then design documents to serve
them. Document layout is designed from queries — never the reverse.

The table below is the pack's **reference collection design** — the canonical
starting point every Firestore layout in this pack derives from. Adapt the
document IDs to your domain; keep the one-collection-per-aggregate +
subcollection shape.

Example (research-job domain), collection `jobs`:

| # | Access pattern | Document design |
|---|---|---|
| 1 | Get job by ID | `jobs/{jobId}` — fields: status, topic, depth, progress{}, budget{}, timestamps |
| 2 | Get job with findings + report | `jobs/{jobId}` + subcollection `findings/{findingId}` (2 reads, no join needed) |
| 3 | List jobs by status, newest first | Query `jobs` where `status == X` orderBy `createdAt` desc — **requires composite index** (declare in Terraform) |
| 4 | Get single finding | `jobs/{jobId}/findings/{findingId}` |
| 5 | Rate-limit counter per key+hour | `rate_limits/{apiKey}_{hour}` with `used` counter + TTL field |

**Rules:**
- If an access pattern has no document design, it does not exist — go back
  and design it. Client-side filtering over a full collection read is not a fix.
- **Status listings use a composite index** (`status ASC, createdAt DESC`) —
  declared in Terraform (`google_firestore_index`), never clicked into the
  console. A missing index fails at runtime, not at deploy time: test the
  listing path.
- **Subcollections for one-to-many** (findings belong to a job) — never arrays
  that grow unbounded, never a second top-level collection joined by hand.

## Step 2: Define the database (Terraform)

```hcl
resource "google_firestore_database" "db" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region          # multi-region only with justification
  type        = "FIRESTORE_NATIVE"
}

# TTL for ephemeral documents (rate counters, findings) — no cleanup cron.
resource "google_firestore_field" "rate_ttl" {
  project    = var.project_id
  database   = google_firestore_database.db.name
  collection = "rate_limits"
  field      = "expires_at"
  ttl_config {}
}

# Composite index for status listings (Step 1, pattern 3).
resource "google_firestore_index" "jobs_by_status" {
  project    = var.project_id
  database   = google_firestore_database.db.name
  collection = "jobs"
  fields {
    field_path = "status"
    order      = "ASCENDING"
  }
  fields {
    field_path = "createdAt"
    order      = "DESCENDING"
  }
}
```

**`location_id` is immutable.** Changing regions later cannot update the
database in place — the procedure is `gcloud firestore databases delete`,
wait for full deletion, then `terraform apply` recreates it in the new
region (scenario 2+3 finding 2026-10-03).

**The pack owns the database.** Never assume a `(default)` database
exists — declare `google_firestore_database` in Terraform (or list it as
an explicit runbook prerequisite). The Pulse slice assumed it and the real
deploy needed a manual `gcloud firestore databases create` (2026-10-04).

**`terraform destroy` does not delete the database.** The provider reports
"Destruction complete" while the database still exists (scenario 2+3
finding 2026-10-03). Delete explicitly —
`gcloud firestore databases delete --quiet` — and verify with
`gcloud firestore databases list`. Never trust destroy output for this
resource.

**Billing rule:** Firestore Native with the free tier (1 GiB + 50k
reads/day) covers test scale. Spiky AI workloads stay on the default
pay-per-use — no provisioned capacity to tune.

## Step 3: Define repositories

One repository per aggregate, wrapping `google-cloud-firestore` — never raw
client calls scattered through business logic:

```python
from google.cloud import firestore

class JobRepository:
    def __init__(self, db: firestore.Client):
        self._col = db.collection("jobs")

    def get(self, job_id: str) -> dict | None:
        doc = self._col.document(job_id).get()
        return doc.to_dict() if doc.exists else None

    def list_by_status(self, status: str, limit: int = 20) -> list[dict]:
        # Uses the composite index from Step 2 — no client-side sorting.
        q = (
            self._col.where("status", "==", status)
            .order_by("createdAt", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        return [d.to_dict() | {"jobId": d.id} for d in q.stream()]
```

## Step 4: Transactions for counters

Rate limits and budget counters use Firestore transactions — never
read-then-write:

```python
@firestore.transactional
def _bump(transaction, ref, ttl):
    snap = ref.get(transaction=transaction)
    used = snap.get("used") + 1 if snap.exists else 1
    transaction.set(ref, {"used": used, "expires_at": ttl}, merge=True)
    return used

used = _bump(db.transaction(), ref, ttl)
```

**⛔ `transactional` decorates the FUNCTION — never call it with the
transaction.** `firestore_v1.transactional` takes the function to wrap, not a
transaction object. `transactional(transaction)` wraps the *transaction
itself* as the callable and fails at runtime with
`AttributeError: 'function' object has no attribute '_read_only'`
(real-deploy bug 2026-10-03). The pattern is always: decorate the function
with `@transactional`, then call the wrapped function passing the
transaction as its first argument.

**Test blind spot:** unit tests that stub the Firestore SDK (ImportError
fallback) will NOT catch this misuse — the failure only surfaces against the
real client. If you wrap SDK access for testability, keep the
`@transactional` application on the real decorator path and test it in the
deployed environment.

## Gotchas

- **No queries without an index plan.** Any `where` + `orderBy` combo needs a
  composite index or it throws at runtime. The emulator does not always catch
  this — test listings against the real API before calling it done.
- **`in` queries are limited to 30 values** — design around it, don't batch
  around it.
- **Document size cap is 1 MiB** — findings go in a subcollection, never in
  an array on the job document.
- **TTL is per collection group via a timestamp field** — it is not a
  per-document setting you toggle in code. Declare it in Terraform.
- **Emulator ≠ production for indexes.** The Firestore emulator is lenient
  about missing composite indexes; CI must run the listing tests against a
  real (or faithfully indexed) backend.

## Where files go

| Artifact | Location |
|---|---|
| Repository classes | `src/<Name>/repository.py` or per-aggregate modules |
| Index/TTL declarations | `infra/firestore.tf` |
| Collection design doc | Design ADR or the skill's Step 1 table, adapted |
