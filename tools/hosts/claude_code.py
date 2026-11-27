#!/usr/bin/env python3
"""Claude Code host adapter for the assembler.

Translates the pack sources into a Claude Code plugin tree under
``hosts/claude-code/``. The packs stay the single source
of truth; this module is the only place that knows Claude Code's format.

Rules the build enforces:

- Agent bodies are emitted byte-identical; only frontmatter is translated.
- Every Copilot tool token must be covered by the tables below. An unmapped
  token raises, failing the build -- a tool is never dropped silently.
- Agent names are slugified to Claude Code's ``[a-z0-9-]`` form; a slug
  collision fails the build.
- Claude Code registers plugin subagents under plugin-namespaced types
  (``<plugin>:<slug>``; measured live 2026-11-14 on Claude Code 2.1.325 --
  a bare slug matches no registered type and an allowlist of bare slugs
  leaves the Agent tool with no spawnable types). ``Agent(...)`` allowlist
  entries and the QA checklist shim therefore carry the namespaced form,
  using the plugin name from the root ``plugin.json``.
- The spawnable registry for a whole session is scoped by the MAIN
  agent's ``Agent(...)`` allowlist, not by each subagent's own list
  (measured live 2026-11-14: a coordinator spawned by the harness saw
  exactly the harness's nine allowlist types as its available agents, and
  its own eleven-reviewer list had no effect). The delegation graph's
  root agent (the one no other agent delegates to -- the supported
  main-thread entry) therefore carries the transitive closure of the
  graph in its allowlist; every other agent keeps its direct list, which
  is the correct registry when that agent itself is the entry point.
- MCP servers shipped by a plugin surface under plugin-namespaced tool
  names, ``mcp__plugin_<plugin>_<server>__<tool>`` (measured live
  2026-11-14: the session's Context7 tool was
  ``mcp__plugin_sdlc-harness_context7__resolve-library-id``, and a
  subagent whose allowlist carried the plain ``mcp__context7__*`` form
  received no MCP tools at all). Emitted wildcards therefore carry the
  plugin namespace; the server names inside ``.mcp.json`` stay plain.
- Known semantic deltas are recorded, not hidden: granular ``azure/<tool>``
  tokens collapse to the server wildcard, and the ``ms-python.python/*``
  editor tools are substituted by ``Bash`` (see CAPABILITY_SUBSTITUTIONS).
- VS Code ``${input:<name>}`` placeholders in MCP server headers become
  environment-variable expansions ``${<NAME>}`` (uppercased), which is the
  mechanism Claude Code offers in ``.mcp.json``.

Frontmatter parsing is a targeted parser for the grammar the pack agents
actually use (single-line scalars and flow lists). Anything outside that
grammar raises instead of being guessed at.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Copilot tool token -> Claude Code tools (fan-out expands in place).
TOOL_MAP: dict[str, list[str]] = {
    "read": ["Read"],
    "search": ["Grep", "Glob"],
    "edit": ["Edit", "Write"],
    "execute": ["Bash"],
    "terminal": ["Bash"],
    "fetch": ["WebFetch"],
    "web": ["WebFetch", "WebSearch"],
    "browser": ["mcp__playwright__*"],
    "todo": ["TodoWrite"],
}

# Copilot "server/*" tokens -> Claude Code MCP wildcards. The server name is
# the name the server carries in the generated .mcp.json, so the two cannot
# drift apart.
MCP_SERVERS = {"github", "context7", "playwright", "microsoft-learn", "azure"}

# Editor-extension tools with no Claude Code equivalent. The substitution is
# a recorded design decision (design note section 5), not a silent drop.
CAPABILITY_SUBSTITUTIONS: dict[str, str] = {
    "ms-python.python/": "Bash",
}

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
_SLUG_OK_RE = re.compile(r"\A[a-z0-9]+(-[a-z0-9]+)*\Z")


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().replace("&", " and ")).strip("-")
    if not _SLUG_OK_RE.match(slug):
        raise ValueError(f"name {name!r} does not slugify to a valid Claude Code name")
    return slug


def _parse_value(value: str, source: str, key: str):
    if value.startswith("["):
        if not value.endswith("]"):
            raise ValueError(f"{source}: frontmatter '{key}' flow list is not single-line")
        inner = value[1:-1].strip()
        if not inner:
            return []
        items = []
        for item in inner.split(","):
            item = item.strip()
            if len(item) >= 2 and item[0] == item[-1] and item[0] in "'\"":
                item = item[1:-1]
            items.append(item)
        return items
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if value in ("true", "false"):
        return value == "true"
    return value


def parse_frontmatter(text: str, source: str) -> tuple[dict, dict, str]:
    """Return (fields, raw_values, body). Raw values keep the source token
    (e.g. the description's quoting) so emission never re-escapes."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{source}: no frontmatter block")
    fields: dict = {}
    raw: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if line[0] in " \t":
            raise ValueError(f"{source}: unsupported frontmatter continuation: {line!r}")
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"{source}: malformed frontmatter line: {line!r}")
        key = key.strip()
        raw[key] = value.strip()
        fields[key] = _parse_value(value.strip(), source, key)
    return fields, raw, text[match.end():]


