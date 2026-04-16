# Cloud Pack Architecture — Phase 1 Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Extract Azure-specific content from the SDLC Harness into a pluggable cloud pack system, making the core harness cloud-agnostic while preserving Azure functionality as the first cloud pack.

**Architecture:** All agents remain flat in `.github/plugin/agents/` (Copilot extension constraint — `plugin.json` only supports a single `"agents"` scalar string). Pack membership is *logical*, declared via `pack.json` manifests. Azure-specific skills *physically* move to `packs/azure/skills/` because the `skills` field in `plugin.json` is already an array and supports multiple directories. MCP config merging is additive at workspace init time.

**Tech Stack:** Markdown agent files, JSON configuration, YAML CI workflows, GitHub Copilot Extensions

**Design Spec:** `docs/specs/2026-04-16-competitive-positioning-design.md`

---

## Critical Constraints (Read Before Starting)

1. **Dual-location sync.** Every file in `.github/plugin/` has an identical copy in `vscode-extension/`. The CI workflow `sync-check.yml` enforces this. **Every task that touches `.github/plugin/` must mirror the same change to `vscode-extension/`.**

2. **`plugin.json` format.** Two files exist and must stay identical:
   - `.github/plugin/plugin.json`
   - `vscode-extension/plugin.json`
   - `"agents"` is a **scalar string** (single directory) — cannot be changed to an array
   - `"skills"` is already an **array** — can add entries like `"packs/azure/skills/"`

3. **`vscode-extension/package.json`** explicitly lists every agent and skill path. When files move or rename, this file must be updated. **This file is currently untracked** — it must be `git add`-ed.

4. **No traditional tests.** This is a markdown/YAML project. Validation is JSON syntax checks, directory sync diffs, and canary schema validation.

5. **Git push pattern.** Always: `unset GITHUB_TOKEN && git push origin evo`

---

## Task 1: Create Pack Directory Structure and Azure Pack Manifest

**Files:**
- Create: `.github/plugin/packs/azure/pack.json`
- Create: `vscode-extension/packs/azure/pack.json` (mirror)

**Step 1: Create directory structure in both locations**

Run:
```bash
mkdir -p .github/plugin/packs/azure/skills
mkdir -p .github/plugin/packs/_template/skills
mkdir -p vscode-extension/packs/azure/skills
mkdir -p vscode-extension/packs/_template/skills
```

**Step 2: Create the Azure pack manifest**

Create `.github/plugin/packs/azure/pack.json` with this exact content:

```json
{
  "name": "azure",
  "displayName": "Azure Cloud Pack",
  "version": "1.0.0",
  "description": "Azure infrastructure support — Bicep/AVM, azd orchestration, Cosmos DB, Blob Storage, and Azure compliance review.",
  "cloud": "azure",
  "agents": {
    "deployer": "azure-deployer.agent.md",
    "complianceReviewer": "azure-compliance-reviewer.agent.md"
  },
  "skills": [
    "sdlc-azure-deployment",
    "sdlc-cosmos-repository",
    "sdlc-blob-storage"
  ],
  "mcpServers": "mcp-servers.json",
  "reviewers": [
    "azure-compliance-reviewer.agent.md"
  ]
}
```

**Step 3: Mirror the manifest to vscode-extension**

Run:
```bash
cp .github/plugin/packs/azure/pack.json vscode-extension/packs/azure/pack.json
```

**Step 4: Validate JSON syntax**

Run:
```bash
python3 -c "import json; json.load(open('.github/plugin/packs/azure/pack.json')); print('✅ pack.json valid')"
python3 -c "import json; json.load(open('vscode-extension/packs/azure/pack.json')); print('✅ mirror valid')"
```

Expected: Both print `✅`.

**Step 5: Commit**

Run:
```bash
git add .github/plugin/packs/ vscode-extension/packs/
git commit -m "feat: create cloud pack directory structure and Azure pack manifest"
```

---

## Task 2: Create Cloud Pack JSON Schema

**Files:**
- Create: `schemas/cloud-pack.schema.json`

**Step 1: Create the JSON schema**

Create `schemas/cloud-pack.schema.json` with this exact content:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Cloud Pack Manifest",
  "description": "Schema for SDLC Harness cloud pack manifest files (pack.json).",
  "type": "object",
  "required": ["name", "displayName", "version", "cloud", "agents", "skills"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Short identifier for the pack (lowercase, hyphens allowed).",
      "pattern": "^[a-z][a-z0-9-]*$"
    },
    "displayName": {
      "type": "string",
      "description": "Human-readable name (e.g., 'Azure Cloud Pack')."
    },
    "version": {
      "type": "string",
      "description": "Semantic version.",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "description": {
      "type": "string",
      "description": "One-line description of what the pack provides."
    },
    "cloud": {
      "type": "string",
      "description": "Cloud provider identifier.",
      "enum": ["azure", "aws", "gcp"]
    },
    "agents": {
      "type": "object",
      "description": "Pack-specific agents. Values are filenames in the flat agents/ directory.",
      "required": ["deployer"],
      "properties": {
        "deployer": {
          "type": "string",
          "description": "Filename of the deployer agent."
        },
        "complianceReviewer": {
          "type": "string",
          "description": "Filename of the compliance reviewer agent."
        }
      },
      "additionalProperties": {
        "type": "string"
      }
    },
    "skills": {
      "type": "array",
      "description": "List of skill directory names provided by this pack.",
      "items": {
        "type": "string"
      },
      "minItems": 0
    },
    "mcpServers": {
      "type": "string",
      "description": "Filename of the MCP server config file (relative to pack directory)."
    },
    "reviewers": {
      "type": "array",
      "description": "List of reviewer agent filenames invoked during QA for this pack.",
      "items": {
        "type": "string"
      }
    }
  },
  "additionalProperties": false
}
```

**Step 2: Validate the schema is valid JSON**

Run:
```bash
python3 -c "import json; json.load(open('schemas/cloud-pack.schema.json')); print('✅ Schema valid')"
```

Expected: `✅ Schema valid`

**Step 3: Validate the Azure pack.json against the schema**

Run:
```bash
python3 -c "
import json
schema = json.load(open('schemas/cloud-pack.schema.json'))
pack = json.load(open('.github/plugin/packs/azure/pack.json'))
required = schema['required']
missing = [f for f in required if f not in pack]
if missing:
    print(f'❌ Missing required fields: {missing}')
