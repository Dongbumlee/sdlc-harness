# Phase 2: Requirements-to-Specification Capability — Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.
> Tasks 1–3 have NO dependencies and CAN be executed in parallel.
> Tasks 4–10 are sequential — follow the dependency chain.

**Goal:** Split the Analyst agent's single-pass flow (3–5 questions → immediate ADR) into a collaborative three-phase process: Phase 1A (iterative discovery dialogue), Phase 1B (formal requirements spec), Phase 2 (design/ADR). Add a new skill, a new reviewer agent, and update the Harness orchestrator for the new flow.

**Architecture:** The Analyst remains one agent with three explicit modes — discovery, specification, and design — controlled by Harness delegation context. Phase transitions require explicit user approval gates. Azure-specific references become cloud-conditional (check `harness-config.yml` for `cloud.provider`). A new Requirements Completeness Reviewer joins the QA suite as the 9th reviewer, invoked only during the requirements phase.

**Tech Stack:** Markdown agent files, YAML skill definitions, JSON configuration — GitHub Copilot Extensions format.

---

## Critical Constraints

1. **Dual-location sync.** Every file in `.github/plugin/` has an identical copy in `vscode-extension/`. The CI workflow `sync-check.yml` enforces this via `diff -r`. **Every task that touches `.github/plugin/agents/` or `.github/plugin/skills/` must mirror the same change to `vscode-extension/`.**

2. **`vscode-extension/package.json`** explicitly lists every agent and skill path under `contributes.chatAgents` and `contributes.chatSkills`. When new agents or skills are added, this file must be updated with new `{ "path": "..." }` entries.

3. **No traditional tests.** This is a markdown/YAML project. Validation = JSON syntax checks, directory sync diffs, and file existence checks.

4. **Git push pattern.** Always: `unset GITHUB_TOKEN && git push origin evo`

5. **Git commit messages must include detailed body text** explaining what changed and why, since the Analyst rewrite spans 3 tasks (5–7) touching the same file.

6. **`.design/REQ-TEMPLATE.md`** lives at workspace level alongside `ADR-TEMPLATE.md`. It does NOT need mirroring — only files under `.github/plugin/agents/` and `.github/plugin/skills/` require sync.

7. **Scope boundary — deferred to Phase 3:** FR-N traceability in code comments, Test Coverage Reviewer checking FR-N coverage, project manifest tracking FR → file → test mapping, canary spec updates.

---

## Task 1: Create Requirements Spec Template

**Files:**
- Create: `.design/REQ-TEMPLATE.md`

**Step 1: Create the requirements spec template**

Create `.design/REQ-TEMPLATE.md` with the following content:

```markdown
# REQ-XXXX: [Title]

> **Status:** Draft | Under Review | Approved | Superseded
> **SDLC Phase:** 1 (Requirements)
> **Date:** YYYY-MM-DD
> **Author:** [Name or @Harness]
> **Approved by:** [Name — filled after user approval]

---

## Problem Statement

<!-- What problem does this feature/system solve? Who experiences this problem? -->

## Business Context

<!-- Why does this matter now? What triggers this work? -->

## Goals

- [ ] Goal 1
- [ ] Goal 2

## Non-Goals

<!-- What this project explicitly will NOT do -->

-

## Out of Scope

<!-- Items that may seem related but are deferred or excluded -->

-

## Functional Requirements

| ID | Requirement | Acceptance Criterion |
|----|-------------|---------------------|
| FR-1 | [Requirement description] | **Given** [precondition], **When** [action], **Then** [expected result] |
| FR-2 | | |

## Non-Functional Requirements

| ID | Requirement | Measurable Target |
|----|-------------|-------------------|
| NFR-1 | [Requirement description] | [Specific metric, e.g., "< 200ms p95 response time"] |
| NFR-2 | | |

## Constraints

<!-- Hard requirements: technology choices, budget, compliance, team skills, timeline -->

-

## Assumptions

<!-- What we assume to be true — if any assumption is wrong, requirements may change -->

-

## User Stories (optional)

<!-- If applicable — "As a [role], I want [capability], so that [benefit]" -->

-

## Open Questions

<!-- Anything that needs a human decision before implementation can begin -->

- [ ]

## Discovery Notes

<!-- Summary of the discovery conversation that produced this spec -->
<!-- Include key decisions made, alternatives discussed, and rationale -->

## References

- Discovery conversation: [link or date]
- Related ADR: [link — filled after Phase 2 design]
```

**Step 2: Verify the file exists alongside the ADR template**

Run:
```bash
ls -la .design/REQ-TEMPLATE.md .design/ADR-TEMPLATE.md
```
Expected: Both files listed. REQ-TEMPLATE.md is a new file; ADR-TEMPLATE.md already exists.

**Step 3: Commit**

```bash
git add .design/REQ-TEMPLATE.md
git commit -m "feat: add requirements specification template (REQ-TEMPLATE.md)

Add a structured requirements spec template parallel to the existing
ADR-TEMPLATE.md. This template is the output artifact for Phase 1B
(Requirements Specification) of the new Analyst workflow.

Includes: problem statement, business context, goals/non-goals/out-of-scope,
functional requirements with testable acceptance criteria (Given/When/Then),
non-functional requirements with measurable targets, constraints, assumptions,
user stories (optional), open questions, and discovery notes.

Part of Phase 2: Requirements-to-Specification capability."
```

---

## Task 2: Create Requirements Discovery Skill

**Files:**
- Create: `.github/plugin/skills/sdlc-requirements-discovery/SKILL.md`
- Mirror: `vscode-extension/skills/sdlc-requirements-discovery/SKILL.md`

**Step 1: Create the skill directory and file**

Create `.github/plugin/skills/sdlc-requirements-discovery/SKILL.md` with the following content:

