---
description: "Use when writing, reviewing, or refactoring Rust code. Enforces copyright headers, rustdoc comments, naming conventions, module organization, dead code removal, and idiomatic Rust patterns."
applyTo: '**/*.rs'
---
# Systematic Code-Quality Pass Instructions for Rust Codebase

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**
> as defined in `.github/SDLC-with-Copilot-and-Azure.md`. It auto-applies when Copilot edits Rust files.

You are performing a systematic code-quality pass on a Rust codebase. Work through every module one at a time. For each Rust file, apply ALL of the following rules, then compile-check every edited file before moving to the next module.

## 1. Copyright Header

- Every `.rs` file must start with:
  ```rust
  // Copyright (c) Microsoft Corporation.
  // Licensed under the MIT License.
  ```
- Place the copyright header on the very first lines of the file, before any `//!` module docs or `use` statements.

## 2. Module Documentation

- Immediately after the copyright header, add or replace the module-level doc comment using `//!` (inner doc comments). It must:
  - Describe what the module does in 1–2 sentences.
  - Mention its role in the broader system (e.g., which service, what it depends on).
  - NOT contain generic filler like "This module provides utilities for…"
- Module organization conventions:
  - Use `mod.rs` or file-named modules (e.g., `foo.rs` + `foo/` directory) — be consistent within the crate.
  - Re-export public items from child modules with `pub use` in the parent module.
  - Keep `lib.rs` and `main.rs` thin: they should declare modules and re-exports, not contain business logic.

## 3. Struct / Enum / Trait Docstrings

- Replace generic docstrings with structured Rustdoc using `///` (outer doc comments):
  ```rust
  /// One-line summary.
  ///
  /// Responsibilities:
  /// 1. First responsibility.
  /// 2. Second responsibility.
  ///
  /// # Fields
  ///
  /// * `field_name` - Description of the field.
  ///
  /// # Examples
  ///
  /// ```
  /// use my_crate::MyStruct;
  ///
  /// let instance = MyStruct::new("value");
  /// assert_eq!(instance.name(), "value");
  /// ```
  ```
- For enums, document each variant with `///`.
- For traits, document each required method and provide a usage example.
- Include `# Examples` with doc-tests where the type has a public constructor or common usage pattern.

## 4. Function / Method Docstrings

- Every public and non-trivial private function must have a Rustdoc comment.
- Use this structure (include sections as applicable):
  ```rust
  /// One-line summary.
  ///
  /// Steps:                    // only for complex multi-step functions
  /// 1. First step.
  /// 2. Second step.
  ///
  /// # Arguments
  ///
  /// * `param` - Description.
  ///
  /// # Returns
  ///
  /// Description of the return value.
  ///
  /// # Errors
  ///
  /// Returns `Err(...)` when condition.
  ///
  /// # Panics
  ///
  /// Panics if invariant is violated.
  ///
  /// # Examples
  ///
  /// ```
  /// let result = my_function("input")?;
  /// assert_eq!(result, "expected");
  /// ```
  ```
- Simple one-line functions (getters, delegates) get a single-line `///` doc comment.

## 5. Comment Cleanup — REMOVE These

- **Redundant inline comments** that just restate the code:
  `// Create a new HashMap` above `let map = HashMap::new();`
- **Banner comments** / section dividers:
  `//////////////////////////////////////////////////////`
  `// ========== Initialize the service ========== //`
- **Commented-out code** (dead imports, old logic, debug prints).
- **Heritage/provenance comments** referencing deleted files:
  `// Replaces old_module::process() from legacy crate`
- **Placeholder comments** that describe unimplemented intent:
  `// Placeholder for document processing logic`
- **"For demonstration" / "Here you would typically"** comments.

## 6. Comment Cleanup — KEEP These

- **Actionable TODOs** with clear intent: `// TODO: Make configurable via feature flag`
- **Non-obvious "why" comments** that explain a design decision:
  `// Use BTreeMap instead of HashMap for deterministic iteration order.`
