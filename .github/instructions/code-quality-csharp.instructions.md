---
description: "Use when writing, reviewing, or refactoring C# code. Enforces copyright headers, XML documentation, naming conventions, using organization, dead code removal, and nullable reference types."
applyTo: '**/*.cs'
---
# Systematic Code-Quality Pass Instructions for C# Codebase

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**
> as defined in `.github/SDLC-with-Copilot-and-Azure.md`. It auto-applies when Copilot edits C# files.

You are performing a systematic code-quality pass on a C# codebase. Work through every folder one at a time. For each C# file, apply ALL of the following rules, then compile-check every edited file before moving to the next folder.

## 1. Copyright & File-Level Documentation
- Every `.cs` file must start with:
  ```csharp
  // Copyright (c) Microsoft Corporation.
  // Licensed under the MIT License.
  ```
- Immediately after, include the namespace and any file-level XML documentation on the primary type.
- The primary type's `<summary>` must:
  - Describe what the type does in 1-2 sentences.
  - Mention its role in the broader system (e.g., which service layer, what it depends on).
  - NOT contain generic filler like "This class provides utilities for…"

## 2. Namespace Organization
- Prefer file-scoped namespaces (`namespace MyApp.Services;`) over block-scoped namespaces.
- Namespace must match the folder path relative to the project root
  (e.g., `src/MyApp/Services/ClaimProcessor.cs` → `namespace MyApp.Services;`).
- One primary type per file. The file name must match the type name (e.g., `ClaimProcessor.cs` → `class ClaimProcessor`).
- Organize `using` directives at the top of the file, outside the namespace:
  ```csharp
  using System;
  using System.Collections.Generic;
  using Microsoft.Extensions.Logging;
  using MyApp.Models;
  ```
- Order: `System.*` → `Microsoft.*` → third-party → project-local. Remove unused usings.

## 3. Class / Record / Struct Documentation
- Replace generic XML doc comments with structured ones:
  ```csharp
  /// <summary>
  /// One-line summary of the type's purpose.
  /// </summary>
  /// <remarks>
  /// <para>Responsibilities:</para>
  /// <list type="number">
  ///   <item>First responsibility.</item>
  ///   <item>Second responsibility.</item>
  /// </list>
  /// </remarks>
  /// <example>
  /// <code>
  /// var processor = new ClaimProcessor(logger, repository);
  /// await processor.ProcessAsync(claim);
  /// </code>
  /// </example>
  ```
- For records and DTOs, document all properties with `<summary>` tags.

## 4. Method / Property Documentation
- Every public and non-trivial private method must have XML documentation.
- Use this structure:
  ```csharp
  /// <summary>
  /// One-line summary of what the method does.
  /// </summary>
  /// <param name="claimId">The unique identifier for the claim to process.</param>
  /// <param name="options">Processing options controlling validation behavior.</param>
  /// <returns>The processed claim result with validation status.</returns>
  /// <exception cref="ArgumentNullException">When <paramref name="claimId"/> is null.</exception>
  /// <exception cref="InvalidOperationException">When the claim is already processed.</exception>
  ```
- Simple one-line methods (getters, delegates) get a single `<summary>` tag.
- Include `<remarks>` with numbered steps only for complex multi-step methods.

## 5. Comment Cleanup — REMOVE These
- **Redundant inline comments** that just restate the code:
  `// Create new claim process entry` above `var claimProcess = new ClaimProcess(...);`
- **Banner comments** / section dividers:
  `////////////////////////////////////////////////////////////`
  `// Initialize AgentFrameworkHelper and add it to the app  //`
  `////////////////////////////////////////////////////////////`
- **Commented-out code** (dead imports, old logic, disabled features).
- **Heritage/provenance comments** referencing deleted files:
  `// Replaces CreateQuietLogger() from QuietLogging.cs`
- **Placeholder comments** that describe unimplemented intent:
  `// Placeholder for document processing logic`
