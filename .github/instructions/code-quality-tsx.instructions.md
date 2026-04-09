---
description: "Use when writing, reviewing, or refactoring React TSX components. Enforces copyright headers, JSDoc, component naming, accessibility patterns, hook conventions, and state management."
applyTo: '**/*.tsx'
---
# Systematic Code-Quality Pass Instructions for React (TSX) Codebase

> **SDLC alignment:** This quality pass supports **Phase 4 (Implementation)** and **Phase 6 (QA Activities)**
> as defined in `.github/SDLC-with-Copilot-and-Azure.md`. It auto-applies when Copilot edits React component files.

You are performing a systematic code-quality pass on a React TypeScript codebase. Work through every folder one at a time. For each `.tsx` file, apply ALL of the following rules, then type-check every edited file before moving to the next folder.

> **Note**: General TypeScript rules (copyright headers, import organization, strict typing,
> comment cleanup, naming for non-component code) are defined in `code-quality-ts.instructions.md`.
> This file extends those rules with React-specific patterns.

## 1. Copyright & Component Header

- Every `.tsx` file must start with:
  ```
  // Copyright (c) Microsoft Corporation.
  // Licensed under the MIT License.
  ```
- Immediately after, add or verify a JSDoc module description:
  ```tsx
  /**
   * Brief description of what this component/page/layout does.
   * Mention its role in the UI hierarchy or user workflow.
   * @module ComponentName
   */
  ```

## 2. File Naming Conventions

| Element                | Convention             | Example                              |
|------------------------|------------------------|--------------------------------------|
| Component file         | PascalCase             | `ClaimSummary.tsx`                   |
| Page / route file      | PascalCase             | `ClaimDetailPage.tsx`                |
| Layout file            | PascalCase             | `DashboardLayout.tsx`                |
| Hook file              | camelCase, `use` prefix| `useClaimData.ts`                    |
| Context file           | PascalCase + Context   | `AuthContext.tsx`                     |
| Utility/helper file    | kebab-case `.ts`       | `format-date.ts`                     |
| Type definition file   | kebab-case `.ts`       | `claim-types.ts`                     |
| Test file              | PascalCase + `.test`   | `ClaimSummary.test.tsx`              |
| Story file             | PascalCase + `.stories`| `ClaimSummary.stories.tsx`           |
| CSS Module             | PascalCase + `.module` | `ClaimSummary.module.css`            |
| Barrel file            | `index.ts`             | `index.ts` (re-exports only)         |

Rules:
- One component per file. The filename must match the default/named export.
- Co-locate component, test, stories, and styles in the same directory when practical.

## 3. Component Structure (Functional Components Only)

- Use **function declarations** for components (not arrow function assignments):
  ```tsx
  // ✅ Preferred
  export function ClaimSummary({ claimId }: ClaimSummaryProps) { ... }

  // ❌ Avoid
  export const ClaimSummary: React.FC<ClaimSummaryProps> = ({ claimId }) => { ... };
  ```
- Do NOT use `React.FC` or `React.FunctionComponent` — they add implicit `children` typing and limit generics.
- No class components unless wrapping a third-party library that requires it.

## 4. Props Typing

- Define props as a named `interface` (not inline or `type` alias) co-located above the component:
  ```tsx
  /** Props for {@link ClaimSummary}. */
  interface ClaimSummaryProps {
    /** The unique claim identifier. */
    claimId: string;
    /** Optional callback when the claim is selected. */
    onSelect?: (claimId: string) => void;
  }
  ```
- Use `readonly` for props that should not be mutated.
- Destructure props in the function signature, not in the body.
- For components that accept `children`, type explicitly:
  ```tsx
  interface LayoutProps {
    children: React.ReactNode;
  }
  ```

## 5. Hooks Rules & Patterns

### Custom Hooks
- File name: `use<Name>.ts` (camelCase with `use` prefix).
- Must start with `use` prefix.
- Always provide a JSDoc comment describing what state/behavior the hook encapsulates.
- Return a typed object (not a tuple) when returning more than two values:
  ```tsx
  /** Manages claim data fetching and pagination state. */
  export function useClaimData(claimId: string): UseClaimDataResult { ... }

  interface UseClaimDataResult {
    data: Claim | null;
    isLoading: boolean;
    error: Error | null;
    refetch: () => Promise<void>;
  }
  ```

### Built-in Hooks
- `useState`: Always provide an explicit type when the initial value is `null` or ambiguous:
  ```tsx
  const [claim, setClaim] = useState<Claim | null>(null);
  ```
- `useEffect`:
  - Every `useEffect` must have a comment explaining **what** it does and **why**:
    ```tsx
    // Fetch claim details when claimId changes.
    useEffect(() => { ... }, [claimId]);
    ```
  - Clean up side effects (subscriptions, timers, abort controllers).
  - Avoid missing or unnecessary dependencies — the linter must pass without `eslint-disable` overrides.
