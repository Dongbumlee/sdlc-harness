---
name: sdlc-qa-bug-checklist
description: >-
  Bug-driven QA checklist distilled from 338 real bugs across 9 CSACTOSOL ADO
  projects with detailed error patterns, Azure error codes, and verification
  commands. Use when reviewing code, PRs, deployments, or running QA checks.
  Triggers on any QA review, pre-deployment validation, or bug-prevention audit.
---

# SDLC QA Bug Checklist

Actionable QA checklist derived from **338 production bugs** across 9 CSACTOSOL projects.
Each item includes the **real error pattern**, **Azure error codes**, and **how to verify** —
so the agent or reviewer can detect the exact conditions that caused real bugs.

## Bug Distribution Summary

| SDLC Phase | Bugs | % | Priority |
|---|---|---|---|
| Deployment | 151 | 45% | 🔴 Critical |
| Implementation | 82 | 24% | 🟠 High |
| QA/Testing | 60 | 18% | 🟡 Medium |
| Release | 23 | 7% | 🟡 Medium |
| Security | 13 | 4% | 🔴 Critical |
| Documentation | 9 | 3% | 🟢 Low |

---

## Checklist 1: Deployment & Provisioning (151 bugs — 45%)

### 1.1 Resource Provisioning Failures

- [ ] **Cognitive Services provisioning state** (Bugs: 34949, 28494)
  - **Error**: `"reached terminal provisioning state 'Failed'"` on `Microsoft.CognitiveServices/accounts`
  - **Root cause**: Cognitive Services account fails, then its Private Endpoint also fails because the parent resource is in a Failed state
  - **How to verify**: `az cognitiveservices account show --name <name> -g <rg> --query provisioningState` — must return `"Succeeded"`
  - **Fix**: Add retry logic in Bicep with `dependsOn` and condition checks; redeploy the Cognitive Services resource before Private Endpoint

- [ ] **Function App host runtime unavailable** (Bug: 26532)
  - **Error**: `"Encountered an error (ServiceUnavailable) from host runtime"` on `functionKeys/clientKey`
  - **Root cause**: Docker-based Function App hasn't started when ARM tries to create function keys
  - **How to verify**: `az functionapp show --name <name> -g <rg> --query state` → `"Running"`, then `curl https://<func>.azurewebsites.net/api/health`
  - **Fix**: Increase deployment timeout; add delay before function key creation; verify container image pulls first

- [ ] **Private Endpoint cascading failures** (Bug: 28494)
  - **Error**: `"ResourceDeploymentFailure"` on `PrivateEndpoint-0` following parent resource failure
  - **Root cause**: When Cognitive Services fails, its Private Endpoint also fails — real error is hidden in parent
  - **How to verify**: If Private Endpoint fails, check parent: `az resource show --ids <parent-id> --query properties.provisioningState`

- [ ] **Quota exceeded for SKU** (13 bugs)
  - **Error**: `"InternalSubscriptionIsOverQuotaForSku"` for Basic VM tier, Cognitive Services TPM
  - **How to verify**: `az cognitiveservices usage list -l <region>` and `az vm list-skus -l <region> --query "[?restrictions]"`
  - **Fix**: Pre-flight quota check script; parameterize SKU names

### 1.2 Post-Deployment Script Failures

- [ ] **Embeddings permission denied in post-deploy** (Bug: 36697)
  - **Error**: `PermissionDenied` in `process_sample_data.sh` and `run_create_agents_scripts.sh` for embeddings action
  - **Root cause**: Managed identity lacks `Cognitive Services OpenAI User` for the embeddings model — chat completion perms alone are NOT sufficient
  - **How to verify**: `grep -i "PermissionDenied\|permission\|forbidden" <post-deploy-log>`
  - **Fix**: Assign RBAC for BOTH chat and embeddings model deployments in Bicep
  - **Validation matrix** — must pass ALL configs:
    ```
    ✅ WAF + EXP:         process_sample_data.sh → no PermissionDenied
    ✅ Non-WAF + EXP:     process_sample_data.sh → no PermissionDenied
    ✅ Non-WAF + Non-EXP: process_sample_data.sh → no PermissionDenied
    ```

