# {{project-name}}

A command-line tool built from the dotnet/cli template. The sample
commands (`text slugify`, `text truncate`) run over a small library
core (`{{ProjectName}}.Cli.Core`) — replace them with your own nouns
and verbs; the contract, gates, and release machinery around them
are the template.

## Install

```bash
# Self-contained binary for your platform — see Releases
# (Windows/Linux/macOS, x64 and arm64, no runtime required)
# As a .NET tool (the language channel):
dotnet tool install -g {{project-name}}
```

Shell completions come from System.CommandLine's suggestion
machinery: install `dotnet-suggest`
(`dotnet tool install -g dotnet-suggest`) and register this tool
with your shell — the command surface itself is the completion
source, nothing is hand-maintained.

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
  (System.CommandLine reports parse failures as 1 by itself, so
  the entry point inspects the parse result and maps them to 2.)
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
  (`<PREFIX>_FORMAT` and friends — the prefix is the tool name
  upper-cased with hyphens as underscores, e.g.
  `TASK_TRACKER_FORMAT`), then defaults. Secrets come from the
  environment, never from a flag (flags leak into shell history
  and process lists).

The contract is pinned by tests: golden files for help and primary
outputs, and exit-code tests per failure mode
(`CliContractTests`). Regenerate goldens deliberately with
`UPDATE_GOLDEN=1 dotnet test` and review the diff like an API
change — changes to the JSON schema, the exit codes, or flag names
are **breaking changes** and ship only in a major release.

## Versioning and releases

Strict semantic versioning. The version lives in
`{{ProjectName}}.Cli.csproj`; releasing means moving the CHANGELOG
*Unreleased* entries under a `## [X.Y.Z] - YYYY-MM-DD` heading,
bumping the csproj to match, and tagging `vX.Y.Z`. The release
workflow refuses a mismatched tag or a missing CHANGELOG section,
tests, then publishes a self-contained single-file binary per
platform (six RIDs), generates a man page from the Linux binary
(help2man), publishes a GitHub Release with a SHA-256
`checksums.txt`, and pushes the tool package to NuGet via trusted
publishing.

## Development

```bash
dotnet restore {{ProjectName}}.sln
dotnet build {{ProjectName}}.sln -c Release
dotnet test {{ProjectName}}.sln -c Release
dotnet format {{ProjectName}}.sln --verify-no-changes
```