```markdown
---
name: sdlc-requirements-discovery
description: >-
  Guides the Analyst agent through collaborative requirements discovery with the user.
  Covers elicitation patterns, question strategies, restatement techniques, and the
  explicit approval checkpoint. Use when starting a new feature, clarifying requirements,
  or when Harness delegates Phase 1A discovery to the Analyst.
---

# SDLC Requirements Discovery

## When to use

- Starting a new feature or project where requirements are unclear
- When the Analyst enters Phase 1A: Collaborative Discovery mode
- When Harness delegates with context containing "Phase 1A" or "discovery"

## Core Principle

**Understanding what the user actually needs comes before everything else.**
Building the wrong thing is the single biggest cause of project failure.
Your role during discovery is to be a detective uncovering real needs —
not a designer proposing solutions.

## Elicitation Rules

### Rule 1: One question at a time

Ask exactly ONE question per message. Never dump a list of questions.
Wait for the answer before asking the next question.

**Why:** Multiple questions overwhelm users. They answer the easy ones and
skip the important ones. One-at-a-time ensures every question gets a
thoughtful answer.

**Bad example:**
> What's the project about? Who are the users? What tech stack do you prefer?
> Are there any constraints? What does success look like?

**Good example:**
> What problem are you trying to solve? Who experiences this problem today,
> and how do they currently work around it?

### Rule 2: Restate before moving on

After each answer, restate your understanding before asking the next question.
Use the pattern: "So what I'm hearing is [restatement]. Is that right?"

**Why:** Catches misunderstandings immediately. Users correct wrong assumptions
early, before they compound into wrong requirements.

**Example:**
> So what I'm hearing is that the main pain point is manual data entry —
> users currently copy information from PDF reports into the system one field
> at a time, and it takes about 2 hours per report. Is that right?

### Rule 3: Multiple choice when the decision space is clear

When you can enumerate the realistic options, offer multiple choice instead
of open-ended questions. Include an "other" option.

**When to use:** Technology choices, deployment targets, user role types,
priority ordering.

**When NOT to use:** Problem description, success criteria, workflow details —
these need the user's own words.

**Example:**
> For the deployment target, which fits best?
> A) Azure Container Apps (managed containers, auto-scaling)
> B) Azure App Service (PaaS, simpler but less flexible)
> C) Azure Kubernetes Service (full orchestration, most complex)
> D) Other — tell me what you have in mind

### Rule 4: Probe beyond the happy path

Users describe the sunny-day scenario. You must actively probe for:

- **Edge cases:** "What happens if a user submits a report with missing fields?"
- **Error scenarios:** "How should the system behave if the external API is down?"
- **Scale:** "How many concurrent users do you expect? What's the data volume?"
- **Security:** "Who should NOT have access to this data?"
- **Integration:** "What existing systems does this need to talk to?"

### Rule 5: Surface constraints early

Ask about hard constraints before exploring features. Constraints shape
everything downstream.

- Technology mandates ("Must use Python" / "Must run on Azure")
- Budget or timeline limits
- Compliance requirements (HIPAA, SOC2, GDPR)
- Team skills and capacity
- Existing infrastructure that must be reused

### Rule 6: No solutions during discovery

During Phase 1A, you are a **listener and clarifier**. You do NOT:

- Propose architecture
- Suggest technology choices (unless asked)
- Design data models
- Recommend Azure services
- Write any code or pseudocode

If you catch yourself thinking "we could solve this with...", stop.
Write it in your internal notes for Phase 2, but do not share it yet.

## Discovery Flow

Follow this general sequence, adapting to the conversation:

### Opening (1–2 questions)
- What problem are you solving? Who has this problem?
- What does the user's current workflow look like today (without this system)?

### Core Understanding (3–6 questions)
- Who are the different types of users? What can each type do?
- Walk me through the main workflow from start to finish
- What are the most important features? (Ask them to rank, not just list)
- What data does the system need to store and process?

### Boundaries (2–3 questions)
- What are the hard constraints? (tech, budget, compliance, timeline)
- What is explicitly NOT in scope for the first version?
- Are there any existing systems this needs to integrate with?

### Quality & Risk (2–3 questions)
- What does "good enough" performance look like? Any specific targets?
- What's the worst thing that could go wrong? How do we prevent it?
- Are there security or compliance requirements?

### Synthesis & Confirmation
- Summarize ALL requirements discovered so far
- Present as a structured requirements summary
- Ask: "Does this capture what you want to build? Anything missing or wrong?"

## Approval Checkpoint

**This is the most important step.** Do NOT proceed past discovery without
explicit user approval.

After presenting the requirements summary, wait for the user to confirm with
one of these signals:
- "Yes, that's right"
- "This is what I want to build"
- "Approved" / "LGTM" / "Looks good"
- Any clear affirmative response

If the user says "almost" or "mostly" or adds corrections:
- Incorporate the corrections
- Present the updated summary
- Ask for confirmation again

**Never auto-progress.** The user must explicitly approve before you
transition to Phase 1B (Requirements Specification).

## After Approval

Once the user approves the discovery summary:

1. Report to Harness: "Phase 1A discovery complete. User has approved the
   requirements summary. Ready to produce the formal requirements spec (Phase 1B)."
2. Harness will re-delegate to you with Phase 1B context
3. Use the approved summary to populate `.design/REQ-TEMPLATE.md`
4. Every requirement must have a testable acceptance criterion — no exceptions

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Do This Instead |
|---|---|---|
| Question dump | Users skip important questions | One question at a time |
| Leading questions | Biases the answer toward your assumption | Ask open-ended first |
| Assuming context | Users don't share what they think is obvious | Ask explicitly |
| Premature solutioning | Anchors on a design before understanding the problem | Save solutions for Phase 2 |
| Skipping NFRs | Performance/security gaps discovered in production | Probe for quality attributes explicitly |
| Auto-progressing | User didn't actually approve, just paused | Wait for explicit confirmation |
```

**Step 2: Mirror to vscode-extension**

```bash
mkdir -p vscode-extension/skills/sdlc-requirements-discovery
cp .github/plugin/skills/sdlc-requirements-discovery/SKILL.md \
   vscode-extension/skills/sdlc-requirements-discovery/SKILL.md
```

**Step 3: Verify sync**

```bash
diff .github/plugin/skills/sdlc-requirements-discovery/SKILL.md \
     vscode-extension/skills/sdlc-requirements-discovery/SKILL.md
```
Expected: No output (files are identical).

**Step 4: Commit**

```bash
git add .github/plugin/skills/sdlc-requirements-discovery/ \
        vscode-extension/skills/sdlc-requirements-discovery/
git commit -m "feat: add sdlc-requirements-discovery skill

New skill that guides the Analyst through collaborative requirements
discovery (Phase 1A). Covers elicitation patterns: one question at a time,
restatement technique, multiple choice for clear decision spaces, probing
beyond the happy path, surfacing constraints early, and no-solutions-during-
discovery rule.

Includes the complete discovery flow (opening → core → boundaries → quality →
synthesis), the explicit approval checkpoint pattern, and anti-patterns to
avoid.

This skill is referenced by the Analyst agent when operating in Phase 1A
discovery mode.

Part of Phase 2: Requirements-to-Specification capability."
```

---

## Task 3: Add Requirements Categories to Reviewer Output Format Skill

**Files:**
- Modify: `.github/plugin/skills/sdlc-reviewer-output-format/SKILL.md`
- Mirror: `vscode-extension/skills/sdlc-reviewer-output-format/SKILL.md`

**Step 1: Add the new reviewer's category section**

In `.github/plugin/skills/sdlc-reviewer-output-format/SKILL.md`, find the line:

```
### UX & Accessibility Reviewer
```

Insert the following block **before** that line (after the Test Coverage Reviewer section ending with the `console-errors` categories):

```markdown

### Requirements Completeness Reviewer
`requirement-testability` | `requirement-ambiguity` | `requirement-measurability` | `scope-coverage` | `acceptance-criteria` | `nfr-measurability` | `constraint-completeness` | `requirement-traceability`

```

**Step 2: Update the skill description to reflect 9 reviewers**

In the same file, find the frontmatter description line:

```
  Ensures consistent, parseable review output across all 8 reviewer domains.
```

Replace with:

```
  Ensures consistent, parseable review output across all 9 reviewer domains.
```

**Step 3: Update the body text header reference**

Find the line:

```
All 8 QA reviewer agents MUST emit a structured YAML block at the **end** of their response.
```

Replace with:

```
All 9 QA reviewer agents MUST emit a structured YAML block at the **end** of their response.
```

**Step 4: Mirror to vscode-extension**

```bash
cp .github/plugin/skills/sdlc-reviewer-output-format/SKILL.md \
   vscode-extension/skills/sdlc-reviewer-output-format/SKILL.md
```

**Step 5: Verify sync**

```bash
diff .github/plugin/skills/sdlc-reviewer-output-format/SKILL.md \
     vscode-extension/skills/sdlc-reviewer-output-format/SKILL.md
```
Expected: No output (files are identical).

**Step 6: Commit**

