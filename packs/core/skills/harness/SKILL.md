---
name: harness
description: "Start or continue an SDLC workflow using the sdlc-harness plugin. Use for any feature development, bug fix, or project task that should go through the full software development lifecycle (requirements, design, scaffolding, implementation, testing, QA, documentation)."
---

# SDLC Harness Entry Point

Invoke the **Harness** agent to orchestrate the full SDLC workflow.

## When to use

- Starting a new feature or project
- Adding a feature to an existing project
- Fixing bugs through the formal workflow
- Any task that needs requirements → design → implementation → QA

## Instructions

1. Delegate to the **Harness** agent with the user's request.
2. If `.SDLC/project-manifest.md` exists, this is an existing project — the Harness will read it and continue with the appropriate phase.
3. If no manifest exists, this is a greenfield project — the Harness will start from Phase 1.

Do NOT try to handle SDLC tasks directly. Always delegate to the Harness agent.
