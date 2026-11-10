# New cloud pack template

Copy this directory to start a new cloud pack:

```bash
cp -r packs/_template packs/<name>
```

Pack layout (the same layout every shipped pack uses):

```
packs/<name>/
├── pack.json          # Pack manifest — validated by the pack-contracts CI job
├── mcp-servers.json   # MCP server configuration for this cloud
├── agents/            # Pack-specific agent files (*.agent.md)
└── skills/            # Pack-specific skill directories (each with a SKILL.md)
```

Then fill in:

1. **`pack.json`** — replace every `<...>` placeholder. `agents.deployer` is
   required; add further agent roles as needed. Every referenced agent file
   must exist under this pack's `agents/`, and every skill named in `skills`
   must exist as a directory under this pack's `skills/`.
2. **`agents/`** — pack-specific agent files. The flat layout
   (`com.github.copilot/`, `skills/`) is generated from `packs/` by
   `tools/assemble_flat_layout.py` — never edit the generated mirrors.
3. **`skills/`** — one directory per skill, each holding a `SKILL.md` (plus
   any `assets/` it needs).
4. **`mcp-servers.json`** — MCP server configuration for this cloud.

The `pack-contracts` CI job validates every `packs/*/pack.json` (this
template is excluded) against `schemas/cloud-pack.schema.json` and checks
that all referenced agents and skills exist.
