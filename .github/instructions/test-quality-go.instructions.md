---
description: "Use when writing or reviewing Go tests. Enforces table-driven tests, naming conventions, mocking patterns, subtests, and test configuration."
applyTo: '**/*_test.go'
---
# Test Quality Instructions for Go

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**
> as defined in `.github/SDLC-with-Copilot-and-Azure.md`. It auto-applies when Copilot edits Go test files.

You are a senior Go test engineer. Your job is to audit, sanitize, and write
comprehensive unit tests for a Go project that follows these conventions.

═══════════════════════════════════════════════════════════════════════════════
1. PROJECT LAYOUT
═══════════════════════════════════════════════════════════════════════════════

Go tests live alongside source files in the same package directory:

    ProjectRoot/
    ├── cmd/                      ← main applications
    │   └── server/
    │       ├── main.go
    │       └── main_test.go
    ├── internal/                 ← private packages
    │   ├── handler/
    │   │   ├── handler.go
    │   │   ├── handler_test.go   ← white-box tests (same package)
    │   │   └── handler_ext_test.go  ← black-box tests (package handler_test)
    │   ├── service/
    │   │   ├── service.go
    │   │   └── service_test.go
    │   ├── repository/
    │   │   ├── repository.go
    │   │   └── repository_test.go
    │   └── model/
    │       ├── model.go
    │       └── model_test.go
    ├── testdata/                  ← test fixtures (automatically ignored by go tool)
    │   ├── golden/
    │   └── fixtures/
    ├── go.mod
    ├── go.sum
    └── Makefile

Key rules:
- Test files MUST be named `*_test.go` and live in the same directory as the source.
- White-box tests use the same package name for access to unexported identifiers.
- Black-box tests use the `_test` package suffix (e.g., `package handler_test`) to test only the public API.
- The `testdata/` directory is for fixtures and golden files — the `go` tool ignores it.
- Integration tests use the `//go:build integration` build tag at the top of the file.

═══════════════════════════════════════════════════════════════════════════════
2. TEST SANITIZATION (run first, before writing new tests)
═══════════════════════════════════════════════════════════════════════════════

Before writing any new tests, audit all existing test files:

a) FIND ORPHANED TESTS — tests that reference types, functions, or packages that
   no longer exist. For every test file, verify that every reference resolves to
   a real source declaration. Delete any test whose references are entirely broken.

b) FIND STALE ASSERTIONS — tests whose assertions reference renamed fields,
   changed method signatures, or removed struct fields.
   Fix these to match the current source code.

c) COMPILE-CHECK every remaining test file:
       go build ./...
       go vet ./...
   Fix any errors or vet warnings.

d) RUN TARGETED TESTS to verify they pass:
       go test -run TestName ./pkg/...
   Fix any failures before proceeding.

e) ADD MISSING COPYRIGHT HEADERS to any file that lacks one.

═══════════════════════════════════════════════════════════════════════════════
3. FILE FORMAT CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

Every test file must follow this exact structure:

    // Copyright (c) Microsoft Corporation.
    // Licensed under the MIT License.

    package <name>  // or <name>_test for black-box tests

    import (
        // Standard library imports
        "context"
        "testing"

        // External imports
        "github.com/stretchr/testify/assert"
        "github.com/stretchr/testify/require"

        // Internal imports
        "github.com/org/project/internal/model"
    )

    // ── Section Name ────────────────────────────────────────────────────────

    func TestFunctionName_scenario(t *testing.T) {
        ...
    }

Rules:
- ALWAYS include the 2-line copyright header.
- ALWAYS group imports: stdlib, external, internal — separated by blank lines.
- Use ASCII banner comments to separate logical test sections.
- Import `testing` in every test file (required by the test framework).

═══════════════════════════════════════════════════════════════════════════════
4. NAMING CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

| Element          | Convention                          | Example                              |
|------------------|-------------------------------------|--------------------------------------|
| Test file        | `<source>_test.go`                  | `handler_test.go`                    |
| Test function    | `Test<Function>_<scenario>`         | `TestNewServer_nilHandler`           |
| Subtest name     | descriptive lowercase with spaces   | `t.Run("returns error on timeout")`  |
| Helper function  | unexported, call `t.Helper()`       | `func newTestServer(t *testing.T)`   |
| Benchmark        | `Benchmark<Function>`               | `BenchmarkProcess_largePayload`      |
| Example          | `Example<Function>`                 | `ExampleNewServer`                   |
| Test fixture     | `testdata/<descriptive_name>`       | `testdata/golden/response.json`      |

Test function naming must clearly identify the unit under test:
    handler.go     → `func TestHandleRequest_validPayload(t *testing.T)`
    service.go     → `func TestProcess_contextCancelled(t *testing.T)`
    repository.go  → `func TestFindByID_notFound(t *testing.T)`

═══════════════════════════════════════════════════════════════════════════════
5. WHAT TO TEST (prioritize by testability)
═══════════════════════════════════════════════════════════════════════════════

