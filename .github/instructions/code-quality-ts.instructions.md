---
description: "Use when writing, reviewing, or refactoring TypeScript code. Enforces copyright headers, JSDoc comments, naming conventions, import organization, strict typing, and dead code removal."
applyTo: '**/*.ts'
---
# Systematic Code-Quality Pass Instructions for TypeScript Codebase

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**
> as defined in `.github/SDLC-with-Copilot-and-Azure.md`. It auto-applies when Copilot edits TypeScript files.

You are performing a systematic code-quality pass on a TypeScript codebase. Work through every folder one at a time. For each TypeScript file, apply ALL of the following rules, then type-check every edited file before moving to the next folder.

## 1. Copyright & Module Header

- Every `.ts` file must start with:
  ```
  // Copyright (c) Microsoft Corporation.
  // Licensed under the MIT License.
  ```
- Immediately after, add or verify a JSDoc module description:
  ```ts
  /**
   * Brief description of what this module does.
   * Mention its role in the broader system.
   * @module module-name
   */
  ```
- Do NOT use generic filler like "This module provides utilities for…".

## 2. Barrel Files (`index.ts`)

- If the barrel file only re-exports, add the copyright header and a module-level JSDoc listing exported members with one-line descriptions.
- Prefer named exports over `export default`.
- Keep barrel files thin — re-exports only, no logic.

## 3. Interface & Type Docstrings

- Every exported `interface` and `type` must have a JSDoc comment:
  ```ts
  /**
   * One-line summary.
   *
   * @remarks
   * Additional context about usage or constraints.
   */
  export interface MyInterface {
    /** Description of this property. */
    propertyName: string;
  }
  ```
- For union types or mapped types, document each variant or the mapping logic.

## 4. Enum Docstrings

- Every exported `enum` must have a JSDoc comment describing its purpose.
- Each member should have an inline comment if the name is not self-explanatory:
  ```ts
  /** Status codes for claim processing pipeline. */
  export enum ClaimStatus {
    /** Initial state before validation. */
    Pending = "PENDING",
    /** Successfully processed and stored. */
    Completed = "COMPLETED",
  }
  ```

## 5. Class Docstrings

- Replace generic class docstrings with structured ones:
  ```ts
  /**
   * One-line summary.
   *
   * @remarks
   * Responsibilities:
   * 1. First responsibility.
   * 2. Second responsibility.
   */
  export class MyService {
  ```
- Document all public properties with inline JSDoc.

## 6. Function & Method Docstrings

- Every exported function and every public/protected class method must have a JSDoc comment.
- Use this structure:
  ```ts
  /**
   * One-line summary.
   *
   * @param paramName - Description.
   * @returns Description of return value.
   * @throws {ErrorType} When condition.
   *
   * @example
   * ```ts
   * const result = myFunction("input");
   * ```
   */
  ```
- Simple one-line functions (getters, delegates) may use a single-line JSDoc: `/** Returns the active session ID. */`

## 7. Naming Conventions

| Element              | Convention             | Example                         |
|----------------------|------------------------|---------------------------------|
| File (module)        | kebab-case             | `claim-processor.ts`            |
| File (class)         | kebab-case             | `claim-service.ts`              |
| Interface            | PascalCase             | `ClaimRequest`                  |
| Type alias           | PascalCase             | `ProcessingResult`              |
| Enum                 | PascalCase             | `ClaimStatus`                   |
| Enum member          | PascalCase             | `Pending`, `Completed`          |
| Class                | PascalCase             | `ClaimService`                  |
| Function / method    | camelCase              | `processClaimAsync`             |
| Variable / parameter | camelCase              | `claimId`                       |
| Constant             | UPPER_SNAKE_CASE       | `MAX_RETRY_COUNT`               |
| Private member       | prefixed with `_`      | `_internalState`                |
| Generic type param   | Single uppercase letter | `T`, `K`, `V`                   |

- Async functions: suffix with `Async` where it aids clarity at call sites.
- Avoid unexplained abbreviations.

## 8. Comment Cleanup — REMOVE These

- **Redundant inline comments** that restate the code:
  `// Create a new claim object` above `const claim = new Claim(...)`.
- **Banner comments** / section dividers using ASCII art or repeated characters.
- **Commented-out code** (dead imports, old logic, console.log statements).
- **Heritage/provenance comments** referencing deleted files or old implementations.
- **Placeholder comments**: `// TODO: implement this`, `// Placeholder for…`.
- **"For demonstration" / "Here you would typically"** comments.
- **Obvious type annotations in comments** when TypeScript already provides them.

## 9. Comment Cleanup — KEEP These

- **Actionable TODOs** with clear intent: `// TODO: Make configurable via environment variable`.
- **Non-obvious "why" comments** that explain a design decision:
  `// Rate-limit to prevent exceeding Azure throttling threshold.`
- **Contract/protocol comments** that document external API behavior:
  `// Azure returns 409 when the resource already exists; treat as success.`
- **Type assertion justifications**: `// Safe cast — API guarantees this shape after v2.`
- **`@ts-expect-error` / `@ts-ignore`** must always include an explanation comment on the same or previous line.

## 10. Import Organization

- Order imports in this sequence, separated by blank lines:
  1. Node.js built-in modules (`node:fs`, `node:path`)
  2. Third-party packages (`@azure/*`, `zod`, `winston`)
  3. Internal/project modules (relative imports)
- Use `type` imports where possible: `import type { MyInterface } from './types';`
- Remove unused imports.
- Prefer named imports over namespace imports (`import * as`).

## 11. Strict TypeScript Practices

- Do NOT use `any`. Prefer `unknown` with type narrowing, or define a proper type.
- Do NOT use non-null assertions (`!`) without a justifying comment.
- Prefer `readonly` for properties that should not be mutated after construction.
- Prefer `const` over `let` where reassignment does not occur.
- Use discriminated unions over type casting for variant data.
- Use `satisfies` operator for type-safe object literals where appropriate.

## 12. Error Handling

- Use typed error classes or error codes — do not throw bare strings.
- Always include contextual information in error messages (IDs, operation names).
- For async code, prefer `try/catch` over `.catch()` for readability.
- Log errors through the project's logger abstraction, not `console.error`.

## 13. Remove Dead Code

- Delete unused imports.
- Delete unused variables, parameters (prefix with `_` if required by interface contract).
- Delete empty `else` blocks.
- Delete duplicate type definitions.
- Delete unreachable code after `return`, `throw`, `break`, or `continue`.

## 14. Type-Check

- After finishing each folder, run `npx tsc --noEmit` on the project.
- Fix any type errors before proceeding to the next folder.

## Working Process

1. List the directory tree of the target folder.
2. Read all TypeScript files in the folder.
3. Create a TODO list for the folder (one item per file + one for type-check).
4. Edit files, marking each TODO as you go.
5. Type-check all edited files.
6. Move to the next folder.