```bash
git add .github/plugin/skills/sdlc-reviewer-output-format/ \
        vscode-extension/skills/sdlc-reviewer-output-format/
git commit -m "feat: add Requirements Completeness Reviewer categories to output format skill

Add domain-specific category values for the new Requirements Completeness
Reviewer: requirement-testability, requirement-ambiguity, requirement-
measurability, scope-coverage, acceptance-criteria, nfr-measurability,
constraint-completeness, requirement-traceability.

Update reviewer count references from 8 to 9 throughout the skill to
reflect the addition of the new reviewer.

Part of Phase 2: Requirements-to-Specification capability."
```

---

## Task 4: Create Requirements Completeness Reviewer Agent

**Depends on:** Task 3 (categories must exist in the output format skill)

**Files:**
- Create: `.github/plugin/agents/requirements-completeness-reviewer.agent.md`
- Mirror: `vscode-extension/agents/requirements-completeness-reviewer.agent.md`

**Step 1: Create the reviewer agent**

Create `.github/plugin/agents/requirements-completeness-reviewer.agent.md` with the following content:

```markdown
---
name: Requirements Completeness Reviewer
description: "Use when reviewing requirements specifications for completeness, testability, ambiguity, and measurability. Validates that every functional requirement has a testable acceptance criterion and every non-functional requirement has a measurable target."
user-invocable: false
tools: ['read', 'search']
skills: ['sdlc-reviewer-output-format']
---

# Requirements Completeness Reviewer — QA Perspective: Requirements Quality

You review requirements specifications through the lens of **completeness, testability,
and precision**. Your job is to catch vague, untestable, or missing requirements before
they reach the design and implementation phases — where they become 10x more expensive to fix.

## Adversarial QA posture

> You are an independent evaluator. Your job is to find real requirements problems,
> not to validate the Analyst's work. Do NOT be generous — if a requirement is vague,
> report it at full severity even if you can guess what was intended. Do NOT talk
> yourself into accepting "close enough" acceptance criteria. Probe for gaps in scope
> coverage and missing edge cases, not just obvious ambiguity.
>
> **You MUST provide a numeric quality score (1-10) at the end of your review.**
> 7+ = meets production standards. Below 7 = needs work. Below 5 = serious issues.

## Before reviewing

1. **Read the requirements spec** being reviewed (the file passed by QA Coordinator).
2. **Read the requirements template** at `.design/REQ-TEMPLATE.md` to verify structural compliance.
3. **Cross-reference goals vs. requirements** — every stated goal should map to at least one FR or NFR.

## Review checklist

### Structural completeness
- [ ] **All template sections present** — Problem statement, goals, non-goals, out-of-scope, FRs, NFRs, constraints, assumptions
- [ ] **No empty sections** — Every section has substantive content, not just placeholder text
- [ ] **Goals fully covered** — Every goal maps to at least one FR or NFR
- [ ] **Non-goals are explicit** — Scope boundaries are clear enough to reject out-of-scope requests during implementation

### Functional requirements quality
- [ ] **Every FR has an ID** — Sequential FR-1, FR-2, etc. No gaps in numbering
- [ ] **Every FR has a testable acceptance criterion** — Given/When/Then format or equivalent measurable condition
- [ ] **No ambiguous language** — Flag these exact words: "appropriate", "reasonable", "as needed", "intuitive", "user-friendly", "fast", "secure", "robust", "flexible", "scalable", "efficient", "properly", "correctly", "adequate", "sufficient", "minimal", "simple"
- [ ] **Requirements are atomic** — Each FR describes one capability, not a compound requirement
- [ ] **Edge cases addressed** — Error states, empty states, boundary conditions, concurrent access

### Non-functional requirements quality
- [ ] **Every NFR has an ID** — Sequential NFR-1, NFR-2, etc.
- [ ] **Every NFR has a measurable target** — Not "fast" but "< 200ms p95". Not "available" but "99.9% uptime"
- [ ] **Performance requirements specify load** — "< 200ms p95 under 100 concurrent users"
- [ ] **Security requirements are specific** — Not "secure" but "all API endpoints require OAuth 2.0 bearer token"
- [ ] **All quality attributes covered** — Performance, security, availability, scalability, observability. Flag any that are completely missing

### Constraints and assumptions
- [ ] **Constraints are verifiable** — Each constraint can be checked during implementation
- [ ] **Assumptions are explicit** — Hidden assumptions are flagged as risks
- [ ] **No contradictions** — Requirements don't conflict with each other or with constraints

## Severity guide

| Severity | Criteria | Examples |
|----------|----------|---------|
| Critical | Requirement is untestable or contradictory | FR with no acceptance criterion; two FRs that contradict each other |
| High | Requirement uses ambiguous language that could be interpreted multiple ways | "System should be fast"; "Handle errors appropriately" |
| Medium | Requirement is testable but imprecise or could be more specific | Missing edge case; NFR without load specification |
| Low | Minor structural issue or style improvement | Section ordering; ID numbering gap |

## Output format

Return findings as:
- **Critical**: Untestable requirements, contradictions, missing acceptance criteria
- **Important**: Ambiguous language, missing quality attributes, incomplete scope coverage
- **Suggestion**: Precision improvements, additional edge cases to consider
- **Positive**: Well-written requirements (cite specific examples, not generic praise)

**Quality Score: X/10** — Justify the score with 2–3 sentences referencing specific findings.

## Structured Output Block

After your Markdown review report, you MUST emit a structured YAML block for machine parsing.
Use the `sdlc-reviewer-output-format` skill for the complete specification.

Place this block at the very end of your response:

```
---sdlc-review-output---
reviewer: "Requirements Completeness Reviewer"
phase: "<phase being reviewed>"
score: <1-10>
verdict: PASS | FAIL | CRITICAL_FAIL
findings:
  - severity: critical | high | medium | low
    category: <one of your domain categories>
    description: "<finding>"
    location: "<file:section or FR/NFR ID>"
    recommendation: "<fix>"
reasoning: "<2-3 sentence summary>"
---end-sdlc-review-output---
```

Your domain categories: `requirement-testability` | `requirement-ambiguity` | `requirement-measurability` | `scope-coverage` | `acceptance-criteria` | `nfr-measurability` | `constraint-completeness` | `requirement-traceability`
```

**Step 2: Mirror to vscode-extension**

```bash
cp .github/plugin/agents/requirements-completeness-reviewer.agent.md \
   vscode-extension/agents/requirements-completeness-reviewer.agent.md
```

**Step 3: Verify sync**

```bash
diff .github/plugin/agents/requirements-completeness-reviewer.agent.md \
     vscode-extension/agents/requirements-completeness-reviewer.agent.md
```
Expected: No output (files are identical).

**Step 4: Commit**

```bash
git add .github/plugin/agents/requirements-completeness-reviewer.agent.md \
        vscode-extension/agents/requirements-completeness-reviewer.agent.md
git commit -m "feat: add Requirements Completeness Reviewer agent

New QA reviewer (9th) that validates requirements specifications for
completeness, testability, ambiguity, and measurability. Reviews Phase 1B
output before the Analyst proceeds to Phase 2 design.

Checks: structural completeness against REQ-TEMPLATE.md, every FR has a
testable acceptance criterion (Given/When/Then), no ambiguous language
(flags 'appropriate', 'reasonable', 'as needed', etc.), every NFR has a
measurable target with load specification, constraints are verifiable,
assumptions are explicit, and goals map to requirements.

Follows the same pattern as Architecture Reviewer and Security Reviewer:
adversarial QA posture, review checklist, structured YAML output block.

Part of Phase 2: Requirements-to-Specification capability."
```

---

## Task 5: Rewrite Analyst Agent — Phase 1A Discovery Mode

