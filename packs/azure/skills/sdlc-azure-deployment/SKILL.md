---
name: sdlc-azure-deployment
description: >-
  Create Azure infrastructure with Bicep using Azure Verified Modules (AVM),
  configure azd orchestration, and manage deployment lifecycle. Use when writing
  Bicep templates, configuring azure.yaml, setting up Container Apps, or
  preparing deployments. Triggers on Bicep, AVM, azd, infrastructure, or
  deployment requests.
version: "1.0"
author: sdlc-harness
user-invocable: false
---

# SDLC Azure Deployment — Bicep + AVM + azd

## When to use

- Creating or updating Bicep infrastructure templates
- Configuring `azure.yaml` for `azd up` orchestration
- Setting up Container Apps environments
- Reviewing infrastructure-as-code for compliance
- Preparing environment promotion (dev → staging → production)

## Step 1: Load deployment best practices

Load from awesome-copilot:

```
mcp_awesome-copil_load_instruction(
  filename: "azure-deployment-preflight/SKILL.md",
  mode: "skills"
)
```

For AVM module updates:

```
mcp_awesome-copil_load_instruction(
  filename: "update-avm-modules-in-bicep/SKILL.md",
  mode: "skills"
)
```

For Bicep coding standards:

```
mcp_awesome-copil_load_instruction(
  filename: "bicep-code-best-practices",
  mode: "instructions"
)
```

## Step 2: Load Bicep/AVM standards (public sources; optional team wiki override)

Start with public guidance (already loaded in Step 1 via awesome-copilot). Supplement with
**Microsoft Learn MCP** for authoritative AVM module documentation.

If `.github/copilot-instructions.md` configures a team Azure DevOps wiki, fetch team-specific
standards — they take precedence over generic practices:

```
mcp_ado_wiki_get_page_content(
  wikiIdentifier: "<ADO_WIKI_IDENTIFIER>",
  project: "<ADO_WIKI_PROJECT>",
  path: "/<team-standards-page>"
)
```

If no wiki is configured or ADO MCP authentication fails, proceed with the public sources above.

## Step 3: AVM modules — MANDATORY for ALL resources

**⛔ NEVER write raw Azure resource declarations (`resource ... 'Microsoft.xxx'`).**
**✅ ALWAYS use AVM modules (`br/public:avm/res/...`) for every resource.**

This is the same rule as "never use raw CosmosClient — always use the approved Cosmos DB library".
AVM modules handle security defaults, diagnostics, RBAC, and WAF alignment automatically.

**WRONG — raw resource declaration:**
```bicep
// ⛔ WRONG: raw resource
resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosAccountName
  location: location
  ...
}

// ⛔ WRONG: raw resource
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  ...
}
```

**CORRECT — AVM module reference:**
```bicep
// ✅ CORRECT: AVM module (omit name: — Bicep auto-generates a unique
// deployment name; explicit names collide at resource-group scope)
module cosmosDb 'br/public:avm/res/document-db/database-account:0.11.2' = {
  params: {
    name: cosmosAccountName
    location: location
    tags: tags
  }
}

// ✅ CORRECT: AVM module
module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.9.1' = {
  params: {
    name: logAnalyticsName
    location: location
    tags: tags
  }
}
```

**AVM module registry for ALL common resources:**

| Resource | AVM Module Path | Use This — Not Raw Resource |
|---|---|---|
| Cosmos DB | `br/public:avm/res/document-db/database-account` | Not `Microsoft.DocumentDB/databaseAccounts` |
| Storage Account | `br/public:avm/res/storage/storage-account` | Not `Microsoft.Storage/storageAccounts` |
| Container Apps Env | `br/public:avm/res/app/managed-environment` | Not `Microsoft.App/managedEnvironments` |
| Container App | `br/public:avm/res/app/container-app` | Not `Microsoft.App/containerApps` |
| Key Vault | `br/public:avm/res/key-vault/vault` | Not `Microsoft.KeyVault/vaults` |
| Log Analytics | `br/public:avm/res/operational-insights/workspace` | Not `Microsoft.OperationalInsights/workspaces` |
| App Insights | `br/public:avm/res/insights/component` | Not `Microsoft.Insights/components` |
| Container Registry | `br/public:avm/res/container-registry/registry` | Not `Microsoft.ContainerRegistry/registries` |
| AI Foundry | `br/public:avm/res/machine-learning-services/workspace` | Not `Microsoft.MachineLearningServices/workspaces` |

**Look up latest versions** from the AVM registry before writing any module reference:
```
fetch: https://azure.github.io/Azure-Verified-Modules/indexes/bicep/bicep-resource-modules/
```

**If an AVM module doesn't exist** for a resource type, only then use a raw resource
declaration — and add a comment: `// No AVM module available — using raw resource`.

## Step 4: WAF toggle parameters

Every Bicep template MUST include Well-Architected Framework toggles:

