---
description: "Create or update Azure deployment infrastructure with Bicep/AVM modules, azd orchestration, and Container Apps configuration."
agent: "Deployer"
argument-hint: "Describe the Azure services and deployment target"
---
<!--
File: .github/prompts/deployment.prompt.md

How to use (VS Code):
1. Open this prompt file in VS Code.
2. In Copilot Chat, say:
   "Use `.github/prompts/deployment.prompt.md` to create the Bicep infrastructure
    and azd deployment configuration for our FastAPI service with Cosmos DB,
    Blob Storage, and Container Apps."
-->

# Deployment & Infrastructure Prompt (SDLC Phase 3 + Phase 8)

You are creating or updating the Azure deployment infrastructure for a project.

This prompt covers two SDLC phases:
- **Phase 3** — Infrastructure as Code (Bicep/AVM) and `azd` configuration
- **Phase 8** — Release script preparation and deployment automation

Follow the Azure Verified Modules (AVM) patterns for Landing Zone alignment,
and use Azure Developer CLI (`azd`) for deployment orchestration.

## Inputs from the user

Ask the user to provide:
- Azure services needed (Cosmos DB, Blob Storage, Container Apps, AI Foundry, etc.).
- Deployment target: **Azure Container Apps** (default for all services).
- Whether this is a new deployment or updating existing infrastructure.
- Environment strategy (dev, staging, production).
- Any Landing Zone constraints (hub-spoke networking, private endpoints, governance policies).

If any of these are unclear, ask 1–2 focused questions before proceeding.

## Goals

1. Generate Bicep templates using Azure Verified Modules (AVM) from the public registry.
2. Configure `azd` for one-command provisioning and deployment.
3. Set up Codespaces / Dev Container for consistent development environments.
4. Follow Azure Landing Zone best practices (naming, tagging, RBAC, diagnostics, networking).
5. Create post-provisioning hooks and deployment scripts.

## Context loading (MCP resources)

Before starting, load these resources in **priority order** (team standards first):

1. **ADO wiki (team AVM/Bicep standards — check FIRST):**
   Team-specific standards take precedence over generic best practices.
   Fetch ALL subsections before writing any Bicep code:
   ```
   # Parent page — overview and guidelines
   mcp_ado_wiki_get_page_content(
     wikiIdentifier: "CSA-CTO-Engineering.wiki",
     project: "CSA CTO Engineering",
     path: "/Bicep-development"
   )

   # Bicep coding standards (naming, structure, parameters)
   mcp_ado_wiki_get_page_content(..., path: "/Bicep-development/Bicep-standards")

   # WAF configuration per resource type
   mcp_ado_wiki_get_page_content(..., path: "/Bicep-development/WAF-configuration-by-resource")

   # AVM module publishing process
   mcp_ado_wiki_get_page_content(..., path: "/Bicep-development/AVM-publishing-process")

   # Reusable network module for AVM WAF
   mcp_ado_wiki_get_page_content(..., path: "/Bicep-development/Reusable-Network-Module-for-AVM-WAF")

   # Network architecture
   mcp_ado_wiki_get_page_content(..., path: "/Bicep-development/network")

   # Network subnet design
   mcp_ado_wiki_get_page_content(..., path: "/Bicep-development/network/network_subnet_design")
   ```
   If ADO MCP authentication fails (browser login required on first use), inform the user
   and proceed with other available sources.
2. **AVM module registry** — look up module availability and latest versions from the official registry:
   `#fetch https://azure.github.io/Azure-Verified-Modules/indexes/bicep/bicep-resource-modules/`
   Cross-reference all `br/public:avm/res/...` references against this authoritative source.
3. **Azure MCP Bicep tools** — use Azure MCP for AVM module discovery, resource type schemas,
   Bicep file validation, and deployment best practices (IaC rules, WAF alignment).
4. **Bicep best practices** — `mcp_awesome-copil_load_instruction` → `"bicep-code-best-practices"`
   (naming conventions, structure, parameters, security, AVM patterns)
5. **Docker best practices** — `mcp_awesome-copil_load_instruction` → `"containerization-docker-best-practices"`
   (multi-stage builds, layer caching, image security)
6. **Kubernetes best practices** — `mcp_awesome-copil_load_instruction` → `"kubernetes-deployment-best-practices"`
   (when deploying to AKS: pod security, resource limits, health checks)