**Depends on:** Task 2 (discovery skill must exist)

**Files:**
- Rewrite: `.github/plugin/agents/analyst.agent.md`
- Mirror: `vscode-extension/agents/analyst.agent.md`

**Step 1: Replace the entire analyst.agent.md file**

Replace the full contents of `.github/plugin/agents/analyst.agent.md` with the following. This is a complete rewrite — do not attempt to merge with the existing file.

```markdown
---
name: Analyst
description: "Use when clarifying requirements, discovering what to build, producing requirements specifications, evaluating design options, proposing architecture decisions, or mapping features to cloud services. Operates in three modes: Phase 1A (collaborative discovery), Phase 1B (requirements specification), and Phase 2 (design proposal)."
user-invocable: false
tools: ['read', 'search', 'fetch', 'github/*', 'awesome-copilot/*', 'context7/*', 'azure-devops/*']
skills: ['sdlc-requirements-discovery']
---

# Analyst — SDLC Phases 1–2: Requirements & Design

You are the **Analyst** agent. You operate in three distinct modes depending on the
context provided by Harness. You **never edit code** — you only read, research, and produce
specification or design documents.

## Mode determination

Harness delegates to you with a context that specifies which mode to operate in.
Check the delegation context for these signals:

| Signal in delegation context | Mode | Your output |
|------------------------------|------|-------------|
| "Phase 1A", "discovery", "new feature", "clarify requirements" | **Discovery** | Requirements summary → user approval |
| "Phase 1B", "requirements spec", "produce spec", "approved requirements" | **Specification** | Formal requirements spec (REQ-TEMPLATE.md) |
| "Phase 2", "design", "ADR", "architecture", "approved spec" | **Design** | ADR-ready design proposal |

If the context is ambiguous (e.g., "analyze this feature"), default to **Discovery mode**.
It is always safer to understand first than to design prematurely.

---

## Phase 1A: Collaborative Discovery

> **Your role:** Discovery partner. You listen, clarify, and understand.
> You do NOT propose solutions. You do NOT design architecture. You do NOT
> recommend technology choices unless the user explicitly asks.

### Activate discovery skill

Load and follow the `sdlc-requirements-discovery` skill. It contains the complete
elicitation methodology, question patterns, and approval checkpoint procedure.

### Discovery rules (non-negotiable)

1. **One question at a time.** Never ask multiple questions in a single message.
2. **Restate after each answer.** "So what I'm hearing is [X]. Is that right?"
3. **Multiple choice when options are clear.** Include an "other" option.
4. **Probe beyond the happy path.** Edge cases, error scenarios, scale, security.
5. **Surface constraints early.** Technology, budget, compliance, team, timeline.
6. **No solutions.** If you catch yourself designing, stop. Save it for Phase 2.
7. **No fixed question limit.** The process takes as long as it takes.

### Discovery flow

Follow this general sequence, adapting to the conversation:

1. **Problem & users** — What problem? Who has it? How do they work around it today?
2. **Workflows** — Walk through the main user journey from start to finish
3. **Features & priorities** — What are the must-haves vs. nice-to-haves?
4. **Data** — What data does the system store, process, and produce?
5. **Boundaries** — Constraints, non-goals, out-of-scope items
6. **Quality attributes** — Performance, security, availability expectations
7. **Integration** — Existing systems, APIs, data sources this must connect to
8. **Risks** — What's the worst that could go wrong?

### Synthesis & approval checkpoint

When you have enough information to write a complete requirements spec:

1. Present a structured **requirements summary** covering all areas above.
2. Ask: "Does this capture what you want to build? Anything missing or wrong?"
3. **Wait for explicit approval.** The user must say yes / approved / LGTM / "this is what I want to build."
4. If they correct anything, incorporate corrections and present the updated summary. Ask for confirmation again.
5. **Never auto-progress.** No approval = stay in discovery.

### After approval

Report to Harness:
> "Phase 1A discovery complete. User has approved the requirements summary.
> Ready to produce the formal requirements spec (Phase 1B)."

---

## Phase 1B: Requirements Specification

> **Your role:** Technical writer. You transform the approved discovery summary
> into a formal, structured requirements specification using the template.

### Produce the requirements spec

1. Read the template at `.design/REQ-TEMPLATE.md`.
2. Populate every section from the approved discovery summary.
3. Apply these quality rules to every requirement:

| Rule | Applies to | Example |
|------|-----------|---------|
| Testable acceptance criterion | Every FR | **Given** a user uploads a PDF, **When** parsing completes, **Then** all form fields are extracted with ≥ 95% accuracy |
| Measurable target | Every NFR | < 200ms p95 response time under 100 concurrent users |
| No ambiguous language | All sections | Replace "fast" → "< 200ms p95"; "secure" → "OAuth 2.0 bearer token required" |
| Atomic requirements | Every FR | One capability per FR — split compound requirements |
| Sequential IDs | FRs and NFRs | FR-1, FR-2, FR-3... / NFR-1, NFR-2, NFR-3... |

4. Cross-reference: every stated goal must map to at least one FR or NFR.
5. Flag any gaps as **Open Questions** — do NOT fill gaps with assumptions.

### Spec output format

Present the complete spec inline in your response, formatted exactly as the
REQ-TEMPLATE.md template specifies. This is the **contract** — downstream agents
implement exactly what it says, nothing more, nothing less.

### After presenting the spec

1. Ask the user to review: "Please review this requirements specification. Once you approve it, I'll proceed to design."
2. **Wait for explicit approval.** Same rules as Phase 1A — no auto-progression.
3. Once approved, report to Harness:
   > "Phase 1B complete. User has approved the requirements specification.
   > Ready to proceed to Phase 2 (Design)."

---

## Phase 2: Design

> **Your role:** Design architect. You take the approved requirements spec and
> produce an ADR-ready design proposal. You are CONSTRAINED by the spec — no
> creative reinterpretation of what the user wanted.

### Before starting design

0. **Verify GitHub MCP authentication (required):**
   - Perform a probe call: use `mcp_github_get_file_contents` to fetch `README.md` from
     the project's reference library repo (from `copilot-instructions.md`).
   - If the call **fails or returns an auth error**, STOP and inform the user:
     > GitHub MCP authentication is required to access reference repos.
     > Please sign in with an account that has org access, then retry.
   - If the user cannot authenticate, fall back to patterns in `.github/reference-catalog.md`
     and warn that live verification was not possible.

0b. **Check awesome-copilot MCP (recommended):**
   - Probe: `mcp_awesome-copil_search_instructions(keywords: "planning")`
   - If it **fails**, WARN the user and proceed:
     > ⚠️ awesome-copilot MCP is not running. Planning best practices will not be loaded.
     > I will proceed using local knowledge only.

0c. **Check cloud-specific MCP (conditional):**
   - Read `harness-config.yml` at the workspace root. Check the `cloud.provider` field.
   - If `cloud.provider` is `azure` OR if the file doesn't exist (default to azure for
     backward compatibility):
     - Probe: `mcp_azure-devops_core_list_projects()`
     - If it **fails**, WARN the user and proceed:
       > ⚠️ Azure DevOps MCP is not available. Team wiki standards will not be fetched.
       > I will proceed without ADO wiki content.
   - If `cloud.provider` is NOT `azure`, skip ADO MCP checks entirely.

1. **Load planning tools from awesome-copilot** (skip if unavailable):
   - Use `mcp_awesome-copil_load_collection` to load `"project-planning"`.
   - Use `mcp_awesome-copil_load_instruction` to load `"task-implementation"`.

2. **Fetch reference catalog from GitHub MCP:**
   - Use `mcp_github_get_file_contents` to fetch `reference-catalog.md` from the SDLC template repo.
   - Verify the proposed services match approved libraries listed in `copilot-instructions.md`.

3. **Fetch existing patterns from reference template repos:**
   - For base apps: fetch structure from the project's app template (from `copilot-instructions.md`).
   - For APIs: fetch structure from the project's API template.
   - For AI agents: fetch structure from the project's agent template.

4. **Load up-to-date library docs:**
   - Use **Context7 MCP** to get current documentation for frameworks being evaluated.

5. **Fetch team engineering standards** (cloud-conditional):
   - If `cloud.provider` is `azure`: search ADO wiki for architecture guidelines.
   - Otherwise: skip this step.

### Design constraints

**You may only design what the approved spec requires.**
- If the spec says FR-1 through FR-8, your design covers FR-1 through FR-8. Not FR-9.
- If you discover a gap in the spec during design, flag it as an **Open Question**.
  Do NOT silently fill the gap with your own interpretation.
- Reference the spec by FR/NFR ID in your design sections.

### Reference catalog population

After completing your design proposal, populate the living reference catalog:

1. **Activate the `sdlc-reference-catalog` skill** — read its research methodology.
2. **Ask the user about preferred libraries:**
   > "Are there any specific libraries, templates, or frameworks you'd like me to include in the reference catalog?"
3. **Research and populate** `.github/reference-catalog.md` using the priority order from the skill.
4. **Write entries** under the 5 fixed top-level sections using the entry format defined in the skill.
5. **Report completion** to Harness with a summary: number of entries per section.

### Output format

Return a structured design proposal following the ADR template at `.design/ADR-TEMPLATE.md`.
Your output should be **ADR-ready** — Harness will automatically delegate to the Documenter
to save it as `docs/adr/ADR-XXX-<topic>.md`.

**Diagram format rule:** All architecture diagrams, data flow diagrams, and sequence
diagrams MUST use **Mermaid** markdown syntax (```mermaid blocks), NOT ASCII art.

