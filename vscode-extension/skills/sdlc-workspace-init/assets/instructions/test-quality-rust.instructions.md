---
description: "Use when writing or reviewing Rust tests. Enforces module-level test organization, naming conventions, mocking patterns, property-based testing, and test configuration."
applyTo: '**/*.rs'
---
# Test Quality Instructions for Rust

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**
> as defined in `.github/SDLC-with-Copilot-and-Azure.md`. It auto-applies when Copilot edits Rust files.

You are a senior Rust test engineer. Your job is to audit, sanitize, and write
comprehensive tests for a Rust project that follows these conventions.

═══════════════════════════════════════════════════════════════════════════════
1. PROJECT LAYOUT
═══════════════════════════════════════════════════════════════════════════════

The project uses standard Rust conventions with three test categories:

    my-crate/
    ├── Cargo.toml                ← dependencies, features, test config
    ├── src/
    │   ├── lib.rs                ← library root (unit tests at bottom)
    │   ├── main.rs               ← binary entry point
    │   ├── config.rs             ← each source file has inline unit tests
    │   ├── error.rs
    │   ├── models/
    │   │   ├── mod.rs
    │   │   └── user.rs           ← #[cfg(test)] mod tests { ... } at bottom
    │   └── services/
    │       ├── mod.rs
    │       └── auth.rs
    ├── tests/                    ← integration tests (separate compilation)
    │   ├── common/
    │   │   └── mod.rs            ← shared test helpers & fixtures
    │   ├── api_test.rs
    │   └── workflow_test.rs
    └── benches/                  ← benchmarks (optional)
        └── benchmark.rs

Key rules:
- **Unit tests** live in `#[cfg(test)] mod tests { }` at the bottom of each source file.
  They can access private items via `use super::*`.
- **Integration tests** live in `tests/` — each `.rs` file is compiled as a separate crate.
  They can only access the public API (`use my_crate::...`).
- **Doc-tests** live in `///` doc comments on public items and are run automatically by `cargo test`.
- **Shared test utilities** go in `tests/common/mod.rs` (imported as `mod common;` in integration tests).
- Test directory structure does not need to mirror `src/` — integration tests are organized by feature or workflow.

═══════════════════════════════════════════════════════════════════════════════
2. TEST SANITIZATION (run first, before writing new tests)
═══════════════════════════════════════════════════════════════════════════════

Before writing any new tests, audit all existing test code:

a) FIND ORPHANED TESTS — test functions that reference structs, functions, or modules
   that no longer exist. For every `#[cfg(test)]` module and integration test file,
   verify that all `use` statements and function calls resolve to existing code.
   Delete any test whose target has been removed.

b) FIND STALE ASSERTIONS — tests whose assertions reference renamed fields,
   changed method signatures, or removed enum variants.
   Fix these to match the current source code.

c) COMPILE-CHECK all tests without running them:
       cargo check --tests
       cargo clippy --tests -- -W clippy::pedantic
       cargo test --no-run
   Fix any compilation errors, type mismatches, or lint warnings.

d) ADD MISSING COPYRIGHT HEADERS to any file that lacks one.

═══════════════════════════════════════════════════════════════════════════════
3. FILE FORMAT CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

### Unit Tests (inline in source files)

Every source file with testable logic must include a test module at the bottom:

```rust
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Module-level documentation.

use std::collections::HashMap;

// ... production code ...

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_descriptive_name() {
        // Arrange
        let input = "test";

        // Act
        let result = my_function(input);

        // Assert
        assert_eq!(result, "expected");
    }
}
```

### Integration Tests (in `tests/` directory)

```rust
// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Integration tests for <feature description>.

mod common;

use my_crate::{Config, Service};

#[test]
fn test_end_to_end_workflow() {
    // ...
}
```

Rules:
- ALWAYS include the 2-line copyright header.
- ALWAYS gate unit test modules with `#[cfg(test)]`.
- ALWAYS use `use super::*` in unit test modules to access parent items.
- Use `// Arrange`, `// Act`, `// Assert` comments in complex tests.
- Import only what is needed — do not use glob imports in integration tests.

═══════════════════════════════════════════════════════════════════════════════
4. NAMING CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

| Element             | Convention                                     | Example                                |
|---------------------|------------------------------------------------|----------------------------------------|
| Test function       | `test_<function>_<scenario>_<expected>`         | `test_parse_config_missing_key_errors` |
| Test module         | `mod tests` (unit), file name (integration)    | `mod tests`, `api_test.rs`             |
| Nested test module  | `mod <group_name>` inside `mod tests`          | `mod validation`, `mod edge_cases`     |
| Helper function     | `_prefixed` or in `common/`                    | `_make_config`, `common::setup_db`     |
| Test fixture struct | `PascalCase`                                   | `TestContext`, `MockService`           |

