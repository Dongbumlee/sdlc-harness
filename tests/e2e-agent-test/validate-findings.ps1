#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Validates QA agent output against expected canary findings.

.DESCRIPTION
    After running a full QA review via @Sassy on the e2e-agent-test project,
    copy the QA Review Summary output into a text file and run this script
    to measure detection rates per reviewer.

.PARAMETER ReviewOutput
    Path to a text file containing the full QA Review Summary output from @Sassy.

.EXAMPLE
    .\validate-findings.ps1 -ReviewOutput .\qa-output.txt
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ReviewOutput
)

if (-not (Test-Path $ReviewOutput)) {
    Write-Error "File not found: $ReviewOutput"
    exit 1
}

$content = Get-Content $ReviewOutput -Raw

# ============================================================
# Canary detection patterns per reviewer
# Each canary has a set of keywords that should appear in the output
# ============================================================

$canaries = @{
    "Architecture Reviewer" = @(
        @{ Id = "A1"; Description = "Controller calls CosmosClient directly"; Keywords = @("layering", "controller.*infrastructure", "direct.*cosmos", "CosmosClient.*route") }
        @{ Id = "A2"; Description = "No application/service layer"; Keywords = @("application layer", "service layer", "missing.*layer", "no.*service") }
    )
    "Azure Compliance Reviewer" = @(
        @{ Id = "AZ1"; Description = "Raw azure-cosmos SDK"; Keywords = @("approved Cosmos DB library", "raw.*cosmos", "azure.cosmos", "CosmosClient") }
        @{ Id = "AZ2"; Description = "Raw azure-storage-blob SDK"; Keywords = @("approved Storage library", "raw.*blob", "azure.storage.blob", "BlobServiceClient") }
        @{ Id = "AZ3"; Description = "Connection string auth"; Keywords = @("connection.string", "DefaultAzureCredential", "Managed.*Identity") }
        @{ Id = "AZ4"; Description = "No AVM modules"; Keywords = @("AVM", "avm/res", "Azure Verified Module", "raw.*resource") }
        @{ Id = "AZ5"; Description = "No tags on resources"; Keywords = @("tag", "azd-env-name", "TemplateName", "CreatedBy") }
        @{ Id = "AZ6"; Description = "No WAF toggles"; Keywords = @("WAF", "enablePrivateNetworking", "enableMonitoring") }
        @{ Id = "AZ7"; Description = "No diagnostics"; Keywords = @("diagnostic", "Log Analytics", "monitor") }
        @{ Id = "AZ8"; Description = "No async with context manager"; Keywords = @("async with", "context manager") }
    )
    "Code Quality Reviewer" = @(
        @{ Id = "CQ1"; Description = "No copyright header (app.py)"; Keywords = @("copyright", "header", "license") }
        @{ Id = "CQ2"; Description = "No copyright header (App.tsx)"; Keywords = @("copyright", "header", "license") }
        @{ Id = "CQ3"; Description = "print() in app.py"; Keywords = @("print\(", "debug.*statement", "structured.*log") }
        @{ Id = "CQ4"; Description = "console.log in App.tsx"; Keywords = @("console\.log", "debug.*code", "remove.*console") }
        @{ Id = "CQ5"; Description = "Missing docstrings"; Keywords = @("docstring", "documentation", "missing.*doc") }
        @{ Id = "CQ6"; Description = "console.log in onClick"; Keywords = @("console\.log", "debug.*click") }
    )
    "Security Reviewer" = @(
        @{ Id = "S1"; Description = "Hardcoded OpenAI API key"; Keywords = @("API.*key", "hardcoded.*key", "secret", "OPENAI_API_KEY", "sk-proj") }
        @{ Id = "S2"; Description = "Hardcoded Cosmos connection string"; Keywords = @("connection.*string", "AccountKey", "secret.*cosmos") }
        @{ Id = "S3"; Description = "Hardcoded storage key"; Keywords = @("storage.*key", "AccountKey", "secret.*storage") }
        @{ Id = "S4"; Description = "No auth on endpoints"; Keywords = @("auth", "authorization", "unauthenticated", "A01", "access control") }
        @{ Id = "S5"; Description = "Error handler leaks details"; Keywords = @("traceback", "stack.*trace", "error.*leak", "internal.*detail") }
        @{ Id = "S6"; Description = "No input sanitization"; Keywords = @("injection", "sanitiz", "validation", "A03", "A08") }
        @{ Id = "S7"; Description = "dangerouslySetInnerHTML XSS"; Keywords = @("dangerouslySetInnerHTML", "XSS", "cross.*site.*script", "innerHTML") }
        @{ Id = "S8"; Description = "Secret in Bicep"; Keywords = @("secret.*bicep", "apiKey.*hardcoded", "key.*in.*bicep") }
        @{ Id = "S9"; Description = "Hardcoded subscription ID"; Keywords = @("subscription.*id", "hardcoded.*subscription", "12345678") }
    )
    "Test Coverage Reviewer" = @(
        @{ Id = "TC1"; Description = "No tests directory"; Keywords = @("no.*test", "missing.*test", "test.*coverage.*0", "no.*unit") }
        @{ Id = "TC2"; Description = "No Playwright tests"; Keywords = @("playwright", "e2e.*test", "no.*playwright") }
        @{ Id = "TC3"; Description = "No test framework configured"; Keywords = @("pytest", "vitest", "test.*framework", "no.*config") }
    )
    "UX & Accessibility Reviewer" = @(
        @{ Id = "UX1"; Description = "img without alt"; Keywords = @("alt.*text", "alt.*attribute", "missing.*alt", "<img") }
        @{ Id = "UX2"; Description = "div onClick without keyboard"; Keywords = @("onClick.*keyboard", "onKeyDown", "keyboard.*handler", "div.*onClick") }
        @{ Id = "UX3"; Description = "outline: none"; Keywords = @("outline.*none", "focus.*indicator", "focus.*visible") }
        @{ Id = "UX4"; Description = "Hardcoded background color"; Keywords = @("hardcoded.*color", "CSS.*variable", "#1a1a2e", "theme.*token") }
        @{ Id = "UX5"; Description = "Fixed width 2000px"; Keywords = @("2000px", "fixed.*width", "viewport", "overflow") }
        @{ Id = "UX6"; Description = "No Enter key handler"; Keywords = @("Enter.*key", "onKeyDown", "keyboard.*submit") }
        @{ Id = "UX7"; Description = "No empty state"; Keywords = @("empty.*state", "zero.*state", "no.*data.*message") }
        @{ Id = "UX8"; Description = "No Error Boundary"; Keywords = @("ErrorBoundary", "error.*boundary", "componentDidCatch") }
        @{ Id = "UX9"; Description = "No aria-label on div"; Keywords = @("aria-label", "accessible.*name", "ARIA") }
        @{ Id = "UX10"; Description = "No input validation before send"; Keywords = @("empty.*message", "validation.*send", "empty.*submit") }
    )
    "LLM Behavior Reviewer" = @(
        @{ Id = "LLM1"; Description = "No prompt injection guard"; Keywords = @("prompt.*injection", "injection.*guard", "reveal.*instructions", "ignore.*previous") }
        @{ Id = "LLM2"; Description = "No out-of-scope handling"; Keywords = @("out.*of.*scope", "domain.*boundary", "decline.*unrelated") }
        @{ Id = "LLM3"; Description = "No identity protection"; Keywords = @("identity", "persona", "system.*prompt.*confidential", "who.*made.*you") }
        @{ Id = "LLM4"; Description = "No max_tokens"; Keywords = @("max_tokens", "token.*limit", "context.*window") }
        @{ Id = "LLM5"; Description = "No retry logic"; Keywords = @("retry", "backoff", "429", "rate.*limit") }
        @{ Id = "LLM6"; Description = "No content filter"; Keywords = @("content.*filter", "content.*safety", "Azure.*AI.*Content.*Safety") }
        @{ Id = "LLM7"; Description = "No citation pattern"; Keywords = @("citation", "reference", "grounding") }
    )
    "Deployment Readiness Reviewer" = @(
        @{ Id = "DR1"; Description = "No health endpoint"; Keywords = @("health", "/health", "health.*check", "health.*endpoint") }
        @{ Id = "DR2"; Description = "Error handler exposes internals"; Keywords = @("traceback", "error.*leak", "internal.*detail", "stack.*trace") }
        @{ Id = "DR3"; Description = "print instead of logging"; Keywords = @("print\(", "structured.*log", "logging.*framework", "import.*logging") }
        @{ Id = "DR4"; Description = "No correlation ID"; Keywords = @("correlation", "trace.*id", "request.*id") }
        @{ Id = "DR5"; Description = "No timeout on HTTP call"; Keywords = @("timeout", "requests\.post.*timeout", "no.*timeout") }
        @{ Id = "DR6"; Description = "Unbounded query"; Keywords = @("unbounded", "LIMIT", "TOP", "SELECT \*.*FROM", "pagination") }
        @{ Id = "DR7"; Description = "Incomplete README"; Keywords = @("README", "missing.*section", "prerequisites", "troubleshooting", "known.*issues") }
        @{ Id = "DR8"; Description = "No dependency manifest"; Keywords = @("pyproject", "package\.json", "dependency.*manifest") }
        @{ Id = "DR9"; Description = "No pagination on list API"; Keywords = @("pagination", "offset", "limit", "page.*size") }
    )
}