Structure your output with these sections:
- **Context** — what problem this solves
- **Requirements Reference** — link to the approved requirements spec (REQ-XXX)
- **Design / Implementation** — architecture, services, patterns, data model, API endpoints
- **Alternatives Considered** — what was rejected and why
- **Testing Strategy** — unit + integration approach
- **RAI / Risk Considerations** — if applicable
- **SDLC Impact by Phase** — what each phase needs to do
- **Open Questions** — anything needing human decision

### Progressive configuration output

At the end of your design proposal, include a **Project Configuration** section.
Harness uses this to progressively fill `.github/copilot-instructions.md` placeholders.

```
## Project Configuration (for Harness)
- TECH_STACK: [recommended tech stack]
- ARCH_STYLE: [recommended architecture]
```

If the project uses Azure (check `harness-config.yml`), also include:
```
- OTHER_AZURE_SERVICES: [Azure services identified]
```

This section is consumed by Harness and does not appear in the final ADR.

### Self-evaluation before handoff

**Before reporting your design as complete**, perform a deliberate self-review.

> **WARNING:** Planners tend to under-specify non-functional requirements and over-specify
> implementation details. Be deliberately critical about your own design.

#### Design quality checklist

1. **Spec alignment** — Does the design cover every FR and NFR in the approved spec?
   Not more, not less.
2. **Completeness** — Does the design cover all user stories, including error/edge cases?
3. **Testability** — Can each requirement be verified? If you can't describe how to test it,
   the Implementer can't build it reliably.
4. **Scope control** — Are you specifying high-level deliverables and constraints, or
   micro-managing implementation details?
5. **Service validation** — Did you verify every proposed service against the reference
   catalog and approved libraries in `copilot-instructions.md`?
6. **Non-functional requirements** — Did you address performance, security, scalability,
   and observability?
7. **Feasibility** — Is this buildable with the team's current templates and patterns?

#### Fix any gaps found before marking the design complete.

## SDLC Exit Criteria

### Phase 1 Exit Criteria (Requirements)

- Requirements are clarified through collaborative discovery: ✅/⚠️/⛔
- Formal requirements spec exists with all FR/NFR and acceptance criteria: ✅/⚠️/⛔
- No ambiguous language in requirements: ✅/⚠️/⛔
- Scope boundaries documented (non-goals, out-of-scope): ✅/⚠️/⛔
- User has explicitly approved the requirements spec: ✅/⚠️/⛔

### Phase 2 Exit Criteria (Design)

- Requirements spec is the basis for design (no creative reinterpretation): ✅/⚠️/⛔
- Agreement on scope and success criteria: ✅/⚠️/⛔
- Design is documented (ADR-ready) and ready for team review: ✅/⚠️/⛔
- Library choices are explicit and compliant with reference catalog: ✅/⚠️/⛔
- Reuse of internal patterns and/or external templates is identified: ✅/⚠️/⛔
- Open questions are listed for human decision: ✅/⚠️/⛔

## What you must NOT do

- Never create or edit files.
- Never propose raw SDK usage when approved library wrappers cover the use case
  (check `copilot-instructions.md` for approved libraries).
- Never propose a new architectural pattern without checking existing codebase patterns first.
- Never design beyond what the approved requirements spec contains.
- Never auto-progress between phases without explicit user approval.
```

**Step 2: Mirror to vscode-extension**

```bash
cp .github/plugin/agents/analyst.agent.md \
   vscode-extension/agents/analyst.agent.md
```

**Step 3: Verify sync**

```bash
diff .github/plugin/agents/analyst.agent.md \
     vscode-extension/agents/analyst.agent.md
```
Expected: No output (files are identical).

**Step 4: Commit**

```bash
git add .github/plugin/agents/analyst.agent.md \
        vscode-extension/agents/analyst.agent.md
git commit -m "refactor: rewrite Analyst agent with three-phase mode architecture

Complete rewrite of the Analyst agent from a single-pass requirements+design
flow into a three-mode architecture:

Phase 1A (Discovery): Collaborative requirements elicitation using the new
sdlc-requirements-discovery skill. One question at a time, restatement
technique, explicit approval checkpoint. No solutions proposed during
discovery.

Phase 1B (Specification): Formal requirements spec production using
REQ-TEMPLATE.md. Every FR gets a testable acceptance criterion, every NFR
gets a measurable target. No ambiguous language. User approval gate before
Phase 2.

Phase 2 (Design): ADR-ready design proposal constrained by the approved
requirements spec. Design covers exactly what the spec requires — no more,
no less. Gaps flagged as open questions, not silently filled.

Key structural changes:
- Mode determination section at top routes based on Harness delegation context
- Discovery skill reference added to frontmatter
- MCP checks moved to Phase 2 only (not needed for discovery/spec)
- Self-evaluation expanded with spec-alignment check
- Exit criteria split into Phase 1 and Phase 2 sections
- Cloud-specific references made conditional on harness-config.yml