Focus on UNIT-TESTABLE code — pure logic that can run without external services:

HIGH PRIORITY (test these thoroughly):
- Pure functions: transformations, validations, computations
- Business logic in service layer: rules, state transitions, calculations
- Model methods: constructors, serialization, validation
- Utility functions: string manipulation, URL building, config parsing
- Error paths: every returned error must have a test

MEDIUM PRIORITY (test with interfaces and mocks):
- HTTP handlers: use `httptest.NewRecorder()` and `httptest.NewRequest()`
- Middleware: test request/response modification and chain behavior
- Database layer: mock the repository interface, test query logic
- External API clients: mock the HTTP transport or use `httptest.Server`

LOW PRIORITY (skip or test only the interface):
- `main()` functions — keep them minimal and untestable-by-design
- Deep orchestration spanning multiple services
- Code that only wraps external SDK calls with no added logic

Use interfaces for dependency injection to make code testable:
    type Repository interface {
        FindByID(ctx context.Context, id string) (*Model, error)
    }

    // Service accepts the interface, making it testable with mocks.
    type Service struct {
        repo Repository
    }

═══════════════════════════════════════════════════════════════════════════════
6. MOCKING PATTERNS
═══════════════════════════════════════════════════════════════════════════════

Use these patterns in order of preference:

a) Hand-written mocks (preferred for small interfaces):
       type mockRepository struct {
           findByIDFunc func(ctx context.Context, id string) (*Model, error)
       }

       func (m *mockRepository) FindByID(ctx context.Context, id string) (*Model, error) {
           return m.findByIDFunc(ctx, id)
       }

b) `gomock` / `mockery` (for larger interfaces with many methods):
       //go:generate mockgen -source=repository.go -destination=mock_repository_test.go -package=service
       // Use generated mocks in tests with gomock controller.

c) `httptest.Server` (for HTTP client testing):
       srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
           w.WriteHeader(http.StatusOK)
           w.Write([]byte(`{"status":"ok"}`))
       }))
       defer srv.Close()
       client := NewClient(srv.URL)

d) `httptest.NewRecorder` (for HTTP handler testing):
       req := httptest.NewRequest(http.MethodGet, "/api/v1/claims", nil)
       rec := httptest.NewRecorder()
       handler.ServeHTTP(rec, req)
       assert.Equal(t, http.StatusOK, rec.Code)

e) `sqlmock` (for database testing):
       db, mock, err := sqlmock.New()
       require.NoError(t, err)
       defer db.Close()
       mock.ExpectQuery("SELECT").WillReturnRows(sqlmock.NewRows([]string{"id"}).AddRow("123"))

f) Environment variable mocking:
       t.Setenv("DATABASE_URL", "postgres://test:test@localhost/testdb")
       // t.Setenv automatically restores the original value after the test.

═══════════════════════════════════════════════════════════════════════════════
7. ASSERTION STYLE
═══════════════════════════════════════════════════════════════════════════════

Standard library `testing` package (always available):

    if got != want {
        t.Errorf("Process() = %v, want %v", got, want)
    }

    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }

`testify/assert` and `testify/require` (popular alternatives):

    assert.Equal(t, expected, actual)
    assert.NoError(t, err)
    assert.ErrorIs(t, err, ErrNotFound)
    assert.Contains(t, body, "success")
    require.NoError(t, err)  // stops test immediately on failure

`google/go-cmp` (for detailed struct comparison):

    if diff := cmp.Diff(want, got); diff != "" {
        t.Errorf("Process() mismatch (-want +got):\n%s", diff)
    }

Guidelines:
- Use `t.Fatalf` / `require` for preconditions that must hold for the rest of the test to make sense.
- Use `t.Errorf` / `assert` for assertions where you want to report all failures.
- Prefer `errors.Is` over string matching for error assertions.
- Use `cmp.Diff` for comparing complex structs — it produces readable diffs.

═══════════════════════════════════════════════════════════════════════════════
8. COVERAGE CONFIGURATION
═══════════════════════════════════════════════════════════════════════════════

Run tests with coverage:

    go test -coverprofile=coverage.out ./...
    go tool cover -html=coverage.out -o coverage.html
    go tool cover -func=coverage.out

For targeted coverage of a specific package:

    go test -coverprofile=coverage.out -covermode=atomic ./internal/service/...

Makefile targets (recommended):

    .PHONY: test test-cover test-race

    test:
    	go test ./...

    test-cover:
    	go test -coverprofile=coverage.out ./...
    	go tool cover -html=coverage.out -o coverage.html

    test-race:
    	go test -race ./...

Coverage exclusion patterns — these are NOT unit-testable and should not count against coverage:
- `cmd/*/main.go` — entry points with minimal logic
- Generated code (`*_gen.go`, `mock_*_test.go`)
- Build-tagged integration tests

═══════════════════════════════════════════════════════════════════════════════
9. DOCKER / GIT EXCLUSIONS
═══════════════════════════════════════════════════════════════════════════════

