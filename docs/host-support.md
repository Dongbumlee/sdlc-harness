# Host Support

SDLC Harness is built from a single source — the packs under `packs/` — for
two hosts. This page states what each host gets, how it is installed, and
where the two differ. Claims here are scoped to what has been measured;
anything not yet measured is labelled as such.

## Support matrix

| | GitHub Copilot (VS Code, Copilot CLI) | Claude Code |
|---|---|---|
| Form | Native pack layout | Generated plugin (`hosts/claude-code/`) |
| Install | `copilot plugin marketplace add Dongbumlee/sdlc-harness`, then `copilot plugin install sdlc-harness@sdlc-harness` | `/plugin marketplace add Dongbumlee/sdlc-harness`, then `/plugin install sdlc-harness@sdlc-harness` |
| Entry point | `/agent harness` | `claude --agent sdlc-harness:harness` (Harness as the main-thread agent) |
| Agents | 22 | 22 — bodies byte-identical to the pack sources |
| Skills | 25 | 25, plus a `qa-bug-checklist` entry-point skill (see deltas) |
| Prompt files / commands | 6 prompt files | 6 commands generated from the same prompt files |
| MCP servers | 3 core (GitHub, Context7, Playwright) plus the vendor servers in your cloud pack | The same set, delivered as the plugin's `.mcp.json` |
| Verification | Canary battery 60/60 (seat-graded), live end-to-end runs | `claude plugin validate` passes; contract tests pin the translation; live probes and one Small end-to-end run measured 2026-11-14 (see "Measured scope on Claude Code") |

## Installing on Claude Code

Inside a Claude Code session:

```
/plugin marketplace add Dongbumlee/sdlc-harness
/plugin install sdlc-harness@sdlc-harness
```

Start work with the Harness as the session's main agent:

```bash
claude --agent sdlc-harness:harness
```

Running Harness as the main agent is the supported entry mode: the
delegation allowlists (which agents Harness and the QA Coordinator may
spawn) are expressed through the main agent's tool list. The agents are
also installed as ordinary subagents and can be mentioned directly, but a
run that starts that way is not the measured configuration.

One requirement follows from the delegation graph: the QA Coordinator
spawns the reviewer panel one level below Harness, so the effective
subagent spawn depth must be at least 2. Claude Code's default (3) is
sufficient; if you have set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` to 1,
raise it before running a QA panel.

## Measured scope on Claude Code

Measured 2026-11-14 with Claude Code 2.1.325 and a Haiku 5.5 seat:

- Plugin validation passes on the repository root and on the generated
  tree.
- Marketplace add and install succeed from a clean profile — including
  the current tree: the installed copy carries the registration and
  report-persistence fixes and passed a two-level delegation smoke
  probe (Harness → QA Coordinator → Security Reviewer).
- Delegation runs two levels deep from the Harness main agent
  (Harness → QA Coordinator → reviewer) under plugin-namespaced agent
  registration.
- Plugin MCP tool wildcards are honored in subagent allowlists — a
  subagent called Context7 live during the run.
- Interactive sessions: the Harness main agent runs in the TUI from
  the installed plugin; a plugin MCP call executed live in auto mode,
  and in manual mode the permission prompt for the plugin's Context7
  tool appeared and the call executed after approval.
- The GitHub MCP server with a real token: a user-scope server
  carrying a personal access token (the configuration route described
  under Differences) authenticated and returned the account. The
  plugin-bundled server carries no credentials by design; the
  measured end-to-end run below used the harness's documented gh CLI
  fallback to create its repository and tracking issue.
- End-to-end runs: one Small run completed Phases 1–4 and stopped on
  the QA panel's failing verdict inside its budget. A second Small
  run traversed Phases 0–5, convened the panel (round 1 stopped the
  run on Critical findings, with the round report persisted before
  the verdict was recorded), prepared the Phase 8 decision package
  without publishing, and wrote the Phase 9 retrospective. That run
  spanned two sessions; the second resumed from the `.SDLC/` records
  alone after the first session ended mid-phase.

Not yet measured:

- A run that passes the QA panel.

## Differences on Claude Code

These are recorded deltas of the generated target, not defects to discover
later:

- **Agent names are slugs.** Claude Code requires lowercase hyphenated
  names, so `QA Coordinator` becomes `qa-coordinator`. The generated
  `hosts/claude-code/NAME-INDEX.md` maps both forms; both name the same
  agent with the same instructions.
- **Skills preload.** On Copilot, an agent's `skills` list scopes which
  skills it may use. On Claude Code, the same list preloads the full skill
  text into the subagent's context at spawn. The lists are identical; the
  context cost is higher.
- **Azure tool granularity collapses.** Copilot grants the Deployer
  individual Azure MCP tools (`azure/keyvault`, `azure/storage`, …).
  Claude Code allowlists MCP access per server, so the generated agents
  carry the whole-server wildcard in its plugin-namespaced form,
  `mcp__plugin_sdlc-harness_azure__*`.
- **Editor-extension tools are substituted.** The VS Code Python
  extension tools in the Implementer's list have no Claude Code
  equivalent; shell access (`Bash`, already in its list) covers the same
  work.
- **`user-invocable` has no equivalent.** Every installed agent can be
  mentioned directly in Claude Code. The one standalone entry point that
  benefits from a command-style surface — the QA Bug Checklist Reviewer —
  additionally ships as a `qa-bug-checklist` skill.
- **MCP credentials are yours to supply.** The Copilot client injects
  GitHub authentication itself; Claude Code does not. Configure
  credentials through your own Claude Code MCP settings (for example a
  GitHub personal access token for the GitHub server, and the
  `GCP_DEVELOPER_KNOWLEDGE_API_KEY` environment variable for the Google
  Developer Knowledge server). Do not edit the generated `.mcp.json` —
  it is regenerated from the packs and your edits will be overwritten.

## How the two hosts stay in sync

There is nothing to sync by hand. One assembler run generates every host
target from the same pack snapshot, `tools/assemble_flat_layout.py
--check` fails if any generated tree differs from what the packs produce,
and one version number is stamped across every manifest. A fix lands in
the packs once and reaches both hosts in the same commit.