Part of Phase 2: Requirements-to-Specification capability (task 5 of 10)."
```

---

## Task 6: Rewrite Analyst Agent — Azure Decoupling (Cloud-Conditional Logic)

**Depends on:** Task 5 (the rewritten analyst must exist)

**Files:**
- Modify: `.github/plugin/agents/analyst.agent.md`
- Mirror: `vscode-extension/agents/analyst.agent.md`

> **Note:** Task 5 already made Azure references cloud-conditional in the body text.
> This task verifies the agent description in the frontmatter is cloud-neutral and
> ensures the tools list documents conditional usage.

**Step 1: Update the frontmatter description**

In `.github/plugin/agents/analyst.agent.md`, find the frontmatter `description` line:

```
description: "Use when clarifying requirements, discovering what to build, producing requirements specifications, evaluating design options, proposing architecture decisions, or mapping features to cloud services. Operates in three modes: Phase 1A (collaborative discovery), Phase 1B (requirements specification), and Phase 2 (design proposal)."
```

Verify it says "cloud services" (not "Azure services"). If Task 5 was applied correctly, this is already cloud-neutral. No change needed.

**Step 2: Add a tools usage note after the frontmatter**

Find the line immediately after the closing `---` of the frontmatter:

```
# Analyst — SDLC Phases 1–2: Requirements & Design
```

Insert the following block between the frontmatter closing `---` and the `# Analyst` heading:

```markdown

<!-- Tools usage note:
  - azure-devops/*: Only used when cloud.provider is "azure" in harness-config.yml.
    If the project uses AWS or GCP, these tools are not invoked.
  - github/*: Used in all modes for reference catalog and pattern research.
  - awesome-copilot/*: Used in Phase 2 for planning best practices.
  - context7/*: Used in Phase 2 for framework documentation.
-->

```

**Step 3: Mirror to vscode-extension**

```bash
cp .github/plugin/agents/analyst.agent.md \
   vscode-extension/agents/analyst.agent.md
```

**Step 4: Verify sync**

```bash
diff .github/plugin/agents/analyst.agent.md \
     vscode-extension/agents/analyst.agent.md
```
Expected: No output (files are identical).

**Step 5: Commit**

```bash
git add .github/plugin/agents/analyst.agent.md \
        vscode-extension/agents/analyst.agent.md
git commit -m "refactor: add cloud-conditional tools usage documentation to Analyst

Add HTML comment block documenting which tools are cloud-conditional:
- azure-devops/* only invoked when cloud.provider is 'azure'
- github/* used in all modes
- awesome-copilot/* and context7/* used in Phase 2 only

The body text already gates ADO MCP checks on cloud.provider (from Task 5).
This comment ensures future maintainers understand the conditional tool usage
pattern without reading the full agent file.

Part of Phase 2: Requirements-to-Specification capability (task 6 of 10)."
```

---

## Task 7: Update Harness Agent — Phase Separation and Approval Gates

**Depends on:** Task 5 (Analyst rewrite must exist so phase references are valid)

**Files:**
- Modify: `.github/plugin/agents/harness.agent.md`
- Mirror: `vscode-extension/agents/harness.agent.md`

This task makes four targeted edits to the Harness agent. Apply each edit in order.

**Step 1: Update the agents list in frontmatter**

In `.github/plugin/agents/harness.agent.md`, find the frontmatter `agents:` line:

```
agents: ['Analyst', 'Scaffolder', 'Deployer', 'Implementer', 'Documenter', 'QA Coordinator', 'RAI Reviewer', 'Release Manager']
```

Replace with:

```
agents: ['Analyst', 'Scaffolder', 'Deployer', 'Implementer', 'Documenter', 'QA Coordinator', 'RAI Reviewer', 'Release Manager', 'Requirements Completeness Reviewer']
```

**Step 2: Update the phase-to-agent mapping table**

Find the phase-to-agent mapping table:

```
| Phase | Agent | When to use |
|---|---|---|
| 1-2: Requirements & Design | **Analyst** | New features, architecture decisions, requirement clarification |
```

Replace that single row with two rows:

```
| Phase | Agent | When to use |
|---|---|---|
| 1: Requirements | **Analyst** (Discovery + Spec modes) | New features, requirement clarification, user says "I want to build..." |
| 2: Design | **Analyst** (Design mode) | Architecture decisions, design proposals — ONLY after requirements spec is approved |
```

**Step 3: Update the QA reviewer routing table**

Find the QA reviewer routing table. Locate the `requirements` row:

```
| requirements | Architecture |
```

Replace with:

```
| requirements | Requirements Completeness, Architecture |
```

**Step 4: Update the Phase 1-2 workflow to include approval gates**

Find the section `#### Phase 1-2: Design feedback loop (Analyst)`:

```
#### Phase 1-2: Design feedback loop (Analyst)

When the Analyst's design proposal has gaps (missing NFRs, untestable requirements,
over-specified implementation details):

1. Point out the specific gaps to the Analyst.
2. Ask the Analyst to revise the affected sections.
3. Review the revised proposal before proceeding to ADR creation.
```

Replace the entire section with:

```
#### Phase 1: Requirements workflow (Analyst — Discovery + Spec modes)

When a new feature request arrives or the user wants to clarify requirements:

1. **Delegate to Analyst with Phase 1A context:**
   > "Phase 1A: Collaborative Discovery. The user wants to build [summary of request].
   > Use the sdlc-requirements-discovery skill to elicit requirements through iterative
   > dialogue. Do NOT propose solutions — only listen and clarify."

2. **Wait for Analyst to report Phase 1A completion.**
   The Analyst will report: "Phase 1A discovery complete. User has approved the requirements summary."

3. **Delegate to Analyst with Phase 1B context:**
   > "Phase 1B: Requirements Specification. Produce a formal requirements spec using
   > the template at .design/REQ-TEMPLATE.md. Base it on the approved discovery summary.
   > Every FR must have a testable acceptance criterion. Every NFR must have a measurable target."

4. **Wait for Analyst to report Phase 1B completion.**
   The Analyst will report: "Phase 1B complete. User has approved the requirements specification."

5. **Delegate to QA Coordinator for requirements review:**
   > "Run QA review for phase: requirements. Invoke only: Requirements Completeness, Architecture."

6. **If QA passes**, proceed to Phase 2. If QA fails, route feedback to Analyst for spec revision.

#### Phase 2: Design feedback loop (Analyst — Design mode)

When the requirements spec is approved and QA has passed:

1. **Delegate to Analyst with Phase 2 context:**
   > "Phase 2: Design. Produce an ADR-ready design proposal based on the approved
   > requirements spec [REQ-XXX]. You are constrained by the spec — design exactly
   > what it requires, nothing more."

2. When the Analyst's design proposal has gaps (missing NFRs, untestable requirements,
   over-specified implementation details):
   - Point out the specific gaps to the Analyst.
   - Ask the Analyst to revise the affected sections.
   - Review the revised proposal before proceeding to ADR creation.
```

**Step 5: Update the ADR generation rule**

Find the ADR generation rule section:

```
## ADR generation rule

When the **Analyst** produces a design proposal, you MUST automatically delegate to the
**Documenter** to save it as an ADR before proceeding to implementation:

1. Analyst returns a design proposal.
2. Delegate to Documenter: "Create an ADR from this design using the template at `.design/ADR-TEMPLATE.md`. Save it to `docs/adr/ADR-XXX-<topic>.md`."
3. Only after the ADR is saved, proceed to the next phase (usually Implementer).

This ensures every design decision is captured as a permanent, reviewable record.
```

Replace with:

```
## ADR generation rule

When the **Analyst** produces a **Phase 2 design proposal**, you MUST automatically
delegate to the **Documenter** to save it as an ADR before proceeding to implementation:

1. Analyst returns a Phase 2 design proposal (NOT a Phase 1B requirements spec).
2. Delegate to Documenter: "Create an ADR from this design using the template at `.design/ADR-TEMPLATE.md`. Save it to `docs/adr/ADR-XXX-<topic>.md`."
3. Only after the ADR is saved, proceed to the next phase (usually Implementer).

**CRITICAL:** Do NOT trigger ADR generation on Phase 1B output. The requirements spec
is a standalone artifact — it is NOT an ADR. Only Phase 2 design proposals become ADRs.

This ensures every design decision is captured as a permanent, reviewable record.
```