_MCP_WILDCARD_RE = re.compile(r"\Amcp__([a-z0-9-]+)__\*\Z")


def _namespaced_mcp(tool: str, plugin_name: str) -> str:
    """Plugin-provided MCP servers surface as
    mcp__plugin_<plugin>_<server>__*; rewrite a plain wildcard to that
    form. Non-wildcard and non-MCP tools pass through unchanged."""
    match = _MCP_WILDCARD_RE.match(tool)
    if match:
        return f"mcp__plugin_{plugin_name}_{match.group(1)}__*"
    return tool


def translate_tools(
    tokens: list[str], allowlist_slugs: list[str], source: str, plugin_name: str
) -> tuple[list[str], list[str]]:
    """Return (claude_tools, substitutions_used). Raises on unmapped tokens."""
    out: list[str] = []
    substitutions: list[str] = []

    def add(tool: str) -> None:
        tool = _namespaced_mcp(tool, plugin_name)
        if tool not in out:
            out.append(tool)

    for token in tokens:
        if token == "agent":
            if allowlist_slugs:
                add(
                    "Agent("
                    + ", ".join(f"{plugin_name}:{slug}" for slug in allowlist_slugs)
                    + ")"
                )
            else:
                add("Agent")
        elif token in TOOL_MAP:
            for tool in TOOL_MAP[token]:
                add(tool)
        elif token.endswith("/*") and token[:-2] in MCP_SERVERS:
            add(f"mcp__{token[:-2]}__*")
        elif token.startswith("azure/"):
            # Granular per-tool ids collapse to the server wildcard; the
            # granularity loss is a recorded delta (design note section 5).
            add("mcp__azure__*")
        elif any(token.startswith(prefix) for prefix in CAPABILITY_SUBSTITUTIONS):
            prefix = next(p for p in CAPABILITY_SUBSTITUTIONS if token.startswith(p))
            substitutions.append(token)
            add(CAPABILITY_SUBSTITUTIONS[prefix])
        else:
            raise ValueError(f"{source}: unmapped tool token {token!r} -- extend the Claude Code mapping table")
    return out, substitutions


def build_agent(
    text: str,
    source: str,
    slug_by_name: dict[str, str],
    plugin_name: str,
    allowlist_slugs: list[str],
) -> tuple[str, str, list[str]]:
    """Return (slug, claude_file_text, substitutions_used)."""
    fields, raw, body = parse_frontmatter(text, source)
    name = fields.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"{source}: agent has no name")
    slug = slug_by_name[name]
    if "description" not in raw:
        raise ValueError(f"{source}: agent has no description")
    tools, substitutions = translate_tools(
        fields.get("tools") or [], allowlist_slugs, source, plugin_name
    )
    lines = ["---", f"name: {slug}", f"description: {raw['description']}"]
    if tools:
        lines.append("tools: " + ", ".join(tools))
    skills = fields.get("skills") or []
    if skills:
        lines.append("skills:")
        lines.extend(f"  - {skill}" for skill in skills)
    lines.append("---")
    return slug, "\n".join(lines) + "\n" + body, substitutions


def build_command(text: str, source: str) -> str:
    """Prompt file -> Claude Code command. The leading HTML comment in the
    prompt body is VS Code usage instructions (host packaging, not
    methodology), so it is stripped; the rest of the body is verbatim."""
    fields, raw, body = parse_frontmatter(text, source)
    stripped = body.lstrip()
    if stripped.startswith("<!--"):
        end = stripped.find("-->")
        if end == -1:
            raise ValueError(f"{source}: unterminated HTML comment in prompt body")
        body = stripped[end + 3:].lstrip("\n")
    lines = ["---"]
    if "description" in raw:
        lines.append(f"description: {raw['description']}")
    if "argument-hint" in raw:
        lines.append(f"argument-hint: {raw['argument-hint']}")
    lines.append("---")
    return "\n".join(lines) + "\n" + body


_INPUT_VAR_RE = re.compile(r"\A\$\{input:([A-Za-z0-9_]+)\}\Z")


