#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Validates SDLC full pipeline e2e test outputs against expected artifacts and keywords.

.DESCRIPTION
    After running each step of the pipeline test (test-scenario.md), save each
    step's output to a separate file (step-0.txt through step-10.txt) and run
    this script to validate detection rates across all agents and skills.

.PARAMETER OutputDir
    Path to directory containing step output files (step-0.txt through step-10.txt).

.EXAMPLE
    .\validate-pipeline.ps1 -OutputDir .\outputs
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDir
)

if (-not (Test-Path $OutputDir)) {
    Write-Error "Directory not found: $OutputDir"
    exit 1
}

# ============================================================
# Step definitions: expected keywords per step
# ============================================================

$steps = @(
    @{
        Step        = 0
        Name        = "MCP Readiness (Sassy)"
        Phase       = "Init"
        Agent       = "Sassy"
        Skills      = @()
        Keywords    = @("MCP Server Status", "awesome-copilot", "GitHub MCP", "Context7", "SmartDoc")
        Artifacts   = @()  # Artifact check is file-based, done separately
    },
    @{
        Step        = 1
        Name        = "Requirements & Design (Analyst)"
        Phase       = "1-2"
        Agent       = "Analyst"
        Skills      = @("sdlc-project-manifest")
        Keywords    = @("architecture", "your-cosmosdb-lib|your-storage-lib", "python_api_application_template|template", "Azure OpenAI|OpenAI", "Cosmos DB|CosmosDB", "Repository Pattern|repository", "RAG|retrieval", "citation")
    },
    @{
        Step        = 2
        Name        = "ADR Creation (Documenter)"
        Phase       = "2"
        Agent       = "Documenter"
        Skills      = @("sdlc-adr-authoring")
        Keywords    = @("ADR|Architecture Decision Record", "Context", "Decision", "Consequences|Alternatives", "your-cosmosdb-lib|your-storage-lib", "Accepted|Proposed")
    },
    @{
        Step        = 3
        Name        = "Project Scaffolding (Scaffolder)"
        Phase       = "3"
        Agent       = "Scaffolder"
        Skills      = @("sdlc-project-scaffolding", "sdlc-project-manifest")
        Keywords    = @("src/SmartDoc", "pyproject.toml", "Dockerfile", "project-manifest", "python_api_application_template|template")
    },
    @{
        Step        = 4
        Name        = "Infrastructure (Deployer)"
        Phase       = "3+8"
        Agent       = "Deployer"
        Skills      = @("sdlc-azure-deployment")
        Keywords    = @("br/public:avm/res|AVM", "enablePrivateNetworking|WAF", "enableMonitoring|monitoring", "azure.yaml|azd", "Cosmos|cosmos", "OpenAI|openai", "Container Apps|containerapp", "tags|tag")
    },
    @{
        Step        = 5
        Name        = "Implementation (Implementer)"
        Phase       = "4"
        Agent       = "Implementer"
        Skills      = @("sdlc-cosmos-repository", "sdlc-blob-storage")
        Keywords    = @("RootEntityBase", "RepositoryBase", "your-cosmosdb-lib", "your-storage-lib|AsyncStorageBlobHelper", "async with", "pytest|test_", "DefaultAzureCredential|ManagedIdentity")
    },
    @{
        Step        = 6
        Name        = "Documentation (Documenter)"
        Phase       = "5"
        Agent       = "Documenter"
        Skills      = @("sdlc-adr-authoring")
        Keywords    = @("docs/api|API doc", "Prerequisites", "Deployment|deploy", "Usage|usage", "Configuration|config", "Troubleshooting|troubleshoot", "Known Issues|known.issue", "License|license")
    },
    @{
        Step        = 7
        Name        = "QA Review (QA Coordinator + 8)"
        Phase       = "6"
        Agent       = "QA Coordinator"
        Skills      = @("sdlc-project-qa", "sdlc-security-review", "sdlc-code-quality", "sdlc-architecture-review")
        Keywords    = @("QA Review Summary", "Critical Issues|Critical", "Important Issues|Important", "Suggestions|Suggestion", "Overall Verdict|Verdict", "SDLC Exit Criteria", "Manual QA Checklist", "Architecture Reviewer|Architecture", "Security Reviewer|Security", "UX.*Accessibility|Accessibility", "LLM Behavior|LLM", "Deployment Readiness|Deployment")
    },
    @{
        Step        = 8
        Name        = "RAI Review (RAI Reviewer)"
        Phase       = "7"
        Agent       = "RAI Reviewer"
        Skills      = @()
        Keywords    = @("RAI|Responsible AI", "Risk Level|risk", "prompt injection|injection", "data leakage|leakage|privacy", "bias|fairness", "transparency", "hallucination|grounding", "mitigation|recommend")
    },
    @{
        Step        = 9
        Name        = "Release Preparation (Release Manager)"
        Phase       = "8-9"
        Agent       = "Release Manager"
        Skills      = @()
        Keywords    = @("Changelog|CHANGELOG|changelog", "Release|release|v1", "PR|Pull Request|pull request", "SDLC Phase|phase|exit criteria", "feat:|fix:|chore:")
    },
    @{
        Step        = 10
        Name        = "Bug Checklist (QA Bug Checklist Reviewer)"
        Phase       = "6-standalone"
        Agent       = "QA Bug Checklist Reviewer"
        Skills      = @("sdlc-qa-bug-checklist")
        Keywords    = @("Bug Checklist|bug checklist", "Blocker|blocker", "Warning|warning", "sourced from|bugs", "Deployment|deployment", "Identity|identity|RBAC", "post-deploy|post.deploy")
    }
)