else:
    print('✅ Azure pack.json has all required fields')
"
```

Expected: `✅ Azure pack.json has all required fields`

**Step 4: Commit**

Run:
```bash
git add schemas/cloud-pack.schema.json
git commit -m "feat: add JSON schema for cloud pack manifest validation"
```

---

## Task 3: Move Azure-Specific Skills to Pack Directory

**Files:**
- Move: `.github/plugin/skills/sdlc-azure-deployment/` → `.github/plugin/packs/azure/skills/sdlc-azure-deployment/`
- Move: `.github/plugin/skills/sdlc-cosmos-repository/` → `.github/plugin/packs/azure/skills/sdlc-cosmos-repository/`
- Move: `.github/plugin/skills/sdlc-blob-storage/` → `.github/plugin/packs/azure/skills/sdlc-blob-storage/`
- Move: Same three directories in `vscode-extension/`

**Step 1: Move skills in `.github/plugin/`**

Run:
```bash
git mv .github/plugin/skills/sdlc-azure-deployment .github/plugin/packs/azure/skills/
git mv .github/plugin/skills/sdlc-cosmos-repository .github/plugin/packs/azure/skills/
git mv .github/plugin/skills/sdlc-blob-storage .github/plugin/packs/azure/skills/
```

**Step 2: Move skills in `vscode-extension/`**

Run:
```bash
git mv vscode-extension/skills/sdlc-azure-deployment vscode-extension/packs/azure/skills/
git mv vscode-extension/skills/sdlc-cosmos-repository vscode-extension/packs/azure/skills/
git mv vscode-extension/skills/sdlc-blob-storage vscode-extension/packs/azure/skills/
```

**Step 3: Verify files landed correctly**

Run:
```bash
ls .github/plugin/packs/azure/skills/sdlc-azure-deployment/SKILL.md && echo "✅ azure-deployment moved"
ls .github/plugin/packs/azure/skills/sdlc-cosmos-repository/SKILL.md && echo "✅ cosmos-repository moved"
ls .github/plugin/packs/azure/skills/sdlc-blob-storage/SKILL.md && echo "✅ blob-storage moved"
ls vscode-extension/packs/azure/skills/sdlc-azure-deployment/SKILL.md && echo "✅ mirror: azure-deployment"
ls vscode-extension/packs/azure/skills/sdlc-cosmos-repository/SKILL.md && echo "✅ mirror: cosmos-repository"
ls vscode-extension/packs/azure/skills/sdlc-blob-storage/SKILL.md && echo "✅ mirror: blob-storage"
```

Expected: All six print `✅`.

**Step 4: Verify old locations are gone**

Run:
```bash
! ls .github/plugin/skills/sdlc-azure-deployment 2>/dev/null && echo "✅ Old azure-deployment removed"
! ls .github/plugin/skills/sdlc-cosmos-repository 2>/dev/null && echo "✅ Old cosmos-repository removed"
! ls .github/plugin/skills/sdlc-blob-storage 2>/dev/null && echo "✅ Old blob-storage removed"
```

Expected: All three print `✅`.

**Step 5: Commit**

Run:
```bash
git add -A
git commit -m "refactor: move Azure-specific skills to packs/azure/skills/"
```

---

## Task 4: Update plugin.json Files for New Skill Paths

**Files:**
- Modify: `.github/plugin/plugin.json`
- Modify: `vscode-extension/plugin.json`

The `skills` array must include the new pack skills directory so the Copilot runtime can discover skills that moved.

**Step 1: Update `.github/plugin/plugin.json`**

Open `.github/plugin/plugin.json`. Find:
```
  "skills": ["skills/"]
```

Replace with:
```
  "skills": ["skills/", "packs/azure/skills/"]
```

**Step 2: Update `vscode-extension/plugin.json`**

Open `vscode-extension/plugin.json`. Make the identical edit — find:
```
  "skills": ["skills/"]
```

Replace with:
```
  "skills": ["skills/", "packs/azure/skills/"]
