# Transparency FAQ

## What is SDLC Harness, in plain terms?

A set of agent definitions, skills, and instructions for GitHub
Copilot (VS Code and Copilot CLI). It drives a software project
through 9 SDLC phases with specialized agents and scored,
adversarial QA review. It is prompts and process — not a hosted
service, and it does not phone home.

## Which AI models does it use?

Whichever models your Copilot seat provides. The harness never names
a model: agents declare a *capability tier* (the judgment the seat
needs), and the platform resolves tiers to models. Runs work with a
single model for all seats or with different models per seat.
Output quality depends on the seat — the process is designed so that
gates check artifacts on disk rather than trusting any seat's claims.

## Where does human oversight stay?

- The engineer approves the run's basis (the task and the artifacts
  that authorize work) and every scope change.
- Escalation ends at a human: at the round cap, or on a critical
  verdict, the run stops and presents results for a user decision.
- Task-grade downgrades, recorded deviations from standards, and
  release decisions require the engineer's explicit approval.
- Repository establishment for a new project is a hard intake gate,
  never assumed.

## What are the limitations?

- The harness enforces process consistency; it cannot make a weak
  model seat produce strong designs. It makes weak output *visible*
  (scores, findings, failed gates) rather than impossible.
- Gates verify records and artifacts — a gate can confirm that an
  ADR exists and its stack claims match the template, not that the
  design is the best one available.
- Live behavior is verified by canary specs and periodic E2E runs;
  between runs, platform or model updates can change behavior in
  ways the static checks do not see.

## What data leaves my machine?

Only what your Copilot client sends to its model provider under
your own account, plus the MCP servers you configure (each is under
your control and listed in the workspace MCP template). The harness
itself collects no telemetry.
