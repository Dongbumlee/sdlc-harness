---
name: sdlc-s3-storage
description: >-
  Implement Amazon S3 object storage with private buckets, presigned URLs, and
  lifecycle rules. Use when uploading, downloading, listing, or managing objects.
  Triggers on S3, storage, file upload, object storage, presigned URL, or bucket
  requests. Never create public buckets or public bucket policies — always
  BlockPublicAccess with presigned URLs for external access.
version: "1.0"
author: sdlc-harness
user-invocable: false
---

# AWS S3 — Private Buckets, Presigned URLs, Lifecycle Rules

## When to use

- Uploading or downloading files to/from S3
- Listing, copying, moving, or deleting objects
- Generating time-limited download URLs (reports, PDFs)
- Configuring lifecycle rules and versioning
- Reviewing code that interacts with S3

## Step 1: Buckets are private — always

```typescript
const artifacts = new s3.Bucket(this, 'Artifacts', {
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL, // ⛔ never a public bucket
  encryption: s3.BucketEncryption.S3_MANAGED,         // SSE-S3 default
  enforceSSL: true,                                  // deny non-TLS requests
  versioned: true,                                   // with lifecycle (Step 3)
});
```

**Rules:**
- `BLOCK_ALL` on every bucket, no exceptions. External access happens via
  **presigned URLs**, never bucket policies.
- **SSE-S3 by default.** SSE-KMS only when compliance explicitly requires
  customer-managed keys — KMS API calls cost money per request.
- One bucket per data class (e.g. `artifacts`, `source-snapshots`), not one
  bucket per environment tangle. Environment separation goes in the key prefix
  or bucket name suffix.

## Step 2: Presigned URLs for external access

Clients never get bucket access — they get a short-lived URL:

```python
import boto3

class ArtifactStorage:
    """S3 access for report artifacts. Business layer."""

    def __init__(self, bucket: str):
        self._s3 = boto3.client("s3")
        self._bucket = bucket

    def upload_report(self, key: str, data: bytes) -> None:
        self._s3.put_object(Bucket=self._bucket, Key=key, Body=data,
                             ContentType="application/pdf")

    def download_url(self, key: str, expires_seconds: int = 900) -> str:
        """Time-limited read URL — the only way clients fetch artifacts."""
        return self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_seconds,  # 15 min default; justify longer
        )

    def list_reports(self, job_id: str) -> list[str]:
        paginator = self._s3.get_paginator("list_objects_v2")
        keys = []
        for page in paginator.paginate(Bucket=self._bucket,
                                       Prefix=f"reports/{job_id}/"):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys
```

**Rules:**
- Default expiry 15 minutes. Longer expiries need a written justification —
  a presigned URL is a bearer token.
- `put_object` from the service, never presigned PUTs from browsers in v1
  (keeps auth in one place).
- Always paginate listings — `list_objects_v2` truncates at 1,000 keys.

## Step 3: Lifecycle rules — data must have an expiry story

```typescript
artifacts.addLifecycleRule({
  id: 'expire-raw-snapshots',
  prefix: 'snapshots/raw/',
  expiration: Duration.days(30),          // fetched source HTML: 30 days
  noncurrentVersionExpiration: Duration.days(7),
});
artifacts.addLifecycleRule({
  id: 'expire-multipart-fragments',
  abortIncompleteMultipartUploadAfter: Duration.days(7),
});
```

**Rules:**
- Every bucket gets lifecycle rules. Raw/intermediate data expires
  (snapshots 30d); final reports are retained per product policy.
- **Versioning without lifecycle is a storage-bloat bug** — noncurrent
  versions accumulate silently. Pair them always.
- Incomplete multipart uploads are abandoned fragments that bill forever —
  the abort rule above is mandatory.

## Step 4: Write unit tests

```python
from unittest.mock import MagicMock, patch

class TestArtifactStorage:
    def _storage(self, client):
        with patch("boto3.client", return_value=client):
            from mymodule import ArtifactStorage
            return ArtifactStorage("artifacts-bucket")

    def test_download_url_is_presigned(self):
        client = MagicMock()
        client.generate_presigned_url.return_value = "https://signed-url"
        storage = self._storage(client)
        url = storage.download_url("reports/j1/report.pdf")
        assert url == "https://signed-url"
        _, kwargs = client.generate_presigned_url.call_args
        assert kwargs["ExpiresIn"] <= 900  # short-lived by default
```

## Gotchas

- **Never a public bucket** — not for "just this demo", not behind
  "obscure key names". BlockPublicAccess + presigned URLs, always.
- **Never put AWS credentials in presigned-URL code paths** — signing uses the
  task role automatically. If you see access keys near S3 code, flag it.
- **Cross-region replication** is out of v1 scope — single region (`us-west-2`
  default), like the rest of the pack.
- **S3 + CloudFront** for public downloads is out of v1 — presigned URLs cover
  the dogfood's report-download flow.
- **Event notifications** (S3 → SQS/Lambda on upload) are allowed when a real
  event-driven flow needs them — not as a polling replacement you forgot to
  design.
- **Storage operations go in the Business layer** — the API layer calls Business
  services, which call storage helpers.

## Where files go

| Artifact | Location |
|---|---|
| Bucket CDK constructs | `infra/lib/data-stack.ts` |
| Storage service class | `src/<Name>Business/src/libs/services/` |
| Unit tests | `src/<Name>Business/tests/unit/` |
| Integration tests | `src/<Name>Business/tests/integration/` |
