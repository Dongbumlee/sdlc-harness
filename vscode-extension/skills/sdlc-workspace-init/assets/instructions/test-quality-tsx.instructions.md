---
description: "Use when writing or reviewing React component tests with Vitest and React Testing Library. Enforces user-centric queries, async patterns, accessibility testing, and snapshot conventions."
applyTo: '**/*.test.tsx'
---
# Test Quality Instructions for React Components (TSX)

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**
> as defined in `.github/SDLC-with-Copilot-and-Azure.md`. It auto-applies when Copilot edits React test files.

You are a senior React test engineer. Your job is to audit, sanitize, and write
comprehensive component tests for a React TypeScript project using Vitest and
React Testing Library.

> **Note**: General TypeScript test conventions (copyright headers, sanitization,
> naming, mocking with Vitest, assertion style, async patterns, configuration)
> are defined in `test-quality-ts.instructions.md`. This file extends those
> rules with React component testing patterns.

═══════════════════════════════════════════════════════════════════════════════
1. PROJECT LAYOUT (React Tests)
═══════════════════════════════════════════════════════════════════════════════

Component tests are co-located with the components they test:

    src/
    ├── components/
    │   ├── ClaimSummary/
    │   │   ├── ClaimSummary.tsx
    │   │   ├── ClaimSummary.test.tsx          ← component test
    │   │   ├── ClaimSummary.module.css
    │   │   └── index.ts
    │   └── shared/
    │       ├── Button.tsx
    │       └── Button.test.tsx
    ├── pages/
    │   ├── DashboardPage.tsx
    │   └── DashboardPage.test.tsx
    ├── hooks/
    │   ├── useClaimData.ts
    │   └── useClaimData.test.ts               ← hook test (in .test.ts)
    └── __test-utils__/
        ├── render-with-providers.tsx           ← shared test utility
        └── mock-data.ts                       ← shared fixtures

Key rules:
- Component test file lives next to the component: `Component.test.tsx`.
- Hook tests that don't render JSX use `.test.ts` (covered by TS instructions).
- Hook tests that use `renderHook` with JSX providers use `.test.tsx`.
- Shared test utilities (custom render, providers, mock data) go in `__test-utils__/`.

═══════════════════════════════════════════════════════════════════════════════
2. FILE FORMAT CONVENTIONS
═══════════════════════════════════════════════════════════════════════════════

Every component test file must follow this structure:

    // Copyright (c) Microsoft Corporation.
    // Licensed under the MIT License.

    /**
     * Tests for {@link ./ComponentName} — brief description.
     */

    import { describe, it, expect, vi, beforeEach } from 'vitest';
    import { render, screen, within } from '@testing-library/react';
    import userEvent from '@testing-library/user-event';

    import { ComponentName } from './ComponentName';
    import type { ComponentNameProps } from './ComponentName';

    // ── Helpers ─────────────────────────────────────────────────────────

    function renderComponent(overrides: Partial<ComponentNameProps> = {}) {
      const defaultProps: ComponentNameProps = {
        // sensible defaults for all required props
      };
      return render(<ComponentName {...defaultProps} {...overrides} />);
    }

    // ── Rendering ───────────────────────────────────────────────────────

    describe('ComponentName', () => {
      it('should render without crashing', () => {
        renderComponent();
        expect(screen.getByRole('...')).toBeInTheDocument();
      });
    });

Rules:
- ALWAYS include the 2-line copyright header.
- ALWAYS create a `renderComponent()` helper with sensible default props.
- ALWAYS import from `@testing-library/react`, not `react-dom/test-utils`.
- NEVER import `render` from `react-dom` directly.

═══════════════════════════════════════════════════════════════════════════════
3. TESTING LIBRARY PRINCIPLES
═══════════════════════════════════════════════════════════════════════════════

Follow the Testing Library guiding principle:
> "The more your tests resemble the way your software is used,
>  the more confidence they can give you."

