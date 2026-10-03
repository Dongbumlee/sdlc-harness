# Pulse API — Dogfood Reference App Spec 2

**Status:** draft (2026-10-03) — awaiting Dongbum's approval
**Purpose:** the second fixed-spec reference app for pack validation. Scenario 1
(Deep Research API, `reference-app-spec.md`) validated the async-job paved road
(API + worker + queue + NoSQL + object storage). This spec validates what
scenario 1 never touched: **scheduled jobs, sync low-latency API, and cache**.
The same spec is built once per cloud; the three builds are compared to find
pack gaps.

**Why this app:** every production system has a cron and a cache. None of the
three packs has a cache skill, and the scheduler path is mentioned only as an
untested alternative. The data source is public and deterministic (no LLM, no
API keys) — the dogfood target is pack surface, not model quality, so E2E stays
hermetic and cheap.

---

## 1. What it is

A scheduled trend digest. Every 30 minutes a collector fetches a public trending
feed, computes a ranked digest with score deltas versus the previous run, stores
it in NoSQL, and warms the cache. A sync API serves the latest digest from cache
against a latency target.

## 2. Functional requirements

| # | Endpoint | Behavior |
|---|----------|----------|
| 1 | `GET /digest/latest` | Latest digest, served from cache. `X-Cache: HIT`/`MISS` header (testability) |
| 2 | `GET /digest/history?limit=` | Past digests, newest first (from NoSQL) |
| 3 | `GET /items/{id}` | Story detail + score history (cache-aside) |
| 4 | `GET /health` | Scheduler last-run status, cache connectivity, `consecutive_failures` |
| 5 | `POST /admin/collect` | Runs the collection pipeline on demand (API key auth). Same code path as the scheduled run, `trigger=manual` — for deterministic E2E without waiting on cron |

**Collector (scheduled, every 30 min):**
- Fetch front page via the public HN Algolia API (no key). Timeout 20s, 2 retries.
- Rank by points (deterministic — no LLM).
- Delta vs previous digest: new entries, dropped entries, movers (points change ≥ 20%).
- Write digest + items to NoSQL; write `digest:latest` + `item:{id}` keys to cache (TTL = 2× interval).
- Record the run in Meta: `trigger` (`scheduled`\|`manual`), duration, item count, `source_error` if the feed failed.
- **Source failure must not delete the last good digest.** On feed failure the collector records `source_error`, keeps serving stale, and staleness is surfaced in `/health`.

**Guardrails (enforced, not advisory):**
- Collector max runtime 5 min; overrun → run marked `failed`, previous digest stays live.
- Cache is never the system of record; NoSQL is.
- No public cache or storage endpoints.

## 3. Data model (NoSQL)

Logical contract; the pack's data-access skill owns the modeling.

- **Digests:** PK = run id (UTC timestamp) → started_at, finished_at, trigger, item_count, top item ids, source_error (if any).
- **Items:** PK = story id → title, url, points, score_history `[{run_id, points}]`, first_seen, last_seen.
- **Meta:** PK = `"collector"` → last_run_id, last_run_at, last_trigger, consecutive_failures.

## 4. Cache (Redis)

Logical contract; no pack owns this yet — expect improvisation, file it as gaps.

- `digest:latest` → serialized latest digest, TTL 3600s.
- `item:{id}` → story detail, TTL 3600s.
- Pattern: cache-aside on reads; write-through on collector runs. On miss, the API reads NoSQL and repopulates. No thundering-herd protection required for v1 (log it if observed).

## 5. Deployment

- Containerized API (sync, request-driven) + collector as a scheduled job (same image, separate entrypoint allowed).
- Each cloud uses its pack's paved road. Mapping hints — the pack owns the final decision:
  - AWS: EventBridge Scheduler → Fargate task (or Lambda); ElastiCache Serverless (Redis); API on the pack's compute road.
  - GCP: Cloud Scheduler → Cloud Run Job (or service); Memorystore for Redis.
  - Azure: Container Apps Job with cron trigger; Azure Cache for Redis.
- Secrets: none required (public data source). If a pack mandates secrets infra anyway, file it as a gap.
- HTTPS required. Private networking not required for v1 (scenario 2 scope). WAF excluded — cost decision 2026-10-03.

## 6. Non-functional targets

- `GET /digest/latest` p99 < 200 ms on cache hit (test client in the same region).
- Scheduler fires within ±2 min of schedule; a missed run surfaces in `/health` (`consecutive_failures > 0`).
- Deterministic tests cover the API contract, cache-aside behavior (`MISS` → `HIT`), collector idempotency (same run id twice → single digest), and the source-failure path (stale served, error recorded).
- No LLM-as-judge needed — output is deterministic; QA asserts exact digest shape.

## 7. Validation criteria (per cloud build)

1. All endpoints respond correctly against the deployed URL; `X-Cache` behaves (`MISS` → `HIT`).
2. ≥2 consecutive **scheduled** runs observed in cloud logs; digests in NoSQL with `trigger=scheduled` at 30-min spacing (±2 min).
3. Manual `POST /admin/collect` produces a digest through the identical code path.
4. Source-failure drill: feed timeout → error recorded, last good digest still served.
5. Compliance reviewer findings addressed (no public cache/storage, least-privilege IAM, scheduler→job auth).
6. Cost report: 24h extrapolated cost (scheduler + cache + API).
7. Cross-cloud comparison: same spec, three builds — agent decision differences are pack gaps.

## 8. Out of scope (v1)

- LLM summarization (deterministic ranking only).
- Private networking (scenario 2), WAF (excluded: cost).
- User accounts (single admin API key for `/admin/collect` only; reads are public).
- Web UI, push notifications, multi-source feeds.

## 9. Expected pack gaps / risks (pre-build)

1. **No cache skill in any pack.** Client library, connection pooling, TLS, and auth will be improvised per cloud — expect divergence (Memorystore needs VPC connector / Private Service Connect; ElastiCache Serverless vs provisioned; Azure Cache TLS).
2. **Serverless compute ↔ private cache networking** — the classic gap scenario 1 never touched (GCP Serverless VPC Connector, AWS Fargate-in-VPC, Azure VNet integration).
3. **Scheduler→job auth.** Cloud Scheduler → Cloud Run needs OIDC config; EventBridge → Fargate needs an IAM role; Container Apps Job cron is native (lowest risk).
4. **Cron dialect differences** (EventBridge vs unix-cron vs Container Apps).
5. **Cache always-on cost** even in short test windows — teardown immediately; the $20 budget guardrail applies.
6. **Source flakiness** (HN API) — acceptance tolerates it via the `source_error` path; E2E must not depend on a single fetch.

---

## Build log

| Date | Cloud | PR / notes | Result |
|------|-------|-----------|--------|
| — | Azure | not started | — |
| — | AWS | not started | — |
| — | GCP | not started | — |
