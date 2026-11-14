# {{project-name}}

A Rust library crate. The sample crate provides small
text-normalization helpers — replace them with your own API; the
structure, gates, and policies around it are the template.

## Quickstart

```rust
use {{CrateName}}::{slugify, truncate};

assert_eq!(slugify("Hello, World!"), "hello-world");
assert_eq!(truncate("a longer sentence", 6), "a lon…");
```

This exact usage is executable: it is the crate-level doctest in
`src/{{ProjectName}}Lib/src/lib.rs`, and `cargo test` runs it on every
supported toolchain — the quickstart cannot drift from the shipped API.

## Install

```toml
[dependencies]
{{project-name}} = "0.1"
```

## Supported toolchains

| Rust     | Status    |
| -------- | --------- |
| 1.85     | Supported (MSRV) |
| stable   | Supported |

The floor is `rust-version` in `Cargo.toml`. CI tests both rows.
Raising the MSRV is a breaking change: it ships only in a major
release.

## Versioning and API stability

Releases follow semantic versioning; the git tag is the version and
must match `version` in `Cargo.toml`. The public API is the crate's
public items. CI runs cargo-semver-checks against the last release tag
and fails on breaking changes — a major release is the only place the
API may break.

Dependencies use caret ranges (Cargo's default): a library declares
the range it can work with; the consumer's build resolves the exact
versions and owns the lock file, so this repository does not commit
`Cargo.lock`.

## Deprecation policy

Mark an item `#[deprecated(since = "…", note = "…")]` in one release;
remove it no earlier than the next major release.

## Development

```bash
cd src/{{ProjectName}}Lib
cargo build
cargo test
cargo fmt --check
cargo clippy --all-targets -- -D warnings
```

Releasing: move the CHANGELOG *Unreleased* entries under a
`## [X.Y.Z] - YYYY-MM-DD` heading, bump `version` in `Cargo.toml`,
then tag `vX.Y.Z`. The release workflow verifies the tag, smoke-tests
the packaged crate from a clean project, publishes to crates.io via
trusted publishing, and creates the GitHub Release.