# ============================================================
# Run validation
# ============================================================

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "  SDLC Full Pipeline E2E Validation Report" -ForegroundColor Cyan
Write-Host "=============================================`n" -ForegroundColor Cyan

$totalKeywords = 0
$totalFound = 0
$stepResults = @()
$agentsCovered = @{}
$skillsCovered = @{}

foreach ($step in $steps) {
    $file = Join-Path $OutputDir "step-$($step.Step).txt"
    $stepNum = $step.Step

    if (-not (Test-Path $file)) {
        Write-Host "Step ${stepNum}: $($step.Name)" -ForegroundColor White -NoNewline
        Write-Host " — SKIPPED (file not found: step-${stepNum}.txt)" -ForegroundColor DarkGray
        $stepResults += [PSCustomObject]@{
            Step    = $stepNum
            Name    = $step.Name
            Phase   = $step.Phase
            Agent   = $step.Agent
            Total   = $step.Keywords.Count
            Found   = 0
            Rate    = "N/A"
            Status  = "SKIP"
        }
        continue
    }

    $content = Get-Content $file -Raw
    $found = 0
    $missed = @()

    foreach ($kw in $step.Keywords) {
        $totalKeywords++
        $patterns = $kw -split '\|'
        $detected = $false

        foreach ($p in $patterns) {
            if ($content -match $p) {
                $detected = $true
                break
            }
        }

        if ($detected) {
            $found++
            $totalFound++
        }
        else {
            $missed += $kw
        }
    }

    $rate = if ($step.Keywords.Count -gt 0) { [math]::Round(($found / $step.Keywords.Count) * 100, 1) } else { 100 }
    $status = if ($rate -ge 80) { "PASS" } elseif ($rate -ge 50) { "WARN" } else { "FAIL" }
    $color = if ($rate -ge 80) { "Green" } elseif ($rate -ge 50) { "Yellow" } else { "Red" }

    Write-Host "Step ${stepNum}: $($step.Name)" -ForegroundColor White -NoNewline
    Write-Host " — $found/$($step.Keywords.Count) keywords ($rate%) " -NoNewline
    Write-Host "[$status]" -ForegroundColor $color

    if ($missed.Count -gt 0) {
        foreach ($m in $missed) {
            Write-Host "  MISSED: $m" -ForegroundColor DarkGray
        }
    }

    # Track agent and skill coverage
    $agentsCovered[$step.Agent] = $status
    foreach ($skill in $step.Skills) {
        $skillsCovered[$skill] = $status
    }

    $stepResults += [PSCustomObject]@{
        Step    = $stepNum
        Name    = $step.Name
        Phase   = $step.Phase
        Agent   = $step.Agent
        Total   = $step.Keywords.Count
        Found   = $found
        Rate    = "$rate%"
        Status  = $status
    }
}

