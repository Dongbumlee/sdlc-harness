---
name: sdlc-reviewer-output-format
description: >-
  Structured YAML output format for SDLC QA reviewer agents.
  Ensures consistent, parseable review output across all 8 reviewer domains.
  Use in conjunction with each reviewer's existing Markdown report format.
---

# SDLC Reviewer Structured Output Format

All 8 QA reviewer agents MUST emit a structured YAML block at the **end** of their response.
This block is parsed by the QA Coordinator to aggregate scores, apply hard-fail rules, and
generate the synthesis report.

## Format Specification

Place the YAML block at the very end of the review response, **after** the Markdown report.
The Markdown report comes first for human readability; the YAML block is additive.

```
---sdlc-review-output---
reviewer: "<agent display name>"
phase: "<sdlc-phase being reviewed>"
score: <1-10>
verdict: PASS | FAIL | CRITICAL_FAIL
findings:
  - severity: critical | high | medium | low
    category: <domain-specific category — see list below>
    description: "<finding description>"
    location: "<file:line or component name>"
    recommendation: "<how to fix>"
reasoning: "<2-3 sentence evaluation summary>"
---end-sdlc-review-output---
```

## Field Rules

| Field | Rule |
|-------|------|
| `reviewer` | Exact agent display name (e.g., `"Security Reviewer"`) |
| `phase` | SDLC phase being reviewed (e.g., `"Phase 4 - Implementation"`) |
| `score` | Integer 1–10. Must be consistent with the Markdown `Quality Score: X/10` |
| `verdict` | `PASS` if score meets threshold and no critical findings; `FAIL` if score below threshold; `CRITICAL_FAIL` if any finding has severity `critical` |
| `findings` | List of all findings. May be empty (`[]`) for a clean review. Include ALL findings from the Markdown report |
| `severity` | `critical` = must fix before merge; `high` = important; `medium` = suggestion; `low` = minor |
| `category` | Domain-specific value from the list below. Use the most specific applicable category |
| `description` | Concise description of the finding |
| `location` | File and line number preferred (e.g., `src/api/routes.py:45`); component name acceptable when line not applicable |
| `recommendation` | Concrete action to fix the finding |
| `reasoning` | 2–3 sentences summarizing the evaluation. Must reference specific findings, not generic praise |

## Score Thresholds & Verdict Rules

| Domain | Pass Threshold | Notes |
|--------|---------------|-------|
| Security Reviewer | ≥ 8 | Higher bar — security issues are never minor |
| All other 7 reviewers | ≥ 7 | Standard production threshold |

**Verdict assignment:**
- Any finding with `severity: critical` → verdict MUST be `CRITICAL_FAIL` regardless of score
- Score below threshold → verdict MUST be `FAIL`
- Score at or above threshold AND no critical findings → verdict is `PASS`

## Domain-Specific Category Values

Use the categories matching your reviewer domain:

### Architecture Reviewer
`layering` | `dependency-direction` | `pattern-reuse` | `god-service` | `cross-layer-shortcut` | `template-alignment` | `documentation-structure`

### Azure Compliance Reviewer
`sdk-abstraction` | `repository-pattern` | `context-manager` | `identity` | `bicep-avm` | `waf-toggles` | `resource-tags` | `diagnostics` | `secrets`

### Code Quality Reviewer
`copyright` | `docstrings` | `naming` | `dead-code` | `comments` | `error-handling` | `type-safety` | `imports` | `function-size` | `dry` | `terminology` | `placeholder-text` | `debug-code`

### Deployment Readiness Reviewer
`error-exposure` | `rate-limiting` | `exception-handler` | `timeout` | `validation` | `unbounded-query` | `n-plus-one` | `pagination` | `readme` | `hyperlinks` | `stale-refs` | `debug-code` | `dependencies` | `logging` | `health-check` | `correlation-ids` | `sensitive-logs`

### LLM Behavior Reviewer
`system-prompt-protection` | `content-filter` | `prompt-injection` | `citation` | `grounding` | `ai-disclaimer` | `multi-turn-context` | `token-limits` | `retry-logic` | `file-type-validation` | `file-size-limits` | `filename-sanitization` | `encoding` | `placeholder-text`

### Security Reviewer
`access-control` | `cryptographic-failures` | `injection` | `insecure-design` | `security-misconfiguration` | `vulnerable-components` | `auth-failures` | `data-integrity` | `logging-failures` | `ssrf` | `secrets` | `credentials` | `cors` | `security-headers` | `cve` | `cdn-audit` | `content-licensing` | `xss` | `error-opacity`

### Test Coverage Reviewer
`test-existence` | `aaa-structure` | `test-naming` | `test-isolation` | `mocking` | `edge-cases` | `assertions` | `coverage-threshold` | `test-pollution` | `integration-tests` | `file-upload` | `international-chars` | `error-paths` | `empty-state` | `playwright-a11y` | `cross-browser` | `keyboard-nav` | `console-errors`

### UX & Accessibility Reviewer
`hardcoded-colors` | `fixed-widths` | `aria-labels` | `alt-text` | `keyboard-handlers` | `focus-indicators` | `enter-key` | `color-contrast` | `form-validation` | `navigation-guards` | `state-reset` | `error-boundary` | `empty-state`

## Example (Clean Review)

```
---sdlc-review-output---
reviewer: "Architecture Reviewer"
phase: "Phase 4 - Implementation"
score: 8
verdict: PASS
findings: []
reasoning: "Code correctly follows API → Application → Domain layering with no cross-layer shortcuts detected. Repository pattern is consistently applied across all new services. Minor template alignment gap in folder naming does not affect production behavior."
---end-sdlc-review-output---
```

## Example (Review With Findings)

```
---sdlc-review-output---
reviewer: "Security Reviewer"
phase: "Phase 4 - Implementation"
score: 5
verdict: CRITICAL_FAIL
findings:
  - severity: critical
    category: secrets
    description: "Azure storage connection string hardcoded in config.py"
    location: "src/config/config.py:42"
    recommendation: "Remove hardcoded string. Load from Azure Key Vault or environment variable."
  - severity: high
    category: injection
    description: "User input concatenated into Cosmos DB query without sanitization"
    location: "src/repositories/claim_repository.py:87"
    recommendation: "Use parameterized queries via the approved SDK wrapper."
  - severity: medium
    category: cors
    description: "CORS configured with wildcard origin in production config"
    location: "src/api/middleware.py:23"
    recommendation: "Restrict CORS origins to known domains."
reasoning: "Critical: hardcoded storage secret exposes credentials in version control. High: unsanitized query input creates injection risk. Security score 5/10 — two pre-merge blockers require immediate remediation before deployment."
---end-sdlc-review-output---
```

## QA Coordinator Parsing Reference

The QA Coordinator extracts YAML blocks by:
1. Finding the `---sdlc-review-output---` delimiter
2. Reading content until `---end-sdlc-review-output---`
3. Parsing the YAML to extract `score`, `verdict`, and `findings`
4. Applying hard-fail rules across all 8 parsed blocks
