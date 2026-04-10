# SDLC Harness Evolution Specification

**Version:** 1.0.0-draft
**Date:** 2026-04-10
**Status:** Draft
**Scope:** sdlc-harness-dev (framework) + sdlc-bench (benchmarking)

---

## Document Purpose

This specification defines the evolution of sdlc-harness from a Copilot-specific, Azure-locked SDLC template into a platform-agnostic, benchmark-driven, multi-cloud orchestration framework aligned with 2025-2026 edge technologies.

It serves as both a strategic guide and a detailed implementation specification. Each section is self-contained and maps to a specific work stream, allowing parallel implementation.

### Repository Boundaries

| Repo | Purpose | Spec Sections |
|---|---|---|
| **sdlc-harness-dev** | The framework: agents, skills, orchestration, config, platform generation | §2 Architecture, §3 Agent Format, §5 MCP, §7 Configuration, §4 Per-Phase Specs |
| **sdlc-bench** | Evaluation & benchmarking: graders, canary system, trend tracking, CI integration | §6 Evaluation & Benchmarking |
| Both | Interoperability, spec import/export | §8 Interoperability |

---

## Table of Contents

1. [Industry Landscape & Trends](#1-industry-landscape--trends)
2. [Harness Architecture](#2-harness-architecture)
3. [Universal Agent Format](#3-universal-agent-format)
4. [Per-Phase Workflow Specifications](#4-per-phase-workflow-specifications)
5. [MCP Capability Model](#5-mcp-capability-model)
6. [Comprehensive Evaluation & Benchmarking](#6-comprehensive-evaluation--benchmarking)
7. [Configuration & Bootstrapping](#7-configuration--bootstrapping)
8. [Interoperability Layer](#8-interoperability-layer)
9. [Migration & Adoption](#9-migration--adoption)

---

## 1. Industry Landscape & Trends

### 1.1 Current State of SDLC Agent Frameworks

The AI-assisted SDLC landscape has matured rapidly from autocomplete to autonomous multi-hour development sessions. Agent mode has become the primary product, not a feature.

**Open-Source Frameworks:**

| Framework | Key Features | Significance |
|---|---|---|
| **OpenHands** (fmr. OpenDevin) | Sandboxed execution, REST+WebSocket APIs, agent delegation, MIT license, 68.6k+ stars | Enterprise-grade open-source leader |
| **SWE-agent** | Clean research architecture, tool-use patterns, flexible model backends | Preferred research framework |
| **Agentless** | No-agent approach: localization → repair → validation pipeline | Research baseline showing harness engineering matters as much as model capability |

**Commercial Platforms:**

| Platform | Differentiator |
|---|---|
| **GitHub Copilot** (Agent Mode) | Deep GitHub ecosystem integration, PR workflows, Actions |
| **Cursor** | Superior codebase understanding, multi-file editing |
| **Devin** (Cognition AI) | Parallel cloud SWE agents, Interactive Planning |
| **OpenAI Codex** | Autonomous feature writing with GPT-5.3 |
| **Claude Code** | Terminal-native, extended thinking, MCP integration |
| **Google Gemini Code Assist** | Firebase integration, full-stack workflow |

**Key trend:** Competition has shifted from autocomplete quality to autonomous task completion, context window management, and multi-session coherence.

### 1.2 Harness Design Patterns

Anthropic published two foundational engineering posts defining the state of the art:

**Two-Agent Architecture (Nov 2025):** Initializer Agent (sets up environment) + Coding Agent (makes incremental progress). Solved four failure modes: premature victory declaration, undocumented progress, premature completion marking, and environment setup confusion.

**Three-Agent GAN-Inspired Architecture (Mar 2026):** Evolved to Planner → Generator → Evaluator. Key innovations:
- Generator-evaluator loop maps to code review/QA in SDLC
- Context resets between sessions prevent drift
- Structured artifacts (JSON feature lists, progress files) bridge context windows
- The evaluator developed reliable "taste" for frontend design quality

This Planner → Generator → Evaluator pattern is now a recognized industry design pattern and is the architectural foundation of this specification.

### 1.3 Benchmarking Landscape

**SWE-bench** remains the foundational benchmark (top scores ~78-81% on Verified), but is saturating and SWE-bench Pro reveals that models perform significantly worse on truly unseen codebases (memorization inflates Verified scores by 20-30+ percentage points).

**Emerging specialized benchmarks:**

| Benchmark | Focus | Significance |
|---|---|---|
| **SWT-Bench** | Test generation quality | Frontier models score under 45% |
| **Terminal-Bench** | CLI/operational competence | Tests multi-step workflows |
| **SlopCodeBench** (Mar 2026) | Long-horizon quality degradation | All agents show structural erosion over iterative sessions |
| **SWE-EVO** | Sequential codebase evolution | Tests handling changes over time |
| **GitTaskBench** | Cost-normalized performance | Alpha metric: quality + tokens + human labor cost |
| **Context-Bench** | Context maintenance and memory | Surfaces cost-to-performance ratios |
| **DPAI Arena** (JetBrains) | Cross-ecosystem multi-language | First truly cross-ecosystem benchmark |
| **SWE-bench-Live** (Microsoft) | Contamination-resistant, monthly updates | Includes Windows-specific tasks |

**Critical gap:** No existing benchmark evaluates the full SDLC pipeline. Individual benchmarks cover bug fixing, test generation, or CLI operations in isolation. The sdlc-bench project addresses this gap by benchmarking all 9 SDLC phases end-to-end.

### 1.4 Key Technologies

**MCP (Model Context Protocol):**
- 5,000+ active servers, universal adoption across Claude, GPT, Gemini, Cursor, Windsurf
- Called "the fastest-growing developer protocol since GraphQL"
- Standardizes tool integration: stdio (local) and HTTP+SSE (remote)
- Growing pains being addressed: auth, discovery, stateful sessions, rate limiting

**Genericization Specifications:**
- **AI-SDLC Framework** (ai-sdlc.io): Pipeline/AgentRole/QualityGate resources, Kubernetes-inspired Spec/Status pattern
- **Open Agent Specification** (Oracle, Oct 2025): Framework-agnostic declarative language for agent portability
- **Agentic SDLC Spec Kit** (tikalk): 12-factor methodology for agentic development workflows

**Evaluation Frameworks:**
- **Anthropic Eval Taxonomy** (Jan 2026): Code-based, model-based, and human graders; capability vs. regression evals
- **LLM-as-Judge**: Mature pattern with Pydantic Evals, Braintrust AutoEvals, Langfuse
- **Promptfoo** (acquired by OpenAI, Mar 2026): Red-teaming and eval infrastructure now considered core AI infrastructure

### 1.5 Where sdlc-harness Positions Itself

sdlc-harness occupies a unique position in this landscape:

| Dimension | Industry Status | sdlc-harness Position |
|---|---|---|
| Full SDLC coverage | No framework covers all phases | 9-phase coverage with phase-specific agents |
| Adversarial QA | Most tools do single-pass review | 9 parallel independent reviewers with hard thresholds |
| Canary benchmarking | Novel approach (no equivalent in SWE-bench ecosystem) | 54 planted bugs with per-reviewer scoring |
| Platform portability | Tools are locked to one platform | Moving to platform-neutral IR with multi-target generation |
| Multi-cloud | Most frameworks are cloud-agnostic by omission | Actively supporting Azure, AWS, GCP with config-driven selection |
| Harness architecture | Anthropic's 3-agent pattern is state of the art | Adopting as meta-layer over existing 9-phase structure |

---

## 2. Harness Architecture

### 2.1 The 3-Agent Meta-Layer

The harness adopts Anthropic's Planner → Generator → Evaluator pattern as a meta-layer. The current 9-phase SDLC model becomes the Generator's internal structure.

```
┌──────────────────────────────────────────────────────────────┐
│                   HARNESS ORCHESTRATOR                        │
│  (Deterministic state machine — NOT an LLM agent)            │
│                                                              │
│  Responsibilities:                                           │
│  • Session management (start, resume, checkpoint)            │
│  • Agent lifecycle (spawn, context inject, collect output)   │
│  • Artifact persistence (read/write structured files)        │
│  • Human escalation routing                                  │
│  • Retry/re-plan decision logic                              │
│  • Progress tracking and reporting                           │
│                                                              │
│  Does NOT: make LLM calls, decide what to build,             │
│  evaluate quality (that's the Evaluator's job)               │
└──────┬──────────────┬────────────────┬───────────────────────┘
       │              │                │
       ▼              ▼                ▼
   PLANNER       GENERATOR        EVALUATOR
```

The orchestrator follows a fixed protocol:

```
1. Receive user intent
2. Spawn Planner → get execution plan
3. For each phase in plan:
   a. Spawn Generator with phase context
   b. Collect phase artifacts
   c. Spawn Evaluator with artifacts + criteria
   d. If PASS → advance to next phase
   e. If FAIL → respawn Generator with Evaluator feedback (max 3 retries)
   f. If CRITICAL_FAIL → respawn Planner for re-planning
4. On completion → produce final report
```

### 2.2 Planner Agent

**Role:** Strategic decomposition — turns user intent into an ordered execution plan.

**Evolves from:** The current `@Harness` coordinator agent, with scope narrowed to planning only.

**Inputs:**
- `user_intent` — natural language request
- `project_context` — harness-config.yml, existing code state, git history
- `previous_plans` — for re-planning scenarios after phase failures

**Output: Execution Plan (JSON)**
```json
{
  "project_id": "string",
  "intent_summary": "string",
  "phases": [
    {
      "phase_id": "requirements",
      "enabled": true,
      "priority": 1,
      "dependencies": [],
      "scope": "what this phase should focus on",
      "constraints": ["specific requirements"],
      "skip_reason": null
    }
  ]
}
```

**Decision protocol:**

| Intent Type | Phases Activated |
|---|---|
| New project | All 9 phases |
| New feature (existing project) | Skip scaffold, maybe skip deploy |
| Bug fix | Requirements (clarify) → implement → QA → release |
| Documentation update | Document → QA (doc review only) → release |
| Infrastructure change | Design → deploy → QA → release |

**Re-planning triggers:** Phase failed 3 consecutive times; Evaluator reports scope mismatch; new user input contradicts current plan.

### 2.3 Generator Agent

**Role:** Phase execution — takes a single phase from the plan and produces artifacts.

**Evolves from:** The current phase-specific worker agents (analyst, architect, scaffolder, deployer, implementer, documenter, QA coordinator, RAI reviewer, release manager).

The Generator is a coordinator that delegates to phase-specific sub-agents:

```yaml
sub_agents_by_phase:
  requirements:
    primary: analyst
    skills: [sdlc-workspace-init]
  design:
    primary: architect
    skills: [sdlc-adr-authoring, sdlc-design-review]
  scaffold:
    primary: scaffolder
    skills: [sdlc-project-scaffolding]
  deploy:
    primary: deployer              # cloud-specific variant
    skills: [sdlc-deployment]      # cloud-specific variant
  implement:
    primary: implementer
    supporting: [code-quality-reviewer]
    skills: [sdlc-code-quality, sdlc-implementation]
  document:
    primary: documenter
    skills: [sdlc-api-documentation]
  qa:
    primary: qa-coordinator
    supporting:                    # 9 parallel reviewers
      - architecture-reviewer
      - security-reviewer
      - code-quality-reviewer
      - test-coverage-reviewer
      - ux-accessibility-reviewer
      - llm-behavior-reviewer
      - deployment-readiness-reviewer
      - cloud-compliance-reviewer  # cloud-specific
      - performance-reviewer
    skills: [sdlc-code-quality, sdlc-test-execution]
  rai:
    primary: rai-reviewer
    skills: [sdlc-rai-review]
  release:
    primary: release-manager
    skills: [sdlc-release-management]
```

**Context reset protocol:** Each phase starts with a fresh LLM context. No conversation history from previous phases. Only structured artifacts bridge the context gap. Within a phase, sub-agents share context.

**Phase artifact schemas:** Each phase produces specific structured output (see §4 for per-phase details).

**Execution protocol per phase:**
1. Read progress notes and previous artifacts
2. Read evaluator feedback (if retry)
3. Select sub-agent(s) for this phase
4. Inject phase context (scope, constraints, artifacts)
5. Execute sub-agent(s)
6. Collect and validate output artifacts
7. Update progress notes
8. Commit to git with descriptive message
9. Return artifacts to orchestrator

### 2.4 Evaluator Agent

**Role:** Quality judgment — grades phase output against concrete, measurable criteria.

**Evolves from:** The current QA coordinator + 9 parallel reviewers, generalized to evaluate every phase.

**Output: Evaluation Report (JSON)**
```json
{
  "phase_id": "string",
  "verdict": "PASS | FAIL | CRITICAL_FAIL",
  "overall_score": 7.4,
  "dimensions": [
    {
      "dimension": "completeness",
      "score": 8.0,
      "weight": 0.3,
      "grader_type": "model-based",
      "findings": ["..."],
      "evidence": ["file:line references"]
    }
  ],
  "feedback_for_generator": "actionable improvement instructions",
  "feedback_for_planner": "only on CRITICAL_FAIL",
  "regression_flag": false,
  "cost_metrics": {
    "tokens_used": 12500,
    "api_cost_usd": 0.04,
    "wall_clock_seconds": 45
  }
}
```

**Multi-strategy grading:** The Evaluator uses three grader types per phase:

| Grader Type | Methods | Best For |
|---|---|---|
| **Code-based (deterministic)** | String match, schema validation, static analysis, test execution, AST analysis | Fast, cheap, reproducible |
| **Model-based (LLM-as-judge)** | Rubric scoring, natural language assertions, pairwise comparison | Captures nuance, subjective quality |
| **Human graders** | SME review, spot-check, calibration | Gold standard, calibrating model-based graders |

**Verdict decision logic:**
- **PASS**: Overall score ≥ threshold, no dimension below minimum
- **FAIL**: Score below threshold → retry with feedback (max 3 attempts)
- **CRITICAL_FAIL**: Score critically low or fundamental scope mismatch → escalate to Planner for re-planning

### 2.5 Structured Artifact Bridging

Artifacts bridge context windows between phases. All inter-phase communication happens through structured files, not conversation history.

**Artifact types:**
- **Feature list** (JSON): Machine-readable list of features with status
- **Progress notes** (Markdown): Human-readable summary of what's been done
- **Evaluation reports** (JSON): Per-phase scores and feedback
- **Git commits**: Descriptive messages that serve as an audit trail

**Why JSON over prose:** JSON forces precision, enables validation, and allows the orchestrator to programmatically inspect artifacts. Progress notes remain Markdown for human readability.

---

## 3. Universal Agent Format

### 3.1 Platform-Neutral Agent Schema

All agents are authored in a platform-neutral IR (Internal Representation) format. Platform-specific files are generated from this source.

```yaml
agent:
  id: string                    # unique identifier
  role_type: planner | generator | evaluator | reviewer | coordinator
  display_name: string
  purpose: string               # what this agent does

  capabilities:
    - code_generation
    - code_review
    - documentation
    - deployment

  context_requirements:
    files: [list of file patterns]
    artifacts: [list of artifact types from prior phases]
    config_sections: [which harness-config.yml sections]

  tool_access:
    required: [list]
    optional: [list]

  prompts:
    system: string              # core instructions
    phase_context: string       # injected per phase
    retry_context: string       # injected on retry with evaluator feedback

  constraints:
    max_retries: integer
    timeout_minutes: integer
    output_format: structured | freeform

  platform_overrides:           # when universal isn't enough
    copilot: { ... }
    claude_code: { ... }
    cursor: { ... }
    amplifier: { ... }
```

### 3.2 Platform-Neutral Skill Schema

```yaml
skill:
  id: string
  display_name: string
  trigger: string               # when to activate
  scope: phase | global
  phases: [list]                # which phases use this skill

  inputs:
    - name: string
      type: string
      source: config | artifact | user

  outputs:
    - name: string
      type: file | artifact | config_update

  instructions: string         # the skill's core content
```

### 3.3 Generation Targets

| Universal Field | Copilot `.agent.md` | Claude Code `AGENTS.md` | Cursor `.cursorrules` | Amplifier bundle |
|---|---|---|---|---|
| `id` | filename | section header | rule name | `meta.name` |
| `purpose` | description block | agent description | rule description | markdown body |
| `prompts.system` | markdown body | instructions section | rule content | system context |
| `tool_access` | `tools:` frontmatter | tool declarations | N/A | `tools:` YAML |
| `context_requirements.files` | `applyTo:` pattern | file references | glob patterns | `@mentions` |

**Generation CLI:**
```bash
harness generate --target copilot           # GitHub Copilot only
harness generate --target copilot,claude-code,amplifier  # multiple targets
harness generate --target all               # all supported platforms
```

**Sync verification:** CI check compares generated files against source IR. Fails if out of sync. Eliminates the current duplication between `vscode-extension/` and `.github/plugin/`.

### 3.4 Agent Lifecycle

1. **Author** in universal IR format (`agents/*.agent.yaml`)
2. **Validate** against schema (`harness validate`)
3. **Generate** platform-specific files (`harness generate --target <platform>`)
4. **Test** per platform (platform-specific test harness)
5. **Sync check** in CI (generated files match source)

Custom platform overrides allow platform-specific additions when the universal format is insufficient, while keeping the core definition shared.

---

## 4. Per-Phase Workflow Specifications

Each phase follows a consistent template with co-located details.

### 4.1 Requirements Phase

| Aspect | Detail |
|---|---|
| **Purpose** | Capture and structure user requirements into testable specifications |
| **Entry conditions** | User intent received, harness-config.yml loaded |
| **Primary agent** | analyst |
| **Skills** | sdlc-workspace-init |
| **MCP capabilities** | documentation-lookup (required), code-search (optional) |
| **Input artifacts** | None (first phase) |
| **Output artifacts** | requirements.md, feature-list.json, acceptance-criteria.json |
| **Quality gate** | Completeness ≥ 80%, ambiguity index < 0.2, no TBD placeholders |
| **Benchmark dimensions** | Requirement clarity score, completeness ratio, testability index |
| **Stack variations** | None (stack-agnostic phase) |
| **Cloud variations** | None (cloud-agnostic phase) |

### 4.2 Design Phase

| Aspect | Detail |
|---|---|
| **Purpose** | Produce architecture decisions and design documentation |
| **Entry conditions** | Requirements phase PASS |
| **Primary agent** | architect |
| **Skills** | sdlc-adr-authoring, sdlc-design-review |
| **MCP capabilities** | documentation-lookup (required), code-search (required), live-best-practices (optional) |
| **Input artifacts** | requirements.md, feature-list.json |
| **Output artifacts** | design-doc.md, ADRs (docs/adr/*.md), architecture-diagram.md |
| **Quality gate** | ADR quality ≥ 7/10, pattern compliance ≥ 6/10, no unresolved TODOs |
| **Benchmark dimensions** | Design completeness, coupling score, traceability to requirements |
| **Stack variations** | Pattern recommendations differ per stack (e.g., repository pattern for Python, dependency injection for .NET) |
| **Cloud variations** | Architecture patterns differ per cloud (e.g., event-driven with Azure Functions vs Lambda) |

### 4.3 Scaffold Phase

| Aspect | Detail |
|---|---|
| **Purpose** | Generate project structure, dependencies, and configuration |
| **Entry conditions** | Design phase PASS |
| **Primary agent** | scaffolder |
| **Skills** | sdlc-project-scaffolding |
| **MCP capabilities** | code-search (required), artifact-storage (optional) |
| **Input artifacts** | design-doc.md, feature-list.json |
| **Output artifacts** | Project structure, dependency manifests, linter/formatter configs, test framework setup |
| **Quality gate** | Structure correctness, dependency manifest valid, linter config present |
| **Benchmark dimensions** | Boilerplate ratio, setup time, convention compliance |
| **Stack variations** | Python: pyproject.toml + uv, Node: package.json + pnpm, Go: go.mod, .NET: .csproj |
| **Cloud variations** | Minimal (cloud specifics handled in Deploy phase) |

### 4.4 Deploy Phase

| Aspect | Detail |
|---|---|
| **Purpose** | Generate infrastructure-as-code, CI/CD pipelines, and environment setup |
| **Entry conditions** | Scaffold phase PASS |
| **Primary agent** | deployer (cloud-specific variant) |
| **Skills** | sdlc-deployment (cloud-specific variant) |
| **MCP capabilities** | deployment-management (required), compliance-checking (required), ci-cd-integration (optional) |
| **Input artifacts** | design-doc.md, project structure |
| **Output artifacts** | IaC files, pipeline configs, environment setup documentation |
| **Quality gate** | IaC syntax valid, security scan pass, no hardcoded secrets |
| **Benchmark dimensions** | Deployment success rate, time-to-environment, security posture score |
| **Stack variations** | Minimal |
| **Cloud variations** | Azure: Bicep + AVM, AWS: Terraform/CDK, GCP: Terraform. CI/CD: GitHub Actions / Azure DevOps / GitLab CI |

### 4.5 Implement Phase

| Aspect | Detail |
|---|---|
| **Purpose** | Write source code and tests that implement the design |
| **Entry conditions** | Deploy phase PASS (or scaffold if deploy skipped) |
| **Primary agent** | implementer |
| **Supporting agents** | code-quality-reviewer |
| **Skills** | sdlc-code-quality, sdlc-implementation |
| **MCP capabilities** | code-search (required), documentation-lookup (optional) |
| **Input artifacts** | design-doc.md, feature-list.json, scaffold output |
| **Output artifacts** | Source code, unit tests, integration tests |
| **Quality gate** | Lint pass, type check pass, test coverage ≥ 80%, no security vulnerabilities |
| **Benchmark dimensions** | Code quality score (lint + complexity), test coverage %, spec conformance |
| **Stack variations** | Python: ruff + pyright + pytest, Node: eslint + tsc + vitest, Go: golangci-lint + go test, .NET: dotnet format + dotnet test |
| **Cloud variations** | SDK-specific patterns (Azure SDK, AWS SDK, GCP client libraries) |

### 4.6 Document Phase

| Aspect | Detail |
|---|---|
| **Purpose** | Generate API documentation, README updates, and inline documentation |
| **Entry conditions** | Implement phase PASS |
| **Primary agent** | documenter |
| **Skills** | sdlc-api-documentation |
| **MCP capabilities** | code-search (required), documentation-lookup (required) |
| **Input artifacts** | Source code, design-doc.md |
| **Output artifacts** | API docs (docs/api/*.md), README.md updates, inline documentation |
| **Quality gate** | Coverage ratio ≥ 90%, accuracy check pass, no broken internal links |
| **Benchmark dimensions** | Documentation completeness, accuracy score, freshness |
| **Stack variations** | Python: docstrings + Sphinx/MkDocs, Node: JSDoc + TypeDoc, Go: godoc, .NET: XML docs |
| **Cloud variations** | Cloud-specific configuration documentation |

### 4.7 QA Phase

| Aspect | Detail |
|---|---|
| **Purpose** | Multi-reviewer adversarial quality assessment |
| **Entry conditions** | Document phase PASS |
| **Primary agent** | qa-coordinator |
| **Supporting agents** | 9 parallel independent reviewers |
| **Skills** | sdlc-code-quality, sdlc-test-execution |
| **MCP capabilities** | code-search (required), compliance-checking (required) |
| **Input artifacts** | All previous phase artifacts |
| **Output artifacts** | Per-reviewer reports, consolidated report, canary scores (if canary test) |
| **Quality gate** | Per-reviewer ≥ 80%, overall ≥ 90%, security reviewer ≥ 80% (hard) |
| **Benchmark dimensions** | Canary detection rate, false positive rate, severity accuracy, review thoroughness |
| **Stack variations** | Review criteria adapt per stack |
| **Cloud variations** | Cloud compliance reviewer is cloud-specific |

### 4.8 RAI (Responsible AI) Phase

| Aspect | Detail |
|---|---|
| **Purpose** | Responsible AI assessment: bias detection, ethical review, compliance |
| **Entry conditions** | QA phase PASS |
| **Primary agent** | rai-reviewer |
| **Skills** | sdlc-rai-review |
| **MCP capabilities** | compliance-checking (required), documentation-lookup (optional) |
| **Input artifacts** | Source code, design-doc.md, QA reports |
| **Output artifacts** | RAI assessment report, bias report |
| **Quality gate** | Compliance checklist complete, no critical findings |
| **Benchmark dimensions** | Issue detection rate, false negative rate, compliance coverage |
| **Stack variations** | None |
| **Cloud variations** | Cloud-specific AI service compliance (Azure AI, AWS Bedrock, GCP Vertex) |

### 4.9 Release Phase

| Aspect | Detail |
|---|---|
| **Purpose** | Prepare release artifacts, changelog, and deployment |
| **Entry conditions** | RAI phase PASS (or QA if RAI skipped) |
| **Primary agent** | release-manager |
| **Skills** | sdlc-release-management |
| **MCP capabilities** | ci-cd-integration (required), deployment-management (required), artifact-storage (optional) |
| **Input artifacts** | All previous phase artifacts, evaluation reports |
| **Output artifacts** | CHANGELOG.md, release notes, git tag, deployment artifacts |
| **Quality gate** | All tests passing, rollback procedure documented, version bumped |
| **Benchmark dimensions** | Release success rate, rollback time, changelog quality |
| **Stack variations** | Package-specific release (PyPI, npm, Docker) |
| **Cloud variations** | Cloud-specific deployment targets |

---

## 5. MCP Capability Model

### 5.1 Abstract Capability Taxonomy

Instead of listing specific MCP servers, the harness defines abstract capabilities that phases require. Any MCP server that provides the capability can be used.

| Capability | Description | Example Servers |
|---|---|---|
| `code-search` | Search and navigate codebases | GitHub MCP, Sourcegraph |
| `documentation-lookup` | Query documentation sources | Microsoft Learn MCP, Context7 |
| `deployment-management` | Manage cloud deployments | Azure MCP, AWS MCP, GCP MCP |
| `compliance-checking` | Verify compliance rules | Azure Policy MCP, custom |
| `ci-cd-integration` | Interact with CI/CD pipelines | Azure DevOps MCP, GitHub Actions |
| `artifact-storage` | Store/retrieve build artifacts | Azure Blob, S3, GCS |
| `live-best-practices` | Fetch up-to-date patterns | awesome-copilot, Context7 |

### 5.2 Capability-to-Phase Mapping

| Phase | Required Capabilities | Optional Capabilities |
|---|---|---|
| Requirements | documentation-lookup | code-search |
| Design | documentation-lookup, code-search | live-best-practices |
| Scaffold | code-search | live-best-practices |
| Deploy | deployment-management, compliance-checking | ci-cd-integration |
| Implement | code-search | documentation-lookup |
| Document | code-search, documentation-lookup | — |
| QA | code-search, compliance-checking | — |
| RAI | compliance-checking | documentation-lookup |
| Release | ci-cd-integration, deployment-management | artifact-storage |

### 5.3 Curated Default Server Sets

| Profile | Servers |
|---|---|
| **Azure** | GitHub MCP, Azure MCP, Azure DevOps MCP, awesome-copilot, Microsoft Learn MCP, Context7 |
| **AWS** | GitHub MCP, AWS MCP, awesome-copilot, Context7 |
| **GCP** | GitHub MCP, GCP MCP, awesome-copilot, Context7 |
| **Minimal** | GitHub MCP, Context7 |

### 5.4 Bootstrap Negotiation

At `harness init`:
1. Check which MCP servers are available
2. Map available servers to abstract capabilities
3. Warn if required capabilities for the chosen config profile aren't met
4. Generate `.vscode/mcp.json` (or platform-appropriate config) with available servers
5. Graceful degradation when optional capabilities are missing

---

## 6. Comprehensive Evaluation & Benchmarking

**Target repo:** sdlc-bench

### 6.1 Evaluation Architecture

Three evaluation layers:

```
Layer 1: Phase-Level Evaluation (real-time)
  └── Evaluator agent grades each phase during execution
  └── Pass/fail/retry decisions

Layer 2: Project-Level Benchmarking (per-run)
  └── Aggregate scores across phases
  └── Overall project quality score
  └── Time-to-completion and cost metrics

Layer 3: Trend Analysis (cross-run)
  └── Track scores across runs, models, and versions
  └── Capability eval → regression eval graduation
  └── Model comparison dashboards
```

### 6.2 Grading Strategies by Phase

Each phase uses a combination of grader types:

**Requirements:**
- Code-based: feature-list.json schema validation, acceptance criteria count ≥ 1 per feature, no TBD placeholders
- Model-based: completeness rubric (0-10), ambiguity index, testability check
- Threshold: pass ≥ 7.0, critical_fail < 4.0

**Design:**
- Code-based: ADR files exist and follow template, architecture diagram present
- Model-based: pattern compliance (0-10), coupling assessment, design-to-requirements traceability
- Threshold: pass ≥ 7.0 and pattern compliance ≥ 6.0, critical_fail < 4.0

**Scaffold:**
- Code-based: directory structure valid, dependency manifest parseable, linter config present
- Model-based: convention compliance (0-10), boilerplate ratio assessment
- Threshold: all code-based pass and overall ≥ 7.0

**Deploy:**
- Code-based: IaC syntax validation, security scan (checkov/tfsec), no hardcoded secrets
- Model-based: completeness, cost estimation, security posture
- Threshold: syntax valid and security clean and overall ≥ 7.0, critical_fail on security critical findings

**Implement:**
- Code-based: lint pass, type check pass, coverage ≥ 80%, no security vulnerabilities
- Model-based: spec conformance (0-10), code quality rubric, error handling completeness
- Threshold: all code-based pass and overall ≥ 7.0, critical_fail on security vulns or coverage < 50%

**Document:**
- Code-based: API endpoints documented, README sections present, no broken links
- Model-based: accuracy (0-10), coverage ratio, clarity assessment
- Threshold: coverage ≥ 90% and overall ≥ 7.0, critical_fail on accuracy < 5.0

**QA:**
- Code-based: all reviewer reports exist, canary detection rate, false positive rate
- Model-based: review thoroughness (0-10), severity accuracy, actionability
- Threshold: per-reviewer ≥ 80%, overall ≥ 90%, critical_fail on security reviewer < 70%

**RAI:**
- Code-based: compliance checklist items checked, bias detection tool ran
- Model-based: RAI completeness (0-10), ethical considerations addressed
- Threshold: checklist complete and overall ≥ 7.0

**Release:**
- Code-based: CHANGELOG updated, version bumped, all tests passing, rollback documented
- Model-based: readiness assessment (0-10), changelog quality
- Threshold: all code-based pass and overall ≥ 7.0

### 6.3 Canary System v2

Evolution of the current 54-canary system:

**Current state:** 54 planted bugs across 8 reviewer categories, keyword-matching detection via PowerShell script, binary PASS/FAIL per reviewer.

**Evolution:**

| Feature | Current | v2 |
|---|---|---|
| Canary count | Fixed 54 | Variable per run |
| Difficulty | Uniform | Tiered: easy / medium / hard / expert |
| Detection method | Keyword matching only | Keyword + LLM-as-judge + AST analysis |
| Categories | 8 fixed | 8 core + extensible custom categories |
| Cross-category | None | Cross-cutting canaries spanning multiple domains |
| Generation | Manual | Automated via code mutation |
| Anti-gaming | None | Randomized placement per run |

**Automated canary generation:**
```
Mutation types:
  - remove_error_handling
  - weaken_auth_check
  - skip_input_validation
  - introduce_race_condition
  - remove_test_assertion
  - hardcode_secret
  - break_accessibility
  - introduce_sql_injection

Protocol:
  1. Start with clean, correct code
  2. Apply mutation → create canary version
  3. Record mutation location, type, and difficulty
  4. Auto-generate expected-findings entry
  5. Randomize placement across files
```

### 6.4 Metrics and Reporting

**Per-run benchmark report (JSON):**
```json
{
  "run_id": "2026-04-10-001",
  "model": "claude-sonnet-4.5",
  "project_type": "rest-api",
  "config_profile": "azure-python-fastapi",
  "phases": {
    "requirements": {
      "score": 8.2,
      "attempts": 1,
      "duration_seconds": 180,
      "tokens_used": 8500,
      "api_cost_usd": 0.03
    }
  },
  "canary_results": {
    "total": 54,
    "detected": 51,
    "rate": 0.944,
    "per_reviewer": { "security": 0.89, "architecture": 1.0 },
    "per_difficulty": { "easy": 1.0, "medium": 0.95, "hard": 0.85, "expert": 0.71 }
  },
  "cost_summary": {
    "total_tokens": 125000,
    "total_api_cost_usd": 0.42,
    "total_wall_clock_seconds": 1800
  },
  "overall_score": 7.9,
  "pass_k_reliability": { "k": 5, "pass_rate": 0.80 },
  "degradation_metrics": {
    "phase_1_quality": 8.5,
    "phase_9_quality": 7.2,
    "degradation_rate": -0.14
  },
  "regression_flags": ["design_score_dropped_from_8.1"]
}
```

**Key metrics tracked:**

| Metric Category | Metrics |
|---|---|
| **Task-level** | Completion rate, pass^k reliability (across k repeated trials), per-phase scores |
| **Quality** | Structural erosion across phases, code complexity trends, spec conformance |
| **Cost** | Tokens per phase, API cost per run, cost per successful outcome, alpha metric (quality × efficiency) |
| **Operational** | Wall-clock time, retry count, human intervention rate |
| **Regression** | Score change vs. baseline, per-model trend lines, capability graduation tracking |

### 6.5 CI/CD Integration

**GitHub Actions workflow:**
```yaml
# .github/workflows/benchmark.yml
on:
  pull_request:
    paths: ['agents/**', 'skills/**']
  schedule:
    - cron: '0 6 * * 1'  # Weekly regression run

jobs:
  benchmark:
    steps:
      - run: harness benchmark --scenario canary-54 --model claude-sonnet-4.5
      - run: harness benchmark --compare baseline.json
      - run: harness benchmark --report pr-comment
```

**PR-gated regression:** New agent/skill changes must not regress benchmark scores below threshold. Scores posted as PR comments for review.

### 6.6 Differentiation Opportunities

Areas where sdlc-bench fills gaps in the existing benchmark landscape:

| Gap | sdlc-bench Coverage |
|---|---|
| No full SDLC pipeline benchmark exists | End-to-end 9-phase benchmark |
| No deployment/IaC correctness benchmark | Deploy phase evaluator with IaC validation |
| No documentation quality benchmark | Document phase evaluator with accuracy scoring |
| No code review effectiveness benchmark | QA phase with 9 independent reviewers |
| No accessibility evaluation benchmark | UX/accessibility reviewer |
| No cross-phase degradation measurement | Phase-over-phase quality erosion tracking |
| No cost-normalized SDLC benchmarks | Alpha metric across all phases |

---

## 7. Configuration & Bootstrapping

### 7.1 harness-config.yml Schema

Single source of truth for project configuration:

```yaml
project:
  name: "{{PROJECT_NAME}}"
  domain: "{{BUSINESS_DOMAIN}}"

organization:
  name: "{{ORG_NAME}}"
  github_org: "{{GITHUB_ORG}}"
  ado_org: "{{ADO_ORG}}"              # optional

stack:
  backend:
    language: python                    # python | java | go | dotnet | nodejs
    framework: fastapi                  # fastapi | django | flask | spring | gin | express
    version: "3.12"
  frontend:
    framework: react                    # react | vue | angular | svelte | none
    language: typescript                # typescript | javascript
    bundler: vite                       # vite | webpack | next | nuxt
  testing:
    unit: pytest                        # pytest | jest | vitest | junit | go-test
    e2e: playwright                     # playwright | cypress | selenium
  package_manager:
    backend: uv                         # uv | pip | poetry | maven | gradle | go-mod
    frontend: npm                       # npm | yarn | pnpm

cloud:
  provider: azure                       # azure | aws | gcp | none
  services:
    database: cosmosdb                  # cosmosdb | dynamodb | firestore | postgresql
    storage: blob                       # blob | s3 | gcs | minio
    compute: container-apps             # container-apps | ecs | cloud-run | k8s
    ai: azure-openai                    # azure-openai | openai | anthropic | gemini
  iac: bicep                            # bicep | terraform | pulumi | cdk

cicd:
  platform: github-actions              # github-actions | azure-devops | gitlab-ci
  registry: acr                         # acr | ecr | gcr | dockerhub

evaluation:
  canary_mode: enabled                   # enabled | disabled | ci-only
  canary_difficulty: balanced            # easy-heavy | balanced | hard-heavy
  benchmark_storage: ./benchmarks/
  regression_threshold: 0.5
  ci_gate: true

distribution:
  targets: [copilot, claude-code]
  sync_check: true

orchestrator:
  max_retries_per_phase: 3
  max_replan_attempts: 2
  human_escalation: true
  parallel_qa_reviewers: 9

libraries:                               # optional org-specific libraries
  - name: my-db-helper
    repo: "org/db-helper"
    install: "uv add my-db-helper"

templates:                               # optional scaffolding templates
  - name: api-template
    repo: "org/api-template"
    use_for: "REST API / web service"
```

### 7.2 Profile System

Pre-built profiles inherit from a base and override stack/cloud specifics:

| Profile | Stack | Cloud | CI/CD |
|---|---|---|---|
| `azure-python-fastapi` | Python + FastAPI + React | Azure (Cosmos, Blob, Container Apps) | GitHub Actions |
| `aws-node-express` | Node.js + Express + React | AWS (DynamoDB, S3, ECS) | GitHub Actions |
| `gcp-go-gin` | Go + Gin + Vue | GCP (Firestore, GCS, Cloud Run) | GitHub Actions |
| `cloud-agnostic-python` | Python + FastAPI + React | None (PostgreSQL, MinIO, K8s) | GitHub Actions |

```bash
harness init --profile azure-python-fastapi  # instant setup
harness init                                  # interactive wizard
```

### 7.3 Bootstrap Pipeline

```
Config → IR generation → adapter generation → MCP config → verification
```

1. Read `harness-config.yml` (or run interactive wizard to create it)
2. Select appropriate agent/skill variants based on config
3. Generate platform-specific files from universal IR
4. Generate MCP config with capability-matched servers
5. Generate `copilot-instructions.md` from template
6. Verify all generated files are valid
7. Progressive initialization: config can start sparse, fill incrementally as phases execute

---

## 8. Interoperability Layer

### 8.1 Harness IR as Canonical Format

```
External specs ──→ Import adapter ──→ Harness IR ──→ Export adapter ──→ External specs
                                         │
                                         ▼
                                  Platform generators
                                  (Copilot, Claude Code, Cursor, Amplifier)
```

The Harness Internal Representation (IR) is the canonical format for agents, skills, workflows, and evaluations. All external formats are imported/exported through adapters.

### 8.2 Spec Import/Export Adapters

| Spec | Direction | Mapping |
|---|---|---|
| **AI-SDLC Framework** | Import/Export | Pipeline → phase sequence, AgentRole → agent IR, QualityGate → evaluator criteria |
| **Open Agent Specification** | Import/Export | Agent definition → agent IR, workflow → phase sequence |
| **Custom specs** | Export SDK | Adapter interface for third-party specs |

### 8.3 Adapter Interface

```python
class SpecAdapter:
    def import_spec(self, external_spec: dict) -> HarnessIR:
        """Convert external spec format to Harness IR."""
        ...

    def export_spec(self, harness_ir: HarnessIR) -> dict:
        """Convert Harness IR to external spec format."""
        ...

    def validate_mapping(self, external: dict, internal: HarnessIR) -> ValidationReport:
        """Verify round-trip fidelity."""
        ...
```

### 8.4 Cross-Repo Integration

sdlc-harness-dev and sdlc-bench share the Harness IR:
- **sdlc-harness-dev** owns: agent IR schemas, skill IR schemas, config schema, platform generators
- **sdlc-bench** owns: evaluation report schemas, grader definitions, canary system, benchmark runners
- **Shared contract**: Evaluation report JSON schema, artifact format schemas

---

## 9. Migration & Adoption

### 9.1 Current → New File Mapping

| Current Location | New Location | Change |
|---|---|---|
| `vscode-extension/agents/*.agent.md` | Generated from `agents/*.agent.yaml` (IR) | Source becomes IR; .agent.md is generated output |
| `.github/plugin/agents/*.agent.md` | Generated from same IR source | Duplication eliminated |
| `vscode-extension/skills/*/SKILL.md` | Generated from `skills/*.skill.yaml` (IR) | Source becomes IR |
| `.github/copilot-instructions.md` | Generated from `templates/copilot-instructions.md.tmpl` | Template-driven |
| Hardcoded Azure/Python references | Driven by `harness-config.yml` | Config-driven |
| `validate-findings.ps1` (keyword only) | Multi-strategy graders in sdlc-bench | Keyword + LLM-as-judge + AST |
| `validate-pipeline.ps1` | Automated benchmark runner in sdlc-bench | CI-integrated |
| Manual benchmark runs | GitHub Actions automated evaluation | PR-gated regression |

### 9.2 Phased Transition Plan

**Phase 1: Architecture + Agent Format** (sdlc-harness-dev)
- Define Harness IR schemas for agents and skills
- Convert existing 18 agents to IR format
- Build generation pipeline for Copilot target
- Verify generated output matches current behavior

**Phase 2: Configuration System** (sdlc-harness-dev)
- Implement `harness-config.yml` schema
- Build bootstrap pipeline with profile system
- Convert hardcoded references to config-driven templates
- Create pre-built profiles for Azure/AWS/GCP

**Phase 3: Evaluation System** (sdlc-bench)
- Implement multi-strategy graders per phase
- Evolve canary system to v2 (difficulty tiers, LLM-as-judge)
- Build benchmark report format and trend tracking
- Integrate with GitHub Actions for CI-gated regression

**Phase 4: Multi-Platform Distribution** (sdlc-harness-dev)
- Add generation targets for Claude Code, Cursor, Amplifier
- Build sync verification CI check
- Implement interoperability adapters

**Phase 5: 3-Agent Orchestrator** (sdlc-harness-dev)
- Implement deterministic orchestrator state machine
- Evolve @Harness into Planner role
- Implement Generator coordinator with sub-agent delegation
- Integrate Evaluator with sdlc-bench graders

### 9.3 Backward Compatibility

- Generated Copilot `.agent.md` files are functionally identical to current ones
- Existing users see no behavior change until they opt into new features
- Current canary benchmarks continue to work during v2 migration
- No behavior change for users who don't adopt the new config system

---

## References

### Industry Sources
- Anthropic: [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) (Nov 2025)
- Anthropic: [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps) (Mar 2026)
- Anthropic: [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (Jan 2026)
- AI-SDLC Framework: [ai-sdlc.io](https://ai-sdlc.io/docs/spec/spec)
- Open Agent Specification: [arXiv:2510.04173](https://arxiv.org/abs/2510.04173)
- Microsoft: [SWE-bench-Live](https://github.com/microsoft/SWE-bench-Live)

### Benchmarks
- [SWE-bench](https://www.swebench.com/)
- [SWE-bench Pro](https://labs.scale.com/leaderboard/swe_bench_pro_public) (Scale AI)
- [SlopCodeBench](https://arxiv.org/abs/2603.24755) — Long-horizon quality degradation
- [SWE-EVO](https://arxiv.org/pdf/2512.18470) — Longitudinal codebase evolution
- [GitTaskBench](https://arxiv.org/html/2508.18993v1) — Cost-normalized performance
- [Terminal-Bench](https://ainativedev.io/news/8-benchmarks-shaping-the-next-generation-of-ai-agents) — CLI competence
- [DPAI Arena](https://blog.jetbrains.com/blog/2025/10/28/introducing-developer-productivity-ai-arena-an-open-platform-for-ai-coding-agents-benchmarks/) (JetBrains)

### Evaluation Platforms
- [Braintrust](https://www.braintrust.dev) — CI/CD-integrated eval
- [Langfuse](https://langfuse.com) — Open-source observability
- [Pydantic Evals](https://ai.pydantic.dev/evals/) — Type-safe eval framework
- [Promptfoo](https://github.com/promptfoo/promptfoo) — Red-teaming + eval (acquired by OpenAI Mar 2026)

### Reports
- Anthropic: [2026 Agentic Coding Trends Report](https://resources.anthropic.com/hubfs/2026+Agentic+Coding+Trends+Report.pdf)
- PwC: [Agentic SDLC in Practice](https://www.pwc.com/m1/en/publications/2026/docs/future-of-solutions-dev-and-delivery-in-the-rise-of-gen-ai.pdf)
- [State of AI-Assisted Coding in 2026](https://generativeprogrammer.com/p/state-of-ai-assisted-coding-in-2026)