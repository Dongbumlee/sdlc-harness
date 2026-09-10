---
name: sdlc-canary-runner
description: "Instructs the Harness agent how to run E2E canary tests against SDLC phase agents. Canary mode validates that the harness orchestration is working correctly by feeding known prompts to phase agents and checking outputs against expected criteria."
version: "1.0"
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
| `rai` | RAI Reviewer | `rai-` |

## Step-by-Step Canary Run Procedure

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
  rai/rai-001-bias-assessment.yaml
```

Parse each spec and extract: `id`, `phase`, `title`, `prompt`, `expected.graders`, `timeout_seconds`.

### Step 2: Run each canary

For each spec:

1. Look up the target agent from the routing table above.
2. Delegate to that agent with **exactly** the `prompt` field from the spec as input.
   - Use the agent's normal invocation — canary mode uses the SAME agents and SAME evaluation gates as production.
   - Do NOT inject extra instructions or modify the prompt.
3. Collect the full agent response text.
4. Grade the response (see Step 3).
5. Record the result.

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

#### Pass/Fail determination

A canary **PASSES** if:
- Composite score ≥ 0.7, AND
- No individual grader score < 0.5.

A canary **FAILS** if:
- Composite score < 0.7, OR
- Any individual grader score < 0.5.

### Step 4: Write results to `bench/results/`

After all canaries complete, write a JSON result file:

**Filename format:** `canary-run-{YYYY-MM-DD}.json`

**JSON structure:**
```json
{
  "run_id": "canary-run-2026-04-13",
  "timestamp": "2026-04-13T07:30:00Z",
  "summary": {
    "total": 9,
    "passed": 8,
    "failed": 1,
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
    }
  ]
}
```

### Step 5: Report to the user

Present a concise summary table:

```
## Canary Run Results — 2026-04-13

| ID | Phase | Title | Score | Verdict |
|----|-------|-------|-------|---------|
| req-001 | requirements | E-commerce API Requirements | 0.91 | ✅ PASS |
| des-001 | design        | E-commerce Architecture    | 0.88 | ✅ PASS |
| scf-001 | scaffold      | FastAPI Project Scaffolding | 0.85 | ✅ PASS |
...

**Summary:** 8/9 passed | Composite: 0.87 | Results saved to bench/results/canary-run-2026-04-13.json
```

For each FAIL, include:
- Which grader(s) failed and why (missing keywords, missing sections, low LLM scores).
- The specific criterion or keyword that caused the failure.

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
