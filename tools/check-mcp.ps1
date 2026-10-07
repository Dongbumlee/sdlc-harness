# Pre-flight MCP server check and auto-setup for sdlc-harness (Windows PowerShell)
# Checks VSCode, Copilot CLI, Claude Code, and Claude Desktop config locations.
# Automatically creates missing configs and adds missing servers. No prompts.
# Usage: .\check-mcp.ps1

$ErrorActionPreference = "Stop"

$requiredServers = @("awesome-copilot", "github", "context7")

$serverDefs = @{
    "awesome-copilot" = @{ command = "docker"; args = @("run", "--rm", "-i", "ghcr.io/microsoft/mcp-dotnet-samples/awesome-copilot:latest") }
    "github"          = @{ type = "http"; url = "https://api.githubcopilot.com/mcp/" }
    "context7"        = @{ command = "npx"; args = @("-y", "@upstash/context7-mcp@latest") }
}

Write-Host "=== sdlc-harness MCP setup ==="
Write-Host ""

$configPaths = @(
    @{ Path = (Join-Path (Get-Location) ".vscode\mcp.json"); Tool = "VSCode"; Claude = $false },
    @{ Path = (Join-Path $env:USERPROFILE ".copilot\mcp-config.json"); Tool = "Copilot CLI"; Claude = $true },
    @{ Path = (Join-Path $env:USERPROFILE ".claude.json"); Tool = "Claude Code"; Claude = $true },
    @{ Path = (Join-Path $env:APPDATA "Claude\claude_desktop_config.json"); Tool = "Claude Desktop"; Claude = $true }
)

$allOk = $true

foreach ($c in $configPaths) {
    $path = $c.Path
    $tool = $c.Tool
    $key = if ($c.Claude) { "mcpServers" } else { "servers" }

    # Load existing config or start fresh (PS 5.1 compatible, no -AsHashtable)
    $configRaw = $null
    if (Test-Path $path) {
        try {
            $configRaw = Get-Content $path -Raw | ConvertFrom-Json
        } catch {
            Write-Host "[$tool] WARNING: existing config is invalid JSON, skipping: $path"
            $allOk = $false
            continue
        }
    }

    # Convert PSCustomObject to Hashtable for PS 5.1 compatibility
    function ConvertTo-Hashtable($obj) {
        if ($obj -is [System.Collections.IEnumerable] -and $obj -isnot [string]) {
            return @($obj | ForEach-Object { ConvertTo-Hashtable $_ })
        } elseif ($obj -is [PSCustomObject]) {
            $ht = @{}
            $obj.PSObject.Properties | ForEach-Object { $ht[$_.Name] = (ConvertTo-Hashtable $_.Value) }
            return $ht
        } else {
            return $obj
        }
    }

    $config = @{}
    if ($null -ne $configRaw) { $config = ConvertTo-Hashtable $configRaw }
    if (-not $config.ContainsKey($key)) { $config[$key] = @{} }

    # Add missing servers or update outdated definitions
    $added = @()
    $updated = @()
    foreach ($srv in $requiredServers) {
        $def = $serverDefs[$srv]
        $shouldWrite = $false

        if (-not $config[$key].ContainsKey($srv)) {
            $shouldWrite = $true
            $added += $srv
        } else {
            # Check if existing definition matches expected (e.g. wrong Docker image)
            $existing = $config[$key][$srv]
            $existingJson = ($existing | ConvertTo-Json -Compress -Depth 10)
            # Build expected entry to compare
            $expectedEntry = @{}
            if ($c.Claude) {
                if ($def.ContainsKey("command")) { $expectedEntry["command"] = $def["command"] }
                if ($def.ContainsKey("args")) { $expectedEntry["args"] = $def["args"] }
                if ($def.ContainsKey("type") -and $def["type"] -eq "http") {
                    $expectedEntry["type"] = "http"; $expectedEntry["url"] = $def["url"]
                }
            } else {
                if ($def.ContainsKey("type")) { $expectedEntry["type"] = $def["type"] } else { $expectedEntry["type"] = "stdio" }
                if ($def.ContainsKey("command")) { $expectedEntry["command"] = $def["command"] }
                if ($def.ContainsKey("args")) { $expectedEntry["args"] = $def["args"] }
                if ($def.ContainsKey("url")) { $expectedEntry["url"] = $def["url"] }
            }
            $expectedJson = ($expectedEntry | ConvertTo-Json -Compress -Depth 10)
            if ($existingJson -ne $expectedJson) {
                $shouldWrite = $true
                $updated += $srv
            }
        }

        if ($shouldWrite) {
            if ($c.Claude) {
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
        }
    }

    if ($added.Count -gt 0 -or $updated.Count -gt 0) {
        $dir = Split-Path $path -Parent
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
        $config | ConvertTo-Json -Depth 10 | Set-Content -Path $path -Encoding UTF8
        if ($added.Count -gt 0) { Write-Host "[$tool] Added: $($added -join ', ') -> $path" }
        if ($updated.Count -gt 0) { Write-Host "[$tool] Updated: $($updated -join ', ') -> $path" }
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
