---
description: "Use when writing or reviewing TypeScript tests with Vitest. Enforces Arrange-Act-Assert structure, naming conventions, mocking patterns, assertion quality, and coverage configuration."
applyTo: '**/*.test.ts'
---
# Test Quality Instructions for TypeScript

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**
> as defined in `.github/SDLC-with-Copilot-and-Azure.md`. It auto-applies when Copilot edits TypeScript test files.

You are a senior TypeScript test engineer. Your job is to audit, sanitize, and write
comprehensive unit tests for a TypeScript project that follows these conventions.

═══════════════════════════════════════════════════════════════════════════════
1. PROJECT LAYOUT
═══════════════════════════════════════════════════════════════════════════════

Tests are co-located with the source files they test:

    ProjectRoot/
    ├── src/
    │   ├── services/
    │   │   ├── claim-service.ts
    │   │   └── claim-service.test.ts      ← co-located test
    │   ├── utils/
    │   │   ├── format-date.ts
    │   │   └── format-date.test.ts
    │   ├── types/
    │   │   └── claim-types.ts             ← pure types — no test needed
    │   └── hooks/
    │       ├── useClaimData.ts
    │       └── useClaimData.test.ts
    ├── vitest.config.ts                   ← Vitest configuration
    ├── tsconfig.json
    └── package.json

Key rules:
- Test file lives next to the source file it tests.
- Test file name: `<source-file>.test.ts` (same base name, `.test.ts` suffix).
- Pure type definition files (`.d.ts`, type-only `.ts`) do not need tests.
- Shared test utilities / fixtures go in `src/__test-utils__/` or `src/test-helpers/`.

═══════════════════════════════════════════════════════════════════════════════
2. TEST SANITIZATION (run first, before writing new tests)
═══════════════════════════════════════════════════════════════════════════════

Before writing any new tests, audit all existing test files:

a) FIND ORPHANED TESTS — tests that import modules that no longer exist.
   For every test file, verify that every import resolves to a real source file.
   Delete any test file whose imports reference deleted/renamed modules.

b) FIND STALE ASSERTIONS — tests whose assertions reference renamed fields,
   changed method signatures, or removed parameters.
   Fix these to match the current source code.

c) TYPE-CHECK every remaining test file:
       npx tsc --noEmit
   Fix any type errors or import failures.

d) ADD MISSING COPYRIGHT HEADERS to any file that lacks one.

═══════════════════════════════════════════════════════════════════════════════
3. FILE FORMAT CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

Every test file must follow this exact structure:

    // Copyright (c) Microsoft Corporation.
    // Licensed under the MIT License.

    /**
     * Tests for {@link ./module-name} — brief description.
     */

    import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

    <application imports>
    <test utility imports>

    // ── Section Name ────────────────────────────────────────────────────

    describe('ModuleName', () => {
      describe('methodName', () => {
        it('should describe expected behavior', () => {
          // Arrange
          // Act
          // Assert
        });
      });
    });

Rules:
- ALWAYS include the 2-line copyright header.
- ALWAYS include a module-level JSDoc comment: `/** Tests for ... */`
- Use ASCII banner comments to separate logical sections.
- Import test utilities (`describe`, `it`, `expect`, `vi`) from `vitest`.

═══════════════════════════════════════════════════════════════════════════════
4. NAMING CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

| Element               | Convention                   | Example                              |
|-----------------------|------------------------------|--------------------------------------|
| Test file             | `<source>.test.ts`           | `claim-service.test.ts`              |
| Top `describe`        | Module or class name         | `describe('ClaimService', ...)`      |
| Nested `describe`     | Method or function name      | `describe('processAsync', ...)`      |
| `it` blocks           | `should` + expected behavior | `it('should throw on invalid ID')`   |
| Helper function       | `_` prefixed or `create*`    | `_makeClaimData`, `createMockRepo`   |
| Mock variable         | `mock` prefixed              | `mockRepository`, `mockLogger`       |
| Fixture / factory     | `create` prefixed            | `createValidClaim()`                 |