```

**Step 3: Verify both files are valid JSON and identical**

Run:
```bash
python3 -c "import json; json.load(open('.github/plugin/plugin.json')); print('✅ .github/plugin/plugin.json valid')"
python3 -c "import json; json.load(open('vscode-extension/plugin.json')); print('✅ vscode-extension/plugin.json valid')"
diff .github/plugin/plugin.json vscode-extension/plugin.json && echo "✅ plugin.json files match" || echo "❌ plugin.json files differ"
```

Expected: Both valid, files match.

**Step 4: Commit**

Run:
```bash
git add .github/plugin/plugin.json vscode-extension/plugin.json
git commit -m "feat: add Azure pack skills directory to plugin.json skills array"
```

---

## Task 5: Rename Deployer Agent and Update package.json

**Files:**
- Rename: `.github/plugin/agents/deployer.agent.md` → `.github/plugin/agents/azure-deployer.agent.md`
- Rename: `vscode-extension/agents/deployer.agent.md` → `vscode-extension/agents/azure-deployer.agent.md`
- Modify: `.github/plugin/agents/azure-deployer.agent.md` (frontmatter name)
- Modify: `vscode-extension/agents/azure-deployer.agent.md` (mirror)
- Modify: `vscode-extension/package.json` (agent and skill paths)

**Step 1: Rename the agent file in both locations**

Run:
```bash
git mv .github/plugin/agents/deployer.agent.md .github/plugin/agents/azure-deployer.agent.md
git mv vscode-extension/agents/deployer.agent.md vscode-extension/agents/azure-deployer.agent.md
```

**Step 2: Update the frontmatter `name` field**

Open `.github/plugin/agents/azure-deployer.agent.md`. Find:
```
name: Deployer
```

Replace with:
```
name: Azure Deployer
```

**Step 3: Update the heading**

In the same file, find:
```
# Deployer — SDLC Phase 3+8: Deployment & Infrastructure
```

Replace with:
```
# Azure Deployer — SDLC Phase 3+8: Deployment & Infrastructure (Azure Pack)
```

**Step 4: Update the self-reference**

In the same file, find:
```
You are the **Deployer** agent. You create infrastructure-as-code, deployment configurations,
```

Replace with:
```
You are the **Azure Deployer** agent. You create infrastructure-as-code, deployment configurations,
```

**Step 5: Update the catalog source tag**

In the same file, find:
```
Include `Source: Deployer (Phase 8)` on your entries.
```

Replace with:
```
Include `Source: Azure Deployer (Phase 8)` on your entries.
```

**Step 6: Mirror frontmatter and heading changes to vscode-extension**

Run:
```bash
cp .github/plugin/agents/azure-deployer.agent.md vscode-extension/agents/azure-deployer.agent.md
```

**Step 7: Update `vscode-extension/package.json` for renamed agent and moved skills**

Open `vscode-extension/package.json`.

Find:
```
      { "path": "agents/deployer.agent.md" },
```

Replace with:
```
      { "path": "agents/azure-deployer.agent.md" },
```

Find:
```
      { "path": "skills/sdlc-azure-deployment/SKILL.md" },
      { "path": "skills/sdlc-blob-storage/SKILL.md" },
```

Replace with:
```
      { "path": "packs/azure/skills/sdlc-azure-deployment/SKILL.md" },
      { "path": "packs/azure/skills/sdlc-blob-storage/SKILL.md" },
```

Find:
```
      { "path": "skills/sdlc-cosmos-repository/SKILL.md" },
```

Replace with:
```
      { "path": "packs/azure/skills/sdlc-cosmos-repository/SKILL.md" },
```

**Step 8: Validate package.json**

Run:
```bash
python3 -c "import json; json.load(open('vscode-extension/package.json')); print('✅ package.json valid')"
```

Expected: `✅ package.json valid`

**Step 9: Commit**

Run:
```bash
git add -A
git commit -m "refactor: rename deployer to azure-deployer and update package.json paths"
```

---

## Task 6: Update Harness Agent for Pack-Aware Routing

**Files:**
- Modify: `.github/plugin/agents/harness.agent.md`
- Mirror: `vscode-extension/agents/harness.agent.md`

This task updates the harness orchestrator to reference the renamed Azure Deployer agent and adds cloud pack awareness for conditional routing.

**Step 1: Update the agents list (frontmatter line 5)**

Open `.github/plugin/agents/harness.agent.md`. Find:
```
agents: ['Analyst', 'Scaffolder', 'Deployer', 'Implementer', 'Documenter', 'QA Coordinator', 'RAI Reviewer', 'Release Manager']
```

Replace with:
```
agents: ['Analyst', 'Scaffolder', 'Azure Deployer', 'Implementer', 'Documenter', 'QA Coordinator', 'RAI Reviewer', 'Release Manager']
```

**Step 2: Update the placeholder filling reference (line 109)**

Find:
```
   - `<OTHER_AZURE_SERVICES>` — fill after the Deployer determines infrastructure (Phase 3).
```

Replace with:
```
   - `<OTHER_AZURE_SERVICES>` — fill after the Azure Deployer determines infrastructure (Phase 3). *(Azure pack only)*
```

**Step 3: Update the phase-to-agent mapping table (line 134)**

Find:
```
| 3+8: Deployment & Infrastructure | **Deployer** | Bicep/AVM, azd config, devcontainers, release automation |
```

Replace with:
```
| 3+8: Deployment & Infrastructure | **Azure Deployer** *(Azure pack)* | Bicep/AVM, azd config, devcontainers, release automation |
```

**Step 4: Update the QA reviewer routing table**

Find the entire QA routing table block:
```
| Phase | Reviewers to invoke |
|-------|---------------------|
| requirements | Architecture |
| design | Architecture, Security |
| scaffold | Architecture, Code Quality, Deployment Readiness |
| implement | All 8 (full review) |
| document | Code Quality |
| qa | All 8 (full review) |
| deploy | Deployment Readiness, Security, Azure Compliance |
| rai | Security, LLM Behavior |
| release | Deployment Readiness, Code Quality |
```

Replace with:
```
| Phase | Reviewers to invoke |
|-------|---------------------|
| requirements | Architecture |
| design | Architecture, Security |
| scaffold | Architecture, Code Quality, Deployment Readiness |
| implement | All core reviewers (7) + active pack reviewers |
| document | Code Quality |
| qa | All core reviewers (7) + active pack reviewers |
| deploy | Deployment Readiness, Security, + active pack compliance reviewer |
| rai | Security, LLM Behavior |
| release | Deployment Readiness, Code Quality |

