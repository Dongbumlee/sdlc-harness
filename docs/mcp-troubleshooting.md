# MCP Setup Troubleshooting

Common issues when setting up MCP servers for sdlc-harness.

## Quick Start

Run the auto-setup script (no prompts, configures all tools):

```powershell
# Windows
.\tools\check-mcp.ps1
```

```bash
# Linux/macOS
./tools/check-mcp.sh
```

Or download without cloning:

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Dongbumlee/sdlc-harness/main/tools/check-mcp.ps1" -OutFile "check-mcp.ps1" -Headers @{"Cache-Control"="no-cache"}
.\check-mcp.ps1
```

## Issues

### 1. MCP servers not loaded after config

**Symptom:** Step 0 reports servers as "Not configured" even though config files exist.

**Cause:** MCP servers load at session start. Config changes require restart.

**Fix:** Completely close and reopen your terminal/VSCode, then re-run.

### 2. GitHub MCP authentication fails

**Symptom:** Twirp error "not_found" when probing GitHub MCP.

**Cause:** The remote GitHub MCP server (`https://api.githubcopilot.com/mcp/`) requires OAuth authentication.

**Fix:**
```powershell
gh auth login
```
Then restart your session.

### 3. Claude Code config invalid JSON warning

**Symptom:** Script reports "existing config is invalid JSON" for `.claude.json`.

**Cause:** Usually a false positive on PowerShell 5.1 (fixed). If on PS 7+, check for trailing commas or comments.

**Fix:** Validate with:
```powershell
Get-Content "$env:USERPROFILE\.claude.json" -Raw | ConvertFrom-Json
```

### 4. Step 0 skipped by model

**Symptom:** Model says "let me try a simpler approach" and skips MCP checks.

**Cause:** (Fixed) Step 0 wasn't forceful enough.

**Fix:** Step 0 is a hard gate with mandatory status table output in current releases.

### 5. Non-interactive mode (`-p`) limitations

**Symptom:** Shell commands fail with "Permission denied because no interactive user response was available."

**Cause:** `copilot -p` blocks shell commands that require approval.

**Impact:** File creation, health checks via curl, and other shell operations won't work.

**Workaround:** Use interactive mode for full SDLC runs. Use `-p` only for read-only checks.

## Config Locations

| Tool | Windows | Linux/macOS |
|------|---------|-------------|
| VSCode | `.vscode\mcp.json` | `.vscode/mcp.json` |
| Copilot CLI | `%USERPROFILE%\.copilot\mcp.json` | `~/.copilot/mcp.json` |
| Claude Code | `%USERPROFILE%\.claude.json` | `~/.claude.json` |
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` | `~/Library/Application Support/Claude/claude_desktop_config.json` |

Note: Claude tools use `"mcpServers"` key; VSCode/Copilot use `"servers"` key.

## Configured Servers

The workspace template configures 7 servers. Posture at run start differs
by server (see `docs/base-definitions.md` §10.2): only awesome-copilot is
a hard stop; a GitHub MCP authentication failure warns and the run
continues in degraded local mode — it never gates a phase.

| Server | Purpose | Type |
|--------|---------|------|
| awesome-copilot | Best practices (OWASP, Docker, Bicep) | Docker (stdio) |
| github | Repo access, PR creation | HTTP |
| azure | Azure resource validation and management | npx (stdio) |
| azure-devops | ADO wikis, pipelines, work items | npx (stdio) |
| microsoft-learn | Microsoft Learn documentation | HTTP |
| context7 | Framework documentation | npx (stdio) |
| playwright | Browser automation for E2E testing | npx (stdio) |

## Still Stuck?

Run Step 0 in isolation to diagnose:
```powershell
copilot --model claude-haiku-4.5 -p "Using the sdlc-harness plugin, run ONLY Step 0 (MCP server readiness check) of the Harness agent. Show me the status table and stop. Do not proceed to Phase 1."
```
