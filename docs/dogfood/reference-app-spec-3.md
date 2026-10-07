# AI Brief — Dogfood Reference App Spec 3

**Status:** draft (2026-10-04) — awaiting Dongbum's approval
**Purpose:** the third fixed-spec reference app. Scenarios 1–2 validated async
jobs, scheduling, sync API, and cache — all with stubbed logic. This spec
validates what none of them touched: **a real LLM in the loop**
(provider integration, prompt versioning, token metering, model-failure
handling, structured-output validation). API-only, no UI.

**Why this app:** every AI product eventually puts a model behind an async job.
The pack has an `llm-behavior-reviewer` but no validated pattern for calling a
model from a worker. The LLM is the only non-deterministic part — E2E asserts
structure, never content.

---

## 1. What it is

POST a topic → worker calls the LLM → structured research brief stored.
`POST /briefs {topic}` → `202 {brief_id, status: queued}` →
worker runs → `GET /briefs/{id}` → `done` with the brief.

## 2. API

| Method | Path | Notes |
|---|---|---|
| POST | /briefs | `{topic: string (1–200 chars)}` → 202 `{brief_id, status}` |
| GET | /briefs/{id} | `{brief_id, topic, status, brief?, tokens?, error?, created_at}` |
| GET | /briefs | list, newest first, limit 20 |
| GET | /health | 200 `{ok: true}` |

`status`: `queued` → `running` → `done` | `failed`.

## 3. Worker (LLM integration)

- **Provider:** Google Gemini (`gemini-flash`), API key from the cloud secret
  manager → env var. Key never in code, image, or logs.
- **Prompt:** versioned template (`prompt_version: "v1"` stored per brief).
  System instruction demands **JSON only** matching the output schema.
- **Output schema** (validated strictly):
  `{"summary": str, "key_points": [str × 3–7], "risks": [str], "confidence": "low|medium|high"}`
- **Invalid output:** retry once with repair instruction; still invalid → `failed`.
- **Timeouts:** LLM call 60s; job 5 min.
- **Token metering:** input/output tokens recorded per brief (`tokens: {in, out}`).

## 4. Failure handling

- Invalid/revoked API key → `failed`, `error: "llm_auth"`, worker stays healthy.
- LLM timeout → one retry → `failed` with `error: "llm_timeout"`.
- Queue/worker infra failures follow the scenario-1 pattern (no new rules).

## 5. Data model

`briefs/{id}`: topic, status, prompt_version, brief (JSON), tokens {in,out},
model, error?, created_at, completed_at.

## 6. E2E acceptance

1. POST /briefs → 202; poll → `done` within 3 min; brief matches schema
   (sections present, types correct, non-empty). Content not asserted.
2. `tokens.in/out` > 0 and recorded.
3. Failure drill: invalid key → `failed` + `error: "llm_auth"` within 2 min;
   worker healthy; valid key still works after.
4. Malformed topic (empty / >200 chars) → 400.
5. Cost: full E2E under $0.10 in LLM charges.

## 7. Cost guardrails

- Model fixed to `gemini-flash` (cheapest tier). No model parameter exposed.
- Max 50 briefs/day per deployment (guardrail, not a product feature).
- Teardown immediately after E2E — same as Pulse.

## 8. Cloud mapping (same pattern as scenario 1)

| Concern | AWS | GCP | Azure |
|---|---|---|---|
| API | Lambda + Function URL | Cloud Run service | Container App |
| Queue | SQS | Pub/Sub | Storage Queue |
| Worker | Fargate | Cloud Run Job | Container Apps Job |
| DB | DynamoDB | Firestore | Cosmos DB |
| Secrets | Secrets Manager | Secret Manager | Key Vault |

## Build log

| Date | Cloud | PR / notes | Result |
|------|-------|-----------|--------|
| — | AWS | not started | — |
| — | GCP | not started | — |
| — | Azure | not started | — |
