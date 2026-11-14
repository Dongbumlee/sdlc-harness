# {{project-name}}

A command-line tool built from the python/cli template. The sample
commands (`text slugify`, `text truncate`) run over a small library
core — replace them with your own nouns and verbs; the contract,
gates, and release machinery around them are the template.

## Install

```bash
# Self-contained binary for your platform — see Releases
# (Linux/macOS/Windows, x86_64 and arm64 where the OS supports it)
# With pipx or uv (the language channel):
pipx install {{project-name}}
uv tool install {{project-name}}
```

## Usage

```bash
{{project-name}} text slugify "Hello, World!"            # hello-world
{{project-name}} text slugify --json "Hello, World!"     # {"result":"hello-world"}
{{project-name}} text truncate --max 6 "a longer sentence"
{{project-name}} text slugify --out slug.txt "Hello, World!"
{{project-name}} --help                                  # full command tree
```

## The CLI contract

Scripts and agents consume this tool, so its interface is an API:

- **Streams.** Primary data goes to **stdout**; diagnostics,
  progress, and errors go to **stderr**. Nothing but data is ever
  written to stdout.
- **Exit codes.** `0` success · `1` failure (the command ran but
  could not complete) · `2` usage error (unknown command, bad
  flags, invalid arguments). The map is also printed by `--help`.
- **Formats.** `--format plain|json` (or `--json`) on data
  commands. In JSON mode the output is an object with a stable
  `result` field. `--version` prints `{{project-name}}, version
  X.Y.Z` — that shape never changes; scripts parse it.
- **Colour.** Diagnostics are styled only at a terminal, and never
  when `NO_COLOR` is set or `--no-color` is passed.
- **Safety.** Results written with `--out` are never overwritten
  without `--force`; `--dry-run` reports what would happen and
  writes nothing; prompting happens only at a terminal, and
  `--no-input` disables it entirely (the command fails instead).
- **Configuration precedence.** Flags, then environment
  (`<PREFIX>_FORMAT` and friends — the prefix is the tool name
  upper-cased with hyphens as underscores, e.g.
  `TASK_TRACKER_FORMAT`), then defaults. Secrets come from the
  environment, never from a flag (flags leak into shell history
  and process lists).

The contract is pinned by tests: golden files for help and primary
outputs, and exit-code tests per failure mode (`tests/test_cli.py`).
Regenerate goldens deliberately with `UPDATE_GOLDEN=1 pytest` and
review the diff like an API change — changes to the JSON schema,
the exit codes, or flag names are **breaking changes** and ship
only in a major release.

## Versioning and releases

Strict semantic versioning. The version lives in `pyproject.toml`;
releasing means moving the CHANGELOG *Unreleased* entries under a
`## [X.Y.Z] - YYYY-MM-DD` heading, bumping `pyproject.toml` to
match, and tagging `vX.Y.Z`. The release workflow refuses a
mismatched tag or a missing CHANGELOG section, tests, then builds
a self-contained PyInstaller binary per platform, generates man
pages (help2man) and shell completions from the Linux binary,
publishes a GitHub Release with a SHA-256 `checksums.txt`, and
publishes the package to PyPI via trusted publishing.

## Development

```bash
uv sync
uv run pytest
uvx ruff check .
uvx ruff format --check .
```
