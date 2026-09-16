---
name: sdlc-canary-runner
description: "Instructs the Harness agent how to run E2E canary tests against SDLC phase agents. Canary mode validates that the harness orchestration is working correctly by feeding known prompts to phase agents and checking outputs against expected criteria."
version: "1.1"
author: sdlc-harness
user-invocable: false
---

# SDLC Canary Runner

Canary tests are **E2E integration tests for the harness itself** — they verify that phase agents
fire correctly and produce outputs that meet quality criteria. They are NOT model benchmarks.

## Trigger Phrases

Activate canary mode when the user says any of:
- "run canary tests"
- "canary mode"
- "run canaries"
- "test the harness"
- "validate phase agents"

## Phase-to-Agent Routing

| Phase | Agent | Canary prefix |
|-------|-------|---------------|
| `requirements` | Analyst | `req-` |
| `design` | Analyst | `des-` |
| `scaffold` | Scaffolder | `scf-` |
| `implement` | Implementer | `impl-` |
| `qa` | QA Coordinator | `qa-` |
| `document` | Documenter | `doc-` |
| `deploy` | Deployer | `dep-` |
| `release` | Release Manager | `rel-` |
| `publish` | Release Manager | `pub-` |
| `rai` | RAI Reviewer | `rai-` |

## Phase MCP Dependencies (defaults)

Each phase agent relies on MCP servers for its core behavior (coding guidance,
security patterns, repo data, deployment schemas). When a required server is
unavailable, the canary cannot meaningfully test the phase — it is recorded as
**SKIP**, not FAIL (see Step 0).

| Phase | Required MCP servers (default) | Why |
|-------|-------------------------------|-----|
| `requirements` | `awesome-copilot`, `context7` | Reference catalog patterns, library docs for requirements quality |
| `design` | `awesome-copilot`, `context7` | ADR/architecture patterns, library docs |
| `scaffold` | `awesome-copilot`, `context7` | Project scaffolding patterns, framework docs |
| `implement` | `awesome-copilot`, `context7` | Language best practices, API docs for implementation |
| `qa` | `awesome-copilot` | Security/code-quality guidance the QA gates are graded against |
| `document` | _(none)_ | Graded on prompt-contained content; MCP is advisory only |
| `deploy` | `awesome-copilot`, `azure` | Deployment patterns, Bicep/deployment schemas |
| `release` | `github` | Changelog/release data comes from the repo |
| `publish` | `github` | Publish verification against repo releases/tags |
| `rai` | `awesome-copilot` | Responsible-AI review guidance |

A canary spec may override this with its own `requires_mcp` list
(see `schemas/canary-spec.schema.json`). An explicit empty list (`requires_mcp: []`)
means the canary has no hard MCP dependency and always runs. All other servers
present in `.vscode/mcp.json` (e.g. `microsoft-learn`, `playwright`, `azure-devops`)
are treated as advisory: their status is recorded in `mcp_status` but never
triggers a SKIP.

## Step-by-Step Canary Run Procedure

### Step 0: MCP preflight (degraded-mode check)

Run this **before** discovering specs. A canary run is only as healthy as the
MCP servers behind it — never let a dead server silently turn into a FAIL.

1. Read the server list from `.vscode/mcp.json` (fallback:
   `skills/sdlc-workspace-init/assets/mcp.template.json`).
2. For each server, determine its status — one of `ready`, `unavailable`, `unknown` —
   and record a short `reason`:
   - **Docker-based stdio** (`command: "docker"`, e.g. `awesome-copilot`):
     run `docker info`. If it fails → `unavailable` (`docker daemon not reachable`).
     If the daemon is up, run `docker image inspect <image>`. If the image is
     missing locally, attempt `docker pull <image>` with a 300s timeout (first
     pull of the .NET image is large and routinely exceeds MCP client spawn
     timeouts — pre-pulling here prevents that). If the image is still missing
     afterwards → `unavailable` (`image not present/pullable: <reason>`).
   - **npx-based stdio**: check `npx --version`. If present → `ready`
     (shallow check: the runtime exists; the package itself is resolved at spawn).
     If npx is missing → `unavailable`.
   - **http**: → `ready` (endpoint assumed reachable; not probed).
   - Anything else → `unknown` with a reason; `unknown` never triggers a SKIP.
