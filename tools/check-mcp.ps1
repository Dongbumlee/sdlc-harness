# Pre-flight MCP server check for sdlc-harness (Windows PowerShell)
# Verifies that required MCP servers are configured before running the harness.
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

Write-Host "=== sdlc-harness MCP pre-flight check ==="
Write-Host ""

$configPaths = @()
if ($Config -ne "") {
    $configPaths = @($Config)
} else {
    $configPaths = @(
        (Join-Path (Get-Location) ".vscode\mcp.json"),
        (Join-Path $env:USERPROFILE ".copilot\mcp.json")
    )
}

$foundConfig = $null
foreach ($p in $configPaths) {
    if (Test-Path $p) {
        $foundConfig = $p
        Write-Host "Config found: $p"
        break
    }
}

if ($null -eq $foundConfig) {
    Write-Host "No MCP config found. Checked:"
    foreach ($p in $configPaths) { Write-Host "  - $p" }
    Write-Host ""

    $target = $configPaths[0]
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
        Set-Content -Path $target -Value $defaultMcpJson -Encoding UTF8
        Write-Host ""
        Write-Host "Created: $target"
        Write-Host "Restart your Copilot session for the servers to load."
        $foundConfig = $target
    } else {
        Write-Host ""
        Write-Host "Skipped. Manual setup:"
        Write-Host "  1. Create .vscode\mcp.json with the required servers"
        Write-Host "  2. See Step 0 in the Harness agent for the JSON template"
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
    Write-Host "See Step 0 in the Harness agent for installation instructions."
    exit 1
} else {
    Write-Host "RESULT: PASS - all required MCP servers are configured."
    exit 0
}