# ============================================================
# Run detection
# ============================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Agent E2E Canary Detection Report" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$totalCanaries = 0
$totalFound = 0
$results = @()

foreach ($reviewer in $canaries.Keys | Sort-Object) {
    $reviewerCanaries = $canaries[$reviewer]
    $found = 0
    $missed = @()

    foreach ($canary in $reviewerCanaries) {
        $totalCanaries++
        $detected = $false

        foreach ($keyword in $canary.Keywords) {
            if ($content -match $keyword) {
                $detected = $true
                break
            }
        }

        if ($detected) {
            $found++
            $totalFound++
        }
        else {
            $missed += $canary
        }
    }

    $rate = if ($reviewerCanaries.Count -gt 0) { [math]::Round(($found / $reviewerCanaries.Count) * 100, 1) } else { 0 }
    $status = if ($rate -ge 80) { "PASS" } elseif ($rate -ge 50) { "WARN" } else { "FAIL" }
    $color = if ($rate -ge 80) { "Green" } elseif ($rate -ge 50) { "Yellow" } else { "Red" }

    Write-Host "$reviewer" -ForegroundColor White -NoNewline
    Write-Host " — $found/$($reviewerCanaries.Count) detected ($rate%) " -NoNewline
    Write-Host "[$status]" -ForegroundColor $color

    if ($missed.Count -gt 0) {
        foreach ($m in $missed) {
            Write-Host "  MISSED: $($m.Id) — $($m.Description)" -ForegroundColor DarkGray
        }
    }

    $results += [PSCustomObject]@{
        Reviewer  = $reviewer
        Total     = $reviewerCanaries.Count
        Found     = $found
        Missed    = $reviewerCanaries.Count - $found
        Rate      = "$rate%"
        Status    = $status
    }
}

$overallRate = [math]::Round(($totalFound / $totalCanaries) * 100, 1)
$overallStatus = if ($overallRate -ge 90) { "PASS" } elseif ($overallRate -ge 70) { "WARN" } else { "FAIL" }
$overallColor = if ($overallRate -ge 90) { "Green" } elseif ($overallRate -ge 70) { "Yellow" } else { "Red" }

Write-Host "`n----------------------------------------" -ForegroundColor Cyan
Write-Host "OVERALL: $totalFound/$totalCanaries canaries detected ($overallRate%) " -NoNewline
Write-Host "[$overallStatus]" -ForegroundColor $overallColor
Write-Host "Target: 80%+ per reviewer, 90%+ overall" -ForegroundColor DarkGray
Write-Host "----------------------------------------`n" -ForegroundColor Cyan

# Output as table
$results | Format-Table -AutoSize
