# Contributing

Issues and pull requests are welcome. Keep each change scoped to one
concern, with tests and documentation updated in the same pull request.

## Where things live

- **Edit `packs/`, never the mirrors.** The flat layout (`.github/`,
  `com.github.copilot/`, `skills/`) is generated from `packs/` by
  `tools/assemble_flat_layout.py`. Edit the pack source, regenerate,
  and commit both.
- Canonical definitions live in `docs/base-definitions.md`. Where a
  pack file and that document disagree, the document is the standard
  and the pack file is the defect. Definition changes are proposed
  there first, then swept into the packs.
- Agent and skill changes require corresponding canary spec updates
  (`bench/canaries/`).

## Before opening a pull request

Run the full verification battery and include its results:

```bash
python3 tools/assemble_flat_layout.py --check
python3 tools/verify_templates.py
python3 tools/check_pack_contracts.py
python3 tools/generate_agent_inventory.py --check
python3 -m pytest tests/ -q
```

## Conventions

- No concrete model names, endpoints, prices, or context sizes in
  agents, skills, or prompts — declare a capability tier and let the
  platform resolve it.
- Measured claims carry their scope: what was run, on which stack,
  in which form (desk exercise, canary, live run).
- Releases are cut with a written scope freeze (an IN list and an
  OUT list) recorded before the tag; release notes describe IN only.
- VSIX distribution is retired — do not recreate `vscode-extension/`,
  `sync-check.yml`, or `build-vsix.yml`. The repo ships as a root
  Agent Plugins package via `plugin.json`, `skills/`, and
  `com.github.copilot/`, with `.claude-plugin/marketplace.json`
  providing marketplace metadata.
- All QA reviewers emit structured YAML output (see the
  `sdlc-reviewer-output-format` skill).

## Repository structure

```
packs/                ← Source of truth: core pack + Azure/AWS/GCP/On-Prem packs
  core/                 agents, skills, prompts, instructions, MCP config
  azure/ aws/ gcp/ onprem/  platform-specific agents and skills
.github/agents/       ← Generated mirrors of packs/*/agents (do not edit)
com.github.copilot/   ← Generated mirrors for the Agent Plugins layout
skills/               ← Generated mirrors of packs/*/skills (do not edit)
plugin.json           ← Root plugin manifest
.claude-plugin/       ← Marketplace metadata
bench/canaries/       ← E2E canary test specs
bench/evals/          ← Frozen skill evaluation specs
schemas/              ← JSON schemas for validation
tests/                ← Repository test suite (pytest)
tools/                ← Assembly, verification, and inventory scripts
docs/                 ← Architecture docs, specs, guides
```

## CI checks

| Workflow | Purpose |
|----------|---------|
| `pack-assembly.yml` | Fails when the generated flat layout drifts from `packs/` |
| `pack-contracts.yml` | Validates pack metadata and cross-pack contracts |
| `python-tests.yml` | Runs the repository test suite |
| `canary-test.yml` | Validates canary spec schema on PRs touching agents/skills |
| `eval-spec-lint.yml` | Validates skill evaluation specs |
| `bump-plugin-version.yml` | Manually bumps the plugin version and synchronizes marketplace metadata |

## Releases

A version bump covers the full surface — `plugin.json`,
`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, all
five `packs/*/pack.json` files, the generated Claude Code host
manifest, the agent inventory header, the README release badge, the
terminal-image generator, and the tests that pin the version. The
Bump Plugin Version workflow updates only the first two surfaces, so
a release bump is completed by hand and verified by the version-sync
tests.