This means:
- Query by **user-visible attributes** (role, text, label), not implementation details.
- Interact using `userEvent`, not `fireEvent` (userEvent simulates real user behavior).
- Assert on **what the user sees**, not internal component state.

═══════════════════════════════════════════════════════════════════════════════
4. QUERY PRIORITY (use in this order)
═══════════════════════════════════════════════════════════════════════════════

Prefer queries in this order (most accessible → least):

1. `screen.getByRole('button', { name: 'Submit' })`     ← best: accessible
2. `screen.getByLabelText('Email address')`              ← form inputs
3. `screen.getByPlaceholderText('Search...')`             ← when no label
4. `screen.getByText('No results found')`                 ← visible text
5. `screen.getByDisplayValue('current-value')`            ← filled inputs
6. `screen.getByAltText('Company logo')`                  ← images
7. `screen.getByTitle('Close dialog')`                    ← tooltips
8. `screen.getByTestId('claim-card-CLM-001')`            ← last resort

Rules:
- NEVER use `container.querySelector()` or DOM traversal.
- NEVER query by class name or CSS selector.
- Use `getByTestId` ONLY when no accessible query is possible (complex visualizations, canvas).
- Use `within()` to scope queries to a specific container:
      const card = screen.getByRole('article');
      expect(within(card).getByText('CLM-001')).toBeInTheDocument();

═══════════════════════════════════════════════════════════════════════════════
5. USER INTERACTION PATTERNS
═══════════════════════════════════════════════════════════════════════════════

ALWAYS use `@testing-library/user-event` (not `fireEvent`):

    import userEvent from '@testing-library/user-event';

    it('should call onSubmit when form is submitted', async () => {
      const user = userEvent.setup();
      const mockOnSubmit = vi.fn();
      renderComponent({ onSubmit: mockOnSubmit });

      await user.type(screen.getByLabelText('Claim ID'), 'CLM-001');
      await user.click(screen.getByRole('button', { name: 'Submit' }));

      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ claimId: 'CLM-001' }),
      );
    });

Common interactions:
- Click: `await user.click(element)`
- Type: `await user.type(element, 'text')`
- Clear + type: `await user.clear(element); await user.type(element, 'new')`
- Select option: `await user.selectOptions(element, 'value')`
- Tab: `await user.tab()`
- Keyboard: `await user.keyboard('{Enter}')`
- Hover: `await user.hover(element)`

Rules:
- ALWAYS call `userEvent.setup()` at the start of the test.
- ALWAYS `await` every user interaction (they are async).
- Do NOT use `fireEvent` unless testing a specific DOM event not covered by userEvent.

═══════════════════════════════════════════════════════════════════════════════
6. ASYNC RENDERING & WAITING
═══════════════════════════════════════════════════════════════════════════════

For components that load data or update asynchronously:

a) `findBy*` queries — waits for element to appear (returns Promise):
       const heading = await screen.findByRole('heading', { name: 'Claims' });
       expect(heading).toBeInTheDocument();

b) `waitFor` — waits for assertion to pass:
       import { waitFor } from '@testing-library/react';
       await waitFor(() => {
         expect(screen.getByText('Loaded')).toBeInTheDocument();
       });

c) `waitForElementToBeRemoved` — waits for element to disappear:
       import { waitForElementToBeRemoved } from '@testing-library/react';
       await waitForElementToBeRemoved(() => screen.queryByText('Loading...'));

Rules:
- Use `queryBy*` when asserting something is NOT present: `expect(screen.queryByText('Error')).not.toBeInTheDocument()`.
- Do NOT use arbitrary `setTimeout` or `sleep` in tests.
- Do NOT use `act()` directly — prefer `userEvent` and `findBy`, which handle `act` internally.

═══════════════════════════════════════════════════════════════════════════════
7. WHAT TO TEST IN COMPONENTS
═══════════════════════════════════════════════════════════════════════════════

