---
description: "Use when writing, reviewing, or refactoring Java code. Enforces copyright headers, Javadoc, naming conventions, import organization, dead code removal, and type safety."
applyTo: '**/*.java'
---
# Systematic Code-Quality Pass Instructions for Java Codebase

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**
> as defined in `.github/SDLC-with-Copilot-and-Azure.md`. It auto-applies when Copilot edits Java files.

You are performing a systematic code-quality pass on a Java codebase. Work through every package one at a time. For each Java file, apply ALL of the following rules, then compile-check every edited file before moving to the next package.

## 1. Copyright & Class Header

- Every `.java` file must start with a copyright block comment:
  ```
  /*
   * Copyright (c) Microsoft Corporation.
   * Licensed under the MIT License.
   */
  ```
- Immediately after the package declaration and imports, add or replace the class-level Javadoc (`/** */`). It must:
  - Describe what the class does in 1–2 sentences.
  - Mention its role in the broader system (e.g., which service layer, what it depends on).
  - NOT contain generic filler like "This class provides utilities for…"

## 2. Package Documentation (`package-info.java`)

- Every non-trivial package should have a `package-info.java` file containing:
  ```java
  /*
   * Copyright (c) Microsoft Corporation.
   * Licensed under the MIT License.
   */

  /**
   * Brief description of what this package contains and its role in the system.
   *
   * <p>Key classes:
   * <ul>
   *   <li>{@link com.example.pkg.MainClass} — one-line description</li>
   *   <li>{@link com.example.pkg.HelperClass} — one-line description</li>
   * </ul>
   */
  package com.example.pkg;
  ```
- If the package already has a `package-info.java`, ensure it is up to date.

## 3. Class Javadoc

- Replace generic class Javadoc with structured documentation:
  ```java
  /**
   * One-line summary.
   *
   * <p>Responsibilities:
   * <ol>
   *   <li>First responsibility.</li>
   *   <li>Second responsibility.</li>
   * </ol>
   *
   * @author team-or-author-name
   * @see RelatedClass
   * @see AnotherRelatedClass
   */
  ```
- For records, DTOs, and entity classes, document all fields:
  ```java
  /**
   * Represents a user account in the system.
   *
   * @param id        unique identifier
   * @param email     email address used for authentication
   * @param role      authorization role assigned at creation
   */
  public record UserAccount(String id, String email, Role role) {}
  ```

## 4. Method Javadoc

- Every public and non-trivial package-private method must have Javadoc.
- Use this structure:
  ```java
  /**
   * One-line summary.
   *
   * <p>Steps:                    ← only for complex multi-step methods
   * <ol>
   *   <li>First step.</li>
   *   <li>Second step.</li>
   * </ol>
   *
   * @param paramName description
   * @return description of the return value
   * @throws ExceptionType when condition
   */
  ```
- Simple one-line methods (getters, delegates) get a single-line Javadoc: `/** Returns the user ID. */`
- Omit `@param`/`@return` Javadoc on trivial overrides where the parent Javadoc is sufficient; use `{@inheritDoc}` when appropriate.

## 5. Comment Cleanup — REMOVE These

- **Redundant inline comments** that just restate the code:
  `// Create a new user entity` above `User user = new User(name, email);`
- **Banner comments** / section dividers:
  ```
  ////////////////////////////////////////////////////////////////////
  // Initialize the application context and register beans           //
  ////////////////////////////////////////////////////////////////////
  ```
- **Commented-out code** (dead imports, old logic, `System.out.println` debug lines).
- **Heritage/provenance comments** referencing deleted files:
  `// Replaces UserHelper.createUser() from legacy-utils module`
- **Placeholder comments** that describe unimplemented intent:
  `// TODO: placeholder for document processing logic` (with no real plan)
- **"For demonstration" / "Here you would typically"** comments.

## 6. Comment Cleanup — KEEP These

- **Actionable TODOs** with clear intent: `// TODO: Make retry count configurable via application.yml`
- **Non-obvious "why" comments** that explain a design decision:
  `// Use a LinkedHashMap to preserve insertion order for deterministic serialization.`
- **Contract/protocol comments** that document external API behavior:
  `// Azure Blob SDK returns null (not empty) when the container does not exist.`

## 7. Fix Stale References

- Search for outdated terminology (old project names, old class names, old API descriptions) and correct them to match the current code.
- Check `@see`, `@link`, and `@throws` tags reference classes and methods that still exist.

## 8. Remove Dead Code

- Delete unused imports.
- Delete unused private methods and fields.
- Delete empty catch blocks (or add a comment explaining why the exception is intentionally swallowed).
- Delete unnecessary casts (e.g., `(String) stringVar` when the variable is already a `String`).
- Delete redundant `toString()` calls on values already used in string context.
- Delete no-op assignments like `this.id = this.id`.

## 9. Compile-Check

- After finishing each package, run the appropriate compile command:
  - **Maven:** `mvn compile -q` (or `mvn compile -q -pl :module-name` for multi-module projects)
  - **Gradle:** `./gradlew compileJava --quiet`
- Fix any errors before proceeding to the next package.

## 10. Working Process

1. List the package tree of the target module/directory.
2. Read all Java files in the package.
3. Create a TODO list for the package (one item per file + one for compile-check).
4. Edit files, marking each TODO as you go.
5. Compile-check all edited files.
6. Move to the next package.

Start with the package I specify and work through it completely before asking what to do next.

## Java-Specific Rules

### Naming Conventions

| Element     | Convention          | Example                     |
|-------------|---------------------|-----------------------------|
| Class       | PascalCase          | `UserAccountService`        |
| Interface   | PascalCase          | `PaymentGateway`            |
| Method      | camelCase           | `findActiveUsers()`         |
| Field       | camelCase           | `retryCount`                |
| Constant    | UPPER_SNAKE_CASE    | `MAX_RETRY_ATTEMPTS`        |
| Package     | all lowercase       | `com.microsoft.claims.util` |
| Enum value  | UPPER_SNAKE_CASE    | `PENDING_APPROVAL`          |

### Lombok Usage

- If the project uses Lombok, do NOT add manual getters, setters, constructors, `toString()`, `equals()`, or `hashCode()` for annotated classes.
- Prefer `@Value` for immutable DTOs, `@Data` for mutable ones, `@Builder` for complex construction.
- Never mix Lombok-generated and hand-written accessors for the same field.

### Spring Annotations

- **Prefer constructor injection** over field injection (`@Autowired` on fields):
  ```java
  // ✅ Good — constructor injection (implicit @Autowired with single constructor)
  private final UserRepository userRepository;

  public UserService(UserRepository userRepository) {
      this.userRepository = userRepository;
  }

  // ❌ Avoid — field injection
  @Autowired
  private UserRepository userRepository;
  ```
- Use `@RequiredArgsConstructor` (Lombok) when constructor injection with many dependencies becomes verbose.
- Prefer `@Service`, `@Repository`, `@Component` stereotypes over generic `@Bean` methods when the class is owned by the project.

### Null Safety

- Use `@Nullable` / `@NonNull` annotations (from `jakarta.annotation` or Spring's `org.springframework.lang`) on public method parameters and return types.
- Prefer `Optional<T>` for return types that may legitimately be absent; do NOT use `Optional` as a field type or method parameter.
- Never return `null` from a method declared to return a collection — return an empty collection instead.

### Import Organization

- Follow this order, separated by blank lines:
  1. `java.*`
  2. `javax.*` / `jakarta.*`
  3. Third-party libraries (Spring, Apache, etc.)
  4. Project imports
- Remove all unused imports.
- Do not use wildcard imports (`import java.util.*`); import each class explicitly.
