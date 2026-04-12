# Orchestrator State Machine

## Overview

The SDLC Harness orchestrator drives the full software development lifecycle through a
state machine that coordinates planning, generation, and evaluation phases.

## States

```
INIT ──→ PLANNING ──→ GENERATING ──→ EVALUATING ──→ COMPLETE
  │          │             │              │             │
  │          ▼             ▼              ▼             │
  └──────── ERROR ◄───── ERROR ◄──────  ERROR          │
              │                                        │
              └──────── RECOVERY ──────────────────────┘
```

### INIT
- Entry state for every orchestration run
- Loads configuration profile and validates inputs
- Transitions to PLANNING on success, ERROR on failure

### PLANNING
- Analyzes the incoming requirement or prompt
- Decomposes into SDLC phase tasks
- Selects appropriate agents and skills per task
- Produces an execution plan (see `schemas/execution-plan.schema.json`)
- Transitions to GENERATING when plan is ready

### GENERATING
- Executes each task in the plan
- Dispatches work to configured AI agents
- Collects artifacts (code, docs, configs)
- Supports parallel execution within phase boundaries
- Transitions to EVALUATING when all tasks complete

### EVALUATING
- Runs grading pipeline against generated artifacts
- Applies configured graders (keyword, AST, structural, LLM-judge)
- Computes scores and trend analysis
- Produces evaluation report (see `schemas/evaluation-report.schema.json`)
- Transitions to COMPLETE on success

### ERROR
- Captures failure context and diagnostics
- Supports retry with exponential backoff
- May transition to RECOVERY or terminate

### RECOVERY
- Attempts to resume from last successful checkpoint
- Replays failed tasks with adjusted parameters
- Transitions back to the interrupted state on success

## Transitions

| From | To | Trigger |
|------|----|---------|
| INIT | PLANNING | Config validated, inputs loaded |
| INIT | ERROR | Invalid config or missing dependencies |
| PLANNING | GENERATING | Execution plan approved |
| PLANNING | ERROR | Planning failure or timeout |
| GENERATING | EVALUATING | All tasks completed |
| GENERATING | ERROR | Task failure (fail-fast mode) |
| EVALUATING | COMPLETE | Evaluation report generated |
| EVALUATING | ERROR | Grading pipeline failure |
| ERROR | RECOVERY | Retry policy allows |
| RECOVERY | (previous) | Recovery successful |

## Configuration

State machine behavior is controlled via profile configuration:

```yaml
orchestrator:
  max_retries: 3
  fail_fast: false
  checkpoint_enabled: true
  parallel_phases: false
```

See `config/profiles/` for example configurations.