TEST THESE (user-visible behavior):
- Renders correct content for given props
- Conditional rendering (shows/hides elements based on state or props)
- User interactions trigger correct callbacks
- Form validation shows/hides error messages
- Loading states render correctly
- Error states render fallback UI
- Accessibility: correct roles, labels, aria attributes

DO NOT TEST THESE (implementation details):
- Internal state values
- Number of re-renders
- Component lifecycle methods
- CSS class names
- Internal method calls between parent and child
- Snapshot tests (they are brittle and rarely catch real bugs)

═══════════════════════════════════════════════════════════════════════════════
8. HOOK TESTING PATTERNS
═══════════════════════════════════════════════════════════════════════════════

Use `renderHook` from `@testing-library/react`:

    import { renderHook, act, waitFor } from '@testing-library/react';
    import { useClaimData } from './useClaimData';

    describe('useClaimData', () => {
      it('should fetch and return claim data', async () => {
        const { result } = renderHook(() => useClaimData('CLM-001'));

        // Initially loading
        expect(result.current.isLoading).toBe(true);

        // Wait for data
        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.data).toEqual(expectedClaim);
        expect(result.current.error).toBeNull();
      });

      it('should handle errors', async () => {
        const { result } = renderHook(() => useClaimData('invalid'));

        await waitFor(() => {
          expect(result.current.error).toBeInstanceOf(Error);
        });
      });
    });

For hooks that need providers (e.g., context, router):

    function createWrapper() {
      return function Wrapper({ children }: { children: React.ReactNode }) {
        return (
          <AuthProvider>
            <RouterProvider>
              {children}
            </RouterProvider>
          </AuthProvider>
        );
      };
    }

    const { result } = renderHook(() => useProtectedData(), {
      wrapper: createWrapper(),
    });

═══════════════════════════════════════════════════════════════════════════════
9. CONTEXT & PROVIDER TESTING
═══════════════════════════════════════════════════════════════════════════════

Create a shared custom render function in `__test-utils__/`:

    // src/__test-utils__/render-with-providers.tsx
    import { render, type RenderOptions } from '@testing-library/react';
    import { AuthProvider } from '../contexts/AuthContext';
    import { ThemeProvider } from '../contexts/ThemeContext';

    interface CustomRenderOptions extends RenderOptions {
      authState?: Partial<AuthState>;
    }

    export function renderWithProviders(
      ui: React.ReactElement,
      options: CustomRenderOptions = {},
    ) {
      const { authState, ...renderOptions } = options;

      function Wrapper({ children }: { children: React.ReactNode }) {
        return (
          <AuthProvider initialState={authState}>
            <ThemeProvider>
              {children}
            </ThemeProvider>
          </AuthProvider>
        );
      }

      return render(ui, { wrapper: Wrapper, ...renderOptions });
    }

Use in tests:

    import { renderWithProviders } from '../__test-utils__/render-with-providers';

    it('should show admin controls for admin users', () => {
      renderWithProviders(<Dashboard />, {
        authState: { role: 'admin' },
      });
      expect(screen.getByRole('button', { name: 'Manage Users' })).toBeInTheDocument();
    });

═══════════════════════════════════════════════════════════════════════════════
10. MOCKING PATTERNS (React-Specific)
═══════════════════════════════════════════════════════════════════════════════

a) Mock child components to isolate the component under test:
       vi.mock('./ChildComponent', () => ({
         ChildComponent: ({ title }: { title: string }) => (
           <div data-testid="mock-child">{title}</div>
         ),
       }));

b) Mock hooks:
       vi.mock('./useClaimData', () => ({
         useClaimData: vi.fn().mockReturnValue({
           data: mockClaim,
           isLoading: false,
           error: null,
         }),
       }));

