# REQ-0001: Deep Research API — Dogfood Reference App

> **Status:** Under Review
> **SDLC Phase:** 1 (Requirements)
> **Date:** 2026-10-02
> **Author:** @Harness (Analyst agent)
> **Approved by:** _[pending — fill after user approval]_

---

## Problem Statement

The SDLC harness needs a **fixed-spec reference application** to validate cloud packs (Azure, AWS, GCP) end to end. Without a common, non-trivial app built identically across all three clouds, there is no reliable way to detect gaps in a cloud pack's paved-road guidance (scaffolding, reference libraries, IaC templates, agent prompts). Engineers maintaining the SDLC harness experience this problem: they cannot tell whether a pack is complete until it has been exercised by a real, complex build.

## Business Context

This app is the vehicle for **dogfooding** the harness's multi-cloud pack system. It must be complex enough to exercise every SDLC agent (analyst, architect, implementer, QA panel, compliance reviewer, deployer) and every pack pillar (containerized API, NoSQL data access, object storage) without artificial contrivance. The same spec will be implemented three times — once per cloud — and the three builds compared to surface pack gaps as actionable findings, not anecdotes.

## Goals

- [ ] Goal 1: Provide a single, unambiguous spec that can be built once per cloud (Azure, AWS, GCP) using that cloud's pack.
- [ ] Goal 2: Exercise a multi-agent AI pipeline (planner → researchers → critic → writer) as the core product logic, validating AI-native patterns in each pack.
- [ ] Goal 3: Exercise all three pack pillars — containerized compute, NoSQL storage, object storage — in every cloud build.
- [ ] Goal 4: Enforce guardrails (cost budget, timeouts, prompt-injection resistance) as testable, deterministic behavior rather than advisory guidance.
- [ ] Goal 5: Produce comparable outputs (deployed API, cost report, compliance findings) across the three cloud builds to identify pack gaps.

## Non-Goals

- Building a production-grade, multi-tenant SaaS product.
- Optimizing for lowest possible cost or latency beyond the stated wall-clock targets.
- Supporting multiple concurrent clouds in a single deployment (each cloud build is independent).

## Out of Scope

- User accounts or teams (single shared API key for v1).
- Web UI (API only; a small client script may be used for demos).
- Cloud-native model services — the LLM is called as an external API so the spec remains portable across clouds.
- Webhooks, real-time collaboration features, and multi-language report output.
- Private networking (not required for v1; HTTPS at the public endpoint is sufficient).

## Functional Requirements