> **Core reviewers (7):** Architecture, Code Quality, Security, Test Coverage, UX/A11y, LLM Behavior, Deployment Readiness.
> **Pack reviewers:** Azure pack adds Azure Compliance Reviewer. When no cloud pack is active, only core reviewers run.
```

**Step 5: Update the "invoke all" note**

Find:
```
For `implement` and `qa` phases, invoke all 8 reviewers (full review).
```

Replace with:
```
For `implement` and `qa` phases, invoke all core reviewers (7) plus any active pack reviewers.
```

**Step 6: Update the infrastructure validation section**

Find:
```
#### Phase 3+8: Infrastructure validation (Deployer)

After the Deployer generates Bicep/azd configuration:

1. Check that Bicep files reference valid AVM module versions.
2. Verify no hardcoded secrets or connection strings.
3. If issues found, ask the Deployer to fix before deployment.
```

Replace with:
```
#### Phase 3+8: Infrastructure validation (Azure Deployer)

After the Azure Deployer generates Bicep/azd configuration:

1. Check that Bicep files reference valid AVM module versions.
2. Verify no hardcoded secrets or connection strings.
3. If issues found, ask the Azure Deployer to fix before deployment.

#### Cloud pack awareness

Before routing to deployment or invoking pack-specific reviewers, detect the active cloud provider:

1. Read `harness-config.yml` in the workspace root. Look for the `cloud_provider` field.
2. If `cloud_provider: azure` — route deployments to **Azure Deployer**, include **Azure Compliance Reviewer** in QA reviews.
3. If `cloud_provider: none` or the field is missing — skip deployment phases. If the user requests deployment, inform them:
   > No cloud pack is active. To enable deployment, run workspace initialization (`/sdlc-workspace-init`) and select a cloud provider.
4. The cloud provider is set during workspace initialization.
```

**Step 7: Mirror to vscode-extension**

Run:
```bash
cp .github/plugin/agents/harness.agent.md vscode-extension/agents/harness.agent.md
```

**Step 8: Commit**

Run:
```bash
git add .github/plugin/agents/harness.agent.md vscode-extension/agents/harness.agent.md
git commit -m "refactor: update harness agent for pack-aware routing and Azure Deployer reference"
```

---

## Task 7: Update Scaffolder Agent References

**Files:**
- Modify: `.github/plugin/agents/scaffolder.agent.md`
- Mirror: `vscode-extension/agents/scaffolder.agent.md`

**Step 1: Update the agent reference in the manifest description (line 119)**

Open `.github/plugin/agents/scaffolder.agent.md`. Find:
```
agents (Implementer, QA, Deployer, Documenter) to ensure pattern consistency.
```

Replace with:
```
agents (Implementer, QA, Azure Deployer, Documenter) to ensure pattern consistency.
```

**Step 2: Update the "must not" rule (line 334)**

Find:
```
- Never generate Bicep/AVM infrastructure — that belongs to the **Deployer** agent.
```

Replace with:
```
- Never generate Bicep/AVM infrastructure — that belongs to the **Azure Deployer** agent (Azure pack).
```

**Step 3: Mirror to vscode-extension**

Run:
```bash
cp .github/plugin/agents/scaffolder.agent.md vscode-extension/agents/scaffolder.agent.md
```

**Step 4: Commit**

Run:
```bash
git add .github/plugin/agents/scaffolder.agent.md vscode-extension/agents/scaffolder.agent.md
git commit -m "refactor: update scaffolder references from Deployer to Azure Deployer"
```

---

## Task 8: Extract Azure MCP Servers to Pack Config and Update Core Template

**Files:**
- Create: `.github/plugin/packs/azure/mcp-servers.json`
- Modify: `.github/plugin/skills/sdlc-workspace-init/assets/mcp.template.json`
- Mirror: `vscode-extension/packs/azure/mcp-servers.json`
- Mirror: `vscode-extension/skills/sdlc-workspace-init/assets/mcp.template.json`

This task splits the MCP server configuration. Azure-specific servers (`azure`, `azure-devops`, `microsoft-learn`) and their inputs (`ado_org`) move to the Azure pack. The core template keeps only universal servers.

**Step 1: Create the Azure pack MCP servers config**

Create `.github/plugin/packs/azure/mcp-servers.json` with this exact content:

```json
{
    "inputs": [
        {
            "id": "ado_org",
            "type": "promptString",
            "description": "Azure DevOps organization name (e.g. 'CSACTOSOL')"
        }
    ],
    "servers": {
        "azure": {
            "type": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@azure/mcp@latest",
                "server",
                "start"
            ]
        },
        "azure-devops": {
            "type": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@azure-devops/mcp",
                "${input:ado_org}"
            ]
        },
        "microsoft-learn": {
            "type": "http",
            "url": "https://learn.microsoft.com/api/mcp"
        }
    }
}
```

**Step 2: Update the core MCP template to remove Azure servers**

Open `.github/plugin/skills/sdlc-workspace-init/assets/mcp.template.json`. Replace the **entire file content** with:

```json
{
    "servers": {
        "awesome-copilot": {
            "type": "stdio",
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "ghcr.io/microsoft/mcp-dotnet-samples/awesome-copilot:latest"
            ]
        },
        "github": {
            "type": "http",
            "url": "https://api.githubcopilot.com/mcp/"
        },
        "context7": {
            "type": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@upstash/context7-mcp@latest"
            ]
        },
        "playwright": {
            "type": "stdio",
            "command": "npx",
            "args": [
                "@playwright/mcp@latest",
                "--headless",
                "--caps=testing",
                "--output-dir=.playwright-mcp"
            ]
        }
    }
}
```

Note: The `inputs` section is removed entirely (the `ado_org` input was only used by `azure-devops`). Only 4 core servers remain.

**Step 3: Mirror both files to vscode-extension**

Run:
```bash
cp .github/plugin/packs/azure/mcp-servers.json vscode-extension/packs/azure/mcp-servers.json
cp .github/plugin/skills/sdlc-workspace-init/assets/mcp.template.json vscode-extension/skills/sdlc-workspace-init/assets/mcp.template.json
```

**Step 4: Validate all JSON files**

Run:
```bash
python3 -c "import json; json.load(open('.github/plugin/packs/azure/mcp-servers.json')); print('✅ Azure mcp-servers.json valid')"
python3 -c "import json; json.load(open('.github/plugin/skills/sdlc-workspace-init/assets/mcp.template.json')); print('✅ Core mcp.template.json valid')"
python3 -c "import json; json.load(open('vscode-extension/packs/azure/mcp-servers.json')); print('✅ Mirror mcp-servers.json valid')"
```

Expected: All three `✅`.

**Step 5: Commit**

Run:
```bash
git add .github/plugin/packs/azure/mcp-servers.json vscode-extension/packs/azure/mcp-servers.json
git add .github/plugin/skills/sdlc-workspace-init/assets/mcp.template.json vscode-extension/skills/sdlc-workspace-init/assets/mcp.template.json
git commit -m "refactor: extract Azure MCP servers to pack config, core template now cloud-agnostic"
```

---

## Task 9: Update Workspace-Init Skill for Cloud Selection and MCP Merging

**Files:**
- Modify: `.github/plugin/skills/sdlc-workspace-init/SKILL.md`
- Mirror: `vscode-extension/skills/sdlc-workspace-init/SKILL.md`

This task adds a cloud provider selection step and updates the MCP deployment logic to merge core + pack servers.

**Step 1: Insert the cloud provider selection step**

Open `.github/plugin/skills/sdlc-workspace-init/SKILL.md`. Find the line:
```
### Step 3: Deploy MCP server configuration
```

Insert the following **immediately before** that line:
```
### Step 2b: Select cloud provider