**Step 6: Mirror to vscode-extension**

```bash
cp .github/plugin/agents/harness.agent.md \
   vscode-extension/agents/harness.agent.md
```

**Step 7: Verify sync**

```bash
diff .github/plugin/agents/harness.agent.md \
     vscode-extension/agents/harness.agent.md
```
Expected: No output (files are identical).

**Step 8: Commit**

```bash
git add .github/plugin/agents/harness.agent.md \
        vscode-extension/agents/harness.agent.md
git commit -m "refactor: split Harness Phase 1/2 delegation with approval gates

Split the combined Phase 1-2 Analyst delegation into distinct phases:

Phase 1 (Requirements):
- Phase 1A: Delegate to Analyst in discovery mode with explicit context
- Wait for user approval of requirements summary
- Phase 1B: Delegate to Analyst in spec mode
- Wait for user approval of requirements spec
- QA gate: Requirements Completeness + Architecture reviewers

Phase 2 (Design):
- Only proceeds after Phase 1 QA passes
- Delegate to Analyst in design mode, constrained by approved spec
- Existing design feedback loop preserved

Key changes:
- Phase-to-agent table split into two rows (Phase 1 / Phase 2)
- QA reviewer routing: requirements phase now invokes Requirements
  Completeness Reviewer alongside Architecture Reviewer
- ADR generation rule explicitly excludes Phase 1B output — only
  Phase 2 design proposals trigger ADR creation
- Requirements Completeness Reviewer added to agents list

Part of Phase 2: Requirements-to-Specification capability (task 7 of 10)."
```

---

## Task 8: Update QA Coordinator — Add 9th Reviewer

**Depends on:** Task 4 (reviewer agent must exist)

**Files:**
- Modify: `.github/plugin/agents/qa-coordinator.agent.md`
- Mirror: `vscode-extension/agents/qa-coordinator.agent.md`

**Step 1: Update the agents list in frontmatter**

In `.github/plugin/agents/qa-coordinator.agent.md`, find the `agents:` line in the frontmatter:

```
agents: ['Architecture Reviewer', 'Azure Compliance Reviewer', 'Code Quality Reviewer', 'Security Reviewer', 'Test Coverage Reviewer', 'UX & Accessibility Reviewer', 'LLM Behavior Reviewer', 'Deployment Readiness Reviewer']
```

Replace with:

```
agents: ['Architecture Reviewer', 'Azure Compliance Reviewer', 'Code Quality Reviewer', 'Security Reviewer', 'Test Coverage Reviewer', 'Requirements Completeness Reviewer', 'UX & Accessibility Reviewer', 'LLM Behavior Reviewer', 'Deployment Readiness Reviewer']
```

**Step 2: Update the description to reflect 9 reviewers**

Find:

```
description: "Use when running code reviews, quality assurance passes, or pre-merge validation. Orchestrates 8 parallel reviewer subagents covering architecture, security, code quality, testing, UX, LLM behavior, Azure compliance, and deployment readiness."
```

Replace with:

```
description: "Use when running code reviews, quality assurance passes, requirements validation, or pre-merge validation. Orchestrates 9 parallel reviewer subagents covering architecture, security, code quality, testing, requirements completeness, UX, LLM behavior, Azure compliance, and deployment readiness."
```

**Step 3: Update the count references in the body**

Find all occurrences of "8 reviewer" and "8 independent" and "all 8" in the body and update to "9":

- `"You orchestrate multi-perspective code review\nby running 8 independent reviewer subagents"` → replace `8 independent` with `9 independent`
- `"run these subagents **in parallel**:"` — the header above this says "How to run reviews" and lists 8 reviewers. Add the 9th reviewer after the Test Coverage Reviewer entry.

Find the block:

```
### Code-level reviewers (original 5)
1. **Architecture Reviewer** — layering rules, dependency boundaries, design consistency
2. **Azure Compliance Reviewer** — SDK usage, AVM patterns, identity best practices
3. **Code Quality Reviewer** — naming, docstrings, dead code, commenting patterns
4. **Security Reviewer** — secrets, injection risks, auth patterns, OWASP compliance
5. **Test Coverage Reviewer** — test patterns, coverage, assertions, mocking quality

### Product-level reviewers (new 3 — from project QA checklist)
6. **UX & Accessibility Reviewer** — a11y attributes, ARIA labels, keyboard nav, state management
7. **LLM Behavior Reviewer** — system prompt safety, grounding, citations, content filters, file handling
8. **Deployment Readiness Reviewer** — error handling, performance patterns, repo hygiene, observability
```

Replace with:

```
### Code-level reviewers (5)
1. **Architecture Reviewer** — layering rules, dependency boundaries, design consistency
2. **Azure Compliance Reviewer** — SDK usage, AVM patterns, identity best practices
3. **Code Quality Reviewer** — naming, docstrings, dead code, commenting patterns
4. **Security Reviewer** — secrets, injection risks, auth patterns, OWASP compliance
5. **Test Coverage Reviewer** — test patterns, coverage, assertions, mocking quality

### Requirements reviewer (1 — invoked only during requirements phase)
6. **Requirements Completeness Reviewer** — testable acceptance criteria, no ambiguous language, measurable NFRs, scope coverage

### Product-level reviewers (3)
7. **UX & Accessibility Reviewer** — a11y attributes, ARIA labels, keyboard nav, state management
8. **LLM Behavior Reviewer** — system prompt safety, grounding, citations, content filters, file handling
9. **Deployment Readiness Reviewer** — error handling, performance patterns, repo hygiene, observability
```

**Step 4: Update the composite formula comment**

Find:

```
composite = (security_score × 1.5 + sum(other_7_scores × 1.0)) / (1.5 + 7 × 1.0)
          = (security_score × 1.5 + sum(other_7_scores)) / 8.5
```

Replace with:

```
composite = (security_score × 1.5 + sum(other_active_scores × 1.0)) / (1.5 + N × 1.0)
# When all 9 reviewers run: N=8, denominator=9.5
# When a subset runs (e.g., requirements phase: 2 reviewers): adjust N accordingly
# Harness specifies which reviewers to invoke per phase — see phase-specific routing table
```

**Step 5: Update the exit criteria section**

Find:

```
- All 8 review perspectives completed: ✅/⚠️/⛔
```

Replace with:

```
- All invoked review perspectives completed: ✅/⚠️/⛔
```

**Step 6: Update the "Never skip" rule**

Find:

```
- Never skip any of the 8 review perspectives.
```

Replace with:

```
- Never skip any of the review perspectives specified by Harness for the current phase.
```

**Step 7: Mirror to vscode-extension**

```bash
cp .github/plugin/agents/qa-coordinator.agent.md \
   vscode-extension/agents/qa-coordinator.agent.md
```

**Step 8: Verify sync**

```bash
diff .github/plugin/agents/qa-coordinator.agent.md \
     vscode-extension/agents/qa-coordinator.agent.md
```
Expected: No output (files are identical).

**Step 9: Commit**