c) Mock navigation (react-router):
       const mockNavigate = vi.fn();
       vi.mock('react-router-dom', async () => {
         const actual = await vi.importActual('react-router-dom');
         return { ...actual, useNavigate: () => mockNavigate };
       });

d) Mock fetch / API calls:
       beforeEach(() => {
         vi.spyOn(globalThis, 'fetch').mockResolvedValue(
           new Response(JSON.stringify(mockData), { status: 200 }),
         );
       });

Rules:
- Prefer mocking at the boundary (API calls, hooks) over mocking child components.
- When mocking child components, keep the mock minimal — just render props for verification.

═══════════════════════════════════════════════════════════════════════════════
11. ACCESSIBILITY TESTING
═══════════════════════════════════════════════════════════════════════════════

Every component test should include basic accessibility checks:

a) Verify semantic roles:
       expect(screen.getByRole('navigation')).toBeInTheDocument();
       expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Claims');

b) Verify form labels:
       expect(screen.getByLabelText('Email address')).toBeRequired();

c) Verify aria attributes:
       expect(screen.getByRole('alert')).toHaveAttribute('aria-live', 'assertive');

d) Verify keyboard navigation (when relevant):
       await user.tab();
       expect(screen.getByRole('button', { name: 'Submit' })).toHaveFocus();

═══════════════════════════════════════════════════════════════════════════════
12. VITEST CONFIGURATION (React)
═══════════════════════════════════════════════════════════════════════════════

vitest.config.ts must include jsdom for component tests:

    import { defineConfig } from 'vitest/config';
    import react from '@vitejs/plugin-react';
    import path from 'path';

    export default defineConfig({
      plugins: [react()],
      test: {
        globals: false,
        environment: 'jsdom',
        include: ['src/**/*.test.{ts,tsx}'],
        exclude: ['node_modules', 'dist'],
        setupFiles: ['./src/__test-utils__/setup.ts'],
        coverage: {
          provider: 'v8',
          reporter: ['text', 'text-summary', 'html'],
          reportsDirectory: './coverage',
          include: ['src/**/*.{ts,tsx}'],
          exclude: [
            'src/**/*.test.{ts,tsx}',
            'src/**/*.stories.tsx',
            'src/**/*.d.ts',
            'src/**/index.ts',
            'src/__test-utils__/**',
          ],
        },
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, './src'),
        },
      },
    });

Test setup file (`src/__test-utils__/setup.ts`):

    import '@testing-library/jest-dom/vitest';

This enables matchers like `toBeInTheDocument()`, `toHaveTextContent()`, etc.

═══════════════════════════════════════════════════════════════════════════════
13. WORKFLOW CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Follow this order:

□ Phase 1 — Sanitize
  1. List all `*.test.tsx` files
  2. For each: verify imports resolve to existing components/hooks
  3. Delete orphaned test files
  4. Fix stale tests (wrong prop names, changed component APIs)
  5. Add missing copyright headers
  6. Type-check: npx tsc --noEmit

□ Phase 2 — Identify gaps
  7. List all components and pages under src/
  8. List all existing component test files
  9. Produce a gap matrix: component → has test? → what's covered?

□ Phase 3 — Write tests
  10. For each uncovered component, create a co-located test file
  11. Prioritize: shared components → pages → layout components → context providers
  12. Every test file must include: rendering, interaction, accessible queries
  13. Type-check each new test file immediately after creation

□ Phase 4 — Validate
  14. Run full suite: npx vitest run
  15. Fix any failures
  16. Run with coverage: npx vitest run --coverage
  17. Review coverage gaps; write additional tests for missed branches

□ Phase 5 — Project hygiene
  18. Ensure vitest.config.ts uses jsdom environment
  19. Ensure setup file imports @testing-library/jest-dom/vitest
  20. Ensure __test-utils__/ has shared renderWithProviders and mock data
  21. Ensure .gitignore excludes coverage artifacts
  22. Ensure .dockerignore excludes test files and artifacts