Test function naming must clearly describe:
1. **What** is being tested (function or method name).
2. **Scenario** / input condition (edge case, error path, happy path).
3. **Expected** behavior (returns, errors, panics).

```rust
#[test]
fn test_validate_email_empty_string_returns_error() { ... }

#[test]
fn test_process_order_insufficient_stock_returns_out_of_stock() { ... }

#[test]
#[should_panic(expected = "index out of bounds")]
fn test_get_item_invalid_index_panics() { ... }
```

Use nested modules for sub-grouping:
```rust
#[cfg(test)]
mod tests {
    use super::*;

    mod validation {
        use super::*;

        #[test]
        fn test_valid_input_succeeds() { ... }

        #[test]
        fn test_empty_input_fails() { ... }
    }

    mod serialization {
        use super::*;

        #[test]
        fn test_round_trip_preserves_data() { ... }
    }
}
```

═══════════════════════════════════════════════════════════════════════════════
5. WHAT TO TEST (prioritize by testability)
═══════════════════════════════════════════════════════════════════════════════

Focus on UNIT-TESTABLE code — pure logic that can run without external services:

HIGH PRIORITY (test these thoroughly):
- Pure functions: parsing, validation, transformation, computation
- Struct constructors and builder patterns: `new()`, `builder().build()`
- Enum behavior: variant construction, `Display` impl, conversions
- Error types: `From` impls, error message formatting, error chains
- Trait implementations: `Default`, `PartialEq`, `FromStr`, serialization
- Type conversions: `From`/`TryFrom` impls, `Into` usage

MEDIUM PRIORITY (test with trait-based mocking):
- Service methods with injected dependencies (via trait objects or generics)
- Repository/storage layers: mock the trait, test the logic
- Configuration loading: test with in-memory data, env var overrides
- Async operations: use `#[tokio::test]` with mock implementations

LOW PRIORITY (skip or test only the public API surface):
- `main()` functions and CLI argument parsing (test the library, not the binary)
- Deep async orchestration with multiple external service calls
- FFI boundaries (test the safe wrapper, not the raw bindings)

═══════════════════════════════════════════════════════════════════════════════
6. MOCKING PATTERNS
═══════════════════════════════════════════════════════════════════════════════

Use these patterns in order of preference:

a) **Hand-written mock structs** (preferred for simplicity and clarity):
   ```rust
   trait Repository {
       fn find_by_id(&self, id: &str) -> Result<Option<User>, DbError>;
   }

   #[cfg(test)]
   struct MockRepository {
       users: HashMap<String, User>,
   }

   #[cfg(test)]
   impl Repository for MockRepository {
       fn find_by_id(&self, id: &str) -> Result<Option<User>, DbError> {
           Ok(self.users.get(id).cloned())
       }
   }
   ```

b) **`mockall` crate** for auto-generating mocks from traits:
   ```rust
   use mockall::automock;

   #[automock]
   trait HttpClient {
       fn get(&self, url: &str) -> Result<Response, Error>;
   }

   #[test]
   fn test_fetch_data_returns_parsed_response() {
       let mut mock = MockHttpClient::new();
       mock.expect_get()
           .with(eq("https://api.example.com/data"))
           .returning(|_| Ok(Response::new(200, "body")));

       let service = DataService::new(mock);
       let result = service.fetch_data();
       assert!(result.is_ok());
   }
   ```

c) **`wiremock` crate** for HTTP mocking in integration tests:
   ```rust
   use wiremock::{MockServer, Mock, ResponseTemplate};
   use wiremock::matchers::{method, path};

   #[tokio::test]
   async fn test_api_client_handles_timeout() {
       let server = MockServer::start().await;

       Mock::given(method("GET"))
           .and(path("/health"))
           .respond_with(ResponseTemplate::new(200))
           .mount(&server)
           .await;

       let client = ApiClient::new(&server.uri());
       let result = client.health_check().await;
       assert!(result.is_ok());
   }
   ```

d) **`sqlx::test` macro** for database tests with automatic rollback:
   ```rust
   #[sqlx::test]
   async fn test_insert_user(pool: PgPool) {
       let user = User::new("test@example.com");
       let result = insert_user(&pool, &user).await;
       assert!(result.is_ok());
   }
   ```

e) **Dependency injection via generics** (compile-time polymorphism):
   ```rust
   struct Service<R: Repository> {
       repo: R,
   }

   impl<R: Repository> Service<R> {
       fn process(&self, id: &str) -> Result<Output, Error> {
           let item = self.repo.find_by_id(id)?;
           // ... business logic ...
           Ok(output)
       }
   }
   ```

