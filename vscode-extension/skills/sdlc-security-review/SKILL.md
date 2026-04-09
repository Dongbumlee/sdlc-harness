---
name: sdlc-security-review
description: >-
  Perform SDLC-aligned security review combining OWASP Top 10 with SAS-specific
  Azure patterns. Use when reviewing code for security vulnerabilities, secrets
  exposure, auth issues, injection risks, or OWASP compliance. Triggers on any
  code review, PR review, or security audit request. Loads fresh OWASP checklist
  from awesome-copilot MCP on every review.
---

# SDLC Security Review

Perform a security-focused code review aligned with SDLC Phase 6 and OWASP Top 10.

## Step 1: Load OWASP checklist (every review — do not cache)

Load the latest OWASP security guidance from awesome-copilot MCP:

```
mcp_awesome-copil_load_instruction(
  filename: "security-and-owasp.instructions.md",
  mode: "instructions"
)
```

Also load the AI safety review skill if the change involves AI/LLM code:

```
mcp_awesome-copil_load_instruction(
  filename: "ai-prompt-engineering-safety-review/SKILL.md",
  mode: "skills"
)
```

## Step 2: OWASP Top 10 checklist

For each item, check the code under review and mark PASS / FAIL / N/A:

| # | Category | What to check |
|---|---|---|
| A01 | Broken Access Control | Authorization checks on all endpoints, RBAC enforced |
| A02 | Cryptographic Failures | No secrets in source, proper encryption, Key Vault usage |
| A03 | Injection | Parameterized queries, no string-concatenated SQL/commands |
| A04 | Insecure Design | Threat model considered, rate limiting present |
| A05 | Security Misconfiguration | No debug mode in prod, secure defaults |
| A06 | Vulnerable Components | Dependencies from approved list, versions current |
| A07 | Auth Failures | Proper session management, MFA where required |
| A08 | Data Integrity | Input validation on all user inputs |
| A09 | Logging Failures | Security events logged, no sensitive data in logs |
| A10 | SSRF | External URLs validated, no uncontrolled redirects |

## Step 3: SAS-specific Azure security checks

These are project-specific patterns that agents wouldn't know without this skill:

### Identity & Authentication
- `DefaultAzureCredential` or `ManagedIdentityCredential` — never connection string auth
- Key Vault for all secrets — never environment variables with sensitive values in production
- RBAC with least privilege — no `Owner` or `Contributor` at subscription level

### Azure SDK abstraction
- `your-cosmosdb-lib` (not raw `azure-cosmos`) — the library handles auth securely
- `your-storage-lib` (not raw `azure-storage-blob`) — the library handles team tokens securely
- `async with` context manager — ensures connections are properly closed

### Container Apps
- No secrets in container environment variables — use Key Vault references
- Health/readiness probes configured
- Ingress restricted to internal where possible

### CORS
- Not wildcard `*` in production — explicit allowed origins only

### Headers
- CSP, HSTS, X-Frame-Options, X-Content-Type-Options set

## Step 4: Secrets scanning

Search the code change for potential secrets:

- API keys (patterns: `sk-`, `AKIA`, `ghp_`, `gho_`)
- Connection strings (patterns: `AccountKey=`, `Password=`, `pwd=`)
- Tokens (patterns: `Bearer `, `token=`, `secret=`)
- Base64-encoded secrets (long random strings in config files)

If found: **CRITICAL** — must be removed and rotated immediately.

## Step 5: Dependency audit

Check `pyproject.toml` or `package.json` for:
- Packages NOT in `.github/reference-catalog.md` — flag for review
- Known CVE versions — check against the latest advisories
- Dev dependencies leaking into production builds

## Gotchas

- `your-cosmosdb-lib` handles partition key routing internally — do NOT add custom
  partition key logic that could bypass the library's security isolation.
- `your-storage-lib` generates User Delegation team with clock skew protection — do NOT
  generate team tokens manually using the raw SDK.
- FastAPI's `Depends()` with `DefaultAzureCredential` must be scoped per-request,
  not cached as a singleton (token refresh).

## Output format

Return findings as:
- **Critical**: Secrets in code, injection vulnerabilities, broken auth
- **Important**: Missing input validation, insecure defaults, CORS issues
- **Suggestion**: Security hardening improvements
- **Positive**: Security practices done well