3. Write the resulting map to the run's `mcp_status` field, e.g.:
   ```json
   "mcp_status": {
     "awesome-copilot": { "status": "unavailable", "reason": "docker daemon not reachable" },
     "github": { "status": "ready", "reason": "http endpoint" },
     "context7": { "status": "ready", "reason": "npx present (shallow check)" }
   }
   ```
4. Resolve each canary's required servers later (Step 2) against this map.
   If **any** required server is `unavailable`, that canary is SKIP.

### Step 1: Discover specs

Read all `.yaml` files recursively from `bench/canaries/`. Each file is one test case.

```
bench/canaries/
  requirements/req-001-ecommerce-api.yaml
  design/des-001-ecommerce-architecture.yaml
  scaffold/scf-001-fastapi-project.yaml
  implement/impl-001-crud-endpoint.yaml
  qa/qa-001-security-review.yaml
  document/doc-001-api-documentation.yaml
  deploy/dep-001-azure-webapp.yaml
  release/rel-001-changelog-generation.yaml
  publish/pub-001-publish-release-execution.yaml
  rai/rai-001-bias-assessment.yaml
```

Parse each spec and extract: `id`, `phase`, `title`, `prompt`, `expected.graders`, `timeout_seconds`.

### Step 2: Run each canary

For each spec:

1. Look up the target agent from the routing table above.
2. **Degraded-mode check.** Resolve the canary's required MCP servers: the spec's
   `requires_mcp` if present, otherwise the phase default from the table above.
   If any required server has preflight status `unavailable`, do NOT invoke the
   agent. Record the result immediately as:
   ```json
   {
     "id": "<canary-id>",
     "phase": "<phase>",
     "title": "<title>",
     "agent": "<agent>",
     "verdict": "SKIP",
     "skip_reason": "mcp_unavailable",
     "missing_mcp": ["awesome-copilot"],
     "mcp_detail": "docker daemon not reachable"
   }
   ```
   Skipped canaries are excluded from grading and from the composite score.
3. Delegate to that agent with **exactly** the `prompt` field from the spec as input.
   - Use the agent's normal invocation — canary mode uses the SAME agents and SAME evaluation gates as production.
   - Do NOT inject extra instructions or modify the prompt.
4. Collect the full agent response text.
5. Grade the response (see Step 3).
6. Record the result.

**Run canaries sequentially** to avoid context overflow. If a phase agent returns an error or times out, record it as FAIL with reason "agent_error".

### Step 3: Grade the response

Apply each grader in `expected.graders` and compute a weighted score.

#### Keyword grader (`type: keyword`)

Check the response text (case-insensitive) against `config.required` and `config.forbidden`:

- For each required keyword present in the response: +1 point.
- For each forbidden keyword present in the response: deduct 1 point.
- Score = `max(0, matched_required / total_required - forbidden_penalty)`.
- Keyword grader passes if score ≥ 0.8.

#### Structural grader (`type: structural`)

Check that each section in `config.required_sections` appears in the response as a heading or label (case-insensitive substring match):

- Score = `sections_found / total_sections`.
- Structural grader passes if score ≥ 0.7.

#### LLM-judge grader (`type: llm-judge`)

Evaluate the response yourself against the criteria in `config.criteria`:

- For each criterion, assess on a 0–1 scale:
  - 1.0 = fully meets the criterion
  - 0.5 = partially meets
  - 0.0 = does not meet
- Score = `average of all criteria scores`.
- LLM-judge passes if score ≥ 0.7.

#### Composite score

```
composite = sum(grader.weight * grader.score for each grader)
```

All grader weights in a spec should sum to 1.0. If they don't, normalize before computing.

#### Phase-specific gate checks

- For `qa` canaries, verify the output explicitly enforces production QA gates:
  - Security threshold `>= 8`
  - Non-security thresholds `>= 7`
  - Weighted composite formula `(security × 1.5 + sum(others)) / 8.5`
  - Automatic fail when composite `< 7`
  - Automatic fail on any Critical finding
- For `publish` canaries, verify the output includes an explicit go/no-go publish decision
  and blocks publication when required phase gates or artifacts are missing.

#### Pass/Fail/Skip determination

A canary **PASSES** if:
- Composite score ≥ 0.7, AND
- No individual grader score < 0.5.

A canary **FAILS** if:
- Composite score < 0.7, OR
- Any individual grader score < 0.5.

A canary is **SKIPPED** (never graded, never counted as pass or fail) if:
- Any of its required MCP servers was `unavailable` at preflight (Step 0).