7. **CI/CD pipelines** — load the one matching your pipeline platform:
   - ADO: `mcp_awesome-copil_load_instruction` → `"azure-devops-pipelines"`
   - GitHub Actions: `mcp_awesome-copil_load_instruction` → `"github-actions-ci-cd-best-practices"`
8. **AVM update prompt** — for existing Bicep files, use `mcp_awesome-copil_load_collection` → `"azure-cloud-development"`
   which includes the `update-avm-modules-in-bicep` prompt for updating AVM module versions.
9. **Microsoft Learn** — use Microsoft Learn MCP for authoritative AVM module documentation.

## Steps

### 1. Analyze required Azure resources

Based on the user's inputs, determine:
- Which Azure resources are needed
- Resource dependencies and ordering
- Managed Identity requirements (which services need access to which)
- Networking requirements (public, private endpoints, VNet integration)

### 2. Generate Bicep templates with AVM

Create `infra/` folder structure:

```
infra/
├── main.bicep                    # Main orchestration (all resources)
├── main.parameters.json          # Default parameters (non-WAF)
├── main.waf.parameters.json      # WAF-aligned parameters (private networking + monitoring)
├── abbreviations.json            # Azure resource abbreviations (azd convention)
├── modules/
│   ├── containerAppsEnvironment.bicep # Shared Container Apps Environment (ONE per solution)
│   ├── containerApp.bicep            # Individual Container App (reusable per service)
│   ├── cosmosDb.bicep              # Cosmos DB with AVM + private endpoints
│   ├── storageAccount.bicep        # Storage with AVM + blob/queue private endpoints
│   ├── ai-services-deployments.bicep # AI Foundry / OpenAI model deployments
│   ├── virtualNetwork.bicep        # VNet + subnets (when enablePrivateNetworking)
│   └── role.bicep                  # Reusable RBAC role assignment
└── vscode_web/                   # VS Code Web launch config (optional)
    └── index.json
scripts/
├── checkquota.sh                 # Pre-deployment quota validation
└── quota_check_params.sh         # Quota check parameter definitions
```

**AVM module rules:**

