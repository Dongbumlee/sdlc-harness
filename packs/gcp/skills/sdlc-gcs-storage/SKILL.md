---
name: sdlc-gcs-storage
description: >-
  Implement Cloud Storage with private buckets, uniform bucket-level access,
  and V4 signed URLs. Use when creating buckets, generating signed URLs,
  configuring lifecycle rules, or reviewing storage code. Triggers on Cloud
  Storage, GCS, bucket, signed URL, or object storage requests. Buckets are
  always private with uniform bucket-level access — access only via
  short-lived signed URLs, never public reads or legacy ACLs.
version: "1.0"
author: sdlc-harness
user-invocable: false
---

# GCP Cloud Storage — Private Buckets, Signed URLs, Lifecycle Rules

## When to use

- Creating buckets for reports, snapshots, or artifacts
- Generating signed URLs for private object downloads
- Configuring lifecycle rules and retention
- Reviewing code that reads/writes Cloud Storage

## Step 1: Buckets are private — always

```hcl
resource "google_storage_bucket" "reports" {
  name                        = "${var.project_id}-reports"
  location                    = var.region
  uniform_bucket_level_access = true   # no legacy ACLs, ever
  public_access_prevention    = "enforced"

  versioning { enabled = false }        # enable only with a lifecycle rule

  lifecycle_rule {
    action    { type = "Delete" }
    condition { age = 90 }              # reports expire — no forgotten objects
  }
}
```

**⛔ NEVER `public_access_prevention = "inherited"` on a new bucket.**
**⛔ NEVER legacy bucket ACLs.** Uniform access + IAM only.

## Step 2: Signed URLs for external access

```python
from google.cloud import storage

def signed_download_url(bucket_name: str, blob_name: str, ttl_seconds: int = 600) -> str:
    """Short-lived V4 signed URL (pack: <= 15 min), never a public read."""
    blob = storage.Client().bucket(bucket_name).blob(blob_name)
    return blob.generate_signed_url(
        version="v4",
        expiration=ttl_seconds,
        method="GET",
    )
```

**Signing permission is separate from read permission.**
`storage.objects.get` lets you *read* the object; *signing* a URL additionally
requires `iam.serviceAccounts.signBlob` on the runtime service account (the
default compute SA gets this via the IAM grant below, or attach a dedicated
signing identity). Test signed-URL generation in the deployed environment —
local ADC signing behaves differently from the runtime SA.

```hcl
# The API service account can sign URLs for the reports bucket.
resource "google_storage_bucket_iam_member" "api_signer" {
  bucket = google_storage_bucket.reports.name
  role   = "roles/iam.serviceAccountTokenCreator"
  member = "serviceAccount:${google_service_account.api.email}"
}
```

## Step 3: Lifecycle rules — data must have an expiry story

Every bucket gets a lifecycle rule. Reports, snapshots, and temp objects all
expire — the pack treats "no lifecycle" the same as "no log retention": a
finding.

## Step 4: Write unit tests

- Signed URLs are generated (mock the client) and expire within the pack
  limit (<= 15 min).
- No code path makes a bucket or object public (`make_public`,
  `public_access_prevention` disabled, legacy ACLs).
- Uploads set explicit `content_type`.

## Gotchas

- **Signing ≠ reading.** The #1 signed-URL failure: the SA can read the
  object but cannot sign. Grant `roles/iam.serviceAccountTokenCreator`
  (signBlob) explicitly.
- **V4 signed URLs cap at 7 days.** `expiration` beyond 604800s fails at
  generation time. The pack limit (<= 15 min) is far below this — if you ever
  need longer-lived links, that is a design discussion, not a parameter bump.
- **Uniform bucket-level access is one-way-ish.** Enabling it disables object
  ACLs permanently for the bucket's lifetime — decide at creation.
- **`generate_signed_url` with default credentials locally** uses your user
  key; in Cloud Run it uses the runtime SA. If local works and deployed
  fails, the difference is the signing identity — check IAM first.
- **Storage operations go in the Business layer** — the API layer calls
  Business services, which call storage helpers.

## Where files go

| Artifact | Location |
|---|---|
| Bucket declarations | `infra/storage.tf` |
| Signed-URL helpers | `src/<Name>/storage.py` or the API service module |
| Upload/download code | Business layer, never the HTTP handler directly |
