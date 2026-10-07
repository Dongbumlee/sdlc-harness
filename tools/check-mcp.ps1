# Pre-flight MCP server check for sdlc-harness (Windows PowerShell)
# Verifies that required MCP servers are configured before running the harness.
# Usage: .\tools\check-mcp.ps1 [-Config <path>]
# Default config locations checked: .vscode\mcp.json, $env:USERPROFILE\.copilot\mcp.json

param(
    [string]$Config = ""
)

$ErrorActionPreference = "Stop"

$requiredServers = @("awesome-copilot", "github", "context7")
$optionalServers = @("azure", "azure-devops")

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
    Write-Host "ERROR: No MCP config found. Checked:"
    foreach ($p in $configPaths) { Write-Host "  - $p" }
    Write-Host ""
    Write-Host "Copy the template from the harness repo:"
    Write-Host "  Copy-Item <harness>\.vscode\mcp.json .vscode\mcp.json"
    exit 1
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