Ask the user:

> **Cloud provider:** Which cloud platform are you targeting?
>
> - **azure** (default) — Adds Azure MCP, Azure DevOps MCP, and Microsoft Learn MCP servers. Enables Bicep/AVM deployment, Cosmos DB, and Blob Storage skills.
> - **none** — Core harness only, no cloud-specific agents or skills. You can add a cloud pack later.

If the user doesn't answer or skips, default to `azure`.

Store the choice for use in Step 3 (MCP deployment) and Step 6b (`harness-config.yml`).

```

**Step 2: Replace the MCP deployment logic in Step 3**

Find the block starting with:
```
> **This is the ONLY place mcp.json should be deployed.** Do NOT deploy it anywhere else.
> **CRITICAL: Use the terminal to write this file — do NOT use create/edit tools.**
> LLM file tools sometimes append instead of overwrite, producing invalid JSON.

1. Check if `.vscode/mcp.json` exists in the workspace.
2. **If NOT found** → deploy using the terminal:
   a. Read [mcp.template.json](./assets/mcp.template.json) to get the content.
   b. **Delete any partial file** and write fresh using the terminal:
      ```bash
      rm -f .vscode/mcp.json
      ```
      Then write the content using a heredoc redirect (which ALWAYS overwrites):
      ```bash
      cat > .vscode/mcp.json << 'MCPEOF'
      <paste the exact content of mcp.template.json here>
      MCPEOF
      ```
   c. **Validate the file is valid JSON:**
      ```bash
      python3 -c "import json; json.load(open('.vscode/mcp.json')); print('✅ mcp.json is valid JSON')"
      ```
      If validation fails → `rm -f .vscode/mcp.json` and retry from step (b) once.
3. **If found** → validate it anyway:
   ```bash
   python3 -c "import json; json.load(open('.vscode/mcp.json')); print('✅ mcp.json is valid JSON')"
   ```
   If valid → Skip. Report: _"Existing `.vscode/mcp.json` found — keeping current config."_
   If invalid → `rm -f .vscode/mcp.json` and deploy fresh from step (b).

After deploying (or confirming it exists), tell the user:
> ✅ `.vscode/mcp.json` — 7 MCP server definitions ready.
> Please start all MCP servers: open `.vscode/mcp.json` and click **"Start"** on each.
```

Replace that entire block with:
```
> **This is the ONLY place mcp.json should be deployed.** Do NOT deploy it anywhere else.
> **CRITICAL: Use the terminal to write this file — do NOT use create/edit tools.**
> LLM file tools sometimes append instead of overwrite, producing invalid JSON.