The run-level `composite_score` is computed over graded canaries only
(passed + failed); skipped canaries are excluded from both numerator and
denominator.

### Step 4: Write results to `bench/results/`

After all canaries complete, write a JSON result file:

**Filename format:** `canary-run-{YYYY-MM-DD}.json`

**JSON structure:**
```json
{
  "run_id": "canary-run-2026-04-13",
  "timestamp": "2026-04-13T07:30:00Z",
  "mode": "degraded",
  "mcp_status": {
    "awesome-copilot": { "status": "unavailable", "reason": "docker daemon not reachable" },
    "github": { "status": "ready", "reason": "http endpoint" },
    "context7": { "status": "ready", "reason": "npx present (shallow check)" }
  },
  "summary": {
    "total": 10,
    "passed": 6,
    "failed": 1,
    "skipped": 3,
    "composite_score": 0.87
  },
  "results": [
    {
      "id": "req-001-ecommerce-api",
      "phase": "requirements",
      "title": "E-commerce API Requirements Generation",
      "agent": "Analyst",
      "verdict": "PASS",
      "composite_score": 0.91,
      "grader_scores": {
        "keyword": { "score": 0.95, "passed": true, "matched": 9, "required": 10, "forbidden_found": [] },
        "structural": { "score": 0.80, "passed": true, "sections_found": 4, "sections_required": 5, "missing": ["acceptance criteria"] },
        "llm-judge": { "score": 0.90, "passed": true, "criteria": {"completeness": 0.9, "testability": 0.9, "specificity": 0.8, "prioritization": 0.9, "coverage_of_all_domains": 0.9} }
      },
      "duration_seconds": 45
    },
    {
      "id": "impl-001-crud-endpoint",
      "phase": "implement",
      "title": "CRUD Endpoint Implementation",
      "agent": "Implementer",
      "verdict": "SKIP",
      "skip_reason": "mcp_unavailable",
      "missing_mcp": ["awesome-copilot"],
      "mcp_detail": "docker daemon not reachable"
    }
  ]
}
```

- `mode` is `"full"` when every required server was ready, `"degraded"` when any
  canary was skipped due to MCP unavailability.
- `mcp_status` is the Step 0 preflight map — always present, even in full mode.
- `summary.skipped` counts SKIP verdicts. `summary.total` = passed + failed + skipped.

### Step 5: Report to the user

Present a concise summary table:

```
## Canary Run Results — 2026-04-13

| ID | Phase | Title | Score | Verdict |
|----|-------|-------|-------|---------|
| req-001 | requirements | E-commerce API Requirements | 0.91 | ✅ PASS |
| des-001 | design        | E-commerce Architecture    | 0.88 | ✅ PASS |
| scf-001 | scaffold      | FastAPI Project Scaffolding | —   | ⏭️ SKIP (mcp_unavailable: awesome-copilot) |
...

**Summary:** 6 passed, 1 failed, 3 skipped / 10 total | Composite: 0.87 (graded only)
**Mode:** degraded — 3 canaries skipped, `awesome-copilot` unavailable (docker daemon not reachable)
**Results:** bench/results/canary-run-2026-04-13.json
```

- In degraded mode, lead with the banner: which servers were unavailable and how
  many canaries were skipped because of it. Never present a degraded run as a
  clean pass.
- For each FAIL, include:
  - Which grader(s) failed and why (missing keywords, missing sections, low LLM scores).
  - The specific criterion or keyword that caused the failure.
  - For `qa` and `publish` canaries, explicitly include gate failure reasons (threshold breach,
    Critical finding, missing required release/publish prerequisites).
- For each SKIP, include the missing server(s) and the preflight reason, so the
  user knows exactly what to fix (e.g. start Docker, pre-pull the image) to get
  a full run.

## Running a Single Canary

If the user specifies a canary ID (e.g., "run canary qa-001"), run only that spec.
Follow the same procedure but skip the discovery step and report a single-row table.

## Canary vs Production Mode Differences

| Aspect | Production | Canary |
|--------|-----------|--------|
| Input source | User message | `prompt` field from YAML spec |
| Output destination | Chat response | `bench/results/` JSON file |
| Evaluation | Human review | Automated graders + LLM-judge |
| Agents invoked | Based on task | Based on `phase` routing table |
| Feedback loop | User can iterate | One-shot, grade and record |