| ID | Requirement | Acceptance Criterion |
|----|-------------|---------------------|
| FR-1 | `POST /research` accepts `{topic, depth}` and creates a research job | **Given** a valid `topic` string and `depth` ∈ {`quick`,`standard`,`deep`}, **When** the client calls `POST /research`, **Then** the API validates the payload, creates a job record, and returns `202 Accepted` with `{jobId}` |
| FR-2 | `POST /research` rejects invalid payloads | **Given** a missing `topic` or an unrecognized `depth` value, **When** the client calls `POST /research`, **Then** the API returns `4xx` with a validation error and does not create a job |
| FR-3 | `GET /research/{id}` returns job status | **Given** a valid job id, **When** the client calls `GET /research/{id}`, **Then** the API returns the job's current state (`queued`\|`planning`\|`researching`\|`reviewing`\|`writing`\|`done`\|`failed`), progress counters (`questionsTotal`, `questionsDone`, `findingsCount`), and timestamps |
| FR-4 | `GET /research/{id}/events` streams phase transitions via SSE | **Given** an in-progress job, **When** a client opens an SSE connection to `GET /research/{id}/events`, **Then** the client receives a server-sent event for each phase transition and each finding-count update until the job reaches a terminal state |
| FR-5 | `GET /research/{id}/report` returns the markdown report | **Given** a job in `done` state, **When** the client calls `GET /research/{id}/report`, **Then** the API returns the markdown report with HTTP 200; **Given** a job not in `done` state, **When** the same endpoint is called, **Then** the API returns a `4xx` indicating the report is not yet available |
| FR-6 | `GET /research/{id}/report.pdf` returns the PDF report | **Given** a job in `done` state, **When** the client calls `GET /research/{id}/report.pdf`, **Then** the API returns the rendered PDF with HTTP 200 and `Content-Type: application/pdf`; **Given** a job not in `done` state, **Then** the API returns a `4xx` |
| FR-7 | `GET /research?status=&limit=` lists jobs with pagination | **Given** zero or more jobs exist, **When** the client calls `GET /research` with optional `status` and `limit` query parameters, **Then** the API returns a paginated list of jobs ordered newest-first, filtered by `status` when provided, bounded by `limit` |
| FR-8 | `DELETE /research/{id}` cancels a non-terminal job | **Given** a job in any non-terminal state, **When** the client calls `DELETE /research/{id}`, **Then** the API transitions the job to a cancelled/terminal state and returns success; **Given** a job already in `done` or `failed` state, **Then** the API returns a `4xx` indicating cancellation is not possible |
| FR-9 | All endpoints require API key authentication | **Given** a request without a valid API key in the `Authorization` header, **When** any `/research*` endpoint is called, **Then** the API returns `401 Unauthorized` |
| FR-10 | Per-key rate limiting is enforced | **Given** an API key has submitted the configured maximum number of jobs within the rolling window (e.g., 10 jobs/hour), **When** that key calls `POST /research` again within the window, **Then** the API returns `429 Too Many Requests` |
| FR-11 | Planner generates research questions scaled by depth | **Given** a job with `depth=quick`, **When** the planning phase runs, **Then** it produces between 3 and 8 research questions, with the count increasing for `standard` and `deep` |
| FR-12 | Researchers execute in parallel, one per question | **Given** a planned set of research questions, **When** the researching phase runs, **Then** one researcher agent processes each question concurrently, each producing findings with source URLs |
| FR-13 | Critic checks coverage and may request at most one follow-up round | **Given** completed findings for all questions, **When** the critic reviews coverage, **Then** it either approves the findings or requests exactly one additional research round to address gaps; a second follow-up request is never issued |
| FR-14 | Writer produces a markdown report with numbered citations | **Given** approved findings, **When** the writing phase runs, **Then** it produces a structured markdown report containing numbered citation markers `[n]` for every claim and a corresponding source list |
| FR-15 | Writer renders the markdown report to PDF | **Given** a completed markdown report, **When** the writing phase finishes, **Then** a PDF rendering of the same report is generated and stored |
| FR-16 | Per-job tool-call budget is enforced and reported | **Given** a job in progress, **When** the cumulative tool-call count reaches the configured budget limit, **Then** the pipeline stops further tool calls for that job, marks it `failed` with a budget-exceeded reason, and the job record reports `{limit, used}` |
| FR-17 | Per-phase timeouts are enforced | **Given** any pipeline phase (planning, researching, reviewing, writing) exceeds its configured timeout, **When** the timeout elapses, **Then** the job transitions to `failed` with a timeout reason recorded on the job record |
| FR-18 | Fetched web content is treated as untrusted data | **Given** content fetched from a web source during research, **When** that content is processed by any agent, **Then** no instructions embedded in the content are followed, and every claim sourced from it carries a citation in the final report |
| FR-19 | Raw source snapshots are stored for auditability | **Given** a researcher fetches a web source, **When** the fetch completes, **Then** a raw snapshot (HTML or markdown) of that source is persisted to object storage |
| FR-20 | Generated PDFs are stored in object storage | **Given** a completed PDF report, **When** generation finishes, **Then** the PDF is persisted to object storage and its object key is recorded on the job/report record |
| FR-21 | Object storage is accessed only via short-lived signed URLs | **Given** a client requests a stored artifact (snapshot or PDF), **When** access is granted, **Then** it is via a time-limited signed URL; no object storage container/bucket is publicly accessible |
| FR-22 | API and worker are deployed as containerized components | **Given** a cloud build (Azure/AWS/GCP), **When** the app is deployed, **Then** the API and worker run as containerized processes (one image or two) using that cloud pack's paved-road deployment target |
| FR-23 | Secrets are stored in the cloud's secret manager and injected at runtime | **Given** the LLM API key and search API key are required at runtime, **When** the container starts, **Then** both secrets are retrieved from the cloud's secret manager (Key Vault / Secrets Manager / Secret Manager) and injected at runtime; neither secret appears as plaintext in an environment variable definition or in the container image |
| FR-24 | All endpoints are served over HTTPS | **Given** any client request to the deployed API, **When** the request is made, **Then** it is only accepted over HTTPS |

## Non-Functional Requirements