def _convert_server(config: dict) -> dict:
    config = dict(config)
    server_type = config.pop("type", "stdio")
    headers = config.get("headers")
    if isinstance(headers, dict):
        converted = {}
        for key, value in headers.items():
            match = _INPUT_VAR_RE.match(value) if isinstance(value, str) else None
            converted[key] = "${" + match.group(1).upper() + "}" if match else value
        config["headers"] = converted
    if server_type == "http":
        return {"type": "http", **config}
    return config


def collect_mcp_servers(packs_dir: Path, init_skill_dir: Path) -> dict:
    """Union of the core template and every cloud pack's mcp-servers.json,
    converted to Claude Code's .mcp.json shape. Name collisions fail."""
    servers: dict = {}

    def add_from(data: dict, origin: str) -> None:
        for name, config in (data.get("servers") or {}).items():
            if name in servers:
                raise ValueError(f"MCP server name collision: {name!r} ({origin})")
            servers[name] = _convert_server(config)

    template = init_skill_dir / "assets" / "mcp.template.json"
    add_from(json.loads(template.read_text(encoding="utf-8")), "core mcp.template.json")
    for pack_dir in sorted(p for p in packs_dir.iterdir() if p.is_dir()):
        manifest_path = pack_dir / "pack.json"
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        ref = manifest.get("mcpServers")
        if isinstance(ref, str):
            add_from(
                json.loads((pack_dir / ref).read_text(encoding="utf-8")),
                f"{pack_dir.name}/pack.json",
            )
    missing = MCP_SERVERS - set(servers)
    if missing:
        raise ValueError(f"agents reference MCP servers missing from the declarations: {sorted(missing)}")
    return servers


