# Expected Findings — Agent E2E Canary Test

This file documents ALL planted issues ("canaries") in the test project.
After running a full QA review via `@Harness`, compare the agent output against
this list to measure reviewer detection rates.

## Scoring

- **Detection Rate** = (found canaries / total canaries) × 100%
- **Target**: 80%+ per reviewer, 90%+ overall
- **False Positive Rate**: track findings that don't match any canary

---

## Architecture Reviewer (2 canaries)

| # | File | Canary | Expected Finding |
|---|---|---|---|
| A1 | `app.py` | Controller (`/api/documents`) directly calls `CosmosClient` | Layering violation — controller calls infrastructure directly |
| A2 | `app.py` | No service/application layer — routes go straight to SDK | Missing Application layer in API → Application → Domain |

---

## Azure Compliance Reviewer (8 canaries)

| # | File | Canary | Expected Finding |
|---|---|---|---|
| AZ1 | `app.py` | `from azure.cosmos import CosmosClient` | Should use `sas-cosmosdb` with RepositoryBase |
| AZ2 | `app.py` | `from azure.storage.blob import BlobServiceClient` | Should use `sas-storage` with AsyncStorageBlobHelper |
| AZ3 | `app.py` | `CosmosClient.from_connection_string()` | Should use DefaultAzureCredential, not connection string |
| AZ4 | `main.bicep` | Raw resource definitions | Should use AVM modules (`br/public:avm/res/...`) |
| AZ5 | `main.bicep` | No `tags` on resource group | Must include `azd-env-name`, `TemplateName`, `CreatedBy` tags |
| AZ6 | `main.bicep` | No WAF toggle parameters | Must include `enablePrivateNetworking`, `enableMonitoring` |
| AZ7 | `main.bicep` | No diagnostics configuration | Resources must send logs to Log Analytics |
| AZ8 | `app.py` | No `async with` context manager on blob client | sas-storage requires `async with` pattern |

---

## Code Quality Reviewer (6 canaries)

| # | File | Canary | Expected Finding |
|---|---|---|---|
| CQ1 | `app.py` | No copyright header | Missing Microsoft copyright header |
| CQ2 | `App.tsx` | No copyright header | Missing Microsoft copyright header |
| CQ3 | `app.py` | `print("Starting application...")` | Debug statement — use structured logging |
| CQ4 | `App.tsx` | `console.log("App rendered")` | Debug statement — remove before production |
| CQ5 | `app.py` | Functions lack proper docstrings | Missing docstrings on public functions |
| CQ6 | `App.tsx` | `console.log("clicked")` in onClick handler | Debug statement in production code |

---

## Security Reviewer (9 canaries)

| # | File | Canary | Expected Finding |
|---|---|---|---|
| S1 | `app.py` | `OPENAI_API_KEY = "sk-proj-abc123..."` | Hardcoded API key in source code |
| S2 | `app.py` | `COSMOS_CONNECTION_STRING = "AccountEndpoint=..."` | Hardcoded connection string |
| S3 | `app.py` | `AccountKey=abc123==` in blob connection string | Hardcoded storage key |
| S4 | `app.py` | No auth on any endpoint | A01: Broken Access Control — no authorization |
| S5 | `app.py` | `str(exc), repr(exc.__traceback__)` in error handler | Error message leaks internal details |
| S6 | `app.py` | No input validation/sanitization on `create_document` | A03: Injection — unsanitized input to Cosmos |
| S7 | `App.tsx` | `dangerouslySetInnerHTML` without sanitization | XSS vulnerability |
| S8 | `main.bicep` | `apiKey: 'sk-proj-hardcoded-key-in-bicep-12345'` | Secret in Bicep template |
| S9 | `main.bicep` | `subscriptionId = '12345678-...'` | Hardcoded subscription ID |

---

## Test Coverage Reviewer (3 canaries)

| # | File | Canary | Expected Finding |
|---|---|---|---|
| TC1 | (none) | No `tests/` directory exists | No tests for any code |
| TC2 | (none) | No `playwright.config.ts` exists | No Playwright e2e tests for frontend |
| TC3 | (none) | No `pytest` or `vitest` config | No test framework configured |

