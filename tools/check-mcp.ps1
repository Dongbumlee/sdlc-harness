# Pre-flight MCP server check for sdlc-harness (Windows PowerShell)
# Verifies that required MCP servers are configured before running the harness.
# Checks VSCode, Copilot CLI, Claude Code, and Claude Desktop config locations.
# If no config exists, offers to create one automatically.
# Usage: .\tools\check-mcp.ps1 [-Config <path>] [-Auto]

param(
    [string]$Config = "",
    [switch]$Auto
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

    # Default to VSCode location for new config
    $target = $configPaths[0].Path
    $template = $defaultMcpJson
    $doCreate = $false

    if ($Auto) {
        $doCreate = $true
    } else {
        $answer = Read-Host "Create default MCP config at $target ? (y/n)"
        if ($answer -eq "y" -or $answer -eq "Y") { $doCreate = $true }
    }

    if ($doCreate) {
        $dir = Split-Path $target -Parent
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
        Set-Content -Path $target -Value $template -Encoding UTF8
        Write-Host ""
        Write-Host "Created: $target"
        Write-Host "Restart your session for the servers to load."
        $foundConfig = $target
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
