# New cloud pack template

Copy this directory to start a new cloud pack:

```bash
cp -r packs/_template packs/aws
```

Then fill in:

1. **`pack.json`** — replace every `<...>` placeholder. `agents.deployer` is required;
   add further agent roles as needed. Every referenced agent file must exist in the
   canonical agent directory (`com.github.copilot/agents/`) until Phase 2 moves
   pack-specific agents under `packs/<name>/agents/`.
2. **`agents/`** — (Phase 2 layout) pack-specific agent files. Leave the `.gitkeep`
   until then.
3. **`skills/`** — (Phase 2 layout) pack-specific skill directories. Leave the
   `.gitkeep` until then. Skill directories referenced in `pack.json` must exist
   under the root `skills/` compatibility layout for now.
4. **`mcp-servers.json`** — MCP server configuration for this cloud.

The `pack-contracts` CI job validates every `packs/*/pack.json` (this template is
excluded) against `schemas/cloud-pack.schema.json` and checks that all referenced
agents and skills exist.
