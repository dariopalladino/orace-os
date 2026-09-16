# Reference — React accessibility, performance, and tests

Load for accessibility work, bundle or render performance, or test setup.

## Accessible components

```tsx
// UI-12: semantics first. This is a button, so it is a <button>.
<button type="button" onClick={onDelete} aria-describedby="delete-hint">
  Delete invoice {invoice.number}
</button>
<p id="delete-hint">This cannot be undone.</p>
```

- A dialog traps focus, returns focus to the trigger on close, closes on `Escape`, and has an accessible name. Use a maintained primitive (Radix, React Aria) rather than reimplementing it.
- Async results announce themselves: `<div role="status" aria-live="polite">` for success, `role="alert"` for errors (UI-16).
- Route changes move focus to the new page heading, or screen-reader users hear nothing happen (UI-11).
- Icon-only buttons need an accessible name — `aria-label`, or visually hidden text.
- Test what you can: `jest-axe` / `vitest-axe` on rendered components catches a real share of violations. It does not replace a keyboard pass.

## Performance that is worth doing

Measure before optimising (RX-15). In order of typical payoff:

1. **Ship less JavaScript.** Route-level `React.lazy` + `Suspense`; check what a heavy dependency costs before adding it; prefer a date library with tree-shaking over a monolith.
2. **Stop refetch storms.** Correct `staleTime` and query keys remove more re-renders than any memo.
3. **Virtualise long lists.** Beyond a few hundred rows, render a window.
4. **Then** memoise: `memo` on a component that re-renders often with equal props; `useCallback` for a prop passed to a memoised child; `useMemo` for a genuinely expensive computation.

Blanket memoisation adds comparison cost and hides the real problem. When you do add it, say in the proposal what you measured and by how much it improved.

Budgets to enforce in CI: initial JS transfer size, largest contentful paint on the main route, interaction-to-next-paint. Exceeding one is a proposal item, not a silent regression (RX-12).

## Testing

```tsx
test('shows a message when there are no orders', async () => {
  server.use(http.get('/api/orders', () => HttpResponse.json({ items: [] })))
  render(<OrdersPage />, { wrapper: Providers })

  expect(await screen.findByRole('status')).toHaveTextContent(/no orders yet/i)
})
```

- Query by role and accessible name (RX-14). If you cannot, the component is probably inaccessible — fix that instead of adding a test id.
- Mock at the network layer (MSW), not by stubbing the fetch hook. Stubbing the hook tests your stub.
- `userEvent` over `fireEvent`: it models real interaction, including focus and keyboard.
- Assert on what the user sees: rendered text, enabled state, announced message. Never on internal state or call counts.
- Give every async assertion a bounded `findBy*`; no arbitrary waits (TEST-09).

## Bundle hygiene

- No secret, private key, or internal hostname in the bundle — everything shipped is public (RX-11).
- Audit what environment variables the build inlines; a prefix like `VITE_`/`NEXT_PUBLIC_` means *published to every visitor*.
- Check the bundle for accidental full-library imports (`import _ from 'lodash'`) in review.