- **Contract/protocol comments** that document external API behavior:
  `// The upstream API returns 204 with empty body on success.`
- **Safety comments** for unsafe blocks:
  `// SAFETY: pointer is guaranteed non-null by the caller's contract.`

## 7. Fix Stale References

- Search for outdated terminology (old crate names, old struct names, old module descriptions) and correct them to match the current code.

## 8. Remove Dead Code

- Delete unused imports (`use` statements the compiler warns about).
- Delete unused variables (prefix with `_` only if genuinely intentional, not to silence warnings).
- Remove unjustified `#[allow(dead_code)]` attributes — if the code is dead, delete it; if it is intentionally reserved, add a comment explaining why.
- Delete unreachable patterns in `match` arms.
- Remove empty `impl` blocks.
- Delete redundant `Clone` or `Copy` on types that are never cloned/copied.

## 9. Compile-Check

- After finishing each module, run:
  - `cargo check` — fast type/borrow checking without full codegen.
  - `cargo clippy -- -W clippy::pedantic` — lint for idiomatic Rust.
  - `cargo fmt --check` — verify formatting.
- Fix any errors or warnings before proceeding to the next module.
- For a full build: `cargo build` (debug) or `cargo build --release` (optimized).

## 10. Working Process

1. List the module tree of the target crate (`src/` structure).
2. Read all Rust files in the current module.
3. Create a TODO list for the module (one item per file + one for compile-check).
4. Edit files, marking each TODO as you go.
5. Compile-check all edited files (`cargo check`, `cargo clippy`).
6. Move to the next module.

Start with the module I specify and work through it completely before asking what to do next.

═══════════════════════════════════════════════════════════════════════════════
## Rust-Specific Rules
═══════════════════════════════════════════════════════════════════════════════

### Error Handling

- Use `Result<T, E>` for all recoverable errors. Never use sentinel values or return codes.
- Use the `thiserror` crate for library error types (structured, strongly-typed errors):
  ```rust
  #[derive(Debug, thiserror::Error)]
  pub enum MyError {
      #[error("failed to parse config: {0}")]
      ConfigParse(#[from] serde_json::Error),
      #[error("item not found: {id}")]
      NotFound { id: String },
  }
  ```
- Use the `anyhow` crate for application error types (quick, context-rich error propagation):
  ```rust
  use anyhow::{Context, Result};

  fn load_config(path: &str) -> Result<Config> {
      let data = std::fs::read_to_string(path)
          .with_context(|| format!("failed to read config from {path}"))?;
      Ok(serde_json::from_str(&data)?)
  }
  ```
- Use the `?` operator for error propagation. Avoid manual `match` on `Result` unless you need to transform the error.
- **Never** use `.unwrap()` in production code. Use `.expect("reason")` only when the invariant is guaranteed and document why.

### Ownership & Borrowing

- Prefer borrowing (`&T`, `&mut T`) over ownership transfer when the callee does not need to own the data.
- Use `Clone` sparingly — if you find yourself cloning frequently, reconsider the data flow.
- Document lifetime requirements in complex signatures:
  ```rust
  /// The returned iterator borrows from `input` and must not outlive it.
  fn parse_tokens<'a>(input: &'a str) -> impl Iterator<Item = Token> + 'a { ... }
  ```
- Prefer `&str` over `String` in function parameters; prefer `&[T]` over `Vec<T>` when ownership is not needed.

### Naming Conventions