File naming must mirror the source module:
  src/services/claim-service.ts  →  src/services/claim-service.test.ts
  src/utils/format-date.ts       →  src/utils/format-date.test.ts

═══════════════════════════════════════════════════════════════════════════════
5. WHAT TO TEST (prioritize by testability)
═══════════════════════════════════════════════════════════════════════════════

Focus on UNIT-TESTABLE code — pure logic that can run without external services:

HIGH PRIORITY (test these thoroughly):
- Zod schemas / type validators: parsing, defaults, error messages
- Utility / helper functions: transformations, formatting, calculations
- Service methods with injectable dependencies
- Custom error classes: message formatting, serialization
- Configuration parsers: loading, defaults, validation
- State machines / reducers: transitions, edge cases

MEDIUM PRIORITY (test with mocks):
- Repository / data-access methods: mock the database client
- API client wrappers: mock fetch/axios
- Logger wrappers: verify correct log level and structure
- Middleware functions: mock request/response objects

LOW PRIORITY (skip or test only the interface):
- Entry points (`index.ts`, server bootstrap)
- Deep async orchestration across multiple services
- Third-party library wrappers with no custom logic

═══════════════════════════════════════════════════════════════════════════════
6. MOCKING PATTERNS (Vitest)
═══════════════════════════════════════════════════════════════════════════════

Use these patterns in order of preference:

a) vi.fn() — for simple function mocks:
       const mockCallback = vi.fn();
       mockCallback.mockReturnValue('result');
       mockCallback.mockResolvedValue('async-result');

b) vi.spyOn() — for observing real method calls:
       const spy = vi.spyOn(service, 'processAsync');
       spy.mockResolvedValueOnce(expected);

c) vi.mock() — for module-level mocking:
       vi.mock('../repositories/claim-repository', () => ({
         ClaimRepository: vi.fn().mockImplementation(() => ({
           findById: vi.fn().mockResolvedValue(mockClaim),
         })),
       }));

d) vi.stubEnv() — for environment variables:
       beforeEach(() => {
         vi.stubEnv('AZURE_STORAGE_CONNECTION', 'test-connection');
       });
       afterEach(() => {
         vi.unstubAllEnvs();
       });

e) Hand-rolled fakes — for complex service stubs:
       class FakeClaimRepository implements ClaimRepository {
         private claims: Map<string, Claim> = new Map();
         async findById(id: string): Promise<Claim | null> {
           return this.claims.get(id) ?? null;
         }
       }

f) vi.useFakeTimers() — for time-dependent code:
       beforeEach(() => { vi.useFakeTimers(); });
       afterEach(() => { vi.useRealTimers(); });

Rules:
- Reset mocks between tests: use `beforeEach(() => { vi.restoreAllMocks(); })`.
- Prefer dependency injection over module mocking when possible.
- Mock at the boundary (repositories, HTTP clients), not internal functions.

═══════════════════════════════════════════════════════════════════════════════
7. ASSERTION STYLE
═══════════════════════════════════════════════════════════════════════════════

Use Vitest's `expect` API. Examples:

    expect(result).toBe(expected);              // strict equality
    expect(result).toEqual(expected);            // deep equality
    expect(result).toMatchObject(partial);       // partial match
    expect(items).toHaveLength(3);
    expect(result).toBeNull();
    expect(result).toBeDefined();
    expect(result).toBeInstanceOf(ClaimError);
    expect(str).toContain('keyword');
    expect(str).toMatch(/pattern/);

For expected exceptions:
    expect(() => riskyFunction()).toThrow(ValidationError);
    expect(() => riskyFunction()).toThrowError(/must include/);

For async exceptions:
    await expect(asyncFunction()).rejects.toThrow(NotFoundError);
    await expect(asyncFunction()).rejects.toThrowError('not found');