# ============================================================
# Overall summary
# ============================================================

$ranSteps = $stepResults | Where-Object { $_.Status -ne "SKIP" }
$passedSteps = $ranSteps | Where-Object { $_.Status -eq "PASS" }
$overallRate = if ($totalKeywords -gt 0) { [math]::Round(($totalFound / $totalKeywords) * 100, 1) } else { 0 }
$overallStatus = if ($overallRate -ge 90) { "PASS" } elseif ($overallRate -ge 70) { "WARN" } else { "FAIL" }
$overallColor = if ($overallRate -ge 90) { "Green" } elseif ($overallRate -ge 70) { "Yellow" } else { "Red" }

Write-Host "`n---------------------------------------------" -ForegroundColor Cyan
Write-Host "PIPELINE: $($ranSteps.Count) steps run, $($passedSteps.Count) passed" -ForegroundColor White
Write-Host "KEYWORDS: $totalFound/$totalKeywords detected ($overallRate%) " -NoNewline
Write-Host "[$overallStatus]" -ForegroundColor $overallColor
Write-Host "---------------------------------------------`n" -ForegroundColor Cyan

# Step results table
Write-Host "=== Step Results ===" -ForegroundColor Yellow
$stepResults | Format-Table -AutoSize

# Agent coverage
Write-Host "=== Agent Coverage ===" -ForegroundColor Yellow
$allAgents = @(
    "Sassy", "Analyst", "Documenter", "Scaffolder", "Deployer",
    "Implementer", "QA Coordinator", "Architecture Reviewer",
    "Azure Compliance Reviewer", "Code Quality Reviewer",
    "Security Reviewer", "Test Coverage Reviewer",
    "UX & Accessibility Reviewer", "LLM Behavior Reviewer",
    "Deployment Readiness Reviewer", "QA Bug Checklist Reviewer",
    "RAI Reviewer", "Release Manager"
)

$agentTable = foreach ($agent in $allAgents) {
    $status = if ($agentsCovered.ContainsKey($agent)) { $agentsCovered[$agent] }
              # QA sub-reviewers are covered by QA Coordinator step
              elseif ($agent -match "Reviewer" -and $agent -ne "RAI Reviewer" -and $agent -ne "QA Bug Checklist Reviewer" -and $agentsCovered.ContainsKey("QA Coordinator")) { $agentsCovered["QA Coordinator"] }
              else { "NOT TESTED" }

    [PSCustomObject]@{
        Agent  = $agent
        Status = $status
    }
}
$agentTable | Format-Table -AutoSize

# Skill coverage
Write-Host "=== Skill Coverage ===" -ForegroundColor Yellow
$allSkills = @(
    "sdlc-project-manifest", "sdlc-adr-authoring", "sdlc-project-scaffolding",
    "sdlc-azure-deployment", "sdlc-cosmos-repository", "sdlc-blob-storage",
    "sdlc-project-qa", "sdlc-security-review", "sdlc-code-quality",
    "sdlc-architecture-review", "sdlc-qa-bug-checklist"
)

$skillTable = foreach ($skill in $allSkills) {
    $status = if ($skillsCovered.ContainsKey($skill)) { $skillsCovered[$skill] } else { "NOT TESTED" }
    [PSCustomObject]@{
        Skill  = $skill
        Status = $status
    }
}
$skillTable | Format-Table -AutoSize

# Final verdict
$untestedAgents = ($agentTable | Where-Object { $_.Status -eq "NOT TESTED" }).Count
$untestedSkills = ($skillTable | Where-Object { $_.Status -eq "NOT TESTED" }).Count
$failedSteps = ($ranSteps | Where-Object { $_.Status -eq "FAIL" }).Count

if ($failedSteps -gt 0) {
    Write-Host "VERDICT: FAIL — $failedSteps step(s) failed" -ForegroundColor Red
}
elseif ($untestedAgents -gt 0 -or $untestedSkills -gt 0) {
    Write-Host "VERDICT: INCOMPLETE — $untestedAgents agent(s) and $untestedSkills skill(s) not tested" -ForegroundColor Yellow
}
else {
    Write-Host "VERDICT: PASS — All agents and skills validated" -ForegroundColor Green
}
