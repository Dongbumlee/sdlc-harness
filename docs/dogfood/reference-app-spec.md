# Deep Research API — Dogfood Reference App Spec

**Status:** draft (2026-09-29)
**Purpose:** the fixed-spec reference app used to validate cloud packs end to end.
The same spec is built once per cloud (Azure, AWS, GCP) using that cloud's pack;
the three builds are compared to find pack gaps.

**Why this app:** it is AI-native (a multi-agent pipeline *is* the product), complex
enough to exercise every SDLC agent (analyst, architect, implementer, QA panel,
compliance reviewer, deployer), and it uses all three pack pillars — containerized
API, NoSQL, object storage — without contrivance.

---

## 1. What it is

A multi-agent research pipeline exposed as an API. A client submits a topic; a
background agent team (planner → researchers → critic → writer) produces a cited
report as markdown and PDF.

## 2. Functional requirements

| # | Endpoint | Behavior |
|---|----------|----------|
| 1 | `POST /research` `{topic, depth}` | Validate, create job, return `202 {jobId}`. `depth`: `quick` \| `standard` \| `deep` |
| 2 | `GET /research/{id}` | Job status: `queued` \| `planning` \| `researching` \| `reviewing` \| `writing` \| `done` \| `failed`, plus progress counters and timestamps |
| 3 | `GET /research/{id}/events` | SSE stream of phase transitions and finding counts |
| 4 | `GET /research/{id}/report` | Markdown report (only when `done`) |
| 5 | `GET /research/{id}/report.pdf` | PDF report (only when `done`) |
| 6 | `GET /research?status=&limit=` | Paginated job list, newest first |
| 7 | `DELETE /research/{id}` | Cancel a non-terminal job |
| 8 | Auth | API key in `Authorization` header; per-key rate limit (e.g. 10 jobs/hour) |

## 3. Agent pipeline

- **Planner:** topic → 3–8 research questions (count scales with `depth`).
- **Researchers:** run in parallel, one per question. Each uses a web-search tool and
  returns findings with source URLs.
- **Critic:** checks coverage across questions; may request one follow-up round
  (max 1) for gaps.
- **Writer:** findings → structured markdown report with numbered citations `[n]`
  and a source list. Then render PDF.
- **Guardrails (enforced, not advisory):**
  - Per-job tool-call budget (cost guardrail); budget reported on the job record.
  - Per-phase timeouts; timeout marks the job `failed` with a reason.
  - Fetched web content is **untrusted data** — prompt-injection handling required
    (no instruction following from page content, citation required for claims).

## 4. Data model (NoSQL)

The pack's data-access skill owns the modeling; the shape below is the *logical*
contract. Single-table design where the store supports it (DynamoDB); adapted to
the native model per cloud (Cosmos DB containers, Firestore collections).

- **Jobs:** PK = job id → status, topic, depth, progress `{phase, questionsTotal,
  questionsDone, findingsCount}`, tool-call budget `{limit, used}`, timestamps,
  error reason (if failed).
- **Findings:** PK = job id, SK = finding id → research question, content excerpt,
  source URLs, retrieved-at.
- **Reports:** PK = job id → markdown, PDF object key, citation map
  (`[n]` → source URL).

## 5. Object storage

- Raw snapshots of fetched sources (HTML/markdown, for auditability).
- Generated PDFs.
- Access **only** via short-lived signed URLs; no public containers/buckets.

## 6. Deployment

- Containerized API + worker (may be one image, separate processes).
- Each cloud uses its pack's paved road:
  - Azure: Bicep + AVM + `azd`, Azure Container Apps.
  - AWS: CDK, Lambda (container image + Function URL) for the API, ECS Fargate
    (Spot) for the worker. (App Runner is closed to new customers since
    2026-04-30 — never use it for new work.)
  - GCP: Terraform, Cloud Run.
- Secrets (LLM API key, search API key) live in the cloud's secret manager
  (Key Vault / Secrets Manager / Secret Manager) and are injected at runtime —
  never plaintext env vars, never in the image.
- HTTPS required. Private networking not required for v1.

## 7. Non-functional targets

- Wall-clock (best effort): quick < 3 min, standard < 10 min, deep < 25 min.
- Report quality is evaluated, not eyeballed: the QA agents define an
  **LLM-as-judge rubric** (coverage of questions, citation accuracy, structure)
  and it runs in CI against a fixed topic set.
- Deterministic tests cover the API contract, state machine transitions, and
  guardrail enforcement (budget exceeded → job stops; timeout → `failed`).

## 8. Validation criteria (per cloud build)

1. All endpoints respond correctly against the deployed URL.
2. A `standard` job completes; every citation resolves to a fetched source.
3. Cloud compliance reviewer findings are addressed (no public storage,
   least-privilege IAM, secrets in the manager, no hardcoded keys).
4. Cost report: tool-call count and estimated cost for one `standard` job.
5. Cross-cloud comparison: same spec, three builds — differences in agent
   decisions are pack gaps to file, not trivia.

## 9. Out of scope (v1)

- User accounts / teams (single API key).
- Web UI (API only; demo via a small client script).
- Cloud-native model services — the LLM is an external API so the spec stays
  portable across clouds.
- Webhooks, real-time collaboration, multi-language reports.

---

## Build log

| Date | Cloud | PR / notes | Result |
|------|-------|-----------|--------|
| — | Azure | not started | — |
| — | AWS | not started (pack not started) | — |
| — | GCP | not started (pack not started) | — |