- ALWAYS use AVM modules from `br/public:avm/res/...` when available.
  Check [Azure Verified Modules registry](https://azure.github.io/Azure-Verified-Modules/indexes/bicep/bicep-resource-modules/)
  for the latest module versions.
- Common AVM modules:

  | Azure Service | AVM Module Path |
  |---|---|
  | Cosmos DB | `br/public:avm/res/document-db/database-account` |
  | Storage Account | `br/public:avm/res/storage/storage-account` |
  | Container Apps Environment | `br/public:avm/res/app/managed-environment` |
  | Container App | `br/public:avm/res/app/container-app` |
  | Key Vault | `br/public:avm/res/key-vault/vault` |
  | Log Analytics | `br/public:avm/res/operational-insights/workspace` |
  | App Insights | `br/public:avm/res/insights/component` |
  | Container Registry | `br/public:avm/res/container-registry/registry` |
  | AI Foundry Hub | `br/public:avm/res/machine-learning-services/workspace` |
  | Virtual Network | `br/public:avm/res/network/virtual-network` |
  | Private Endpoint | `br/public:avm/res/network/private-endpoint` |

- For each module, configure:
  - **Diagnostic settings** — send logs/metrics to Log Analytics
  - **Managed Identity** — prefer user-assigned identity shared across services
  - **RBAC role assignments** — use AVM's `roleAssignments` param with least-privilege
  - **Tags** — standard tags (azd-env-name, TemplateName, CreatedBy)
  - **Private endpoints** — conditional on `enablePrivateNetworking` toggle
  - **Import AVM common types** — `import { roleAssignmentType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'`

**Well-Architected Framework (WAF) toggle parameters:**

Every `main.bicep` MUST include these boolean parameters for Landing Zone alignment:

```bicep
@description('Optional. Enable private networking for applicable resources.')
param enablePrivateNetworking bool = false

@description('Optional. Enable monitoring (App Insights + Log Analytics).')
param enableMonitoring bool = false

@description('Optional. Enable redundancy (zone redundancy, geo-replication).')
param enableRedundancy bool = false

@description('Optional. Enable scalability (autoscaling, higher SKUs).')
param enableScalability bool = false

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true
```

**Two-tier parameter files:**
- `main.parameters.json` — default (non-WAF): all toggles `false`
- `main.waf.parameters.json` — WAF-aligned: `enablePrivateNetworking`, `enableMonitoring`, `enableScalability` all `true`

**Landing Zone alignment:**

```bicep
targetScope = 'resourceGroup'

// Deployer info for CreatedBy tag
var deployerInfo = deployer()
var deployerIdentityName = deployerInfo.?userPrincipalName != null
  ? split(deployerInfo.userPrincipalName, '@')[0]
  : 'Identity-${deployerInfo.objectId}'

// Naming convention
var solutionSuffix = toLower('${solutionName}${solutionUniqueText}')

// Standard tags
var allTags = union({
  'azd-env-name': solutionName
  'TemplateName': '<PROJECT_NAME>'
  'CreatedBy': deployerIdentityName
}, tags)

// Conditional private networking
module virtualNetwork './modules/virtualNetwork.bicep' = if (enablePrivateNetworking) { ... }

// Conditional monitoring
module logAnalytics 'br/public:avm/res/operational-insights/workspace:<VERSION>' = if (enableMonitoring) { ... }
module appInsights 'br/public:avm/res/insights/component:<VERSION>' = if (enableMonitoring) { ... }

// Outputs for azd
output AZURE_COSMOS_ENDPOINT string = cosmosDb.outputs.endpoint
output AZURE_STORAGE_ACCOUNT_NAME string = storage.outputs.name
```

**Module pattern** (follow application project style — each module wraps AVM):

```bicep
// modules/cosmosDb.bicep
@description('Required. Name of the Cosmos DB Account.')
param name string
param location string
param tags object = {}
param privateEndpointSubnetResourceId string?
param sqlPrivateDnsZoneResourceId string?
param dataAccessIdentityPrincipalId string?
param logAnalyticsWorkspaceResourceId string?
param zoneRedundant bool

var privateNetworkingEnabled = !empty(sqlPrivateDnsZoneResourceId) && !empty(privateEndpointSubnetResourceId)

module cosmosAccount 'br/public:avm/res/document-db/database-account:<VERSION>' = {
  name: take('avm.res.document-db.account.${name}', 64)
  params: {
    name: name
    location: location
    disableLocalAuthentication: true  // Managed Identity only
    publicNetworkAccess: privateNetworkingEnabled ? 'Disabled' : 'Enabled'
    diagnosticSettings: !empty(logAnalyticsWorkspaceResourceId)
      ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : []
    privateEndpoints: privateNetworkingEnabled ? [{ ... }] : []
    tags: tags
  }
}
```

**Shared Container Apps Environment pattern (mandatory):**

When deploying multiple container apps, ALL apps MUST share a single Container Apps Environment.
Deploy the environment once, then pass its resource ID to each container app module:

```bicep
// main.bicep — deploy ONE shared environment
module containerAppsEnv 'br/public:avm/res/app/managed-environment:<VERSION>' = {
  name: 'containerAppsEnvironment'
  params: {
    name: 'cae-${solutionSuffix}'
    location: location
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspaceResourceId : ''
    zoneRedundant: enableRedundancy
    tags: allTags
  }
}

// Deploy each container app referencing the SAME environment
module apiApp 'br/public:avm/res/app/container-app:<VERSION>' = {
  name: 'apiContainerApp'
  params: {
    name: 'ca-api-${solutionSuffix}'
    environmentResourceId: containerAppsEnv.outputs.resourceId  // shared
    // ...
  }
}

module webApp 'br/public:avm/res/app/container-app:<VERSION>' = {
  name: 'webContainerApp'
  params: {
    name: 'ca-web-${solutionSuffix}'
    environmentResourceId: containerAppsEnv.outputs.resourceId  // same environment
    // ...
  }
}
```

### 3. Configure `azure.yaml` for `azd`

Generate the `azure.yaml` at repo root (follow application project pattern):

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/Azure/azure-dev/main/schemas/v1.0/azure.yaml.json

name: <PROJECT_NAME>
metadata:
  template: <PROJECT_NAME>@1.0

requiredVersions:
  azd: '>=1.18.2'

services:
  api:
    project: ./src/api            # Each service is independent under src/
    host: containerapp
    language: python
    docker:
      path: ./src/api/Dockerfile
      context: ./src/api
  agent:
    project: ./src/agent
    host: containerapp
    language: python
    docker:
      path: ./src/agent/Dockerfile
      context: ./src/agent
  # For multi-container deployments, add additional services:
  # web:
  #   project: ./src/web
  #   host: containerapp
  #   language: typescript
  #   docker:
  #     path: ./src/web/Dockerfile
  #     context: ./src/web

# NOTE: All container apps MUST share a single Container Apps Environment.
# The environment is defined once in infra/main.bicep and referenced by all apps.
# This ensures shared networking, logging, and Dapr configuration.

hooks:
  postdeploy:
    posix:
      shell: sh
      run: |
        echo "-----"
        echo "🧭 App Details:"
        echo "✅ Name: $CONTAINER_APP_NAME"
        echo "🌐 Endpoint: https://$CONTAINER_APP_FQDN"
        echo "🔗 Portal: https://portal.azure.com/#resource/subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$AZURE_RESOURCE_GROUP/providers/Microsoft.App/containerApps/$CONTAINER_APP_NAME"
        echo "-----"
      interactive: true
    windows:
      shell: pwsh
      run: |
        Write-Host "-----"
        Write-Host "🧭 App Details:"
        Write-Host "✅ Name: $env:CONTAINER_APP_NAME"
        Write-Host "🌐 Endpoint: https://$env:CONTAINER_APP_FQDN"
        Write-Host "🔗 Portal: https://portal.azure.com/#resource/subscriptions/$env:AZURE_SUBSCRIPTION_ID/resourceGroups/$env:AZURE_RESOURCE_GROUP/providers/Microsoft.App/containerApps/$env:CONTAINER_APP_NAME" -ForegroundColor Cyan
        Write-Host "-----"
      interactive: true
```

### 4. Generate Dockerfile (mandatory)

Every project MUST include a Dockerfile for Container Apps deployment:

```dockerfile
# Multi-stage build for production
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev --frozen

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
# or COPY app/ ./app/  (for FastAPI template)
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5. Configure Dev Containers (per-service isolation)

Following the application project pattern, each service under `src/` gets its **own** `.devcontainer/` with
service-specific tooling and dependencies. This per-service isolation ensures that engineers
working on one layer can build, test, and run independently — without pulling in dependencies
from other services.

Generate a `.devcontainer/` folder **inside each service directory** using the matching template below.
Each devcontainer uses a **custom Dockerfile** (not just `image`) so service-specific system
dependencies (e.g., `poppler-utils`, `libpq-dev`) can be added without affecting other services.

---

#### 5a. Python Console / Worker / Pipeline App

Based on `the base app template repo`. Use for processor services, workers, CLI tools, and data pipelines.

`src/<service>/.devcontainer/Dockerfile`:
```dockerfile
ARG DEBIAN_VERSION=bookworm
FROM mcr.microsoft.com/devcontainers/python:3.12-${DEBIAN_VERSION}
WORKDIR /app

# Install service-specific system dependencies here, for example:
# RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils && rm -rf /var/lib/apt/lists/*
```

`src/<service>/.devcontainer/devcontainer.json`:
```json
{
  "name": "<SERVICE_NAME>",
  "build": {
    "context": "..",
    "dockerfile": "Dockerfile",
    "args": {
      "DEBIAN_VERSION": "bookworm"
    }
  },
  "features": {
    "ghcr.io/va-h/devcontainers-features/uv:1": { "version": "latest" },
    "ghcr.io/devcontainers/features/azure-cli:1": {},
    "ghcr.io/azure/azure-dev/azd:latest": {},
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/dhoeric/features/hadolint:1": {}
  },
  "containerEnv": {
    "PYTHONUNBUFFERED": "True",
    "UV_LINK_MODE": "copy",
    "UV_PROJECT_ENVIRONMENT": "/home/vscode/.venv"
  },
  "postCreateCommand": "uv sync --frozen",
  "postStartCommand": "uv tool install pre-commit --with pre-commit-uv --force-reinstall",
  "customizations": {
    "vscode": {
      "extensions": [
        "github.copilot",
        "github.copilot-chat",
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff",
        "njpwerner.autodocstring",
        "exiasr.hadolint",
        "ms-azuretools.vscode-bicep",
        "ms-azuretools.azure-dev",
        "ms-azuretools.vscode-docker",
        "redhat.vscode-yaml",
        "tamasfe.even-better-toml",
        "shardulm94.trailing-spaces",
        "yzhang.markdown-all-in-one"
      ]
    }
  },
  "remoteUser": "vscode"
}
```

Key points:
- **`context: ".."`** — build context is the service root (one level up from `.devcontainer/`)
- **No `forwardPorts`** — console/worker apps do not expose HTTP endpoints
- **No `humao.rest-client`** — not needed for non-API services
- **`postStartCommand`** installs pre-commit hooks for code quality on every container start
- **`UV_PROJECT_ENVIRONMENT`** uses absolute path `/home/vscode/.venv` for consistency

---

#### 5b. Python FastAPI Service

Based on `the API template repo`. Use for REST APIs, web services, and health-probed microservices.

`src/<service>/.devcontainer/Dockerfile`:
```dockerfile
ARG DEBIAN_VERSION=bookworm
FROM mcr.microsoft.com/devcontainers/python:3.12-${DEBIAN_VERSION}
WORKDIR /app

# Install service-specific system dependencies here if needed
```

`src/<service>/.devcontainer/devcontainer.json`:
```json
{
  "name": "<SERVICE_NAME>",
  "build": {
    "context": "..",
    "dockerfile": "Dockerfile",
    "args": {
      "DEBIAN_VERSION": "bookworm"
    }
  },
  "features": {
    "ghcr.io/va-h/devcontainers-features/uv:1": { "version": "latest" },
    "ghcr.io/devcontainers/features/azure-cli:1": {},
    "ghcr.io/azure/azure-dev/azd:latest": {},
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/dhoeric/features/hadolint:1": {}
  },
  "containerEnv": {
    "PYTHONUNBUFFERED": "True",
    "UV_LINK_MODE": "copy",
    "UV_PROJECT_ENVIRONMENT": "/home/vscode/.venv"
  },
  "postCreateCommand": "uv sync --frozen",
  "postStartCommand": "uv tool install pre-commit --with pre-commit-uv --force-reinstall",
  "forwardPorts": [8000],
  "customizations": {
    "vscode": {
      "extensions": [
        "github.copilot",
        "github.copilot-chat",
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff",
        "njpwerner.autodocstring",
        "exiasr.hadolint",
        "ms-azuretools.vscode-bicep",
        "ms-azuretools.azure-dev",
        "ms-azuretools.vscode-docker",
        "redhat.vscode-yaml",
        "tamasfe.even-better-toml",
        "shardulm94.trailing-spaces",
        "yzhang.markdown-all-in-one",
        "humao.rest-client"
      ]
    }
  },
  "remoteUser": "vscode"
}
```

Key differences from 5a:
- **Port 8000** forwarded for Uvicorn
- **`humao.rest-client`** included for testing endpoints via `.http` files

---

#### 5c. TypeScript / React Frontend

Use for React SPAs, Vite-based frontends, and TypeScript web applications.

`src/frontend/.devcontainer/base.Dockerfile`:
```dockerfile
ARG VARIANT=20-bookworm
FROM mcr.microsoft.com/devcontainers/javascript-node:${VARIANT}
# Install global packages needed for the build toolchain
RUN npm install -g typescript yarn react-app-rewired
```

`src/frontend/.devcontainer/devcontainer.json`:
```json
{
  "name": "<PROJECT_NAME>-frontend",
  "build": {
    "dockerfile": "base.Dockerfile",
    "context": "..",
    "args": {
      "VARIANT": "20-bookworm"
    }
  },
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  "postCreateCommand": "yarn install",
  "forwardPorts": [5173],
  "customizations": {
    "vscode": {
      "extensions": [
        "github.copilot",
        "github.copilot-chat",
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "christian-kohler.path-intellisense",
        "christian-kohler.npm-intellisense",
        "xabikos.ReactSnippets",
        "ms-vscode.vscode-typescript-next",
        "bradlc.vscode-tailwindcss",
        "ms-azuretools.vscode-docker",
        "ms-azuretools.azure-dev"
      ]
    }
  },
  "remoteUser": "node"
}
```

Key differences from Python services:
- **`remoteUser: "node"`** (not `"vscode"`) — Node.js container convention
- **`yarn install`** as post-create command (or `npm install` if the project uses npm)
- **No Python, Ruff, or uv tooling** — completely separate toolchain
- **React-specific extensions**: ReactSnippets, path-intellisense, npm-intellisense, TypeScript Next

---

#### Choosing the right template

| Service type | Template | Base image | Forwarded port | Key differences |
|---|---|---|---|---|
| Console, worker, pipeline, CLI | 5a | `python:3.12-bookworm` | None | No HTTP port, no REST Client |
| FastAPI / REST API | 5b | `python:3.12-bookworm` | 8000 | Uvicorn port + REST Client |
| React / TypeScript SPA | 5c | `javascript-node:20-bookworm` | 5173 | Node toolchain, yarn, `remoteUser: "node"` |

**Common across all templates:**
- **`context: ".."`** — build context points to the service root
- **Custom Dockerfile** — allows service-specific system dependency installation
- **GitHub Copilot + Copilot Chat** extensions included in all templates

> **Note:** Do **not** generate a single integrated devcontainer at the repo root.
> Each service is an independent project with its own dependencies, tooling, and container image.

### 6. Environment promotion strategy

Define how deployments flow through environments:

```
┌──────────┐     ┌──────────┐     ┌──────────────┐
│   Dev    │────▶│ Staging  │────▶│  Production  │
│ (auto)   │     │ (auto)   │     │ (approval)   │
└──────────┘     └──────────┘     └──────────────┘
     │                │                   │
  azd up          azd up             azd up
  (dev.env)     (staging.env)      (prod.env)
```

For each environment, generate:
- `.azure/<env>/.env` — environment-specific variables
- Separate parameter files if resource SKUs differ by environment

### 7. Quota check and post-provisioning scripts

Generate `scripts/checkquota.sh` for pre-deployment validation:

```bash
#!/bin/bash
# Validates Azure OpenAI quota availability across regions
# Usage: Called by CI/CD or manually before azd up
#
# Required env vars:
#   AZURE_SUBSCRIPTION_ID, AZURE_REGIONS (comma-separated), GPT_MIN_CAPACITY

IFS=', ' read -ra REGIONS <<< "$AZURE_REGIONS"
for REGION in "${REGIONS[@]}"; do
  echo "🔍 Checking region: $REGION"
  QUOTA_INFO=$(az cognitiveservices usage list --location "$REGION" --output json)
  # Check available capacity vs minimum required
  # Output VALID_REGION if sufficient quota found
done
```

Generate cross-platform post-deploy hooks (inline in `azure.yaml` — see Step 3).
For complex post-provisioning, create `scripts/post-provision.sh`:

```bash
#!/bin/bash
set -euo pipefail
echo "Running post-provisioning setup..."
azd env get-values > .env
echo "✅ Post-provisioning complete."
```

### 8. SDLC Exit Criteria check (Phase 3 + Phase 8)

Verify the following exit criteria:

**Phase 3 — Repo Structure & CI/CD:**
- Bicep templates use AVM modules and follow Landing Zone conventions.
- `azure.yaml` is configured for `azd up` / `azd deploy`.
- `.devcontainer/devcontainer.json` is configured for Codespaces.
- Pipeline definitions include `azd` deployment stages.

**Phase 8 — Release Preparation:**
- Deployment is repeatable via `azd up` (idempotent).
- Environment promotion strategy is defined.
- Post-provisioning hooks exist and are tested.
- Rollback steps are documented.

For each criterion, mark it as:
  - ✅ satisfied
  - ⚠️ partially satisfied (explain what remains)
  - ⛔ not satisfied (explain what is missing)

## Output format

Return a single markdown response with these sections:

- **Resource Analysis** — Azure services needed and their dependencies
- **Bicep Templates** — full file content for `infra/` (ready to paste)
- **`azure.yaml`** — full configuration
- **Dockerfile** — multi-stage production build
- **Dev Container** — `devcontainer.json` configuration
- **Environment Strategy** — promotion flow and env-specific configs
- **Post-Provisioning Scripts** — hook scripts
- **Follow-up Tasks** — manual steps (secrets, DNS, custom domains)
- **SDLC Exit Criteria Check (Phase 3 + Phase 8)** with ✅/⚠️/⛔

<!--
Example invocation for engineers:

"Copilot, use `.github/prompts/deployment.prompt.md` to create the deployment
 infrastructure for our order processing FastAPI service. We need:
 - Cosmos DB (SQL API) for order data via the approved Cosmos DB library
 - Blob Storage for invoice PDFs via the approved Storage library
 - Container Apps for hosting
 - AI Foundry for agent integration
 - Private endpoints for all data services
 Deploy to East US with dev/staging/prod environments using azd."
-->
