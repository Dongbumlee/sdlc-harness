# sample

A command-line tool built from the typescript/cli template. The
sample commands (`text slugify`, `text truncate`) run over a small
library core — replace them with your own nouns and verbs; the
contract, gates, and release machinery around them are the
template.

## Install

```bash
# Self-contained binary for your platform — see Releases
# (Linux/macOS/Windows; no Node runtime required)
# From npm (the language channel):
npm install -g sample
pnpm add -g sample
```

## Usage

```bash
sample text slugify "Hello, World!"            # hello-world
sample text slugify --json "Hello, World!"     # {"result":"hello-world"}
sample text truncate --max 6 "a longer sentence"
sample text slugify --out slug.txt "Hello, World!"
sample completions bash                        # completion script, generated from the command tree
sample --help                                  # full command tree
```

## The CLI contract

Scripts and agents consume this tool, so its interface is an API:

- **Streams.** Primary data goes to **stdout**; diagnostics,
  progress, and errors go to **stderr**. Nothing but data is ever
  written to stdout.
- **Exit codes.** `0` success · `1` failure (the command ran but
  could not complete) · `2` usage error (unknown command, bad
  flags, invalid arguments). The map is also printed by `--help`.
  (Commander reports parse failures as 1 by itself, so the entry
  point catches its errors and maps them to 2.)
- **Formats.** `--format plain|json` (or `--json`) on data
  commands. In JSON mode the output is an object with a stable
  `result` field. `--version` prints `sample X.Y.Z` —
  that shape never changes; scripts parse it.
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
outputs, and exit-code tests per failure mode (`tests/cli.test.ts`).
Regenerate goldens deliberately with `UPDATE_GOLDEN=1 pnpm test`
and review the diff like an API change — changes to the JSON
schema, the exit codes, or flag names are **breaking changes** and
ship only in a major release.

## Versioning and releases

Strict semantic versioning. The version lives in `package.json`;
releasing means moving the CHANGELOG _Unreleased_ entries under a
`## [X.Y.Z] - YYYY-MM-DD` heading, bumping `package.json` to
match, and tagging `vX.Y.Z`. The release workflow refuses a
mismatched tag or a missing CHANGELOG section, tests, then builds
a Node SEA binary per platform, generates a man page (help2man)
and shell completions from the Linux binary, publishes a GitHub
Release with a SHA-256 `checksums.txt`, and publishes the package
to npm via trusted publishing.

## Development

```bash
pnpm install
pnpm build
pnpm test
pnpm lint
pnpm format:check
```
