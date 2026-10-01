---
name: sdlc-dynamodb-repository
description: >-
  Implement DynamoDB data access with single-table design and the Repository
  Pattern over boto3. Use when creating entities, repositories, key designs, or
  any DynamoDB CRUD operations. Triggers on DynamoDB, database, entity,
  repository, data model, or data access requests. Never use Scan on hot paths
  and never substitute FilterExpression for key design — always model access
  patterns as keys and sparse GSIs first.
version: "1.0"
author: sdlc-harness
user-invocable: false
---

# AWS DynamoDB — Single-Table Design with Repository Pattern

## When to use

- Designing a DynamoDB table for a new domain (key design comes first)
- Adding CRUD operations for any domain object
- Implementing queries, filtering, or pagination against DynamoDB
- Reviewing code that accesses DynamoDB

## Step 1: List access patterns BEFORE designing keys

Write down every query the application needs, then design keys to serve them.
Keys are designed from queries — never the reverse.

Example (research-job domain):

| # | Access pattern | Key design |
|---|---|---|
| 1 | Get job by ID | PK=`JOB#<id>`, SK=`METADATA` |
| 2 | Get job with findings + report | PK=`JOB#<id>`, SK begins_with `""` (Query, one round trip) |
| 3 | List jobs by status, newest first | GSI1: PK=`STATUS#<status>`, SK=`created_at` (sparse) |
| 4 | Get single finding | PK=`JOB#<id>`, SK=`FINDING#<finding_id>` |

**Rules:**
- If an access pattern has no key design, it does not exist — go back and
  design it. Adding a Scan later is not a fix.
- **Sparse GSIs** for status/type listings: only items carrying the GSI keys
  are indexed. `STATUS#<status>` as GSI1PK means "list running jobs" never
  touches terminal ones.

## Step 2: Define the table (CDK)

```typescript
const table = new dynamodb.Table(this, 'AppTable', {
  partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'sk', type: dynamodb.AttributeType.STRING },
  billingMode: dynamodb.BillingMode.PAY_PER_REQUEST, // on-demand default
  timeToLiveAttribute: 'expires_at',                  // TTL for ephemeral items
  pointInTimeRecovery: true,                          // prod safety net
});
table.addGlobalSecondaryIndex({
  indexName: 'gsi1',
  partitionKey: { name: 'gsi1pk', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'gsi1sk', type: dynamodb.AttributeType.STRING },
  projectionType: dynamodb.ProjectionType.ALL,
});
```

**Billing rule:** on-demand (`PAY_PER_REQUEST`) unless traffic is predictable
and provisioned-with-autoscaling is provably cheaper. Spiky AI workloads are
on-demand workloads.

## Step 3: Define repositories

One repository per aggregate, wrapping boto3 — never raw client calls
scattered through business logic:

```python
import boto3
from boto3.dynamodb.conditions import Key

class JobRepository:
    """Repository for research jobs (single-table: pk=JOB#<id>)."""

    def __init__(self, table_name: str):
        self._table = boto3.resource("dynamodb").Table(table_name)

    def get(self, job_id: str) -> dict | None:
        resp = self._table.get_item(Key={"pk": f"JOB#{job_id}", "sk": "METADATA"})
        return resp.get("Item")

    def get_with_findings(self, job_id: str) -> list[dict]:
        # One Query returns the job + all findings + report
        resp = self._table.query(
            KeyConditionExpression=Key("pk").eq(f"JOB#{job_id}")
        )
        return resp["Items"]

    def list_by_status(self, status: str, limit: int = 50) -> list[dict]:
        # Sparse GSI: only jobs currently in this status are indexed
        resp = self._table.query(
            IndexName="gsi1",
            KeyConditionExpression=Key("gsi1pk").eq(f"STATUS#{status}"),
            ScanIndexForward=False,  # newest first
            Limit=limit,
        )
        return resp["Items"]

    def transition_status(self, job_id: str, expected: str, new: str) -> None:
        # Conditional write: the job state machine, enforced by the database
        self._table.update_item(
            Key={"pk": f"JOB#{job_id}", "sk": "METADATA"},
            UpdateExpression="SET #s = :new, gsi1pk = :gsi",
            ConditionExpression="#s = :expected",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":new": new,
                ":expected": expected,
                ":gsi": f"STATUS#{new}",
            },
        )
```

**Rules:**
- Repository goes in the **Business** layer; the API layer imports from Business.
- State transitions use **conditional writes** — the database enforces the state
  machine, not application `if` statements. Keep GSI keys in sync on every
  transition (see `gsi1pk` update above).
- Researcher fan-in writes use `batch_write_item` (25 per batch), with
  unprocessed-item retry.
- Pagination: return `LastEvaluatedKey` to callers; never accumulate full scans.

## Step 4: TTL for ephemeral data

Items that must not outlive their usefulness carry `expires_at` (epoch seconds)
and the table's TTL attribute reaps them for free:

- Failed-job debug payloads → expire after 7 days
- Raw fetch caches → expire after 30 days

**Never** implement "cleanup cron jobs" for data DynamoDB TTL can delete.

## Step 5: Write unit tests

```python
from unittest.mock import MagicMock, patch

class TestJobRepository:
    def _repo(self, table):
        with patch("boto3.resource", return_value=MagicMock(Table=lambda n: table)):
            from mymodule import JobRepository
            return JobRepository("app-table")

    def test_get_builds_correct_key(self):
        table = MagicMock()
        table.get_item.return_value = {"Item": {"pk": "JOB#1"}}
        repo = self._repo(table)
        assert repo.get("1")["pk"] == "JOB#1"
        table.get_item.assert_called_once_with(
            Key={"pk": "JOB#1", "sk": "METADATA"}
        )

    def test_transition_status_uses_condition(self):
        table = MagicMock()
        repo = self._repo(table)
        repo.transition_status("1", "running", "succeeded")
        _, kwargs = table.update_item.call_args
        assert "ConditionExpression" in kwargs  # state machine enforced in DB
```

## Gotchas

- **Never `Scan` on a hot path** — if you need a Scan, the key design is wrong.
  Scans are for one-off admin/backfill scripts only.
- **Never substitute `FilterExpression` for key design** — filters run *after*
  the read, so you pay for every item examined.
- **Hot partitions**: a single `STATUS#running` GSI partition with thousands of
  writes/sec will throttle. Shard it (`STATUS#running#<n>`) if write volume
  demands it — for v1 workloads this is a documented non-issue, not a design
  to pre-build.
- **Eventual consistency is the default** — use `ConsistentRead=True` only for
  read-after-write flows that need it (e.g. job status polling right after
  creation), not everywhere.
- **Empty-string attributes**: DynamoDB rejects empty strings — sanitize or
  omit them before writes.
- **On-demand has a price** — it is the default for unpredictable workloads,
  not a license to skip key design. Bad keys cost money in every billing mode.

## Where files go

| Artifact | Location |
|---|---|
| Table CDK construct | `infra/lib/data-stack.ts` |
| Entity/key documentation | `src/<Name>Business/src/libs/models/` |
| Repository class | `src/<Name>Business/src/libs/repositories/` |
| Unit tests | `src/<Name>Business/tests/unit/` |
| Integration tests (moto/local) | `src/<Name>Business/tests/integration/` |
