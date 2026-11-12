# {{project-name}}

A command-line tool built from the rust/cli template. The sample
commands (`text slugify`, `text truncate`) run over a small library
core — replace them with your own nouns and verbs; the contract,
gates, and release machinery around them are the template.

## Install

```bash
# Shell installer (Linux/macOS) / PowerShell installer (Windows) —
# attached to every release
curl --proto '=https' --tlsv1.2 -LsSf https://example.com/{{project-name}}/releases/latest/download/{{project-name}}-installer.sh | sh
# Homebrew (via the tap configured in dist-workspace.toml)
brew install example/tap/{{project-name}}
# Release archives (Linux/macOS/Windows, amd64/arm64) — see Releases
# With a Rust toolchain:
cargo install --git https://example.com/{{project-name}}
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
  `result` field. `--version` prints `{{project-name}} X.Y.Z` —
  that shape never changes; scripts parse it.
- **Colour.** Diagnostics are styled only at a terminal, and never
  when `NO_COLOR` is set or `--no-color` is passed.
- **Safety.** Results written with `--out` are never overwritten
  without `--force`; `--dry-run` reports what would happen and
  writes nothing; prompting happens only at a terminal, and
  `--no-input` disables it entirely (the command fails instead).
- **Configuration precedence.** Flags, then environment
  (`{{ProjectName}}_FORMAT` and friends — the prefix is the
  upper-cased tool name), then defaults. Secrets come from the
  environment, never from a flag (flags leak into shell history
  and process lists).

The contract is pinned by tests: golden files for help and primary
outputs, and exit-code tests per failure mode
(`tests/cli_test.rs`). Regenerate goldens deliberately with
`UPDATE_GOLDEN=1 cargo test` and review the diff like an API
change — changes to the JSON schema, the exit codes, or flag names
are **breaking changes** and ship only in a major release.

## Versioning and releases

Strict semantic versioning. The version lives in `Cargo.toml`;
releasing means moving the CHANGELOG *Unreleased* entries under a
`## [X.Y.Z] - YYYY-MM-DD` heading, bumping `Cargo.toml` to match,
and tagging `vX.Y.Z` — the release workflow refuses a tag that
does not match `Cargo.toml` or has no CHANGELOG section, then runs
cargo-dist: binaries for linux/darwin/windows × amd64/arm64,
archives with a SHA-256 checksums file, shell/PowerShell
installers, a Homebrew cask in the configured tap, and generated
man pages and shell completions (from the hidden `man` and
`completions` commands). After changing `dist-workspace.toml`,
regenerate the workflow with `dist generate` and commit the result.

## Development

```bash
cd src/{{ProjectName}}CLI
cargo fetch
cargo test
cargo fmt --check
cargo clippy --all-targets -- -D warnings
```