def build_root_manifest(repo_root: Path, agent_slugs: list[str]) -> bytes:
    """The repo-root .claude-plugin/plugin.json (generated).

    The root marketplace manifest keeps ``source: "."``, so Claude Code
    resolves the plugin at the repo root and follows these component paths
    into hosts/claude-code/. The ``agents`` field must list .md files
    explicitly (a directory path is rejected by ``claude plugin
    validate``); skills/commands take directory paths. Verified
    2026-11-14: this manifest validates, and Copilot's marketplace
    install is unaffected by its presence.
    """
    root_manifest = json.loads((repo_root / "plugin.json").read_text(encoding="utf-8"))
    manifest = {
        key: root_manifest[key]
        for key in ("name", "version", "description", "author", "license", "keywords")
        if key in root_manifest
    }
    manifest["agents"] = [
        f"./hosts/claude-code/agents/{slug}.md" for slug in sorted(agent_slugs)
    ]
    manifest["skills"] = "./hosts/claude-code/skills"
    manifest["commands"] = "./hosts/claude-code/commands"
    manifest["mcpServers"] = "./hosts/claude-code/.mcp.json"
    return (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def qa_checklist_shim(plugin_name: str) -> str:
    return f"""---
name: qa-bug-checklist
description: "Run the QA Bug Checklist Reviewer against the current change, on demand: 338 known-bug patterns checked by a dedicated reviewer agent."
---

<!-- Generated by tools/assemble_flat_layout.py from the pack sources.
     Claude Code has no user-invocable flag for subagents, so this skill is
     the on-demand entry point for the qa-bug-checklist-reviewer agent. -->

Use the Agent tool to invoke the `{plugin_name}:qa-bug-checklist-reviewer`
subagent with the user's request. Default scope is the current change (the
working-tree diff, or the branch diff against its base if the tree is
clean); if the user names files, a directory, or a past change, pass that
scope instead. Relay the reviewer's findings to the user when it returns.
"""


def build_tree(
    repo_root: Path,
    packs_dir: Path,
    agents: dict[str, Path],
    skills: dict[str, Path],
) -> dict[str, bytes | Path]:
    """Return the Claude Code plugin tree: relative path -> file bytes, or
    a source directory to copy (skills). Raises on any unmapped token,
    slug collision, or MCP inconsistency."""
    root_manifest = json.loads((repo_root / "plugin.json").read_text(encoding="utf-8"))
    plugin_name = root_manifest["name"]

    # First pass: name -> slug, with collision detection.
    parsed: dict[str, tuple[dict, dict, str, Path]] = {}
    slug_by_name: dict[str, str] = {}
    slug_owner: dict[str, str] = {}
    for filename, src in sorted(agents.items()):
        text = src.read_text(encoding="utf-8")
        fields, raw, body = parse_frontmatter(text, str(src))
        name = fields.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(f"{src}: agent has no name")
        slug = slugify(name)
        if slug in slug_owner and slug_owner[slug] != name:
            raise ValueError(f"agent slug collision: {slug!r} for {slug_owner[slug]!r} and {name!r}")
        slug_owner[slug] = name
        slug_by_name[name] = slug
        parsed[filename] = (fields, raw, body, src)

    # Delegation graph: name -> direct delegates (from the agents: field).
    # The main-thread entry point is the agent nobody delegates to whose
    # closure reaches every delegated agent (standalone agents are also
    # delegated by nobody, but their closures reach nothing beyond their
    # own lists). The entry's allowlist is its transitive closure, because
    # Claude Code scopes the session's spawnable registry to the main
    # agent's list; every other agent keeps its direct list, which is the
    # correct registry when that agent itself is the entry point.
    direct: dict[str, list[str]] = {
        fields["name"]: list(fields.get("agents") or [])
        for fields, _raw, _body, _src in parsed.values()
    }
    delegated = {name for names in direct.values() for name in names}

    def closure(start: str) -> list[str]:
        seen: list[str] = []
        stack = list(direct[start])
        while stack:
            current = stack.pop()
            if current == start or current in seen:
                continue
            seen.append(current)
            stack.extend(direct.get(current) or [])
        return seen

    candidates = [name for name in direct if name not in delegated]
    closures = {name: closure(name) for name in candidates}
    entry = max(candidates, key=lambda name: len(closures[name]))
    if not delegated <= set(closures[entry]):
        raise ValueError(
            f"no entry agent reaches every delegated agent: entry {entry!r} "
            f"misses {sorted(delegated - set(closures[entry]))}"
        )
    if sum(1 for names in closures.values() if len(names) == len(closures[entry])) > 1:
        raise ValueError(f"delegation graph entry is ambiguous among {candidates}")

    allowlists: dict[str, list[str]] = {}
    for name, names in direct.items():
        effective = closures[name] if name == entry else names
        allowlists[name] = sorted(slug_by_name[a] for a in effective)

    entries: dict[str, bytes | Path] = {}
    index_rows = []
    for filename, (fields, raw, body, src) in sorted(parsed.items()):
        text = src.read_text(encoding="utf-8")
        slug, emitted, _subs = build_agent(
            text, str(src), slug_by_name, plugin_name, allowlists[fields["name"]]
        )
        entries[f"agents/{slug}.md"] = emitted.encode("utf-8")
        index_rows.append((slug, fields["name"], src.relative_to(repo_root)))

    for skill_name, skill_dir in sorted(skills.items()):
        entries[f"skills/{skill_name}"] = skill_dir
    entries["skills/qa-bug-checklist/SKILL.md"] = qa_checklist_shim(plugin_name).encode(
        "utf-8"
    )

    init_skill_dir = skills.get("sdlc-workspace-init")
    if init_skill_dir is None:
        raise ValueError("sdlc-workspace-init skill not resolved; cannot build commands or MCP config")
    prompts_dir = init_skill_dir / "assets" / "prompts"
    for prompt in sorted(prompts_dir.glob("*.prompt.md")):
        command_name = prompt.name[: -len(".prompt.md")]
        entries[f"commands/{command_name}.md"] = build_command(
            prompt.read_text(encoding="utf-8"), str(prompt)
        ).encode("utf-8")

    servers = collect_mcp_servers(packs_dir, init_skill_dir)
    entries[".mcp.json"] = (
        json.dumps({"mcpServers": servers}, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")

    plugin_manifest = {
        key: root_manifest[key]
        for key in ("name", "version", "description", "author", "license", "keywords")
        if key in root_manifest
    }
    entries[".claude-plugin/plugin.json"] = (
        json.dumps(plugin_manifest, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")

    index_lines = [
        "<!-- Generated by tools/assemble_flat_layout.py from packs/*/. Do not edit. -->",
        "",
        "# Agent name index",
        "",
        "Copilot agent names and their Claude Code agent types. Claude Code",
        "registers plugin subagents under plugin-namespaced types",
        "(`<plugin>:<slug>`), so the type below is the exact string the Agent",
        "tool accepts. The body of every generated agent file is",
        "byte-identical to its pack source.",
        "",
        "| Claude Code agent type | Copilot name | Pack source |",
        "| --- | --- | --- |",
    ]
    for slug, name, rel in sorted(index_rows):
        index_lines.append(f"| `{plugin_name}:{slug}` | {name} | `{rel}` |")
    entries["NAME-INDEX.md"] = ("\n".join(index_lines) + "\n").encode("utf-8")
    return entries