| ID | Requirement | Measurable Target |
|----|-------------|-------------------|
| NFR-1 | Wall-clock completion time for `quick` jobs | Best-effort median completion < 3 minutes |
| NFR-2 | Wall-clock completion time for `standard` jobs | Best-effort median completion < 10 minutes |
| NFR-3 | Wall-clock completion time for `deep` jobs | Best-effort median completion < 25 minutes |
| NFR-4 | Report quality is evaluated automatically | An LLM-as-judge rubric scoring coverage of questions, citation accuracy, and structure runs in CI against a fixed topic set; no manual/eyeballed quality review substitutes for this |
| NFR-5 | API contract is covered by deterministic tests | 100% of endpoints in FR-1–FR-10 have passing automated contract tests (request/response schema, status codes) |
| NFR-6 | State machine transitions are covered by deterministic tests | All valid and invalid job-state transitions (`queued`→...→`done`/`failed`/cancelled) have passing automated tests |
| NFR-7 | Guardrail enforcement is covered by deterministic tests | Automated tests verify: tool-call budget exceeded → job stops and is marked `failed`; phase timeout exceeded → job marked `failed` with reason |
| NFR-8 | Cloud compliance posture meets baseline | Compliance reviewer findings for each cloud build show: no publicly accessible storage, least-privilege IAM roles, all secrets in the cloud secret manager, zero hardcoded keys in source or image |
| NFR-9 | Cost is measurable per job | For a single `standard` job, a cost report is produced showing total tool-call count and estimated monetary cost |
| NFR-10 | Cross-cloud behavioral parity is measurable | The same spec, built independently on Azure, AWS, and GCP, is compared endpoint-by-endpoint and phase-by-phase; any behavioral divergence is logged as a candidate pack gap |

## Constraints

- Each cloud build must use that cloud's pack paved road:
  - **Azure:** Bicep + AVM + `azd`, deployed to Azure Container Apps.
  - **AWS:** CDK; API as Lambda (container image) with a Function URL; worker as ECS Fargate (Spot). App Runner must **not** be used for new work (closed to new customers as of 2026-04-30).
  - **GCP:** Terraform, deployed to Cloud Run.
- The LLM must be accessed as an external API — no cloud-native model service may be used, to keep the spec portable across clouds.
- Secrets (LLM API key, search API key) must live in the cloud's secret manager and be injected at runtime; plaintext environment variables and image-baked secrets are prohibited.
- Single shared API key model only — no user/team accounts in v1.
- No web UI — API only, optionally demonstrated via a client script.
- Private networking is not required for v1; public HTTPS endpoint is acceptable.

## Assumptions

- An LLM provider API and a web-search tool API are available and budgeted for in all three clouds.
- "Fixed topic set" for the LLM-as-judge rubric (NFR-4) will be defined during Phase 2 design or QA planning; it is not enumerated in this spec.
- The per-key rate limit default (10 jobs/hour) and the tool-call budget default are configuration values to be finalized during design, not hardcoded requirements.
- NoSQL data model (Jobs, Findings, Reports) described in the source spec is a logical contract; the physical schema is owned by each pack's data-access pattern (e.g., Cosmos DB containers, DynamoDB single-table, Firestore collections) and will be finalized in Phase 2 design.

## User Stories (optional)

- As a **harness maintainer**, I want to build the same spec on three clouds, so that I can identify gaps in each cloud pack's guidance.
- As an **API client**, I want to submit a research topic and poll or stream its progress, so that I can retrieve a cited report once it's ready.
- As a **compliance reviewer**, I want every cloud build to meet the same security baseline (no public storage, secrets in the manager, least-privilege IAM), so that pack guidance can be trusted for production use.

## Open Questions

- [ ] What is the exact fixed topic set used for the LLM-as-judge rubric in CI (NFR-4)? Needs a human decision before QA phase.
- [ ] What are the default values for per-key rate limit and per-job tool-call budget (referenced in FR-10 and FR-16)? Source spec gives an example (10 jobs/hour) but does not finalize it.
- [ ] Should the "one follow-up round" critic behavior (FR-13) be configurable per `depth`, or fixed at exactly one round regardless of depth?
- [ ] What specific LLM provider and web-search tool should be used as the reference implementation across all three clouds, to ensure true cross-cloud comparability?

## Discovery Notes

This spec was derived directly from an already-approved discovery document (`docs/dogfood/reference-app-spec.md`), which itself resulted from prior stakeholder discussion establishing: the app's purpose (cross-cloud pack validation), its AI-native multi-agent architecture, the three pack pillars it must exercise, and its validation criteria. No additional discovery conversation was held in this session — this document formalizes the already-approved source spec into the FR/NFR/testable-acceptance-criteria structure required for downstream implementation.

## References

- Discovery/source spec: `docs/dogfood/reference-app-spec.md` (approved, 2026-09-29 draft)
- Related ADR: _[to be filled after Phase 2 design]_

---

Please review this requirements specification. Once you approve it, I'll proceed to design (Phase 2).