---

## UX & Accessibility Reviewer (10 canaries)

| # | File | Canary | Expected Finding |
|---|---|---|---|
| UX1 | `App.tsx` | `<img src="/logo.png" />` without `alt` | Missing alt attribute on image |
| UX2 | `App.tsx` | `<div onClick={...}>` without `onKeyDown` | Interactive div has no keyboard handler |
| UX3 | `App.tsx` | `outline: "none"` in inputStyle | Focus indicator removed without replacement |
| UX4 | `App.tsx` | `backgroundColor: "#1a1a2e"` hardcoded | Should use CSS variable for theme support |
| UX5 | `App.tsx` | `width: "2000px"` on header | Fixed width exceeds standard viewport |
| UX6 | `App.tsx` | No `onKeyDown` on input for Enter key | Enter key doesn't submit message |
| UX7 | `App.tsx` | No empty state when `messages` is empty | Blank area shown instead of helpful message |
| UX8 | `App.tsx` | No Error Boundary component | App will crash on render error with white screen |
| UX9 | `App.tsx` | No `aria-label` on interactive div | Interactive element has no accessible name |
| UX10 | `App.tsx` | No input validation before sendMessage | Can submit empty message |

---

## LLM Behavior Reviewer (7 canaries)

| # | File | Canary | Expected Finding |
|---|---|---|---|
| LLM1 | `system_prompt.txt` | No prompt injection guard | Missing "do not reveal instructions" clause |
| LLM2 | `system_prompt.txt` | No out-of-scope handling instruction | No "decline unrelated questions" clause |
| LLM3 | `system_prompt.txt` | No identity protection | No "stay in persona" instruction |
| LLM4 | `app.py` | No `max_tokens` in API call | Context window overflow risk |
| LLM5 | `app.py` | No retry logic on chat endpoint | No handling for 429/5xx from LLM |
| LLM6 | `app.py` | No content filter configuration | No Azure AI Content Safety integration |
| LLM7 | `app.py` | Chat response returned raw without citation | No citation/reference pattern |

---

## Deployment Readiness Reviewer (9 canaries)

| # | File | Canary | Expected Finding |
|---|---|---|---|
| DR1 | `app.py` | No `/health` endpoint | Missing health check |
| DR2 | `app.py` | No global exception handler (existing one leaks details) | Error handler exposes internals |
| DR3 | `app.py` | `print()` instead of structured logging | No logging framework |
| DR4 | `app.py` | No correlation ID / request tracing | Missing observability |
| DR5 | `app.py` | `requests.post()` without `timeout=` | External HTTP call has no timeout |
| DR6 | `app.py` | `SELECT * FROM c` without LIMIT/TOP | Unbounded query |
| DR7 | `README.md` | Missing: prerequisites, deployment steps, configuration, troubleshooting, known issues, license | Incomplete README (6 missing sections) |
| DR8 | (none) | No `pyproject.toml` or `package.json` | No dependency manifest |
| DR9 | `app.py` | No pagination on `/api/documents` | List API has no offset/limit |

---

## Summary

| Reviewer | Canaries | Notes |
|---|---|---|
| Architecture | 2 | Layering violations |
| Azure Compliance | 8 | Raw SDK, no AVM, no tags/diagnostics |
| Code Quality | 6 | Copyright, debug code, docstrings |
| Security | 9 | Secrets, XSS, no auth, injection |
| Test Coverage | 3 | No tests at all |
| UX & Accessibility | 10 | Missing a11y, hardcoded styles, no keyboard |
| LLM Behavior | 7 | Prompt safety, no retry, no filters |
| Deployment Readiness | 9 | Health, logging, README, timeouts |
| **Total** | **54** | |

## How to run

```text
@Harness Run a full QA review on the e2e agent test project at tests/e2e-agent-test/.
Review all code, infrastructure, and documentation.
```

Then compare the QA Review Summary output against this file.
Count how many canaries each reviewer found vs. how many were planted.
