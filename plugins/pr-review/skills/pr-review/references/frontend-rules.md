# Frontend Review Rules

Comprehensive frontend review rules for React/TypeScript projects. These rules are generic and apply to most modern React applications. When a project has specific conventions documented in its own CLAUDE.md or contributing guide, defer to that - but these rules are the baseline.

---

## React Hooks

- **Dependency arrays:** Every value referenced inside a `useEffect`, `useMemo`, or `useCallback` must be listed in the dependency array. Missing dependencies lead to stale closures. Extra dependencies cause unnecessary re-runs. Both are Important findings.
- **Cleanup functions:** Return cleanup functions from `useEffect` for subscriptions, timers, event listeners, or anything else that needs teardown. Missing cleanup is a memory leak - Critical on long-lived mounted components, Important otherwise.
- **Rules of hooks:** Never call hooks conditionally, in loops, or after early returns. Custom hooks must start with `use`. Violations are Critical - they break React's internal state tracking.
- **`useState` batching:** React 18+ batches state updates automatically, even in promises and timeouts. Callers shouldn't rely on synchronous reads of state after `setState`.
- **`useMemo` / `useCallback` overuse:** These are not free. Only use them when there is a measurable performance need, or when referential stability is required for downstream memoized components. Wrapping everything is Minor noise.
- **`useRef` for mutable values:** Use `useRef` for values that shouldn't trigger re-renders on change. Storing rendering-relevant values in a ref is usually a bug.
- **`useLayoutEffect` vs `useEffect`:** `useLayoutEffect` runs synchronously before paint and is needed for DOM measurements. It blocks rendering, so use sparingly. Wrong choice is Minor unless it causes visible flicker.

## Component Patterns

- **List keys:** Every element in a rendered list needs a `key` prop. Use a stable unique ID (database ID, UUID). Index as key is only acceptable for truly static lists that never reorder.
- **Controlled vs uncontrolled:** Be consistent within a component. Mixing them causes subtle bugs where state and DOM drift apart.
- **Props destructuring:** Destructure props at the top of the component for clarity.
- **Inline object/array creation:** Avoid `<Child data={{ foo: 1 }} />` in frequently-rendered components - it creates a new reference on every render, defeating memoization.
- **Inline arrow functions:** Usually fine, but flag in hot paths or when passed to memoized children.
- **Component size:** Components over ~300 lines mixing many concerns should usually be split. Important finding.
- **Default exports vs named exports:** Follow project convention.
- **Boolean props:** Prefer named props over positional booleans. `isOpen`, not a boolean in the third position.

## State Management

- **Never mutate state:** `state.items.push(x)` is wrong. `setState([...state.items, x])` is right. Mutation is a Critical correctness bug - React won't re-render and subscribers won't fire.
- **Derived state:** Don't store values that can be computed from props or other state. Compute them at render time, or memoize if expensive.
- **Lift state up when needed:** But not higher than necessary. State should live at the lowest common ancestor of the components that use it.
- **Global state:** Use context, Zustand, Redux, or the project's store for widely-shared state. Don't put component-local state in global state just because it's easier.
- **Server state:** Use React Query, TanStack Query, SWR, or the project's data layer for server state. Never roll your own `useState + useEffect` to fetch data unless there is a clear reason - you will get loading, error, caching, and race conditions wrong.

## Async and Data Fetching