- [ ] **Scripts exit 0 but contain errors** (38+ bugs)
  - **Root cause**: Post-deploy scripts complete successfully but logs contain error lines that are not caught
  - **How to verify**: Scripts must check for errors in output:
    ```bash
    # Bad: exits 0 even with errors
    ./process_sample_data.sh
    # Good: fail on any error in logs
    ./process_sample_data.sh 2>&1 | tee /tmp/deploy.log
    grep -iE "error|failed|denied|forbidden" /tmp/deploy.log && exit 1
    ```

### 1.3 AVM WAF vs Non-WAF Divergence

- [ ] **Network-related WAF failure** (Bug: 31226)
  - **Error**: Code Modernization AVM WAF fails with network AND cosmos error — Non-WAF works
  - **Root cause**: WAF enables private networking → DNS resolution changes, NSG rules differ, VNet integration breaks public endpoint code
  - **Fix**: All service-to-service communication must use private endpoints consistently; add VNet-integrated DNS zones

- [ ] **Application Insights removal causes blank page** (Bug: 35309)
  - **Repro**: Deploy WAF without EXP → Remove App Insights env var → Restart → Click "Start Translating" → **blank page, no error**
  - **Root cause**: Backend crashes on missing env var; frontend has no error boundary
  - **How to verify**: Search for optional env vars handled unsafely:
    ```python
    # Bad: crash if missing
    APPINSIGHTS = os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]
    # Good: graceful fallback
    APPINSIGHTS = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    ```

### 1.4 Pre-Deployment Verification Commands

```bash
# 1. Check Cognitive Services quota
az cognitiveservices usage list -l <region> -o table

# 2. Check VM SKU availability
az vm list-skus -l <region> --size <sku> -o table

# 3. Verify parameter files exist
ls infra/main.parameters.json infra/main.waf.parameters.json

# 4. Validate Bicep syntax
az bicep build --file infra/main.bicep --stdout > /dev/null

# 5. Check resource group for conflicts
az resource list -g <rg> --query "[].{name:name, type:type, state:provisioningState}" -o table
```

---

## Checklist 2: CosmosDB & Data Layer (8 bugs)

### 2.1 CosmosDB RBAC Data Plane Access

- [ ] **AAD token blocked on data plane** (Bug: 21980)
  - **Error**: `"(Forbidden) Request blocked by Auth <cosmos-name>: The given request [POST /dbs/<db>/colls/] cannot be authorized by AAD token in data plane. Learn more: https://aka.ms/cosmos-native-rbac"`
  - **Root cause**: Cosmos DB requires **native RBAC** (SQL role assignments) for data plane. Azure portal RBAC alone is NOT enough
  - **How to verify**:
    ```bash
    # Check native RBAC is enabled
    az cosmosdb show --name <name> -g <rg> --query "disableLocalAuth"
    # List SQL role assignments (must have entries)
    az cosmosdb sql role assignment list --account-name <name> -g <rg>
    # Create if missing
    az cosmosdb sql role assignment create --account-name <name> -g <rg> \
      --role-definition-id "00000000-0000-0000-0000-000000000002" \
      --principal-id <managed-identity-object-id> --scope "/"
    ```
  - **Fix**: In Bicep, use `Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments` — NOT just Azure RBAC

### 2.2 Database Initialization Race Conditions

- [ ] **Container creation fails on first request** (Bug: 21980)
  - **Root cause**: App lazy-initializes Cosmos containers on first API call, but MI lacks create permissions
  - **Fix**: Create containers in post-deployment script with proper RBAC, not at runtime

---

## Checklist 3: AI/ML & Agent Components (57 bugs — 17%)

### 3.1 Model Deployment & Permissions

- [ ] **Embeddings model separate RBAC** (Bug: 36697)
  - Chat completion works but embeddings returns `PermissionDenied` — separate RBAC needed
  - **How to verify**: `az cognitiveservices account deployment list --name <name> -g <rg> -o table` then check RBAC for each deployment

- [ ] **AI Foundry "Project not found"** (intermittent across multiple accelerators)
  - **Error**: `"Project not found"` immediately after deployment
  - **Root cause**: Azure AI Foundry eventual consistency — project created but not yet visible via API
  - **Fix**: Add retry with backoff in `run_create_agents_scripts.sh`:
    ```bash
    for i in 1 2 3 4 5; do
      result=$(create_agent) && break
      echo "Attempt $i failed, retrying in 30s..."
      sleep 30
    done
    ```

### 3.2 Model Availability & Quota