1. Check if `.vscode/mcp.json` exists in the workspace.
2. **If found** → validate it:
   ```bash
   python3 -c "import json; json.load(open('.vscode/mcp.json')); print('✅ mcp.json is valid JSON')"
   ```
   If valid → Skip. Report: _"Existing `.vscode/mcp.json` found — keeping current config."_
   If invalid → `rm -f .vscode/mcp.json` and continue to step 3.
3. **If NOT found** (or removed in step 2) → build and deploy:
   a. Read [mcp.template.json](./assets/mcp.template.json) to get the **core** MCP servers (4 servers: awesome-copilot, github, context7, playwright).
   b. Check the cloud provider selection from Step 2b.
   c. **If cloud provider is `azure`:** Read the Azure pack's MCP server config at
      `.github/plugin/packs/azure/mcp-servers.json` (path relative to repository root).
      Merge the pack's config into the core config:
      - Add all pack `inputs` to the top-level `inputs` array
      - Add all pack `servers` into the top-level `servers` object
      This produces a merged JSON with 3 Azure `inputs` entries and 7 total servers.
   d. **If cloud provider is `none`:** Use only the core servers as-is (4 servers, no `inputs` section).
   e. **Delete any partial file** and write the merged result using the terminal:
      ```bash
      rm -f .vscode/mcp.json
      ```
      Then write the content using a heredoc redirect (which ALWAYS overwrites):
      ```bash
      cat > .vscode/mcp.json << 'MCPEOF'
      <paste the merged JSON content here>
      MCPEOF
      ```
   f. **Validate the file is valid JSON:**
      ```bash
      python3 -c "import json; json.load(open('.vscode/mcp.json')); print('✅ mcp.json is valid JSON')"
      ```
      If validation fails → `rm -f .vscode/mcp.json` and retry from step (e) once.

After deploying (or confirming it exists), tell the user:
> ✅ `.vscode/mcp.json` — N MCP server definitions ready (4 core + M cloud pack).
> Please start all MCP servers: open `.vscode/mcp.json` and click **"Start"** on each.

Where N = total servers deployed, M = pack servers (3 for Azure, 0 for none).
```

**Step 3: Update the harness-config.yml section in Step 6b**

Find:
```
Store the answer in `harness-config.yml` as:

```yaml
catalog_review: true   # "review" → true (default)
catalog_review: false  # "auto" → false
```

If the user doesn't answer or skips the question, default to `catalog_review: true`.
```

Replace with:
```
Store the answer in `harness-config.yml` alongside the cloud provider from Step 2b:

```yaml
cloud_provider: azure  # from Step 2b (default: azure)
catalog_review: true   # "review" → true (default)
```

If the user doesn't answer the catalog question, default to `catalog_review: true`.
The `cloud_provider` field is read by the Harness agent for pack-aware routing.
```

**Step 4: Update the Step 9 report template**

Find:
```
## ✅ SDLC Workspace Initialized

- ✅ `.vscode/mcp.json` — 7 MCP server definitions deployed
- ✅ `.github/copilot-instructions.md` — customized for "{{PROJECT_NAME}}"
- ✅ `.github/instructions/` — X quality instruction files deployed
- ✅ `.github/prompts/` — 6 SDLC prompt files deployed
- ✅ `.github/reference-catalog.md` — empty catalog template created (Analyst will populate during Phase 1-2)

**Next steps:**
1. **Start MCP servers** — open `.vscode/mcp.json` and click "Start" on each server.
   All 7 servers are required.
2. Review `.github/copilot-instructions.md` and adjust if needed.
3. Use `@Harness` to start your first SDLC task.
4. Use `/requirement-and-design` to begin Phase 1-2.
```

Replace with:
```
## ✅ SDLC Workspace Initialized

- ✅ `.vscode/mcp.json` — N MCP server definitions deployed (4 core + M cloud pack)
- ✅ Cloud provider: {{CLOUD_PROVIDER}} (stored in `harness-config.yml`)
- ✅ `.github/copilot-instructions.md` — customized for "{{PROJECT_NAME}}"
- ✅ `.github/instructions/` — X quality instruction files deployed
- ✅ `.github/prompts/` — 6 SDLC prompt files deployed
- ✅ `.github/reference-catalog.md` — empty catalog template created (Analyst will populate during Phase 1-2)

**Next steps:**
1. **Start MCP servers** — open `.vscode/mcp.json` and click "Start" on each server.
2. Review `.github/copilot-instructions.md` and adjust if needed.
3. Use `@Harness` to start your first SDLC task.
4. Use `/requirement-and-design` to begin Phase 1-2.
```

**Step 5: Mirror to vscode-extension**

Run:
```bash
cp .github/plugin/skills/sdlc-workspace-init/SKILL.md vscode-extension/skills/sdlc-workspace-init/SKILL.md
```

**Step 6: Commit**

Run:
```bash
git add .github/plugin/skills/sdlc-workspace-init/SKILL.md vscode-extension/skills/sdlc-workspace-init/SKILL.md
git commit -m "feat: add cloud provider selection and additive MCP merging to workspace-init"
```

---

## Task 10: Create Pack Template for Community Contributors

**Files:**
- Create: `.github/plugin/packs/_template/pack.json`
- Create: `.github/plugin/packs/_template/mcp-servers.json`
- Create: `.github/plugin/packs/_template/skills/example-cloud-skill/SKILL.md`
- Create: `.github/plugin/packs/_template/README.md`
- Mirror: all four files to `vscode-extension/packs/_template/`

**Step 1: Create the template pack manifest**

Create `.github/plugin/packs/_template/pack.json` with this exact content:

```json
{
  "name": "<cloud-name>",
  "displayName": "<Cloud Name> Cloud Pack",
  "version": "0.1.0",
  "description": "<One-line description of what this pack provides.>",
  "cloud": "<cloud-name>",
  "agents": {
    "deployer": "<cloud-name>-deployer.agent.md",
    "complianceReviewer": "<cloud-name>-compliance-reviewer.agent.md"
  },
  "skills": [],
  "mcpServers": "mcp-servers.json",
  "reviewers": [
    "<cloud-name>-compliance-reviewer.agent.md"
  ]
}
```

**Step 2: Create the template MCP servers config**

Create `.github/plugin/packs/_template/mcp-servers.json` with this exact content:

```json
{
    "inputs": [],
    "servers": {}
}
```

**Step 3: Create the example skill**

Create `.github/plugin/packs/_template/skills/example-cloud-skill/SKILL.md` with this exact content:

```markdown
---
name: example-cloud-skill
description: >-
  Example cloud-specific skill. Replace this with your actual skill content.
  This file shows the expected structure for a pack skill.
