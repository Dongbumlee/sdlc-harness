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

세 클라우드 공통:
1. **gemini-2.0-flash 단종 (404)** — 3곳 전부 걸림. 모델 ID는 env 주입, 하드코딩 금지.
2. **Invalid key = HTTP 400** (401/403 아님) — 3곳 전부. 바디 보고 `llm_auth` 매핑해야 함.
3. **Free-tier 쿼터 ~15–20 calls/day** — E2E+디버깅 몇 번에 바닥남.

클라우드별:
- GCP: 429 미매핑 → brief가 `running`에 고착. catch-all 추가. Cloud Run Job cold start ~4분.
- AWS: SQS→Fargate 직접 연결 불가 (poller Lambda + RunTask 필요). Cold VPC Lambda 첫 호출 hang (ENI).
- Azure: Key Vault 시크릿이 배포보다 먼저 있어야 함 + 시크릿명에 언더스코어 불가. 간헐적 503 → 재시도 추가.

## Caveats

- GCP happy-path 6분 — 스펙 3분 목표 미달 (cold start 4분). 목표 조정 or warm 정책 필요.
- Azure happy-path는 OpenRouter `openrouter/free`로 검증 (Gemini free tier 2일간 503). 스펙 이탈이므로 결과에 별표. `LLM_PROVIDER` env 스위치로 코드 포크 없이 전환 가능하게 구현됨.

## Pack gaps

- GCP `PACK_GAPS.md` #17–21, AWS (4건), Azure `PACK_GAPS.md` #6–12 — 각 리포트에 기록됨. 팩 반영은 별도 작업.

## Cost

- LLM: $0.00 (3곳 모두)
- Infra: ~$0 (scale-to-zero; Azure overnight ~$0.40)
- Teardown 후 잔여 리소스 0건 확인 (3곳 모두)

---
*Detail: `gcp/brief/TEST_REPORT.md`, `aws/brief/TEST_REPORT.md`, `azure/brief/TEST_REPORT.md` (each worktree)*