- **"For demonstration" / "Here you would typically"** comments.

## 6. Comment Cleanup — KEEP These
- **Actionable TODOs** with clear intent: `// TODO: Make configurable via IOptions`
- **Non-obvious "why" comments** that explain a design decision:
  `// Avoid unbounded growth on very chatty endpoints.`
- **Contract/protocol comments** that document external API behavior:
  `// Image files bypass the 'extract' step.`
- **Suppression justifications**: `// Suppressed because X requires this pattern`

## 7. Fix Stale References
- Search for outdated terminology (old project names, old class names, old pipeline descriptions) and correct them to match the current code.
- Update XML doc `<see cref="..."/>` and `<paramref name="..."/>` references to match current type/member names.

## 8. Remove Dead Code
- Delete unused `using` directives.
- Delete unreachable code after `return`, `throw`, or unconditional `break`.
- Delete empty `catch` blocks that swallow exceptions without logging or rethrowing.
- Delete members marked with `[Obsolete]` that have no remaining callers.
- Delete redundant assignments like `claimId = claimId;`.
- Delete `#region` / `#endregion` wrappers (they hide complexity; remove the markers, keep the code).

## 9. Compile-Check
- After finishing each folder, run `dotnet build --no-restore -q` on the affected project.
- Fix any errors or warnings before proceeding to the next folder.
- Treat all nullable reference type warnings as errors.

## 10. C#-Specific Quality Rules

### Nullable Reference Types
- Projects must enable `<Nullable>enable</Nullable>` in the `.csproj`.
- Use `?` annotations to express nullability intent explicitly.
- Prefer `ArgumentNullException.ThrowIfNull(param)` over manual null checks (.NET 6+).
- Never use the null-forgiving operator (`!`) to suppress warnings without a justifying comment.

### Records vs Classes
- Prefer `record` or `record struct` for DTOs, value objects, and immutable data carriers.
- Use `class` for types with mutable state, complex behavior, or identity semantics.
- Prefer `required` properties or primary constructors to enforce initialization.

### Async/Await
- Suffix async methods with `Async` (e.g., `ProcessClaimAsync`).
- Use `ConfigureAwait(false)` in library code (non-UI, non-controller methods).
- Never use `async void` except for event handlers.
- Prefer `ValueTask<T>` over `Task<T>` when the result is frequently synchronous.
- Never call `.Result` or `.Wait()` on tasks — always `await`.

### Dependency Injection
- Use constructor injection for required dependencies.
- Use `IOptions<T>` / `IOptionsSnapshot<T>` / `IOptionsMonitor<T>` for configuration.
- Register services with the narrowest lifetime: `Transient` → `Scoped` → `Singleton`.
- Prefer interface-based dependencies (`ILogger<T>`, `IRepository`, `IHttpClientFactory`).

### Naming Conventions
| Element              | Convention                          | Example                        |
|----------------------|-------------------------------------|--------------------------------|
| Public member        | PascalCase                          | `ProcessClaim`, `ClaimId`      |
| Private field        | `_camelCase`                        | `_logger`, `_repository`       |
| Local variable       | camelCase                           | `claimResult`, `isValid`       |
| Constant             | PascalCase                          | `MaxRetryCount`                |
| Interface            | `I` prefix + PascalCase             | `IClaimRepository`             |
| Generic type param   | `T` prefix                          | `TEntity`, `TResult`           |
| Async method         | Suffix with `Async`                 | `GetClaimsAsync`               |
| Boolean property     | `Is`, `Has`, `Can`, `Should` prefix | `IsValid`, `HasPermission`     |

## Working Process
1. List the directory tree of the target folder.
2. Read all C# files in the folder.
3. Create a TODO list for the folder (one item per file + one for compile-check).
4. Edit files, marking each TODO as you go.
5. Compile-check all edited files with `dotnet build --no-restore -q`.
6. Move to the next folder.

Start with the folder I specify and work through it completely before asking what to do next.