- `useMemo` / `useCallback`: Use only when there is a measured performance need or to stabilize a reference passed to a child's dependency array. Do NOT wrap every function or value.
- `useRef`: Type explicitly: `useRef<HTMLInputElement>(null)`.

## 6. State Management Rules

- **Local state** (`useState`): Prefer for state scoped to a single component.
- **Lifted state**: Lift to the nearest common ancestor, not further.
- **Context**: Use for cross-cutting concerns (auth, theme, locale). Do NOT use Context for high-frequency updates — prefer a state management library if updates cause excessive re-renders.
- **Derived state**: Compute from existing state/props during render. Do NOT store in `useState` if it can be derived:
  ```tsx
  // ✅ Derived
  const isOverdue = claim.dueDate < new Date();

  // ❌ Duplicated state
  const [isOverdue, setIsOverdue] = useState(false);
  useEffect(() => setIsOverdue(claim.dueDate < new Date()), [claim.dueDate]);
  ```

## 7. Side-Effect Rules

- **Data fetching**: Extract into a custom hook (`useClaimData`, `useUserProfile`).
- **Event listeners**: Add in `useEffect`, remove in cleanup function.
- **Timers**: Create with `setTimeout`/`setInterval` in `useEffect`, clear in cleanup.
- **Abort controllers**: Use `AbortController` for fetch requests; abort in cleanup:
  ```tsx
  useEffect(() => {
    const controller = new AbortController();
    fetchClaim(claimId, { signal: controller.signal }).then(setClaim);
    return () => controller.abort();
  }, [claimId]);
  ```
- Do NOT perform side effects directly in the render body or in event handlers that should be `useEffect`.

## 8. JSX Patterns

- Self-close tags with no children: `<ClaimBadge status={status} />`.
- Use fragments (`<>...</>`) instead of unnecessary wrapper `<div>`.
- Extract complex conditional rendering into named sub-components or helper functions.
- Avoid inline object/array literals in JSX props (causes unnecessary re-renders):
  ```tsx
  // ❌ New object every render
  <Chart style={{ marginTop: 8 }} />

  // ✅ Stable reference
  const chartStyle = { marginTop: 8 } as const;
  <Chart style={chartStyle} />
  ```
- For lists, always use a stable, unique `key` — never array index (unless the list is static and never reordered).

## 9. Comment Cleanup — React-Specific

### REMOVE These
- Comments that describe what JSX renders: `{/* Render the claim list */}`.
- Commented-out JSX blocks.
- `// eslint-disable-next-line` without an explanation comment.
- `@ts-ignore` without justification.

### KEEP These
- **"Why" comments** for non-obvious rendering logic:
  `{/* Portal needed to escape overflow:hidden on parent card. */}`
- **Accessibility notes**: `{/* aria-live for screen reader announcements. */}`
- **Performance notes**: `{/* Memoized to prevent re-render of 500+ row table. */}`

## 10. Error Boundaries

- Wrap top-level routes or major UI sections with an error boundary.
- Error boundaries must:
  - Log the error through the project's logger.
  - Display a user-friendly fallback UI.
  - Provide a recovery action (e.g., "Retry" or "Go back").

## 11. Component Docstrings

- Every exported component must have a JSDoc comment:
  ```tsx
  /**
   * Displays a summary card for a single claim.
   *
   * @remarks
   * Used on the dashboard and in search results. Receives claim data
   * from the parent list component.
   *
   * @example
   * ```tsx
   * <ClaimSummary claimId="CLM-001" onSelect={handleSelect} />
   * ```
   */
  export function ClaimSummary({ claimId, onSelect }: ClaimSummaryProps) { ... }
  ```

## 12. Import Organization (extends TS rules)

- Order imports in this sequence, separated by blank lines:
  1. React / React DOM (`react`, `react-dom`)
  2. Third-party packages (`@azure/*`, `react-router-dom`, `zod`)
  3. Internal components (absolute or alias imports)
  4. Internal hooks
  5. Internal types / constants / utilities
  6. Styles / CSS modules
- Use `type` imports where possible: `import type { ClaimSummaryProps } from './types';`

## 13. Remove Dead Code (extends TS rules)

- Delete unused component props from the interface AND the destructuring.
- Delete unused state variables and their setters.
- Delete `useEffect` calls with empty bodies or no meaningful side effect.
- Delete components that are no longer rendered anywhere.

## 14. Type-Check

- After finishing each folder, run `npx tsc --noEmit` on the project.
- Fix any type errors before proceeding to the next folder.

## Working Process

1. List the directory tree of the target folder.
2. Read all `.tsx` files in the folder.
3. Create a TODO list for the folder (one item per file + one for type-check).
4. Edit files, marking each TODO as you go.
5. Type-check all edited files.
6. Move to the next folder.
