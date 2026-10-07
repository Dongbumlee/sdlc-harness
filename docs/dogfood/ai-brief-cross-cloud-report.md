# AI Brief (Scenario 5) — 3-Cloud Test Report

**Date:** 2026-10-04 ~ 10-05 (PDT) · **Spec:** `reference-app-spec-3.md` · **Model:** `gemini-3.8-flash` · **LLM cost:** $0 (all clouds, free tier)

## Result

| Cloud | Deploy | E2E | Happy-path | Teardown |
|---|---|---|---|---|
| GCP | ✅ | 5/5 PASS | ✅ done (~6 min, Gemini) | ✅ 0 residuals |
| AWS | ✅ | 5/5 PASS | ✅ done ×2 (Gemini) | ✅ 0 residuals |
| Azure | ✅ | non-LLM PASS | ✅ done (OpenRouter `openrouter/free`*) | ✅ 0 residuals |

\* Azure: Gemini free tier 503 for 2 days → spec-deviation fallback to OpenRouter. See below.

## Bugs found by real deploy (all fixed)

Common to all three clouds:
1. **gemini-2.0-flash retired (404)** — hit all three. Model ID must come from env injection; hardcoding forbidden.
2. **Invalid key = HTTP 400** (not 401/403) — all three. Map `llm_auth` from the response body.
3. **Free-tier quota ~15–20 calls/day** — exhausted after a few E2E + debug runs.

Per cloud:
- GCP: unmapped 429 → brief stuck in `running`. Added catch-all. Cloud Run Job cold start ~4 min.
- AWS: SQS→Fargate direct wiring not possible (poller Lambda + RunTask required). Cold VPC Lambda hangs on first invocation (ENI).
- Azure: Key Vault secrets must exist before deploy + no underscores in secret names. Intermittent 503 → added retry.

## Caveats

- GCP happy-path 6 min — missed the 3-min spec target (cold start 4 min). Target needs adjusting or a warm policy.
- Azure happy-path verified via OpenRouter `openrouter/free` (Gemini free tier 503 for 2 days). Spec deviation — flagged in results. Implemented as an `LLM_PROVIDER` env switch so no code fork is needed to switch providers.

## Pack gaps

- GCP `PACK_GAPS.md` #17–21, AWS (4 items), Azure `PACK_GAPS.md` #6–12 — recorded in each report. Pack reflection is separate work.

## Cost

- LLM: $0.00 (all three)
- Infra: ~$0 (scale-to-zero; Azure overnight ~$0.40)
- Zero residual resources confirmed after teardown (all three)

---
*Detail: `gcp/brief/TEST_REPORT.md`, `aws/brief/TEST_REPORT.md`, `azure/brief/TEST_REPORT.md` (each worktree)*