.gitignore must exclude test artifacts (NOT the test files themselves):
    coverage.out
    coverage.html
    *.test
    bin/
    vendor/  # if not vendoring

.dockerignore must exclude tests and artifacts from the build context:
    *_test.go
    testdata/
    coverage.out
    coverage.html
    *.test
    vendor/
    bin/
    .git/

═══════════════════════════════════════════════════════════════════════════════
10. WORKFLOW CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Follow this order:

□ Phase 1 — Sanitize
  1. List all `*_test.go` files across the project
  2. For each: verify that all referenced types and functions exist in the source
  3. Delete orphaned test files (references to deleted types/packages)
  4. Fix stale tests (wrong field names, changed signatures, removed methods)
  5. Add missing copyright headers
  6. Compile-check all remaining tests: `go build ./...` and `go vet ./...`

□ Phase 2 — Identify gaps
  7. List all packages under `cmd/`, `internal/`, and `pkg/`
  8. List all existing `*_test.go` files
  9. Produce a gap matrix: package → has tests? → coverage gaps

□ Phase 3 — Write tests
  10. For each uncovered package, create test files following the conventions
  11. Prioritize: models → utils → repository → service → handler → middleware
  12. Compile-check each new test file immediately after creation

□ Phase 4 — Validate
  13. Run full suite: `go test ./... -v -count=1`
  14. Fix any failures
  15. Run with coverage: `go test -coverprofile=coverage.out ./...`
  16. Run with race detector: `go test -race ./...`
  17. Review coverage gaps; write additional tests for missed branches if practical

□ Phase 5 — Project hygiene
  18. Ensure test files live alongside source files (not in a separate `tests/` directory)
  19. Ensure Makefile has `test`, `test-cover`, and `test-race` targets
  20. Ensure .gitignore excludes test artifacts
  21. Ensure .dockerignore excludes test files and artifacts from the build context

═══════════════════════════════════════════════════════════════════════════════
11. TABLE-DRIVEN TESTS
═══════════════════════════════════════════════════════════════════════════════

Always prefer table-driven tests for functions with multiple input/output combinations:

    func TestParseStatus(t *testing.T) {
        tests := []struct {
            name    string
            input   string
            want    Status
            wantErr bool
        }{
            {name: "valid active", input: "active", want: StatusActive},
            {name: "valid pending", input: "pending", want: StatusPending},
            {name: "empty string", input: "", wantErr: true},
            {name: "unknown value", input: "invalid", wantErr: true},
        }

        for _, tt := range tests {
            t.Run(tt.name, func(t *testing.T) {
                got, err := ParseStatus(tt.input)
                if tt.wantErr {
                    assert.Error(t, err)
                    return
                }
                require.NoError(t, err)
                assert.Equal(t, tt.want, got)
            })
        }
    }

Rules for table-driven tests:
- Every test case MUST have a `name` field used with `t.Run`.
- Use `tt` as the loop variable (Go convention).
- Keep test logic inside `t.Run` to get proper subtest isolation and reporting.
- For parallel table tests, capture `tt` and call `t.Parallel()`:
      t.Run(tt.name, func(t *testing.T) {
          t.Parallel()
          // ... test logic using tt
      })

═══════════════════════════════════════════════════════════════════════════════
12. GO-SPECIFIC TEST PATTERNS
═══════════════════════════════════════════════════════════════════════════════

a) TestMain — for global setup/teardown:
       func TestMain(m *testing.M) {
           // Global setup (e.g., start test database)
           code := m.Run()
           // Global teardown (e.g., stop test database)
           os.Exit(code)
       }

b) t.Helper() — mark helper functions for better error reporting:
       func newTestServer(t *testing.T, handler http.Handler) *httptest.Server {
           t.Helper()
           srv := httptest.NewServer(handler)
           t.Cleanup(func() { srv.Close() })
           return srv
       }

c) t.Parallel() — enable parallel execution for independent tests:
       func TestProcess(t *testing.T) {
           t.Parallel()
           // ... test logic
       }

d) t.Cleanup() — register cleanup functions (preferred over defer in tests):
       func TestWithTempFile(t *testing.T) {
           f, err := os.CreateTemp("", "test-*")
           require.NoError(t, err)
           t.Cleanup(func() { os.Remove(f.Name()) })
           // ... use f
       }

e) Build tags — separate integration tests from unit tests:
       //go:build integration

       package service_test

       func TestDatabaseIntegration(t *testing.T) {
           // Requires a running database
       }
   Run with: `go test -tags=integration ./...`

f) Benchmarks — measure performance:
       func BenchmarkProcess(b *testing.B) {
           svc := setupService()
           b.ResetTimer()
           for i := 0; i < b.N; i++ {
               svc.Process(context.Background(), testInput)
           }
       }

g) t.Setenv() — set environment variables scoped to the test:
       func TestConfig(t *testing.T) {
           t.Setenv("APP_PORT", "9090")
           cfg := LoadConfig()
           assert.Equal(t, 9090, cfg.Port)
       }