---

# Example Cloud Skill

## When to use

- Describe when this skill should be activated

## Step 1: Load relevant configuration

Describe what configuration or best practices to load.

## Step 2: Apply patterns

Describe the cloud-specific patterns this skill teaches.
```

**Step 4: Create the template README**

Create `.github/plugin/packs/_template/README.md` with this exact content:

```markdown
# Cloud Pack Template

Use this template to create a new cloud pack for the SDLC Harness.

## Steps

1. Copy this `_template/` directory to `packs/<your-cloud>/`
2. Edit `pack.json` — replace all `<cloud-name>` placeholders with your cloud identifier (e.g., `aws`, `gcp`)
3. Create your deployer agent at `.github/plugin/agents/<cloud>-deployer.agent.md`
4. Create your compliance reviewer at `.github/plugin/agents/<cloud>-compliance-reviewer.agent.md`
5. Add cloud-specific skills under `packs/<your-cloud>/skills/<skill-name>/SKILL.md`
6. Create `mcp-servers.json` with your cloud's MCP server definitions (inputs + servers)
7. Update `.github/plugin/plugin.json` — add `"packs/<your-cloud>/skills/"` to the `skills` array
8. Update `vscode-extension/package.json` — add explicit paths for new agents and skills under `chatAgents` and `chatSkills`
9. Mirror your entire pack directory to `vscode-extension/packs/<your-cloud>/`
10. Run validation: `python3 -c "import json; json.load(open('.github/plugin/packs/<your-cloud>/pack.json'))"`
11. Submit a PR

## Required files

| File | Purpose |
|------|---------|
| `pack.json` | Pack manifest declaring agents, skills, MCP servers |
| `mcp-servers.json` | MCP server definitions merged into `.vscode/mcp.json` at init |
| `skills/` | Cloud-specific skill directories (each with `SKILL.md`) |

## Required agents (created in flat `agents/` directory)

| Agent | Purpose |
|-------|---------|
| `<cloud>-deployer.agent.md` | Infrastructure-as-code generation for your cloud |
| `<cloud>-compliance-reviewer.agent.md` | Cloud-specific compliance checks during QA |

## Validation

Validate your pack manifest against the schema:
```bash
python3 -c "
import json
schema = json.load(open('schemas/cloud-pack.schema.json'))
pack = json.load(open('.github/plugin/packs/<your-cloud>/pack.json'))
required = schema['required']
missing = [f for f in required if f not in pack]
print('✅ Valid' if not missing else f'❌ Missing: {missing}')
"
```
```

**Step 5: Mirror all template files to vscode-extension**

Run:
```bash
mkdir -p vscode-extension/packs/_template/skills/example-cloud-skill
cp .github/plugin/packs/_template/pack.json vscode-extension/packs/_template/pack.json
cp .github/plugin/packs/_template/mcp-servers.json vscode-extension/packs/_template/mcp-servers.json
cp .github/plugin/packs/_template/skills/example-cloud-skill/SKILL.md vscode-extension/packs/_template/skills/example-cloud-skill/SKILL.md
cp .github/plugin/packs/_template/README.md vscode-extension/packs/_template/README.md
```

**Step 6: Commit**

Run:
```bash
git add .github/plugin/packs/_template/ vscode-extension/packs/_template/
git commit -m "feat: add cloud pack template for community contributors"
```

---

## Task 11: Update Sync-Check CI Workflow

**Files:**
- Modify: `.github/workflows/sync-check.yml`

The current CI only checks `agents/` and `skills/` sync. It must also check the `packs/` directory.

**Step 1: Add packs sync check**

Open `.github/workflows/sync-check.yml`. Find the end of the file (after the skill sync check step):
```
      - name: Check skill directory sync
        run: |
          echo "=== Checking skill sync ==="
          diff -r \
            --exclude="plugin.json" \
            --exclude="package.json" \
            vscode-extension/skills/ .github/plugin/skills/ \
            && echo "✅ Skills in sync" \
            || { echo "❌ Skill directories have diverged!"; exit 1; }
```

Append the following new step immediately after:
```

      - name: Check packs directory sync
        run: |
          echo "=== Checking packs sync ==="
          if [ -d ".github/plugin/packs" ] || [ -d "vscode-extension/packs" ]; then
            diff -r \
              vscode-extension/packs/ .github/plugin/packs/ \
              && echo "✅ Packs in sync" \
              || { echo "❌ Pack directories have diverged!"; exit 1; }
          else
            echo "✅ No packs directory found (skipping)"
          fi
