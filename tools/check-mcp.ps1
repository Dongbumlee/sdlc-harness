# Pre-flight MCP server check for sdlc-harness (Windows PowerShell)
# Verifies that required MCP servers are configured before running the harness.
# Checks VSCode, Copilot CLI, Claude Code, and Claude Desktop config locations.
# If no config exists, offers to create one automatically.
# Usage: .\tools\check-mcp.ps1 [-Config <path>] [-Auto] [-All]
#   -All: create config for ALL supported tools (VSCode, Copilot CLI, Claude Code, Claude Desktop)

param(
    [string]$Config = "",
    [switch]$Auto,
    [switch]$All
)

$ErrorActionPreference = "Stop"

$requiredServers = @("awesome-copilot", "github", "context7")
$optionalServers = @("azure", "azure-devops")

$defaultMcpJson = @'
{
  "servers": {
    "awesome-copilot": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "--rm", "-i", "ghcr.io/github/awesome-copilot:latest"]
    },
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
'@

# Claude uses "mcpServers" key instead of "servers"
$defaultClaudeJson = @'
{
  "mcpServers": {
    "awesome-copilot": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "ghcr.io/github/awesome-copilot:latest"]
    },
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
'@

Write-Host "=== sdlc-harness MCP pre-flight check ==="
Write-Host ""

$configPaths = @()
if ($Config -ne "") {
    $configPaths = @(@{ Path = $Config; Tool = "Custom"; Claude = $false })
} else {
    $configPaths = @(
        @{ Path = (Join-Path (Get-Location) ".vscode\mcp.json"); Tool = "VSCode"; Claude = $false },
        @{ Path = (Join-Path $env:USERPROFILE ".copilot\mcp.json"); Tool = "Copilot CLI"; Claude = $false },
        @{ Path = (Join-Path $env:USERPROFILE ".claude.json"); Tool = "Claude Code"; Claude = $true },
        @{ Path = (Join-Path $env:APPDATA "Claude\claude_desktop_config.json"); Tool = "Claude Desktop"; Claude = $true }
    )
}

$foundConfig = $null
$foundTool = ""
$isClaude = $false
foreach ($c in $configPaths) {
    if (Test-Path $c.Path) {
        $foundConfig = $c.Path
        $foundTool = $c.Tool
        $isClaude = $c.Claude
        Write-Host "Config found ($foundTool): $($c.Path)"
        break
    }
}

if ($null -eq $foundConfig) {
    Write-Host "No MCP config found. Checked:"
    foreach ($c in $configPaths) { Write-Host "  - [$($c.Tool)] $($c.Path)" }
    Write-Host ""

    # Determine targets: -All creates for every tool, otherwise just the first
    $targets = @()
    if ($All) {
        foreach ($c in $configPaths) {
            $tpl = if ($c.Claude) { $defaultClaudeJson } else { $defaultMcpJson }
            $targets += @{ Path = $c.Path; Template = $tpl; Tool = $c.Tool }
        }
    } else {
        $c = $configPaths[0]
        $tpl = if ($c.Claude) { $defaultClaudeJson } else { $defaultMcpJson }
        $targets += @{ Path = $c.Path; Template = $tpl; Tool = $c.Tool }
    }

    $label = if ($All) { "all tools ($($targets.Count) locations)" } else { $targets[0].Path }
    $doCreate = $false

    if ($Auto) {
        $doCreate = $true
    } else {
        $answer = Read-Host "Create default MCP config for $label ? (y/n)"
        if ($answer -eq "y" -or $answer -eq "Y") { $doCreate = $true }
    }

    if ($doCreate) {
        foreach ($t in $targets) {
            $dir = Split-Path $t.Path -Parent
            if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
            # Don't overwrite existing files
            if (Test-Path $t.Path) {
                Write-Host "Skipped (exists): [$($t.Tool)] $($t.Path)"
                continue
            }
            Set-Content -Path $t.Path -Value $t.Template -Encoding UTF8
            Write-Host "Created: [$($t.Tool)] $($t.Path)"
        }
        Write-Host ""
        Write-Host "Restart your sessions for the servers to load."
        $foundConfig = $targets[0].Path
    } else {
        Write-Host ""
        Write-Host "Skipped. See Step 0 in the Harness agent for manual setup."
        exit 1
    }
}

$content = Get-Content $foundConfig -Raw

Write-Host ""
Write-Host "--- Required servers ---"
$missing = $false
foreach ($srv in $requiredServers) {
    if ($content -match "`"$srv`"") {
        Write-Host "  [OK] $srv"
    } else {
        Write-Host "  [MISSING] $srv"
        $missing = $true
    }
}

Write-Host ""
Write-Host "--- Optional servers (degraded mode if missing) ---"
foreach ($srv in $optionalServers) {
    if ($content -match "`"$srv`"") {
        Write-Host "  [OK] $srv"
    } else {
        Write-Host "  [--] $srv (not configured, will use degraded mode)"
    }
}

Write-Host ""
if ($missing) {
    Write-Host "RESULT: FAIL - required MCP servers are missing."
    exit 1
} else {
    Write-Host "RESULT: PASS - all required MCP servers are configured."
    exit 0
}
