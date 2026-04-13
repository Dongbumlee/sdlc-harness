---
name: sdlc-azure-deployment
description: >-
  Create Azure infrastructure with Bicep using Azure Verified Modules (AVM),
  configure azd orchestration, and manage deployment lifecycle. Use when writing
  Bicep templates, configuring azure.yaml, setting up Container Apps, or
  preparing deployments. Triggers on Bicep, AVM, azd, infrastructure, or
  deployment requests.
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

## Step 2: Fetch team standards from ADO wiki

Team-specific standards take precedence over generic practices:

```
mcp_ado_wiki_get_page_content(
  wikiIdentifier: "CSA-CTO-Engineering.wiki",
  project: "CSA CTO Engineering",
  path: "/Bicep-development"
)
```

If ADO MCP authentication fails, proceed with the rules below.

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
// ✅ CORRECT: AVM module
module cosmosDb 'br/public:avm/res/document-db/database-account:0.11.2' = {
  name: 'cosmosDbDeployment'
  params: {
    name: cosmosAccountName
    location: location
    tags: tags
  }
}

// ✅ CORRECT: AVM module
module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.9.1' = {
  name: 'logAnalyticsDeployment'
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
