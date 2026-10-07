# Pre-flight MCP server check and auto-setup for sdlc-harness (Windows PowerShell)
# Checks VSCode, Copilot CLI, Claude Code, and Claude Desktop config locations.
# Automatically creates missing configs and adds missing servers. No prompts.
# Usage: .\check-mcp.ps1

$ErrorActionPreference = "Stop"

$requiredServers = @("awesome-copilot", "github", "context7")

$serverDefs = @{
    "awesome-copilot" = @{ command = "docker"; args = @("run", "--rm", "-i", "ghcr.io/github/awesome-copilot:latest") }
    "github"          = @{ type = "http"; url = "https://api.githubcopilot.com/mcp/" }
    "context7"        = @{ command = "npx"; args = @("-y", "@upstash/context7-mcp@latest") }
}

Write-Host "=== sdlc-harness MCP setup ==="
Write-Host ""

$configPaths = @(
    @{ Path = (Join-Path (Get-Location) ".vscode\mcp.json"); Tool = "VSCode"; Claude = $false },
    @{ Path = (Join-Path $env:USERPROFILE ".copilot\mcp.json"); Tool = "Copilot CLI"; Claude = $false },
    @{ Path = (Join-Path $env:USERPROFILE ".claude.json"); Tool = "Claude Code"; Claude = $true },
    @{ Path = (Join-Path $env:APPDATA "Claude\claude_desktop_config.json"); Tool = "Claude Desktop"; Claude = $true }
)

$allOk = $true

foreach ($c in $configPaths) {
    $path = $c.Path
    $tool = $c.Tool
    $key = if ($c.Claude) { "mcpServers" } else { "servers" }

    # Load existing config or start fresh
    $config = $null
    if (Test-Path $path) {
        try {
            $config = Get-Content $path -Raw | ConvertFrom-Json -AsHashtable
        } catch {
            Write-Host "[$tool] WARNING: existing config is invalid JSON, skipping: $path"
            $allOk = $false
            continue
        }
    }
    if ($null -eq $config) { $config = @{} }
    if (-not $config.ContainsKey($key)) { $config[$key] = @{} }

    # Add missing servers
    $added = @()
    foreach ($srv in $requiredServers) {
        if (-not $config[$key].ContainsKey($srv)) {
            $def = $serverDefs[$srv]
            if ($c.Claude) {
                # Claude format: no "type" for stdio, uses command/args directly
                $entry = @{}
                if ($def.ContainsKey("command")) { $entry["command"] = $def["command"] }
                if ($def.ContainsKey("args")) { $entry["args"] = $def["args"] }
                if ($def.ContainsKey("type") -and $def["type"] -eq "http") {
                    $entry["type"] = "http"; $entry["url"] = $def["url"]
                }
            } else {
                $entry = @{}
                if ($def.ContainsKey("type")) { $entry["type"] = $def["type"] } else { $entry["type"] = "stdio" }
                if ($def.ContainsKey("command")) { $entry["command"] = $def["command"] }
                if ($def.ContainsKey("args")) { $entry["args"] = $def["args"] }
                if ($def.ContainsKey("url")) { $entry["url"] = $def["url"] }
            }
            $config[$key][$srv] = $entry
            $added += $srv
        }
    }

    if ($added.Count -gt 0) {
        $dir = Split-Path $path -Parent
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
        $config | ConvertTo-Json -Depth 10 | Set-Content -Path $path -Encoding UTF8
        Write-Host "[$tool] Added: $($added -join ', ') -> $path"
    } else {
        Write-Host "[$tool] OK (all servers present)"
    }
}

Write-Host ""
if ($allOk) {
    Write-Host "RESULT: PASS - all tools configured."
    Write-Host "Restart your sessions for the servers to load."
    exit 0
} else {
    Write-Host "RESULT: WARNING - some configs need manual attention (see above)."
    exit 1
}