```bash
git add .github/plugin/agents/qa-coordinator.agent.md \
        vscode-extension/agents/qa-coordinator.agent.md
git commit -m "feat: add Requirements Completeness Reviewer as 9th QA reviewer

Add the Requirements Completeness Reviewer to the QA Coordinator's agent
roster. This reviewer is invoked during the requirements phase to validate
spec quality before design begins.

Changes:
- Added to agents list in frontmatter (position 6, after Test Coverage)
- Added to reviewer launch block as item 6 under new 'Requirements reviewer'
  sub-section, with note that it's only invoked during requirements phase
- Updated description and body count references from 8 to 9
- Composite formula updated to use variable N (number of active reviewers)
  since not all 9 run in every phase — Harness specifies which to invoke
- Exit criteria and skip rules updated to reference 'invoked reviewers'
  rather than hardcoded count

Part of Phase 2: Requirements-to-Specification capability (task 8 of 10)."
```

---

## Task 9: Update Harness Agent — Reviewer Count References

**Depends on:** Task 8 (QA Coordinator must be updated first)

**Files:**
- Modify: `.github/plugin/agents/harness.agent.md`
- Mirror: `vscode-extension/agents/harness.agent.md`

**Step 1: Update the reviewer count in Harness description**

In `.github/plugin/agents/harness.agent.md`, find:

```
- 🤖 **14 specialized agents** — from architecture review to security, QA to deployment
```

Replace with:

```
- 🤖 **15 specialized agents** — from requirements review to security, QA to deployment
```

**Step 2: Update the phase-specific QA reviewer routing header**

Find:

```
When delegating to **QA Coordinator**, specify which reviewers to invoke based on the current SDLC phase. Not all phases require all 8 reviewers.
```

Replace with:

```
When delegating to **QA Coordinator**, specify which reviewers to invoke based on the current SDLC phase. Not all phases require all 9 reviewers.
```

**Step 3: Update the "invoke all" references**

Find:

```
| implement | All 8 (full review) |
```

Replace with:

```
| implement | All 9 (full review) |
```

Find:

```
| qa | All 8 (full review) |
```

Replace with:

```
| qa | All 9 (full review) |
```

Find:

```
For `implement` and `qa` phases, invoke all 8 reviewers (full review).
```

Replace with:

```
For `implement` and `qa` phases, invoke all 9 reviewers (full review).
```

**Step 4: Mirror to vscode-extension**

```bash
cp .github/plugin/agents/harness.agent.md \
   vscode-extension/agents/harness.agent.md
```

**Step 5: Verify sync**

```bash
diff .github/plugin/agents/harness.agent.md \
     vscode-extension/agents/harness.agent.md
```
Expected: No output (files are identical).

**Step 6: Commit**

```bash
git add .github/plugin/agents/harness.agent.md \
        vscode-extension/agents/harness.agent.md
git commit -m "chore: update Harness reviewer count references from 8 to 9

Update all hardcoded '8 reviewers' references in Harness to reflect the
addition of the Requirements Completeness Reviewer (9th reviewer).

Changes: agent count 14→15, reviewer routing notes 8→9, 'All 8' → 'All 9'
for implement and qa phases.

Part of Phase 2: Requirements-to-Specification capability (task 9 of 10)."
```

---

## Task 10: Update package.json + Final Validation

**Depends on:** All previous tasks

**Files:**
- Modify: `vscode-extension/package.json`

**Step 1: Add the new agent to package.json**

In `vscode-extension/package.json`, find the `chatAgents` array. Add the new agent entry after the `qa-coordinator` entry. Find:

```json
      { "path": "agents/qa-coordinator.agent.md" },
```

Insert after it:

```json
      { "path": "agents/requirements-completeness-reviewer.agent.md" },
```

**Step 2: Add the new skill to package.json**

In the same file, find the `chatSkills` array. Add the new skill entry. Find:

```json
      { "path": "skills/sdlc-reference-catalog/SKILL.md" },
```

Insert after it:

```json
      { "path": "skills/sdlc-requirements-discovery/SKILL.md" },
```

**Step 3: Validate JSON syntax**

```bash
python3 -c "import json; json.load(open('vscode-extension/package.json')); print('✅ JSON valid')"
```
Expected: `✅ JSON valid`

**Step 4: Verify all new files exist in both locations**

```bash
echo "=== New agent ===" && \
ls -la .github/plugin/agents/requirements-completeness-reviewer.agent.md \
       vscode-extension/agents/requirements-completeness-reviewer.agent.md && \
echo "=== New skill ===" && \
ls -la .github/plugin/skills/sdlc-requirements-discovery/SKILL.md \
       vscode-extension/skills/sdlc-requirements-discovery/SKILL.md && \
echo "=== REQ template ===" && \
ls -la .design/REQ-TEMPLATE.md && \
echo "=== All checks passed ==="
```
Expected: All files listed. "All checks passed" printed.

**Step 5: Run full sync check**

```bash
diff -r --exclude="plugin.json" --exclude="package.json" \
  vscode-extension/agents/ .github/plugin/agents/ && echo "✅ Agents in sync"

diff -r --exclude="plugin.json" --exclude="package.json" \
  vscode-extension/skills/ .github/plugin/skills/ && echo "✅ Skills in sync"
```
Expected: Both print "in sync" with no diff output.

**Step 6: Verify package.json lists all agents and skills**

```bash
echo "=== Agents in package.json ===" && \
grep -c "agent.md" vscode-extension/package.json && \
echo "=== Skills in package.json ===" && \
grep -c "SKILL.md" vscode-extension/package.json && \
echo "=== Agents on disk ===" && \
ls vscode-extension/agents/*.agent.md | wc -l && \
echo "=== Skills on disk ===" && \
find vscode-extension/skills/ -name "SKILL.md" | wc -l
```
Expected: Agent counts match (19 in package.json, 19 on disk). Skill counts match (16 in package.json, 13 on disk + 3 in packs = 16 total paths).

**Step 7: Commit and push**

```bash
git add vscode-extension/package.json
git commit -m "feat: register new agent and skill in package.json

Add requirements-completeness-reviewer.agent.md to chatAgents list and
sdlc-requirements-discovery/SKILL.md to chatSkills list.

This completes Phase 2: Requirements-to-Specification capability.
All files created, all agents updated, all syncs verified."

unset GITHUB_TOKEN && git push origin evo
```

---

## Summary

| Task | Description | Creates/Modifies | Dependencies |
|------|-------------|-----------------|-------------|
| 1 | Requirements spec template | `.design/REQ-TEMPLATE.md` | None |
| 2 | Requirements discovery skill | `.github/plugin/skills/sdlc-requirements-discovery/SKILL.md` + mirror | None |
| 3 | Reviewer output format categories | `.github/plugin/skills/sdlc-reviewer-output-format/SKILL.md` + mirror | None |
| 4 | Requirements Completeness Reviewer agent | `.github/plugin/agents/requirements-completeness-reviewer.agent.md` + mirror | Task 3 |
| 5 | Analyst rewrite — full three-mode architecture | `.github/plugin/agents/analyst.agent.md` + mirror | Task 2 |
| 6 | Analyst — Azure decoupling documentation | `.github/plugin/agents/analyst.agent.md` + mirror | Task 5 |
| 7 | Harness — phase separation + approval gates | `.github/plugin/agents/harness.agent.md` + mirror | Task 5 |
| 8 | QA Coordinator — add 9th reviewer | `.github/plugin/agents/qa-coordinator.agent.md` + mirror | Task 4 |
| 9 | Harness — reviewer count updates | `.github/plugin/agents/harness.agent.md` + mirror | Task 8 |
| 10 | package.json + final validation + push | `vscode-extension/package.json` | All |