Design production code for testability: accept trait bounds, not concrete types.
DO NOT use `#[cfg(test)]` to swap out implementations in production code — use
dependency injection instead.

═══════════════════════════════════════════════════════════════════════════════
7. ASSERTION STYLE
═══════════════════════════════════════════════════════════════════════════════

Use standard Rust assertion macros:

```rust
assert!(condition);
assert!(condition, "custom message: {}", detail);
assert_eq!(actual, expected);
assert_eq!(actual, expected, "values should match for input: {input}");
assert_ne!(left, right);
```

For expected panics:
```rust
#[test]
#[should_panic(expected = "index out of bounds")]
fn test_panics_on_invalid_index() {
    get_item(&[], 5);
}
```

For pattern matching assertions:
```rust
assert!(matches!(result, Ok(Value::Number(_))));
assert!(matches!(result, Err(MyError::NotFound { .. })));
```

For `Result` assertions:
```rust
// Assert success
let value = my_function().expect("should succeed");
assert_eq!(value, expected);

// Assert specific error variant
let err = my_function().unwrap_err();
assert!(matches!(err, MyError::InvalidInput { .. }));
assert!(err.to_string().contains("invalid"));
```

For improved diff output, add `pretty_assertions` as a dev dependency:
```rust
// In Cargo.toml:
// [dev-dependencies]
// pretty_assertions = "1"

#[cfg(test)]
use pretty_assertions::assert_eq;
```

═══════════════════════════════════════════════════════════════════════════════
8. COVERAGE CONFIGURATION
═══════════════════════════════════════════════════════════════════════════════

Use `cargo tarpaulin` or `cargo llvm-cov` for code coverage.

### cargo-tarpaulin

Install: `cargo install cargo-tarpaulin`

Configure in `Cargo.toml` or `.cargo/config.toml`:

```toml
# Cargo.toml
[package.metadata.tarpaulin]
out = ["Html", "Lcov"]
output-dir = "coverage"
exclude-files = ["tests/*", "benches/*", "examples/*"]
```

Run with: `cargo tarpaulin --out Html --output-dir coverage`

### cargo-llvm-cov

Install: `cargo install cargo-llvm-cov`

Run with:
```bash
cargo llvm-cov --html --output-dir coverage
cargo llvm-cov --text    # terminal summary
```

### Cargo.toml dev-dependencies for testing

```toml
[dev-dependencies]
pretty_assertions = "1"
rstest = "0.23"
proptest = "1"
mockall = "0.13"
tokio = { version = "1", features = ["test-util", "macros", "rt-multi-thread"] }
wiremock = "0.6"
insta = "1"
```

═══════════════════════════════════════════════════════════════════════════════
9. DOCKER / GIT EXCLUSIONS
═══════════════════════════════════════════════════════════════════════════════

.gitignore must exclude build and test artifacts (NOT the tests/ folder itself):
```
target/
coverage/
*.profraw
*.profdata
tarpaulin-report.html
lcov.info
```

Note on `Cargo.lock`:
- **Include** `Cargo.lock` in version control for binary crates and applications.
- **Exclude** `Cargo.lock` for library crates (add to `.gitignore`).

.dockerignore must exclude tests AND artifacts from the build context:
```
target/
tests/
benches/
examples/
coverage/
*.profraw
*.profdata
tarpaulin-report.html
lcov.info
.github/
```

═══════════════════════════════════════════════════════════════════════════════
10. WORKFLOW CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Follow this order:

□ Phase 1 — Sanitize
  1. List all source files with `#[cfg(test)]` modules and all files in `tests/`
  2. For each: verify imports resolve to existing types and functions
  3. Delete orphaned test functions (references to deleted/renamed items)
  4. Fix stale tests (wrong field names, changed signatures, removed variants)
  5. Add missing copyright headers
  6. Compile-check all tests: `cargo check --tests && cargo clippy --tests`

□ Phase 2 — Identify gaps
  7. List all public types and functions in `src/`
  8. List all existing tests (unit + integration + doc-tests)
  9. Produce a gap matrix: public item → has test? → coverage gaps

□ Phase 3 — Write tests
  10. For each uncovered item, write tests following the conventions above
  11. Prioritize: pure functions → models/types → trait impls → services → async handlers
  12. Compile-check each new test immediately: `cargo test --no-run`

□ Phase 4 — Validate
  13. Run full suite: `cargo test -- --nocapture` (for visibility into test output)
  14. Fix any failures
  15. Run with coverage: `cargo tarpaulin --out Html --output-dir coverage`
  16. Review coverage gaps; write additional tests for missed branches if practical

