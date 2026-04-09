 # SDLC Agent Template — SDLC Harness

 > **An agent-driven SDLC template that accelerates application development with guaranteed quality,
 > reusability, and zero fragmentation from our dev standards.**

 This repository is the **SDLC (Software Development Lifecycle) Agent Template** — a ready-to-adopt
 configuration package that enables teams to build [production-ready applications](https://accelerators.ms)
 at production speed while maintaining full compliance with team development standards.

 It combines **GitHub Copilot Agent mode**, structured prompt files, and reusable quality
 instructions so that every new application or Azure-based service starts from proven patterns — not
 from scratch — and stays aligned throughout its lifecycle.

 **What this template provides:**

 - **Agent-driven development** — Copilot Agent mode and Copilot Coding Agent (CCA) automate
   implementation, testing, and documentation across all 9 SDLC phases.
 - **Harness-quality QA** — inspired by [Anthropic's harness design research](https://www.anthropic.com/engineering/harness-design-long-running-apps),
   the QA system uses adversarial evaluation, numeric scoring with hard fail thresholds,
   and iterative feedback loops (QA → fix → re-QA) to catch issues that single-pass reviews miss.
 - **application quality guarantee** — enforced architecture, Azure SDK abstractions, and code/test
   quality standards ensure every repository meets the same production bar.
 - **Zero fragmentation** — standardized scaffolding templates, shared libraries, and consistent
   patterns eliminate divergence across teams and repositories.
 - **Reusability at scale** — Scaffolding Templates and reusable components (`sas-cosmosdb`,
   `sas-storage`, Bicep/AVM modules) reduce duplication and accelerate delivery.
 - **Azure best practices built in** — identity management, infrastructure-as-code, resource
   governance, and Well-Architected Framework alignment are embedded, not bolted on.
 - **One-command install** — distributed as an [Agent Plugin](#quick-start--install-in-any-repo)
   for both VS Code and GitHub Copilot CLI. No manual file copying needed.

 > **New here?** Start with the [Hands-On Guide](.design/hands-on-guide.md) for a step-by-step walkthrough of the SDLC workflow with practical examples.

 ---

 ## Goals

 This SDLC Agent Template is designed to:

 1. **Accelerate implementation via agent-driven workflows**
    - Use Copilot Agent mode and CCA to generate, modify, and review code following established patterns.
    - Automate boilerplate and repetitive changes (e.g., new endpoints, repositories, pipelines)
      through structured prompt files that encode team knowledge.

 2. **Strengthen quality assurance**
    - Use Copilot to generate tests, inspect failing tests, and propose fixes.
    - Run structured code-quality and test-quality passes based on language-specific checklists.

 3. **Enforce consistent architecture**
    - Apply layered and clean design principles with well-defined dependency boundaries.
    - Maintain predictable documentation (ADRs, API docs) using common structure and locations.

 4. **Standardize Azure best practices**
    - Use approved Azure SDK abstractions (`sas-cosmosdb`, `sas-storage`) instead of raw SDK clients.
    - Follow identity management, infrastructure-as-code, and resource governance conventions.

 5. **Promote Scaffolding Template and reusable components**
    - Scaffold new projects from standardized templates (base app, FastAPI, AI agent).
    - Reuse shared libraries and proven patterns to reduce duplication across repositories.

 6. **Prevent fragmentation across applications**
    - Ensure every new application or service starts from the same template, instructions, and quality bar.
    - Eliminate team-by-team divergence in architecture, SDK usage, testing, and documentation patterns.
    - Maintain a single source of truth for dev standards that evolves with the organization.

 ---

 ## Quick Start — Install in Any Repo

 Install the SDLC Agent Template as an **Agent Plugin** with one command.
 This works in both **VS Code** and **GitHub Copilot CLI**.

 ### VS Code

 ```
 Command Palette (Ctrl+Shift+P) → Chat: Install Plugin From Source
 → https://github.com/gim-home/sdl_with_agent
 ```

 ### GitHub Copilot CLI

 ```bash
 copilot plugin install gim-home/sdl_with_agent
 ```

 ### First use

 Open your project and invoke Harness — it auto-detects a new repo and bootstraps everything:

 ```
 @Harness help me set up this project
 ```

 Harness will ask for your project name and domain, then generate all workspace files
 (`copilot-instructions.md`, quality instructions, prompt files) customized for your project.

 > **What you get instantly:** 18 agents (including 9 parallel QA reviewers), 12 domain skills,
 > and the full SDLC workflow — from requirements to release.
 >
 > See [How to Adopt This Template](#how-to-adopt-this-template-in-a-new-gsa--app-repo)
 > for detailed options including manual file copy.

 ---

 ## Agent Harness Design

 The QA system in this template draws from [Anthropic's research on harness design
 for long-running applications](https://www.anthropic.com/engineering/harness-design-long-running-apps),
 which found that separating the generator from the evaluator — and tuning the evaluator
 to be skeptical — dramatically improves output quality.

 **Key patterns applied across the full SDLC:**

 | Pattern | What the research found | How we apply it |
 |---|---|---|
 | **Generator-evaluator separation** | Agents asked to evaluate their own work are inherently lenient — they identify real issues then talk themselves into approving anyway. | 9 independent QA reviewers run in parallel, each in its own context window. None sees what the others found. |
 | **Adversarial QA posture** | Out-of-the-box LLM QA agents test superficially and skip edge cases. | Every reviewer has explicit anti-leniency instructions: _"Do NOT be generous. Do NOT downgrade findings."_ |
 | **Numeric scoring with hard thresholds** | Vague categories ("looks good") enable drift. Concrete scores create accountability. | Each reviewer scores 1-10. Security requires ≥8. Any Critical finding = automatic ⛔. Composite < 7 = fail. |
 | **Iterative feedback loops** | A single-pass review that identifies issues but never verifies fixes leaves quality gaps. | Every phase transition is an evaluation point. QA uses scored re-review loops. All phases validate before handoff. |
 | **Planner scope control** | Over-specifying implementation upfront leads to cascading errors. Under-specifying means the generator drifts. | The Analyst focuses on deliverables and constraints, not implementation details. The Implementer defines testable acceptance criteria before coding. |
 | **Self-evaluation before handoff** | Generators are overly positive about their own work. | ALL generator agents (Analyst, Scaffolder, Deployer, Implementer, Documenter) run domain-specific self-evaluation checklists before reporting complete. |

 **Applied per agent:**

 | Agent | Self-evaluation | Acceptance criteria | Feedback loop |
 |---|---|---|---|
 | **Analyst** | ✅ Design completeness, testability, scope control, NFR coverage | — (produces criteria for others) | Design revision loop via Harness |
 | **Scaffolder** | ✅ Template fidelity, file existence, dependency correctness | ✅ Required files checklist | Structure validation via Harness |
 | **Deployer** | ✅ AVM versions, compilation, no hardcoded values, diagnostics, WAF | ✅ Infrastructure quality checklist | Bicep fix loop via Harness |
 | **Implementer** | ✅ Acceptance criteria coverage table | ✅ Sprint contract before coding | QA re-review loop (up to 3 rounds) |
 | **Documenter** | ✅ Template compliance, code accuracy, no placeholders, link integrity | — | Revision loop via Harness |
 | **QA Reviewers** | — (they ARE the evaluators) | — | Adversarial scoring with thresholds |

 ---

 ## Design Overview

 The SDLC is organized into nine phases:

 1. **Requirement Analysis**
    Clarify problem, goals, constraints, and scope.

 2. **Design (Services, Technologies, Patterns)**
    Choose architecture, Azure services, and patterns, reusing internal and template repos.

 3. **Repo Structure & CI/CD (ADO)**
    Align repo layout with templates, update or add Azure DevOps (ADO) pipelines.

 4. **Implementation & Tests (Unit + Integration)**
    Implement features in small steps, with tests, using the correct Azure SDKs and patterns.

 5. **Repository Documentation**
    Update or create design docs, ADRs, and API documentation.

 6. **QA Activities**
    Run automated tests and targeted manual QA based on a structured plan.

 7. **RAI (Responsible AI) Review**
    For AI- or data-sensitive changes, assess and mitigate risks.

 8. **Release Script Preparation**
    Create or update release scripts and checklists.

 9. **Publish to GitHub**
    Use PRs, Copilot code review, and ADO pipelines to safely merge and release.

 The full, detailed SDLC is in:

 - `.github/SDLC-with-Copilot-and-Azure.md`

 ---

 ## Agent Architecture

 This template includes a **multi-agent subagent system** powered by VS Code's Copilot subagent
 capability. A single user-facing agent — **Harness** (Your SDLC Orchestrator for helping
 and accelerating building solution accelerators based on SDLC) — orchestrates specialized
 worker agents, each scoped to a specific SDLC Phase with least-privilege tool access.

 ```mermaid
 flowchart TD
     Request["🧑‍💻 Engineer Request"] --> Coordinator["🎯 Harness"]

     Coordinator --> Analyst["📋 Analyst<br/>Phase 1-2"]
     Coordinator --> Scaffolder["🏗️ Scaffolder<br/>Phase 3"]
     Coordinator --> Deployer["☁️ Deployer<br/>Phase 3+8"]
     Coordinator --> Implementer["⚡ Implementer<br/>Phase 4"]
     Coordinator --> Documenter["📝 Documenter<br/>Phase 5"]
     Coordinator --> QA["🔍 QA Coordinator<br/>Phase 6"]
     Coordinator --> RAI["🛡️ RAI Reviewer<br/>Phase 7"]
     Coordinator --> Release["📦 Release Manager<br/>Phase 8-9"]

     QA -->|parallel| AR["Arch Review"]
     QA -->|parallel| AZ["Azure Compliance"]
     QA -->|parallel| CQ["Code Quality"]
     QA -->|parallel| SR["Security Review"]
     QA -->|parallel| TC["Test Coverage"]
     QA -->|parallel| UX["UX & A11y"]
     QA -->|parallel| LLM["LLM Behavior"]
     QA -->|parallel| DR["Deploy Ready"]
     QA -->|parallel| BUG["Bug Patterns"]

     style Coordinator fill:#4A90D9,color:#fff
     style QA fill:#E67E22,color:#fff
     style Request fill:#2ECC71,color:#fff
 ```

 **Key design principles:**

 - **Context isolation** — each agent runs in its own context window, preventing bloat.
 - **Parallel QA** — 9 independent reviewers run simultaneously with no anchoring bias.
 - **Adversarial evaluation** — reviewers are tuned to be skeptical, not generous. Each scores 1-10 with hard fail thresholds.
 - **Iterative QA loop** — QA → fix → targeted re-QA, up to 3 rounds until all domains pass.
 - **Least-privilege tools** — reviewers get read-only; implementer gets full edit + terminal.
 - **MCP-powered** — agents leverage GitHub MCP, awesome-copilot, Azure MCP, Microsoft Learn MCP,
   and Context7 for live patterns, fresh best practices, and authoritative documentation.
 - **Worker agents are hidden** — only **Harness** appears in the agent dropdown.

 All agent files live in `.github/agents/` and are copyable to any application repo.

 ### How engineers and agents work together

 The SDLC Agent Template is designed for **human-AI collaboration** — engineers stay in control
 while agents handle the heavy lifting. Here's the end-to-end workflow:

 #### Step 1: Engineer opens a task

 An engineer receives a GitHub issue, a feature request, or identifies a bug. They open
 VS Code, switch to the **Harness** agent in Copilot Chat, and describe the task:

 ```text
 @Harness Implement the order history API from ADR-012.
 It needs Cosmos DB for order data and Blob Storage for invoice PDFs.
 ```

 #### Step 2: Harness identifies the phase and delegates

 The Coordinator reads the request, identifies this as a **Phase 4 (Implementation)** task,
 and checks whether a design exists. If an ADR is referenced, it proceeds. If not, it first
 delegates to the **Analyst** agent for a design proposal.

 ```
 Harness
  └─ "This is a Phase 4 task with an existing ADR. Delegating to Implementer."
     └─ Implementer (subagent) starts working...
 ```

 #### Step 3: Worker agent executes with MCP-powered context

 The **Implementer** agent doesn't work from stale knowledge — it actively fetches live context:

 1. **Fetches the latest team dev reusable components and patterns** from GitHub MCP
    (e.g., `sas-cosmosdb` Repository Pattern, `sas-storage` context manager usage)
 2. **Loads current framework documentation** via Context7 MCP (FastAPI, Pydantic, React, etc.)
 3. **Reads the project's reference catalog** to verify approved libraries and scaffolding templates
 4. Writes the implementation following established patterns, creates entities, repositories, and endpoints
 5. Writes unit tests alongside every new function

 The engineer sees the Implementer's work appearing as a collapsible tool call in Chat.
 They can expand it to see every file read, search, and edit the agent made.

 #### Step 4: Automatic QA review — 9 perspectives in parallel

 After implementation, the Coordinator delegates to the **QA Coordinator**, which spawns
 9 independent reviewer subagents **simultaneously**, each with an adversarial QA posture:

 ```
 QA Coordinator (adversarial posture — never downgrade findings)
  ├─ Architecture Reviewer      → checks layering rules, dependency boundaries
  ├─ Azure Compliance Reviewer  → verifies sas-cosmosdb usage, no raw SDK calls
  ├─ Code Quality Reviewer      → checks naming, docstrings, dead code
  ├─ Security Reviewer          → scans for secrets, injection, auth issues (loads OWASP fresh)
  ├─ Test Coverage Reviewer     → runs pytest, checks coverage, validates assertions
  ├─ UX & Accessibility Rev.    → checks ARIA labels, keyboard nav, dark mode CSS
  ├─ LLM Behavior Reviewer      → checks prompt safety, grounding, citations, content filters
  ├─ Deployment Readiness Rev.  → checks error handling, performance, repo hygiene, observability
  └─ QA Bug Checklist Reviewer  → validates against 338 real production bug patterns
 ```

 Each reviewer works in its own context window — no anchoring bias. Every reviewer provides
 a **numeric quality score (1-10)** with hard fail thresholds (Security requires ≥8, others ≥7).
 The Security Reviewer loads the **OWASP Top 10 checklist fresh** from awesome-copilot on every review.
 The 3 product-level reviewers use the **`sdlc-accelerator-qa`** skill for comprehensive QA.

 #### Step 5: Engineer reviews the synthesized QA report

 The QA Coordinator synthesizes all 9 perspectives into a single prioritized report
 with numeric scores:

 ```
 ## QA Review Summary

 ### Quality Scores by Domain
 | Reviewer | Score | Threshold | Verdict |
 |---|---|---|---|
 | Architecture | 8/10 | ≥7 | ✅ Pass |
 | Security | 6/10 | ≥8 | ⛔ Fail |
 | Code Quality | 7/10 | ≥7 | ✅ Pass |
 | ... | ... | ... | ... |

 ### Critical Issues (must fix)
 - [Security] Endpoint /orders/{id} missing authorization check
 - [Azure Compliance] Using raw CosmosClient instead of sas-cosmosdb RepositoryBase

 ### Important Issues (should fix)
 - [Code Quality] Missing docstring on OrderRepository class
 - [Test Coverage] No test for the error path when order not found

 ### Overall Verdict: ⛔ Request changes — Security score below threshold
 ```

 If the verdict is ⛔, Harness enters the **iterative QA loop**: delegates fixes to the
 Implementer, then re-runs only the failing reviewers. This continues up to 3 rounds
 until all domains pass their thresholds.

 The engineer decides which issues to address. They can ask the Implementer to fix the
 critical issues, or fix them manually. **The engineer always has the final say.**

 #### Step 6: Documentation and release

 Once fixes are applied, the Coordinator delegates to:
 - **Documenter** — updates the ADR with implementation details and creates API docs
 - **Release Manager** — generates a changelog from commits, creates a PR with the required
   SDLC-compliant PR body, and verifies all exit criteria are met

 The engineer reviews the PR, adds any final notes, and merges.

 #### The complete flow at a glance

 ```mermaid
 sequenceDiagram
     participant E as 🧑‍💻 Engineer
     participant C as 🎯 Harness
     participant I as ⚡ Implementer
     participant Q as 🔍 QA Coordinator
     participant D as 📝 Documenter
     participant R as 📦 Release Manager

     E->>C: "Implement order API from ADR-012"
     C->>C: Identify phase, verify ADR exists
     C->>I: Delegate implementation

     Note over I: Fetch sas-cosmosdb patterns (GitHub MCP)<br/>Load FastAPI docs (Context7)<br/>Read reference catalog<br/>Write code + tests

     I-->>C: Implementation complete

     C->>Q: Review implementation

     Note over Q: 9 parallel reviewers (adversarial, scored 1-10):<br/>Architecture | Azure Compliance | Code Quality<br/>Security | Test Coverage | UX & A11y<br/>LLM Behavior | Deploy Ready | Bug Patterns

     Q-->>C: QA report with prioritized findings
     C-->>E: "QA found 2 critical issues"

     E->>C: "Fix the auth issue"
     C->>I: Apply targeted fixes
     I-->>C: Fixes applied

     C->>Q: Re-review fixes
     Q-->>C: ✅ All clear

     par Documentation & Release
         C->>D: Update ADR + API docs
         C->>R: Create PR + changelog
     end

     R-->>C: PR #42 ready
     C-->>E: "PR ready for review"
     E->>E: Review & merge
 ```

 #### Key principles

 - **Engineers stay in control** — agents propose, engineers decide. Every critical decision
   requires human approval.
 - **Agents are transparent** — every subagent call is visible in Chat as a collapsible tool call.
   Expand it to see exactly what the agent read, searched, and changed.
 - **Quality is automatic** — the 9-perspective QA review runs on every change with numeric
   scoring and hard fail thresholds. If any domain fails, Harness runs an iterative fix loop
   (up to 3 rounds). The QA Coordinator also emits a **manual QA checklist** for items
   requiring human testing and can **file bugs in Azure DevOps** with user confirmation.
 - **Context is live** — agents don't rely on stale training data. They fetch current patterns,
   documentation, and best practices from MCP servers on every run.
 - **The SDLC process is enforced** — Harness ensures no phase is skipped and quality
   standards are met before release.

 #### MCP data flow — how agents leverage external tools

 ```mermaid
 flowchart LR
     subgraph "MCP Servers"
         GH["🐙 GitHub MCP"]
         AC["⭐ Awesome-Copilot"]
         AZ["☁️ Azure MCP"]
         MD["📚 MS Learn MCP"]
         C7["📖 Context7"]
     end

     subgraph "Agents"
         Impl["Implementer"]
         Sec["Security Reviewer"]
         Deploy["Deployer"]
         Analyst2["Analyst"]
     end

     Impl -->|"fetch sas-cosmosdb patterns"| GH
     Impl -->|"load React/FastAPI docs"| C7
     Impl -->|"load Python MCP instructions"| AC

     Sec -->|"load OWASP Top 10"| AC
     Sec -->|"scan dependencies"| GH

     Deploy -->|"fetch Bicep patterns from applications"| GH
     Deploy -->|"load Bicep best practices"| AC
     Deploy -->|"validate Azure resources"| AZ
     Deploy -->|"get AVM module docs"| MD

     Analyst2 -->|"fetch template structures"| GH
     Analyst2 -->|"load planning prompts"| AC
     Analyst2 -->|"get framework docs"| C7

     style GH fill:#333,color:#fff
     style AC fill:#E74C3C,color:#fff
     style AZ fill:#0078D4,color:#fff
     style MD fill:#68217A,color:#fff
     style C7 fill:#16A085,color:#fff
 ```

 ---

 ## Prerequisites

 Before working with this SDLC Agent Template or any application repo that adopts it, ensure the following tools are installed.

 > **Azure subscription:** You need an [Azure subscription](https://azure.microsoft.com/free/) with
 > permissions to create resource groups, resources, and role assignments (Contributor + RBAC at
 > subscription or resource group level). Verify quota availability for Azure OpenAI models before deployment.

 > **Dev Containers:** Following the [application accelerator pattern](https://accelerators.ms),
 > each service under `src/` provides its **own** `.devcontainer/` with service-specific tooling.
 > This per-service isolation ensures that engineers working on one layer (e.g., backend API,
 > processor, frontend) can build, test, and run independently — without pulling in dependencies
 > from other services. There is no single integrated devcontainer at the repo root.
 > To use Dev Containers locally, install **Docker + VS Code** with the
 > [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

 ### Required

 | Tool                            | Version | Purpose                                                              | Install                                                                                                                         |
 | ------------------------------- | ------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
 | **Python**                      | 3.12+   | Primary language for all templates and libraries                     | [python.org](https://www.python.org/downloads/) or `winget install Python.Python.3.12`                                          |
 | **uv**                          | latest  | Python package manager used by all templates (`uv add`, `uv sync`)   | `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` ([docs](https://docs.astral.sh/uv/getting-started/installation/)) |
 | **Docker**                      | latest  | Container builds, Dev Containers, MCP server                         | [Docker Desktop](https://www.docker.com/products/docker-desktop/) or `winget install Docker.DockerDesktop`                      |
 | **Git**                         | 2.40+   | Version control                                                      | [git-scm.com](https://git-scm.com/downloads) or `winget install Git.Git`                                                        |
 | **Azure CLI (`az`)**            | latest  | Azure resource management, authentication, quota checks              | `winget install Microsoft.AzureCLI` ([docs](https://learn.microsoft.com/cli/azure/install-azure-cli))                           |
 | **Azure Developer CLI (`azd`)** | 1.18.2+ | One-command provisioning and deployment (`azd up`)                   | `winget install Microsoft.Azd` ([docs](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd))            |
 | **Bicep CLI**                   | latest  | Infrastructure-as-Code (ships with Azure CLI, or install standalone) | `az bicep install` ([docs](https://learn.microsoft.com/azure/azure-resource-manager/bicep/install))                             |
 | **VS Code**                     | latest  | Primary IDE — prompt files, MCP config, Dev Containers               | [code.visualstudio.com](https://code.visualstudio.com/) or `winget install Microsoft.VisualStudioCode`                          |

 ### Required VS Code Extensions

 | Extension                                                                                      | Purpose                                        |
 | ---------------------------------------------------------------------------------------------- | ---------------------------------------------- |
 | [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot)           | AI-assisted development (core to this SDLC)     |
 | [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) | Chat interface for prompt files and agent mode |
 | [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)                 | Python language support                        |

 ### Conditional (based on your stack)

 | Tool           | Version | When needed                            | Install                                                                 |
 | -------------- | ------- | -------------------------------------- | ----------------------------------------------------------------------- |
 | **Node.js**    | 20 LTS+ | Projects with TypeScript or React code | [nodejs.org](https://nodejs.org/) or `winget install OpenJS.NodeJS.LTS` |
 | **pnpm / npm** | latest  | TypeScript/React package management    | `npm install -g pnpm`                                                   |

 ### Recommended VS Code Extensions

 | Extension                                                                                        | Purpose                                   |
 | ------------------------------------------------------------------------------------------------ | ----------------------------------------- |
 | [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)                   | Python linter and formatter               |
 | [Bicep](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-bicep)          | Bicep language support for IaC            |
 | [Azure Dev](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.azure-dev)         | `azd` integration in VS Code              |
 | [Docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker)        | Dockerfile and container management       |
 | [Azure Account](https://marketplace.visualstudio.com/items?itemName=ms-vscode.azure-account)     | Azure sign-in and subscription management |
 | [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)             | Test HTTP endpoints from `.http` files    |
 | [YAML](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)                   | YAML validation (`azure.yaml`, pipelines) |
 | [Even Better TOML](https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml) | `pyproject.toml` editing                  |
 | [Hadolint](https://marketplace.visualstudio.com/items?itemName=exiasr.hadolint)                  | Dockerfile linting                        |

 ### Verify your setup

 Run the following to confirm all required tools are available:

 ```bash
 python --version          # 3.12+
 uv --version              # any
 docker --version           # any
 git --version              # 2.40+
 az --version               # latest
 azd version                # 1.18.2+
 az bicep version           # latest
 code --version             # latest
 ```

 ### Python testing tools

 Tests are installed as dev dependencies in each project (no global install needed):

 | Tool       | Framework                    | Install (per project) |
 | ---------- | ---------------------------- | --------------------- |
 | **pytest** | Python test runner           | `uv add --dev pytest` |
 | **Vitest** | TypeScript/React test runner | `pnpm add -D vitest`  |

 ---

 ## Scaffolding Template and Practices

 The team maintains a **Reference Catalog** at `.github/reference-catalog.md` with detailed documentation,
 API examples, and Copilot behavior rules for all libraries and templates.

 ### Reusable libraries (install via PyPI)

 | Library                                                                                         | PyPI Package   | Use for                                         |
 | ----------------------------------------------------------------------------------------------- | -------------- | ----------------------------------------------- |
 | [python_cosmosdb_helper](https://github.com/mcaps-microsoft/python_cosmosdb_helper)             | `sas-cosmosdb` | Cosmos DB SQL + MongoDB with Repository Pattern |
 | [python_storageaccount_helper](https://github.com/mcaps-microsoft/python_storageaccount_helper) | `sas-storage`  | Azure Blob Storage + Queue operations           |

 **Mandatory usage rules:**

 - Use `sas-cosmosdb` for all Cosmos DB access. Do **not** use the raw `azure-cosmos` SDK.
 - Use `sas-storage` for all Blob and Queue access. Do **not** use the raw `azure-storage-blob` SDK.

 ### Scaffolding templates (clone to start a new project)

 | Template                                                                                                      | Use for                                   |
 | ------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
 | [python_application_template](https://github.com/mcaps-microsoft/python_application_template)                 | Base app (console, worker, pipeline, CLI) |
 | [python_api_application_template](https://github.com/mcaps-microsoft/python_api_application_template)         | FastAPI service with advanced DI          |
 | [python_agent_framework_dev_template](https://github.com/mcaps-microsoft/python_agent_framework_dev_template) | AI agent apps with Azure AI Foundry + MCP |

 ### Internal patterns

 Each product repo must also define **internal patterns** based on its existing codebase.
 When adding similar functionality, review existing code first and follow the same patterns.
 New code must reuse these patterns where applicable.

 ---

 ## Copilot Integration

 This SDLC uses four mechanisms to steer Copilot:

 1. **Multi-agent subagent system** (agent-driven workflows via Harness — see [Agent Architecture](#agent-architecture) above)
 2. **Repo-level instructions** (always active)
 3. **Language-specific quality instructions** (auto-applied by file type)
 4. **Prompt files** (reusable workflows invoked manually)

 The agent system and prompt files serve the same purpose — guiding Copilot through SDLC phases —
 but agents automate orchestration while prompts give engineers direct manual control.

 ### 1. Copilot repo-level instructions

 File: `.github/copilot-instructions.md`

 - Describes the project's architecture and layering.
 - Defines Azure SDK standards and which internal abstractions to use.
 - States test and documentation expectations.
 - Explains the 9 SDLC phases at a high level so Copilot understands context.

 Copilot automatically reads this when assisting in this repo.

 ### 2. Language-specific quality instructions

 These files live in `.github/` and **auto-apply** when Copilot works on matching files.
 They enforce code-quality and test-quality standards aligned with SDLC Phases 4 and 6.

 | File                               | Applies to      | Purpose                                                              |
 | ---------------------------------- | --------------- | -------------------------------------------------------------------- |
 | `code-quality-py.instructions.md`  | `**.py`         | Python code quality (docstrings, comments, dead code, compile-check) |
 | `code-quality-ts.instructions.md`  | `**/*.ts`       | TypeScript code quality (JSDoc, naming, imports, strict typing)      |
 | `code-quality-tsx.instructions.md` | `**/*.tsx`      | React component quality (patterns, hooks, JSX, props)                |
 | `test-quality.instructions.md`     | `tests/**`      | Python test quality (pytest, sanitization, coverage)                 |
 | `test-quality-ts.instructions.md`  | `**/*.test.ts`  | TypeScript test quality (Vitest, mocking, assertions)                |
 | `test-quality-tsx.instructions.md` | `**/*.test.tsx` | React test quality (Testing Library, userEvent, a11y)                |

 These files are not invoked manually — Copilot applies them automatically when editing matching files.

 ### 3. Prompt files

 Prompt files live under `.github/prompts/` and define reusable workflows:

 - `.github/prompts/requirement-and-design.prompt.md`
   - Used in **Phase 1-2**
   - Clarifies requirements, proposes designs, and maps work to SDLC phases.

 - `.github/prompts/repo-structure-and-cicd.prompt.md`
   - Used in **Phase 3**
   - Scaffolds repo structure and generates CI/CD pipelines (GitHub Actions + ADO).

 - `.github/prompts/deployment.prompt.md`
   - Used in **Phase 3 + Phase 8**
   - Generates Bicep/AVM infrastructure, azd config, Codespaces, and deployment automation.

 - `.github/prompts/implementation-and-tests.prompt.md`
   - Used in **Phase 4**
   - Creates step-by-step implementation plans with matching tests.

 - `.github/prompts/repo-documentation.prompt.md`
   - Used in **Phase 5**
   - Generates or updates ADRs, design docs, and API docs with a consistent structure.

 - `.github/prompts/qa-rai-release.prompt.md`
   - Used in **Phase 6-8**
   - Produces QA plans, RAI risk/mitigation lists, and release checklists/scripts.

 **Prompt-to-agent routing:** Each prompt file uses the `agent:` frontmatter field to route
 to its corresponding custom agent, ensuring the prompt inherits the agent's tool restrictions,
 persona, MCP access, and subagent permissions:

 | Prompt | Routes to | Tools inherited |
 |---|---|---|
 | `requirement-and-design` | **Analyst** | read, search, fetch, GitHub MCP, Context7 |
 | `repo-structure-and-cicd` | **Scaffolder** | read, search, edit, terminal, GitHub MCP |
 | `deployment` | **Deployer** | read, search, edit, terminal, Azure MCP |
 | `implementation-and-tests` | **Implementer** | edit, execute, terminal, all coding MCPs |
 | `repo-documentation` | **Documenter** | read, search, edit, GitHub MCP |
 | `qa-rai-release` | **Harness** | agent (orchestrates QA + RAI + Release subagents) |

 This means engineers get the **same behavior and tool access** whether they invoke
 `@Harness implement the order API` or use `/implementation-and-tests`.

 #### How to use prompt files in VS Code

 In Copilot Chat:

 ```text
 Copilot, use `.github/prompts/requirement-and-design.prompt.md`
 to design a new order history API using Cosmos DB and Blob Storage.


Or:


 Copilot, use `.github/prompts/implementation-and-tests.prompt.md`
 to implement the design in docs/adr/ADR-012-order-history.md.


-----------------------------------------------------------------------------------------------------------------------------------------------------------------------


Repository Layout

Recommended structure for this “SDLC & Copilot” configuration repo (or for each app repo):


 .
 ├── README.md
 ├── .design/                                  ← SDLC design templates and guidance
 │   ├── ADR-TEMPLATE.md                      ← Standard ADR format for all applications
 │   ├── DESIGN-DOC-TEMPLATE.md               ← General design document template
 │   ├── API-DOC-TEMPLATE.md                  ← API documentation template
 │   ├── README.template.md                   ← application-aligned project README template
 │   └── hands-on-guide.md                    ← Step-by-step SDLC walkthrough
 ├── docs/                                     ← App documentation (created by engineers + agents)
 │   ├── adr/                                 ← Architecture Decision Records
 │   └── api/                                 ← API endpoint documentation
 ├── .github/
 │   ├── copilot-instructions.md              ← repo-level instructions (always active)
 │   ├── SDLC-with-Copilot-and-Azure.md        ← full SDLC definition (9 phases)
 │   ├── reference-catalog.md                 ← library & template registry
 │   ├── PULL_REQUEST_TEMPLATE.md             ← PR form (auto-populates on new PRs)
 │   ├── ISSUE_TEMPLATE/                      ← GitHub issue templates
 │   ├── pr-form-validation.workflow.yml      ← Template: copy to .github/workflows/ in app repos
 │   ├── acl/                                 ← Access control policies
 │   ├── compliance/                          ← Compliance inventory
 │   ├── policies/                            ← JIT and governance policies
 │   ├── code-quality-py.instructions.md       ← Python code quality (auto: **.py)
 │   ├── code-quality-ts.instructions.md       ← TypeScript code quality (auto: **/*.ts)
 │   ├── code-quality-tsx.instructions.md      ← React code quality (auto: **/*.tsx)
 │   ├── test-quality.instructions.md          ← Python test quality (auto: tests/**)
 │   ├── test-quality-ts.instructions.md       ← TypeScript test quality (auto: **/*.test.ts)
 │   └── test-quality-tsx.instructions.md      ← React test quality (auto: **/*.test.tsx)
 ├── .vscode/
 │   └── mcp.json                              ← MCP servers (GitHub, awesome-copilot, Azure, MS Learn, Context7)
 ├── .github/agents/                                    ← Subagent system (Harness coordinator + phase workers + QA reviewers)
 │   ├── harness.agent.md                         ← User-facing orchestrator ("@Harness")
 │   ├── analyst.agent.md                      ← Phase 1-2: Requirements & Design
 │   ├── scaffolder.agent.md                   ← Phase 3: Repo Structure & CI/CD
 │   ├── deployer.agent.md                     ← Phase 3+8: Deployment & Infrastructure
 │   ├── implementer.agent.md                  ← Phase 4: Implementation & Tests
 │   ├── documenter.agent.md                   ← Phase 5: Documentation
 │   ├── qa-coordinator.agent.md               ← Phase 6: QA orchestrator (9 parallel reviewers)
 │   ├── architecture-reviewer.agent.md        ← QA: Layering, patterns
 │   ├── azure-compliance-reviewer.agent.md    ← QA: SDK, AVM, identity
 │   ├── code-quality-reviewer.agent.md        ← QA: Naming, docstrings, dead code
 │   ├── security-reviewer.agent.md            ← QA: OWASP, secrets, auth
 │   ├── test-coverage-reviewer.agent.md       ← QA: Tests, coverage, assertions
 │   ├── ux-accessibility-reviewer.agent.md    ← QA: A11y, ARIA, keyboard nav, UX state
 │   ├── llm-behavior-reviewer.agent.md        ← QA: Prompt safety, grounding, citations
 │   ├── deployment-readiness-reviewer.agent.md ← QA: Error handling, perf, repo hygiene
 │   ├── qa-bug-checklist-reviewer.agent.md     ← QA: 338-bug pattern validation
 │   ├── rai-reviewer.agent.md                 ← Phase 7: RAI review
 │   └── release-manager.agent.md              ← Phase 8-9: Release & publish
 ├── .github/prompts/
 │   ├── requirement-and-design.prompt.md       ← Phase 1–2
 │   ├── repo-structure-and-cicd.prompt.md      ← Phase 3
 │   ├── deployment.prompt.md                   ← Phase 3 + 8 (Bicep/AVM/azd)
 │   ├── implementation-and-tests.prompt.md     ← Phase 4
 │   ├── repo-documentation.prompt.md           ← Phase 5
 │   └── qa-rai-release.prompt.md               ← Phase 6–8
 ├── infra/                                     ← Bicep templates (shared across services)
 ├── scripts/                                   ← Deployment and utility scripts
 ├── azure.yaml                                 ← azd orchestration config
 └── src/                                       ← Source code (per-service isolation)
     ├── backend-api/                            ← Python API service
     │   ├── .devcontainer/                      ← Service-specific dev environment
     │   ├── src/                                ← Service source code
     │   ├── Dockerfile                          ← Service container image
     │   ├── pyproject.toml                      ← Service dependencies
     │   └── uv.lock
     ├── processor/                              ← Python agent/worker service
     │   ├── .devcontainer/                      ← Service-specific dev environment
     │   ├── src/
     │   ├── Dockerfile
     │   ├── pyproject.toml
     │   └── uv.lock
     └── frontend/                               ← React/TypeScript web app (if applicable)
         ├── src/
         ├── Dockerfile
         ├── package.json
         └── vite.config.js

-----------------------------------------------------------------------------------------------------------------------------------------------------------------------


How to Adopt This Template in a New application / App Repo

### Option A: Install as a Plugin (recommended)

 The SDLC Agent Template is available as an **Agent Plugin** — installable with one
 command in both VS Code and Copilot CLI. The plugin distributes all 18 agents and
 all skills automatically. Workspace-specific files (instructions, prompts,
 `copilot-instructions.md`) are generated on first use by the `sdlc-workspace-init` skill.

 #### VS Code

 ```
 Command Palette → Chat: Install Plugin From Source → https://github.com/gim-home/sdl_with_agent
 ```

 Or configure this repo as a marketplace in your VS Code settings:

 ```json
 // .vscode/settings.json
 "chat.plugins.marketplaces": ["gim-home/sdl_with_agent"]
 ```

 #### GitHub Copilot CLI

 ```bash
 # Install directly from the GitHub repo
 copilot plugin install gim-home/sdl_with_agent

 # Verify installation
 copilot plugin list
 ```

 #### After installing the plugin

 Open any project repo and invoke Harness:

 ```
 @Harness help me set up this project
 ```

 Harness detects that `.github/copilot-instructions.md` is missing and automatically
 runs the `sdlc-workspace-init` skill, which:

 1. Asks for your project name, domain, and tech stack.
 2. Generates a customized `.github/copilot-instructions.md`.
 3. Deploys quality instruction files (`.github/instructions/`) matching your language stack.
 4. Deploys SDLC prompt files (`.github/prompts/`) for all 9 phases.

 You can also run this manually:

 ```
 /sdlc-workspace-init
 ```

 #### Manage plugin updates

 ```bash
 # CLI
 copilot plugin update sdlc-agent-template

 # VS Code — updates automatically every 24h, or manually:
 # Command Palette → Extensions: Check for Extension Updates
 ```

 #### Uninstall

 ```bash
 copilot plugin uninstall sdlc-agent-template
 ```

### Option B: Copy files manually

 If you prefer not to use the plugin system, copy files directly:

 1 Copy the template files
    • Copy .github/ into the new repo (includes SDLC definition, quality instructions,
      copilot instructions, PR template, issue templates, and governance policies).
    • Copy .github/prompts/ folder.
    • Copy .github/agents/ folder, .design/ folder, and .vscode/mcp.json.
    • Copy .github/pr-form-validation.workflow.yml to .github/workflows/pr-form-validation.yml
      (this activates the PR form enforcement).
 2 Customize for your project
    • Set `<PROJECT_NAME>` in .github/copilot-instructions.md (the only manual edit needed).
    • Harness progressively fills `<BUSINESS_DOMAIN>`, `<TECH_STACK>`, `<ARCH_STYLE>`,
      `<OTHER_AZURE_SERVICES>`, and `<LOGGER_ABSTRACTION>` from actual design decisions.
    • Select quality instruction files matching your stack:
       • Python → code-quality-py.instructions.md + test-quality.instructions.md
       • TypeScript → code-quality-ts.instructions.md + test-quality-ts.instructions.md
       • React → code-quality-tsx.instructions.md + test-quality-tsx.instructions.md
    • Adjust prompt file examples and paths to match your repo.

 3 Set up enforcement
    • Enable branch protection on main and add Validate PR Form as a required status check.
    • Update ADO pipelines so they:
       • Run the required tests and checks defined in the SDLC.
       • Optionally run additional quality passes for key areas.
 4 Educate the team
    • Share the README and .github/SDLC-with-Copilot-and-Azure.md.
    • Walk through the Hands-On Guide (.design/hands-on-guide.md) in a team session.
    • Demonstrate how to invoke prompt files from Copilot Chat (agent mode).
    • Show how repo-level instructions and CCA steer Copilot behavior automatically.
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------


Adoption Checklist

#### Plugin install (Option A)

 • [ ] Install the plugin via VS Code (`Chat: Install Plugin From Source`) or CLI (`copilot plugin install gim-home/sdl_with_agent`).
 • [ ] Run `@Harness` or `/sdlc-workspace-init` in the target repo to generate workspace files.
 • [ ] Review the generated `.github/copilot-instructions.md` and adjust if needed.
 • [ ] Copy `.github/pr-form-validation.workflow.yml` to `.github/workflows/pr-form-validation.yml`.
 • [ ] Enable **branch protection** on `main` and add `Validate PR Form` as a required status check.

#### Manual copy (Option B)

 • [ ] Copy `.github/`, `.github/prompts/`, `.github/agents/`, `.design/`, `.vscode/mcp.json` into the target repo.
 • [ ] Set `<PROJECT_NAME>` in `.github/copilot-instructions.md` (the only placeholder you need to fill manually —
       Harness progressively fills the remaining values as design decisions are made during the SDLC process).
 • [ ] Copy `.github/pr-form-validation.workflow.yml` to `.github/workflows/pr-form-validation.yml`.
 • [ ] Enable **branch protection** on `main` and add `Validate PR Form` as a required status check.
 • [ ] Select and keep only the quality instruction files matching the repo's language stack.

#### Recommended (complete during first sprint)

 • [ ] Confirm Azure SDK standards with the platform/architecture team.
 • [ ] Confirm internal patterns and template repos to reference.
 • [ ] Customize quality instruction files if needed (test framework, coverage thresholds, etc.).
 • [ ] Align ADO pipelines with SDLC expectations (build, tests, security scans, release).
 • [ ] Walk the team through the [Hands-On Guide](.design/hands-on-guide.md).
 • [ ] Socialize this README and `.github/SDLC-with-Copilot-and-Azure.md` with all engineers and leads.

Once adopted, every engineer can open the repo, use Copilot Agent mode with the prompt files, and work through
a consistent SDLC from requirements to release — with guaranteed application quality, full reusability, and zero
fragmentation from the team's dev standards.