```

**Step 2: Commit**

Run:
```bash
git add .github/workflows/sync-check.yml
git commit -m "ci: add packs directory to sync-check workflow"
```

---

## Task 12: Run Final Validation and Push

**Files:** None (validation only)

**Step 1: Validate all JSON files**

Run:
```bash
python3 -c "
import json, sys
files = [
    '.github/plugin/plugin.json',
    'vscode-extension/plugin.json',
    'vscode-extension/package.json',
    '.github/plugin/packs/azure/pack.json',
    '.github/plugin/packs/azure/mcp-servers.json',
    'vscode-extension/packs/azure/pack.json',
    'vscode-extension/packs/azure/mcp-servers.json',
    '.github/plugin/skills/sdlc-workspace-init/assets/mcp.template.json',
    'schemas/cloud-pack.schema.json',
]
ok = True
for f in files:
    try:
        json.load(open(f))
        print(f'✅ {f}')
    except Exception as e:
        print(f'❌ {f}: {e}')
        ok = False
sys.exit(0 if ok else 1)
"
```

Expected: All 9 files print `✅`.

**Step 2: Verify directory sync — agents**

Run:
```bash
diff -r --exclude="plugin.json" --exclude="package.json" vscode-extension/agents/ .github/plugin/agents/ && echo "✅ Agents in sync" || echo "❌ Agents diverged"
```

Expected: `✅ Agents in sync`

**Step 3: Verify directory sync — skills**

Run:
```bash
diff -r --exclude="plugin.json" --exclude="package.json" vscode-extension/skills/ .github/plugin/skills/ && echo "✅ Skills in sync" || echo "❌ Skills diverged"
```

Expected: `✅ Skills in sync`

**Step 4: Verify directory sync — packs**

Run:
```bash
diff -r vscode-extension/packs/ .github/plugin/packs/ && echo "✅ Packs in sync" || echo "❌ Packs diverged"
```

Expected: `✅ Packs in sync`

**Step 5: Verify the deployer rename is complete**

Run:
```bash
ls .github/plugin/agents/azure-deployer.agent.md > /dev/null 2>&1 && echo "✅ azure-deployer.agent.md exists" || echo "❌ MISSING"
ls vscode-extension/agents/azure-deployer.agent.md > /dev/null 2>&1 && echo "✅ mirror exists" || echo "❌ MISSING"
! ls .github/plugin/agents/deployer.agent.md > /dev/null 2>&1 && echo "✅ old deployer.agent.md removed" || echo "❌ OLD FILE STILL EXISTS"
! ls vscode-extension/agents/deployer.agent.md > /dev/null 2>&1 && echo "✅ old mirror removed" || echo "❌ OLD FILE STILL EXISTS"
```

Expected: All four `✅`.

**Step 6: Verify skills moved correctly**

Run:
```bash
for skill in sdlc-azure-deployment sdlc-cosmos-repository sdlc-blob-storage; do
  ls ".github/plugin/packs/azure/skills/$skill/SKILL.md" > /dev/null 2>&1 && echo "✅ $skill in pack" || echo "❌ $skill MISSING from pack"
  ! ls ".github/plugin/skills/$skill" > /dev/null 2>&1 && echo "✅ $skill removed from skills/" || echo "❌ $skill STILL IN skills/"
done
```

Expected: All six `✅`.

**Step 7: Verify pack schema validation**

Run:
```bash
python3 -c "
import json
schema = json.load(open('schemas/cloud-pack.schema.json'))
pack = json.load(open('.github/plugin/packs/azure/pack.json'))
required = schema['required']
missing = [f for f in required if f not in pack]
if missing:
    print(f'❌ Missing required fields: {missing}')
else:
    print('✅ Azure pack.json passes schema validation')
"
```

Expected: `✅ Azure pack.json passes schema validation`

**Step 8: Run canary schema validation (if validator exists)**

Run:
```bash
if [ -f "tools/validate_canaries.py" ]; then
    python3 tools/validate_canaries.py && echo "✅ Canary schemas valid" || echo "❌ Canary validation failed"
else
    echo "⚠️ Canary validator not found (skipping)"
fi
```

**Step 9: Push all commits**

Run:
```bash
unset GITHUB_TOKEN && git push origin evo
```

---

## Summary of Changes

| Category | What Changed |
|----------|-------------|
| **New directories** | `.github/plugin/packs/azure/`, `.github/plugin/packs/_template/`, `vscode-extension/packs/` (mirrors) |
| **New files** | `pack.json` (azure + template), `mcp-servers.json` (azure + template), `cloud-pack.schema.json`, template README + example skill |
| **Moved skills** | 3 Azure skills from `skills/` → `packs/azure/skills/` (both locations) |
| **Renamed agent** | `deployer.agent.md` → `azure-deployer.agent.md` (both locations) |
| **Updated agents** | `harness.agent.md` (pack-aware routing), `scaffolder.agent.md` (Deployer → Azure Deployer), `azure-deployer.agent.md` (name update) |
| **Updated skills** | `sdlc-workspace-init` (cloud selection + MCP merging) |
| **Updated config** | `plugin.json` (new skills path), `package.json` (renamed agent + moved skill paths) |
| **Updated CI** | `sync-check.yml` (packs directory sync) |
| **Updated MCP template** | Core template now has 4 servers (was 7); Azure-specific servers in pack |