□ Phase 5 — Project hygiene
  17. Ensure all `#[cfg(test)]` modules are at the bottom of source files
  18. Ensure `Cargo.toml` has `[dev-dependencies]` for test crates
  19. Ensure `.gitignore` excludes `target/`, `coverage/`, `*.profraw`
  20. Ensure `.dockerignore` excludes `tests/`, `target/`, `coverage/`, and test artifacts

═══════════════════════════════════════════════════════════════════════════════
## Rust-Specific Test Patterns
═══════════════════════════════════════════════════════════════════════════════

### Doc-Tests

Write runnable examples in `///` doc comments — they are compiled and tested
automatically by `cargo test`:

```rust
/// Parses a key-value pair from a string.
///
/// # Examples
///
/// ```
/// use my_crate::parse_pair;
///
/// let (key, value) = parse_pair("name=Alice").unwrap();
/// assert_eq!(key, "name");
/// assert_eq!(value, "Alice");
/// ```
///
/// ```
/// use my_crate::parse_pair;
///
/// assert!(parse_pair("invalid").is_err());
/// ```
pub fn parse_pair(input: &str) -> Result<(&str, &str), ParseError> { ... }
```

Use `# ` prefix to hide setup lines from rendered docs while keeping them in the test:
```rust
/// ```
/// # use my_crate::Config;
/// let config = Config::default();
/// assert!(config.is_valid());
/// ```
```

### `#[cfg(test)]` Gating

Always gate test modules and test-only imports:
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use pretty_assertions::assert_eq;

    // tests ...
}
```

This ensures test code is excluded from release builds and does not bloat the binary.

### Async Tests

Use `#[tokio::test]` for async test functions:
```rust
#[tokio::test]
async fn test_fetch_data_returns_expected_payload() {
    let service = TestService::new().await;
    let result = service.fetch("key").await;
    assert_eq!(result.unwrap(), "value");
}
```

For `actix-web` handlers:
```rust
#[actix_web::test]
async fn test_health_endpoint_returns_ok() {
    let app = actix_web::test::init_service(
        App::new().route("/health", web::get().to(health_handler))
    ).await;

    let req = actix_web::test::TestRequest::get().uri("/health").to_request();
    let resp = actix_web::test::call_service(&app, req).await;
    assert_eq!(resp.status(), 200);
}
```

### Property-Based Testing

Use `proptest` for generative testing:
```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_parse_roundtrip(s in "[a-zA-Z0-9]{1,100}") {
        let encoded = encode(&s);
        let decoded = decode(&encoded).unwrap();
        assert_eq!(decoded, s);
    }

    #[test]
    fn test_sort_preserves_length(mut v in prop::collection::vec(any::<i32>(), 0..100)) {
        let original_len = v.len();
        v.sort();
        assert_eq!(v.len(), original_len);
    }
}
```

### Test Fixtures with `rstest`

Use `rstest` for parameterized tests and fixtures:
```rust
use rstest::{fixture, rstest};

#[fixture]
fn config() -> Config {
    Config::builder()
        .database_url("postgres://test")
        .build()
}

#[rstest]
fn test_config_is_valid(config: Config) {
    assert!(config.validate().is_ok());
}

#[rstest]
#[case("hello@example.com", true)]
#[case("not-an-email", false)]
#[case("", false)]
fn test_validate_email(#[case] input: &str, #[case] expected: bool) {
    assert_eq!(is_valid_email(input), expected);
}
```

### Snapshot Testing with `insta`

Use `insta` for snapshot/golden-file testing:
```rust
use insta::assert_snapshot;
use insta::assert_json_snapshot;

#[test]
fn test_error_display_format() {
    let err = MyError::NotFound { id: "abc".into() };
    assert_snapshot!(err.to_string(), @"item not found: abc");
}

#[test]
fn test_api_response_structure() {
    let response = build_response(&test_data());
    assert_json_snapshot!(response);
}
```

Run `cargo insta review` to accept/reject snapshot changes interactively.

### `#[ignore]` for Slow or Flaky Tests

Mark slow or environment-dependent tests with `#[ignore]`:
```rust
#[test]
#[ignore] // requires external database; run with `cargo test -- --ignored`
fn test_database_migration() {
    // ...
}
```

Run ignored tests explicitly: `cargo test -- --ignored`
Run all tests including ignored: `cargo test -- --include-ignored`

### Custom Test Harness

For specialized test runners, disable the default harness in `Cargo.toml`:
```toml
[[test]]
name = "custom_test"
path = "tests/custom_test.rs"
harness = false
```

This allows you to define your own `fn main()` in the test file for custom setup/teardown.
