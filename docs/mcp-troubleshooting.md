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

### 1. Script downloads old version (CDN cache)

**Symptom:** Downloaded script doesn't match the latest on GitHub.

**Cause:** `raw.githubusercontent.com` caches aggressively at edge nodes.

**Fix:** Add `-Headers @{"Cache-Control"="no-cache"}` (PowerShell) or wait a few minutes.

```powershell
Invoke-WebRequest -Uri "<url>" -OutFile "check-mcp.ps1" -Headers @{"Cache-Control"="no-cache"}
```

### 2. PowerShell 5.1 compatibility

**Symptom:** `ConvertFrom-Json -AsHashtable` fails.

**Cause:** `-AsHashtable` requires PowerShell 7+.

**Fix:** The script now uses a `ConvertTo-Hashtable` helper for PS 5.1 compatibility. No action needed.

### 3. MCP servers not loaded after config

**Symptom:** Step 0 reports servers as "Not configured" even though config files exist.

**Cause:** MCP servers load at session start. Config changes require restart.

**Fix:** Completely close and reopen your terminal/VSCode, then re-run.

### 4. GitHub MCP authentication fails

**Symptom:** Twirp error "not_found" when probing GitHub MCP.

**Cause:** The remote GitHub MCP server (`https://api.githubcopilot.com/mcp/`) requires OAuth authentication.

**Fix:**
```powershell
gh auth login
```
Then restart your session.

### 5. Claude Code config invalid JSON warning

**Symptom:** Script reports "existing config is invalid JSON" for `.claude.json`.

**Cause:** Usually a false positive on PowerShell 5.1 (fixed). If on PS 7+, check for trailing commas or comments.

**Fix:** Validate with:
```powershell
Get-Content "$env:USERPROFILE\.claude.json" -Raw | ConvertFrom-Json
```

### 6. Step 0 skipped by model

**Symptom:** Model says "let me try a simpler approach" and skips MCP checks.

**Cause:** (Fixed) Step 0 wasn't forceful enough.

**Fix:** Updated in Harness agent v1.0.2+. Step 0 is now a hard gate with mandatory status table output.

### 7. Non-interactive mode (`-p`) limitations

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

## Required Servers

| Server | Purpose | Type |
|--------|---------|------|
| awesome-copilot | Best practices (OWASP, Docker, Bicep) | Docker |
| github | Repo access, PR creation | HTTP |
| context7 | Framework documentation | npx |

## Still Stuck?

Run Step 0 in isolation to diagnose:
```powershell
copilot --model claude-haiku-4.5 -p "Using the sdlc-harness plugin, run ONLY Step 0 (MCP server readiness check) of the Harness agent. Show me the status table and stop. Do not proceed to Phase 1."
```
