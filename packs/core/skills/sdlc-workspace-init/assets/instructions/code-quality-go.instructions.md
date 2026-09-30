---
description: "Use when writing, reviewing, or refactoring Go code. Enforces copyright headers, GoDoc comments, naming conventions, package organization, dead code removal, and idiomatic Go patterns."
applyTo: '**/*.go'
---
# Systematic Code-Quality Pass Instructions for Go Codebase

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**
> as defined in `.github/SDLC-with-Copilot-and-Azure.md`. It auto-applies when Copilot edits Go files.

You are performing a systematic code-quality pass on a Go codebase. Work through every package one at a time. For each Go file, apply ALL of the following rules, then compile-check every edited file before moving to the next package.

## 1. Copyright Header

- Every `.go` file must start with:
  ```go
  // Copyright (c) Microsoft Corporation.
  // Licensed under the MIT License.
  ```
- The copyright header must appear before the `package` declaration.

## 2. Package Documentation

- Every package must have a `doc.go` file containing:
  ```go
  // Copyright (c) Microsoft Corporation.
  // Licensed under the MIT License.

  // Package <name> provides <one-line summary>.
  //
  // <Additional paragraph describing the package's role in the broader system,
  // what it depends on, and which pipeline stage it supports.>
  package <name>
  ```
- Package names must be short, lowercase, single-word. No underscores, no mixedCaps.
- The package comment must NOT contain generic filler like "Package util provides utility functions."

## 3. Type / Struct Documentation

- Every exported type must have a GoDoc comment directly above its declaration:
  ```go
  // Server represents an HTTP server that handles claim processing requests.
  //
  // It manages connection pooling, request routing, and graceful shutdown.
  // The zero value is not usable; create instances with NewServer.
  type Server struct {
      // addr is the listen address in host:port format.
      addr string
      // handler routes incoming requests to the appropriate processor.
      handler http.Handler
  }
  ```
- The comment must start with the type name.
- For structs with exported fields, document each field with an inline `//` comment.
- For interfaces, document each method's contract:
  ```go
  // Processor handles document processing operations.
  type Processor interface {
      // Process processes the given document and returns the result.
      // It returns an error if the document format is unsupported.
      Process(ctx context.Context, doc *Document) (*Result, error)
  }
  ```

## 4. Function / Method Documentation

- Every exported function and method must have a GoDoc comment.
- The comment must start with the function name:
  ```go
  // NewServer creates a Server with the given address and handler.
  // If handler is nil, http.DefaultServeMux is used.
  //
  // The server is configured with sensible defaults for read/write timeouts
  // and maximum header size. Use WithOption functions to customize.
  func NewServer(addr string, handler http.Handler) *Server {
  ```
- Document parameters and return values in prose, not with tags.
- Simple one-line functions (getters, delegates) get a single-line comment.
- Document error conditions: when and what errors are returned.

## 5. Comment Cleanup — REMOVE These

- **Redundant inline comments** that restate the code:
  `// create a new server` above `srv := NewServer(addr, handler)`
- **Banner comments** / section dividers:
  `////////////////////////////////////////////////////////////////`
  `// ============ Initialize Server ============ //`
- **Commented-out code** (dead imports, old logic, debug prints).
- **Heritage/provenance comments** referencing deleted files:
  `// Replaces initLogger() from old_logging.go`
- **Placeholder comments** that describe unimplemented intent:
  `// TODO: implement document processing logic` (with no actual plan)
- **"For demonstration" / "Here you would typically"** comments.

## 6. Comment Cleanup — KEEP These

- **Actionable TODOs** with clear intent: `// TODO: make configurable via environment variable`
- **Non-obvious "why" comments** that explain a design decision:
  `// Limit to 100 concurrent requests to avoid exhausting file descriptors.`
- **Contract/protocol comments** that document external API behavior:
  `// Image files bypass the extract step per the pipeline spec.`
- **Build constraint comments**: `//go:build integration`
- **Compiler directive comments**: `//go:generate`, `//nolint:`, `//go:embed`

## 7. Fix Stale References

- Search for outdated terminology (old project names, old type names, old package paths) and correct them to match the current code.
- Update any comments referencing moved or renamed packages.

## 8. Remove Dead Code