| Element          | Convention              | Example                          |
|------------------|-------------------------|----------------------------------|
| Functions        | `snake_case`            | `parse_config`, `get_user_by_id` |
| Variables        | `snake_case`            | `user_count`, `is_valid`         |
| Modules          | `snake_case`            | `auth`, `data_store`             |
| Types / Structs  | `PascalCase`            | `UserProfile`, `HttpClient`      |
| Traits           | `PascalCase`            | `Serialize`, `EventHandler`      |
| Enums            | `PascalCase`            | `Status::Active`                 |
| Enum variants    | `PascalCase`            | `Color::DarkBlue`                |
| Constants        | `SCREAMING_SNAKE_CASE`  | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Statics          | `SCREAMING_SNAKE_CASE`  | `GLOBAL_CONFIG`                  |
| Crate names      | `kebab-case`            | `my-service`, `data-pipeline`    |
| Type parameters  | Single uppercase letter | `T`, `E`, `K`, `V`              |

### Type System

- Use newtypes for domain concepts to prevent mixing unrelated values:
  ```rust
  pub struct UserId(pub u64);
  pub struct OrderId(pub u64);
  ```
- Prefer enums over boolean flags for clarity:
  ```rust
  // Bad:  fn process(data: &[u8], compress: bool, encrypt: bool)
  // Good:
  enum Compression { None, Gzip, Zstd }
  enum Encryption  { None, Aes256 }
  fn process(data: &[u8], compression: Compression, encryption: Encryption)
  ```
- Use `Option<T>` instead of sentinel values (e.g., `-1`, `""`, `null`).
- Prefer strong typing over stringly-typed APIs.

### Traits

- Implement standard traits where applicable:
  - `Debug` — always derive on public types.
  - `Display` — implement for types that have a user-facing string representation.
  - `Clone`, `PartialEq`, `Eq`, `Hash` — derive when semantically correct.
  - `Default` — derive or implement when a sensible default exists.
  - `From` / `TryFrom` — implement for type conversions.
- Use `#[derive(...)]` whenever possible; hand-implement only when custom behavior is needed.
- Prefer trait bounds over concrete types in public APIs for flexibility.

### Unsafe Code

- Minimize `unsafe` blocks. Always look for a safe alternative first.
- Document safety invariants with a `// SAFETY: ...` comment immediately above the `unsafe` block:
  ```rust
  // SAFETY: `ptr` is guaranteed non-null and properly aligned by the
  // allocator contract established in `allocate_buffer()`.
  unsafe { *ptr = value; }
  ```
- Encapsulate unsafe code in safe abstractions — expose a safe public API that upholds the invariants internally.
- Never introduce undefined behavior. When in doubt, do not use `unsafe`.

### Project Layout

```
my-crate/
├── Cargo.toml              ← crate metadata, dependencies, feature flags
├── src/
│   ├── lib.rs              ← library root (module declarations, re-exports)
│   ├── main.rs             ← binary entry point (thin: parse args, call lib)
│   ├── bin/                ← additional binaries
│   │   └── tool.rs
│   ├── config.rs           ← configuration types
│   ├── error.rs            ← crate-level error types
│   ├── models/             ← domain models
│   │   ├── mod.rs
│   │   ├── user.rs
│   │   └── order.rs
│   └── services/           ← business logic
│       ├── mod.rs
│       └── auth.rs
├── tests/                  ← integration tests
│   ├── common/
│   │   └── mod.rs          ← shared test helpers
│   └── integration_test.rs
├── benches/                ← benchmarks
│   └── benchmark.rs
└── examples/               ← runnable examples
    └── basic_usage.rs
```

- `src/lib.rs` for libraries, `src/main.rs` for binaries.
- `src/bin/` for multiple binaries in the same crate.
- Feature flags in `Cargo.toml` for optional functionality:
  ```toml
  [features]
  default = ["json"]
  json = ["dep:serde_json"]
  ```

### Linting

- Run `cargo clippy -- -W clippy::pedantic` for strict linting on every change.
- Run `cargo fmt` before committing — all code must pass `cargo fmt --check`.
- Suppress Clippy lints only with justification: `#[allow(clippy::lint_name)] // reason`.
- Configure project-wide lint levels in `Cargo.toml`:
  ```toml
  [lints.clippy]
  pedantic = "warn"
  unwrap_used = "deny"
  ```
