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