- Delete unused imports (the Go compiler enforces this, but catch them proactively).
- Delete unused variables and constants.
- Delete unreachable code after `return`, `panic`, or `os.Exit`.
- Delete empty function bodies that serve no purpose.
- Delete unused type declarations and unexported functions with no callers.

## 9. Compile-Check

- After finishing each package, run:
  ```
  go build ./...
  go vet ./...
  ```
- Fix any errors before proceeding to the next package.

## 10. Error Handling

- Always check returned errors. Never assign an error to `_` unless explicitly justified with a comment:
  ```go
  // Safe to ignore: Close on read-only file cannot fail meaningfully.
  _ = f.Close()
  ```
- Wrap errors with context using `fmt.Errorf`:
  ```go
  if err != nil {
      return fmt.Errorf("failed to open config %s: %w", path, err)
  }
  ```
- Use `errors.Is` and `errors.As` for error inspection, not string matching.
- Define sentinel errors as package-level variables: `var ErrNotFound = errors.New("not found")`
- Return errors rather than logging and continuing — let the caller decide.

## 11. Interfaces

- Define interfaces where they are used (consumer side), not where they are implemented.
- Keep interfaces small — 1 to 3 methods. Prefer composing small interfaces over large ones.
- Accept interfaces, return concrete types:
  ```go
  // Good: accepts interface, returns concrete
  func NewService(repo Repository) *Service { ... }

  // Avoid: returning an interface
  func NewService(repo Repository) Service { ... }
  ```
- Name single-method interfaces with the `-er` suffix: `Reader`, `Writer`, `Processor`.

## 12. Naming Conventions

- **Exported** identifiers: `PascalCase` — `ProcessDocument`, `ClaimStatus`
- **Unexported** identifiers: `camelCase` — `processDocument`, `claimStatus`
- **No underscores** in Go names (except in test function names like `Test_helper`).
- **Acronyms** are all caps: `HTTP`, `URL`, `ID`, `API`, `JSON`, `SQL`.
  - `httpServer` (unexported), `HTTPServer` (exported), `userID` (unexported), `UserID` (exported).
- **Receiver names**: short (1-2 letters), consistent across methods: `func (s *Server) Start()`.
- **Local variables**: prefer short names in small scopes (`i`, `n`, `err`), descriptive in larger scopes.

## 13. Zero Values and Pointers

- Design structs so that the zero value is useful when possible.
- Use pointer fields only when `nil` is a meaningful state distinct from the zero value.
- Document when a struct's zero value is NOT usable:
  ```go
  // Server manages HTTP connections. The zero value is not usable;
  // create instances with NewServer.
  type Server struct { ... }
  ```

## 14. Concurrency

- Document goroutine safety on every exported type:
  ```go
  // Cache is safe for concurrent use by multiple goroutines.
  type Cache struct { ... }
  ```
- Use channels for communication between goroutines, mutexes for protecting shared state.
- Always propagate `context.Context` as the first parameter:
  ```go
  func (s *Service) Process(ctx context.Context, req *Request) (*Response, error)
  ```
- Never start goroutines without a clear shutdown mechanism (context cancellation, done channels, or `sync.WaitGroup`).
- Prefer `sync.Once` for one-time initialization over manual mutex/flag patterns.

## 15. Project Layout

- Follow the standard Go project layout:
  ```
  ProjectRoot/
  ├── cmd/                  ← main applications
  │   └── server/
  │       └── main.go
  ├── internal/             ← private packages (not importable by external modules)
  │   ├── handler/
  │   ├── service/
  │   ├── repository/
  │   └── model/
  ├── pkg/                  ← public library packages (if needed)
  ├── go.mod
  ├── go.sum
  └── Makefile
  ```
- Use `internal/` for packages that should not be imported by other modules.
- Each `cmd/<app>/main.go` should be minimal — parse flags, wire dependencies, call `Run()`.

## 16. Linting

- Use `golangci-lint run` as the standard linter.
- Fix all linter warnings before committing.
- Do not disable linter rules without a `//nolint:` comment explaining why.

## Working Process

1. List the directory tree of the target package.
2. Read all Go files in the package.
3. Create a TODO list for the package (one item per file + one for compile-check).
4. Edit files, marking each TODO as you go.
5. Compile-check all edited files with `go build ./...` and `go vet ./...`.
6. Move to the next package.

Start with the package I specify and work through it completely before asking what to do next.