- **Loading states:** Every async operation needs a visible loading UI. Missing loading state is Important.
- **Error states:** Every async operation needs a visible error UI. Swallowing errors is Important-to-Critical depending on the operation.
- **Empty states:** Every list needs an empty-state UI. Users should never see a blank space.
- **Race conditions:** Cancel outdated requests (via `AbortController` or the data layer's built-in cancellation). Alternatively, check a ref or mounted flag before committing state on resolution. Race conditions are subtle but Important.
- **Stale data:** On mutations, invalidate or refetch relevant queries. Stale UI after a mutation is Important.
- **Optimistic updates:** When used, make sure rollback on error actually works. Broken rollback is Important.

## Accessibility

- **Semantic HTML:** Use `<button>` for buttons, `<a href>` for links, `<input>` with proper `type`, `<label>` for form labels. `<div onClick>` is Important - keyboard users and screen readers will miss it.
- **Alt text:** Every `<img>` needs `alt`. Decorative images should use `alt=""` (empty string, not missing).
- **Form labels:** Every input needs an associated `<label>` (via `htmlFor`) or `aria-label`. Placeholder is not a label.
- **Keyboard navigation:** All interactive elements must be reachable via Tab and operable via Enter/Space. Custom dropdowns, modals, and menus need explicit keyboard handling.
- **Focus management:** Modals should trap focus and return it on close. Route changes should announce new page content or move focus.
- **ARIA:** Only use ARIA attributes when native semantics don't suffice. Misused ARIA is worse than no ARIA.
- **Color contrast:** Text needs sufficient contrast against its background (WCAG AA: 4.5:1 for normal text). Automated tools can't catch everything - flag obvious low-contrast cases.
- **Screen reader announcements:** Dynamic content changes should use `aria-live` regions.
- **Skip links:** Long navigation should offer a "skip to main content" link.

## Performance

- **Large bundle imports:** `import _ from 'lodash'` pulls the entire library. Use `import debounce from 'lodash/debounce'` or the modular `lodash-es`. Same for other large libraries (moment, date-fns v1, etc.).
- **Image optimization:** Use next-gen formats (WebP, AVIF). Lazy-load below-fold images with `loading="lazy"`. Provide explicit width/height to prevent layout shift.
- **Code splitting:** Large routes should be lazy-loaded via `React.lazy` and `Suspense`. Loading the entire app on first paint is Important.
- **Virtualization:** Lists over 100 items should be virtualized (react-window, react-virtual, TanStack Virtual). Rendering thousands of DOM nodes is Important.
- **Memoization:** Only memoize where profiled as slow. `React.memo`, `useMemo`, `useCallback` add complexity - they should pay for themselves.
- **Re-render audit:** Frequently re-rendering components should be investigated. React DevTools Profiler is the tool. The reviewer should flag obvious re-render storms.
- **Expensive computations:** Derivations over large data should be memoized. Computing a derived list of 10,000 items on every render is Important.

## Forms

- **Validation timing:** Validate on blur or on submit for expensive checks (uniqueness). Cheap checks (required, format) can be on change.
- **Error messages:** Clear, specific, placed near the field. Generic "Invalid input" is poor UX.
- **Submit state:** Loading state on the submit button. Disable the button during submission to prevent double-submit.
- **Disabled states:** Clear visual indication when a field or button is disabled, and a reason if the disable is surprising.
- **Required fields:** Indicate required fields clearly (either mark required or mark optional - be consistent).
- **Form libraries:** Use the project's form library (react-hook-form, Formik) consistently. Rolling your own for one form is Minor unless it leads to bugs.

## TypeScript

- **Component props:** Typed as `type Props = { ... }` (prefer `type` unless the project uses `interface`).
- **Children:** `children: React.ReactNode` for anything renderable. `JSX.Element` is too narrow - it forbids strings, numbers, arrays, null.
- **Event handlers:** Use specific types: `React.MouseEvent<HTMLButtonElement>`, `React.ChangeEvent<HTMLInputElement>`, etc.
- **Refs:** `useRef<HTMLDivElement>(null)` with the element type.
- **No `any` on props:** Component props should never be `any`. If you need a generic prop, use `unknown` and narrow it.
- **`as const`:** Use for enum-like objects to narrow the type.
- **Discriminated unions:** Prefer for props with mutually exclusive variants (`{ type: 'foo', foo: ... } | { type: 'bar', bar: ... }`).

## Security

- **`dangerouslySetInnerHTML`:** Only with sanitized content (DOMPurify or similar). Unsanitized user content is Critical XSS.
- **URL construction:** Don't construct URLs with user input without encoding. Use `encodeURIComponent` or the URL API.
- **`href` and `src`:** Don't pass user-controlled strings to `href` or `src` without scheme checking. `javascript:` URLs are XSS vectors.
- **CSP:** If the project has a Content Security Policy, flag inline scripts and inline styles.
- **Client-side validation is UX, not security:** The server must also validate. Flag comments or architecture that implies client-side validation is sufficient.
- **Token storage:** Follow the project's convention. If the project uses HTTP-only cookies, new code putting tokens in `localStorage` is a regression.
- **External links:** `target="_blank"` should pair with `rel="noopener noreferrer"` to prevent tabnabbing.

## CSS and Styling

- **Tailwind arbitrary values:** Flag `className="bg-[#123456]"` when a theme token exists. Arbitrary values should be rare.
- **Project convention:** CSS modules, Tailwind, styled-components, or whatever - follow the existing pattern. Mixing approaches is Minor unless it causes maintenance pain.
- **Responsive design:** Mobile-first where the project supports mobile. Desktop-only layouts on a responsive app is Important.
- **Dark mode:** If the project supports dark mode, check both themes. Hardcoded light-mode colors in dark mode is Important.
- **Z-index:** Avoid ad-hoc z-index values. Follow the project's layering scheme.
- **Global styles:** Avoid adding to global CSS unless truly global. Component-scoped styles are preferred.

## Testing

- **Non-trivial logic:** Components with non-trivial logic (state transitions, async handling, complex rendering) should have tests.
- **User-centric queries:** Prefer `getByRole`, `getByLabelText`, `getByText` over `getByTestId`. Tests should match how users interact with the UI.
- **Mock at the network boundary:** Use MSW or similar to mock HTTP calls. Don't mock React internals or internal components.
- **Test user flows:** Prefer tests that exercise "user fills form and clicks submit" over tests that inspect component internals.
- **Snapshot tests:** Use sparingly. Large snapshots become noise and nobody reviews them.
- **Accessibility in tests:** Tests that use `getByRole` naturally verify basic accessibility.

## Internationalization

- **Hardcoded strings:** If the project has i18n, hardcoded user-facing strings are Important.
- **Pluralization:** Use the i18n library's pluralization - don't build your own.
- **RTL support:** If the project supports RTL, flag layout that assumes LTR.

## Routing

- **Lazy loading:** Routes should be code-split via lazy imports where the project supports it.
- **Auth guards:** Protected routes need auth checks. A new protected route without an auth guard is Critical.
- **Deep link support:** URLs should be shareable and deep-linkable. Storing critical state only in component state breaks this.
- **Navigation patterns:** Use the router's `<Link>` or `navigate()`, not raw `<a href>` or `window.location` for in-app navigation.

## Project-Specific Component Libraries

Many projects have a custom component library (often called a design system). When present:

- **Use the library:** Flag raw `<button>`, `<input>`, `<select>`, `<dialog>` etc. when the project has equivalents in its component library.
- **Design tokens:** Flag hardcoded colors, spacing, fonts when the project has tokens for them.
- **Formatting helpers:** Flag `toLocaleString`, `toLocaleDateString`, and ad-hoc number/date formatting when the project has a formatting helper.
