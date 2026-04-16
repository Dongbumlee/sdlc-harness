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