For mock verification:
    expect(mockFn).toHaveBeenCalledOnce();
    expect(mockFn).toHaveBeenCalledWith('arg1', expect.any(Number));
    expect(mockFn).not.toHaveBeenCalled();

═══════════════════════════════════════════════════════════════════════════════
8. ASYNC TEST PATTERNS
═══════════════════════════════════════════════════════════════════════════════

- Use `async/await` directly in `it` blocks (Vitest supports this natively):
      it('should fetch claim data', async () => {
        const result = await service.getClaimAsync('CLM-001');
        expect(result).toEqual(expectedClaim);
      });

- For testing rejected promises:
      it('should reject with NotFoundError', async () => {
        await expect(service.getClaimAsync('invalid'))
          .rejects.toThrow(NotFoundError);
      });

- DO NOT use `.then()`/`.catch()` chains in tests — always use async/await.

═══════════════════════════════════════════════════════════════════════════════
9. TEST CONFIGURATION
═══════════════════════════════════════════════════════════════════════════════

vitest.config.ts must include:

    import { defineConfig } from 'vitest/config';
    import path from 'path';

    export default defineConfig({
      test: {
        globals: false,              // explicit imports preferred
        environment: 'node',         // use 'jsdom' only for DOM tests
        include: ['src/**/*.test.ts'],
        exclude: ['node_modules', 'dist'],
        coverage: {
          provider: 'v8',
          reporter: ['text', 'text-summary', 'html'],
          reportsDirectory: './coverage',
          include: ['src/**/*.ts'],
          exclude: [
            'src/**/*.test.ts',
            'src/**/*.test.tsx',
            'src/**/*.d.ts',
            'src/**/index.ts',
            'src/__test-utils__/**',
          ],
          thresholds: {
            statements: 80,
            branches: 80,
            functions: 80,
            lines: 80,
          },
        },
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, './src'),
        },
      },
    });

package.json scripts:

    "scripts": {
      "test": "vitest run",
      "test:watch": "vitest",
      "test:coverage": "vitest run --coverage"
    }

═══════════════════════════════════════════════════════════════════════════════
10. GIT / DOCKER EXCLUSIONS
═══════════════════════════════════════════════════════════════════════════════

.gitignore must exclude test artifacts (NOT the test files themselves):
    coverage/
    .vitest-cache/

.dockerignore must exclude test files AND artifacts from the build context:
    **/*.test.ts
    **/*.test.tsx
    **/__test-utils__/
    coverage/
    .vitest-cache/
    vitest.config.ts

═══════════════════════════════════════════════════════════════════════════════
11. WORKFLOW CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Follow this order:

□ Phase 1 — Sanitize
  1. List all `*.test.ts` files
  2. For each: verify imports resolve to existing source modules
  3. Delete orphaned test files (imports reference deleted modules)
  4. Fix stale tests (wrong field names, changed signatures, renamed params)
  5. Add missing copyright headers
  6. Type-check all remaining tests: npx tsc --noEmit

□ Phase 2 — Identify gaps
  7. List all source modules under src/ (excluding *.d.ts, index.ts, types-only)
  8. List all existing test files
  9. Produce a gap matrix: source module → has test? → coverage gaps

□ Phase 3 — Write tests
  10. For each uncovered module, create a co-located test file
  11. Prioritize: schemas/validators → utils → services → repositories → hooks
  12. Type-check each new test file immediately after creation

□ Phase 4 — Validate
  13. Run full suite: npx vitest run
  14. Fix any failures
  15. Run with coverage: npx vitest run --coverage
  16. Review coverage gaps; write additional tests for missed branches if practical

□ Phase 5 — Project hygiene
  17. Ensure vitest.config.ts has correct include/exclude patterns
  18. Ensure .gitignore excludes test artifacts
  19. Ensure .dockerignore excludes test files and artifacts
  20. Ensure all mocks are properly cleaned up (no leaking state between tests)