```bicep
@description('Enable private networking (WAF reliability + security)')
param enablePrivateNetworking bool = false

@description('Enable monitoring and diagnostics (WAF operational excellence)')
param enableMonitoring bool = true

@description('Enable redundancy and high availability (WAF reliability)')
param enableRedundancy bool = false

@description('Enable auto-scaling (WAF performance efficiency)')
param enableScalability bool = false
```

Create two parameter files:
- `main.parameters.json` — defaults (non-WAF, for dev)
- `main.waf.parameters.json` — WAF-aligned (for production)

## Step 5: Infrastructure rules

- **Shared Container Apps Environment** — ALL container apps share ONE environment
- **Managed Identity + RBAC** — never connection strings in production
- **Standard tags** on all resources: `azd-env-name`, `TemplateName`, `CreatedBy`
- **Diagnostic settings** — all resources send logs to Log Analytics
- **Key Vault** — all secrets stored here, referenced by Container Apps

## Step 6: azure.yaml structure

```yaml
name: <project-name>
metadata:
  template: <project-name>
services:
  api:
    project: src/<Name>API
    host: containerapp
    language: python
    docker:
      path: src/<Name>API/Dockerfile
  web:
    project: src/<Name>Web
    host: containerapp
    language: js
    docker:
      path: src/<Name>Web/Dockerfile
hooks:
  postprovision:
    shell: sh
    run: scripts/postprovision.sh
```

## Gotchas

- **Omit `name:` on Bicep module declarations at resource-group scope** —
  nested deployment names are flat at RG scope, so an explicit `name:` on a
  module can collide with an inner module's deployment name → the deployment
  sits in `DeploymentActive` forever. Bicep auto-generates unique names
  (`deployStorage-{uniqueString}`…). (Found in real deploy: 4 stuck runs
  before the fix.)
- **AVM Cosmos `isZoneRedundant` defaults to true** — regions without
  zone-redundant capacity (e.g. westus2) reject the account. For test/dev
  slices pass explicit
  `locations: [{ failoverPriority: 0, locationName: location, isZoneRedundant: false }]`.
- **AVM Cosmos `publicNetworkAccess` defaults to `Disabled`** — a non-private
  slice (no VNet) gets `Forbidden … blocked by your Cosmos DB account
  firewall settings` on every data-plane call. Set
  `networkRestrictions: { publicNetworkAccess: 'Enabled', ipRules: [],
  virtualNetworkRules: [] }`.
- **Key Vault `secretRef` must exist at Container App creation time** —
  Container Apps validates secret references on create; creating secrets in a
  postprovision hook runs too late. Either grant the deployer Key Vault
  Secrets Officer and create placeholder secrets in a pre-deploy step, or
  split into a two-phase deploy (infra → secrets → apps).
- **User-assigned managed identity needs `AZURE_CLIENT_ID`** —
  `DefaultAzureCredential` with a user-assigned MI requires the
  `AZURE_CLIENT_ID` env var. Wire it via Bicep outputs (e.g. `apiClientId` /
  `workerClientId` from the AVM identities module) into both the app and the
  job environment.
- **Never set container images via CLI** — `az containerapp update` image
  changes are silently reverted by the next incremental Bicep deploy (the
  template default wins). Always pass `apiImage` / `workerImage` as
  deployment parameters: the flow is build → deploy with image params.
- **KEDA azure-queue scaler + MI auth needs `accountName` metadata** — with
  managed-identity auth the scaler fails with
  `error parsing azure queue metadata: no accountName given` when metadata
  carries only `storageAccountResourceId`. Use
  `metadata: { queueName, queueLength, accountName }`. Confirmed working
  MI-only with no connection strings.
- **NEVER use raw `resource` declarations** when an AVM module exists — this is the #1
  mistake. Always use `module ... 'br/public:avm/res/...'`. The same way you never use
  raw `CosmosClient` when `the approved Cosmos DB library` exists.
- **AVM module versions change** — always check the registry for the latest version
  before hardcoding a version number.
- **ALL resources need AVM** — including Log Analytics, App Insights, and Container Registry.
  Don't use AVM for "main" resources and raw resources for "supporting" ones.
- **Container Apps shared environment is mandatory** — creating separate environments
  per app wastes resources and breaks service-to-service networking.
- **`azd up` = `azd provision` + `azd deploy`** — ensure both work independently.
- **Post-provisioning hooks** run after `azd provision` — use them for RBAC
  assignments, data seeding, or Cosmos DB container creation.

## Infrastructure layout

```
infra/
├── main.bicep                    # Entry point
├── main.parameters.json          # Non-WAF parameters
├── main.waf.parameters.json      # WAF-aligned parameters
├── abbreviations.json            # Resource name abbreviations
└── modules/
    ├── cosmos-db.bicep
    ├── storage.bicep
    ├── container-apps.bicep
    ├── key-vault.bicep
    ├── monitoring.bicep
    └── ai-foundry.bicep          # If AI features present
```
