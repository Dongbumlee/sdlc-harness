---
name: sdlc-code-quality
description: >-
  Review and enforce code quality standards for Python, TypeScript, React,
  Java, C#, Go, and Rust following SDLC quality instruction files. Use when
  performing code quality reviews, cleaning up code, or enforcing naming and
  documentation standards. Triggers on code quality, code review, naming,
  docstring, dead code, or comment cleanup requests.
---

# SDLC Code Quality Review

## When to use

- Reviewing code for naming, documentation, and style compliance
- Cleaning up dead code, redundant comments, or stale references
- Enforcing copyright headers and docstring standards
- Performing systematic quality passes on folders

## Step 1: Load quality best practices

Load from awesome-copilot:

```
mcp_awesome-copil_load_instruction(
  filename: "self-explanatory-code-commenting",
  mode: "instructions"
)
```

```
mcp_awesome-copil_load_instruction(
  filename: "performance-optimization",
  mode: "instructions"
)
```

```
mcp_awesome-copil_load_instruction(
  filename: "object-calisthenics",
  mode: "instructions"
)
```

## Step 2: Identify the language and load SDLC rules

Read the applicable quality instruction file:

| Language | Instruction File |
|---|---|
| Python | `.github/instructions/code-quality-py.instructions.md` |
| TypeScript | `.github/instructions/code-quality-ts.instructions.md` |
| React/TSX | `.github/instructions/code-quality-tsx.instructions.md` |
| Java | `.github/instructions/code-quality-java.instructions.md` |
| C# | `.github/instructions/code-quality-csharp.instructions.md` |
| Go | `.github/instructions/code-quality-go.instructions.md` |
| Rust | `.github/instructions/code-quality-rust.instructions.md` |

These files auto-apply when editing files of the matching type, but load them
explicitly during quality reviews for the full checklist.

## Step 3: Quality checklist

### Copyright & documentation
- [ ] Every file has the Microsoft copyright header
- [ ] Module-level docstrings describe purpose and role in system
- [ ] Public classes have structured docstrings (summary, responsibilities, attributes)
- [ ] Public methods have docstrings (summary, args, returns, raises)
- [ ] Simple one-liners get single-line docstrings

### Naming
- [ ] Clear, intention-revealing names (no unexplained abbreviations)
- [ ] Async methods suffixed with `Async` where idiomatic
- [ ] Test files mirror source structure:
  - Python: `src/utils/foo.py` → `tests/unit/utils/test_foo.py`
  - Java: `src/main/java/.../Foo.java` → `src/test/java/.../FooTest.java`
  - C#: `src/Project/Foo.cs` → `tests/Project.Tests/FooTests.cs`
- [ ] Test classes use `TestPascalCase`, test methods use language-appropriate convention

### Comment cleanup — REMOVE these
- Redundant inline comments that restate the code
- Banner comments / section dividers (`#####`)
- Commented-out code (dead imports, old logic)
- Heritage comments referencing deleted files
- Placeholder comments for unimplemented intent
- "For demonstration" / "Here you would typically" comments

### Comment cleanup — KEEP these
- Actionable TODOs with clear intent
- Non-obvious "why" comments explaining design decisions
- Contract/protocol comments about external API behavior

### Dead code
- [ ] No unused imports / unused usings
- [ ] No `pass` in `else` blocks (Python), empty catch blocks (Java/C#)
- [ ] No redundant assignments (`x = x`)
- [ ] No duplicate imports (module-level AND inside function)

### Type safety
- [ ] Python: proper type annotations on public functions
- [ ] TypeScript: strict mode, no `any` unless justified
- [ ] React: typed props interfaces, no inline type assertions
- [ ] Java: no raw generic types, use `Optional<T>` for nullable returns
- [ ] C#: nullable reference types enabled, `?` annotations on nullable members
- [ ] Go: exported names PascalCase, error values always checked, `go vet` clean
- [ ] Rust: no `unwrap()` in production, proper `Result<T,E>` propagation, `clippy` clean

### Error handling
- [ ] Uses project's logging abstraction (not `print()`)
- [ ] Includes correlation IDs in log context where applicable
- [ ] No bare `except:` — always catch specific exceptions

## Step 4: Compile-check

After editing each folder:

- **Python:** `python -m py_compile <file>` on every edited file
- **TypeScript:** `npx tsc --noEmit` to verify type correctness
- **React:** `npx tsc --noEmit` + verify no ESLint errors
- **Java:** `mvn compile -q` (Maven) or `gradle compileJava` (Gradle)
- **C#:** `dotnet build --no-restore -q`
- **Go:** `go build ./...` and `go vet ./...`
- **Rust:** `cargo check` and `cargo clippy`

## Working process for quality passes

1. List the directory tree of the target folder
2. Read all source files in the folder
3. Create a TODO list (one item per file + compile-check)
4. Edit files, marking each TODO complete
5. Compile-check all edited files
6. Move to the next folder

## Output format

Return findings as:
- **Critical**: Missing copyright headers, no docstrings on public API
- **Important**: Dead code, poor naming, missing type annotations
- **Suggestion**: Minor readability improvements, comment cleanup
- **Positive**: Well-written, clean code aspects
