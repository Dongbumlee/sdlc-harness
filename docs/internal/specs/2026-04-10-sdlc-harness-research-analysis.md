# SDLC Harness Research & Analysis

**Version:** 1.0.0-draft
**Date:** 2026-04-10
**Status:** Draft
**Scope:** sdlc-harness (Dongbumlee/sdlc-harness)

> **Companion document:** For the technical specification, see [SDLC Harness Specification](2026-04-10-sdlc-harness-spec.md).

---

## Table of Contents

1. [Industry Landscape & Trends](#1-industry-landscape--trends)
2. [References](#references)

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

**Critical gap:** No existing benchmark evaluates the full SDLC pipeline. Individual benchmarks cover bug fixing, test generation, or CLI operations in isolation. The bench/ evaluation system addresses this gap by benchmarking all 9 SDLC phases end-to-end.

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