- [ ] **GPT model not available in region** (multiple bugs)
  - **How to verify**: `az cognitiveservices model list -l <region> --query "[?model.name=='gpt-4o']" -o table`
  - **Fix**: Parameterize model name/version; add pre-flight check

- [ ] **Jailbreak / prompt injection** (Bug: QA CWYD-Cosmos)
  - **Error**: "Getting backend jailbreak error"
  - **How to verify**: Search system prompt — must include content filtering instructions
  - **Fix**: Azure AI Content Safety + system prompt guards

### 3.3 Token & Response Errors

- [ ] **500 on large inputs** — prompt + response exceeds context window
- [ ] **429 rate limiting** — missing retry with exponential backoff
- [ ] **Raw error JSON shown to user** — no graceful fallback when model unavailable

---

## Checklist 4: Frontend/UI (40 bugs — 12%)

### 4.1 Blank Page Syndrome

- [ ] **Blank page after deployment** (Bugs: 35309, 39055)
  - **Pattern**: Deploy → page loads → perform action (upload/translate) → **blank white page, no error**
  - **Root causes**:
    1. Missing env var causes unhandled exception (Bug 35309: App Insights removed)
    2. Backend error but no frontend error boundary
    3. Long operation times out, React state corrupted
  - **How to verify**:
    ```bash
    # Check error boundaries exist
    grep -r "ErrorBoundary\|componentDidCatch\|error-boundary" src/
    # Check env vars are validated on startup
    grep -r "process.env\." src/ | grep -v "node_modules"
    ```
  - **Fix**: React Error Boundary at app root; validate all `process.env.*` on startup

### 4.2 File Upload & Processing

- [ ] **Intermittent upload failures** (Bug: 39055)
  - **Repro**: Upload files → fails 1st & 2nd attempt → succeeds 3rd → translation then fails for all files
  - **Root cause**: Race condition or connection pool exhaustion; no frontend retry
  - **Fix**: Frontend retry with backoff; backend connection pool tuning; proper error with retry-after header

- [ ] **Processing status shows "Error" incorrectly** (multiple bugs)
  - Backend returns partial success but frontend marks entire batch as "Error"
  - **Fix**: Backend must return per-file status, not batch-level error

### 4.3 State Management

- [ ] **Stale data between selections** (Bug: 15153)
  - Clicking unprocessed item shows output from previously clicked item
  - **Fix**: Clear component state on selection change; use key prop to force re-render

- [ ] **Duplicate warning messages** — messages rendered twice in chat history
- [ ] **Unfriendly error messages** — raw JSON or stack traces shown to users

---

## Checklist 5: API/Backend (23 bugs — 7%)

### 5.1 Health Endpoint

- [ ] **Shallow health check** (multiple bugs)
  - `/health` returns 200 but dependent services not connected
  - **Fix**: Deep health check that verifies downstream dependencies:
    ```python
    @app.get("/health")
    async def health():
        checks = {
            "cosmos": await check_cosmos_connection(),
            "openai": await check_openai_connection(),
            "storage": await check_storage_connection(),
        }
        all_ok = all(checks.values())
        return {"status": "healthy" if all_ok else "degraded", "checks": checks}
    ```

### 5.2 CORS & Networking

- [ ] **CORS policy error** (KM Generic and others)
  - **Error**: `"CORS Policy Error and 404 (Not Found) Issue"` after deployment
  - **How to verify**: `curl -H "Origin: https://<frontend>" -I https://<backend>/api/health` — check `Access-Control-Allow-Origin`
  - **Fix**: CORS origins must include actual frontend URL from deployment output, not hardcoded localhost

### 5.3 Error Handling

- [ ] **500 for all failures** — catch-all handler returns 500 even for client errors (should be 400)
- [ ] **502 from upstream timeouts** — long-running operations need proper timeout + retry
- [ ] **Admin API returns 502** (Bug: Content Generation) — post-provision step fails

---

## Checklist 6: Identity & Authentication (21 bugs — 6%)

### 6.1 Managed Identity RBAC Matrix

Every accelerator's managed identity must have these roles assigned in Bicep:

| Resource | Required Role | Verify |
|---|---|---|
| Cognitive Services (chat) | `Cognitive Services OpenAI User` | `az role assignment list --assignee <mi> --scope <cog>` |
| Cognitive Services (embeddings) | `Cognitive Services OpenAI User` | Same — per model deployment |
| Cosmos DB (data plane) | SQL Role Assignment (native) | `az cosmosdb sql role assignment list` |
| Key Vault | `Key Vault Secrets User` | `az role assignment list --assignee <mi> --scope <kv>` |
| Storage Account | `Storage Blob Data Contributor` | `az role assignment list --assignee <mi> --scope <sa>` |
| AI Foundry Project | `Azure AI Developer` | `az role assignment list --assignee <mi> --scope <proj>` |

### 6.2 Hardcoded Values

- [ ] **Hardcoded workspace names** (Bug: UDF Notebooks)
  - **How to verify**: `grep -rn "workspace_name\s*=\s*['\"]" . --include="*.py" --include="*.ipynb"`
- [ ] **Subscription-specific values**
  - **How to verify**: `grep -rn "subscriptions/[a-f0-9-]\{36\}" . --include="*.bicep" --include="*.json" --include="*.py"`
- [ ] **Fix**: Use `azd env get-values` or environment variables for all resource references

---

## Checklist 7: Smoke Testing Matrix (60 bugs discovered in QA)

Every accelerator must pass ALL cells before release:

| Config | Upload | Chat | Process | Admin | Post-Deploy Scripts |
|---|---|---|---|---|---|
| AVM Non-WAF + Non-EXP | ☐ | ☐ | ☐ | ☐ | ☐ |
| AVM Non-WAF + EXP | ☐ | ☐ | ☐ | ☐ | ☐ |
| AVM WAF + Non-EXP | ☐ | ☐ | ☐ | ☐ | ☐ |
| AVM WAF + EXP | ☐ | ☐ | ☐ | ☐ | ☐ |
| Dev Container / Codespace | ☐ | ☐ | ☐ | ☐ | N/A |

**Key rule**: A bug fixed in one config must be validated across ALL configs (Bug 36697 lesson).

---

## Top 5 Cross-Cutting Lessons from 338 Bugs

### 1. "Deployment Succeeded" ≠ "Application Works" (38+ bugs)
ARM/Bicep completing does NOT mean the app functions. Always verify:
(1) post-deploy scripts have no errors in logs, (2) `/health` checks pass with dependency verification, (3) core user flows work.

### 2. WAF Breaks What Non-WAF Doesn't (20+ bugs)
Private networking changes DNS, NSG rules, and VNet integration. Bug 31226: works Non-WAF, fails WAF. Bug 35309: removing App Insights var → blank page only in WAF.

### 3. Cosmos DB Native RBAC ≠ Azure Portal RBAC (Bug: 21980)
Azure portal role assignment does NOT grant data plane access. Use `sqlRoleAssignments` in Bicep or `az cosmosdb sql role assignment create` CLI.

### 4. Embeddings ≠ Chat Completion Permissions (Bug: 36697)
Embeddings model needs its own RBAC assignment. Most commonly missed permission — post-deploy scripts fail with `PermissionDenied` even though chat works.

### 5. Intermittent Failures Are Real Bugs (8+ bugs)
Upload failing on 1st attempt but working on 3rd (Bug 39055), "Project not found" in AI Foundry — these are race conditions, not flaky tests. Add retry logic.

---

## Output Format

Return findings as:

- **🔴 Blocker** (N bugs): Exact match to known bug pattern — will fail in production
  > Include the error string or code pattern detected
- **🟠 Warning** (N bugs): High-probability match — same conditions as known bugs
  > Include what to verify
- **🟡 Info**: Potential issue, not identical but similar to known patterns
- **✅ Pass**: Verified condition does not match any known bug pattern

Example:
> 🔴 **Blocker** (38 bugs): `process_sample_data.sh` has no error checking — `grep -c "PermissionDenied"` returns 3 but script exits 0. Matches Bug 36697 pattern.

## Data Source

- **338 bugs** from CSACTOSOL Azure DevOps organization
- **9 projects**: CSA Solutioning (309), Multi-Agent BiB (10), Modernize Code v2 (5), Content Processing (4), Document Processing (4), Modernize Code Generic (2), MAAG Data Foundation (2), Agentic Content Processing (1), GSA Landing Page (1)
- **Time range**: October 2024 – April 2026
- **Detail level**: Repro steps, actual error messages, Azure error codes, and fix patterns extracted from bug work items
