---
id: play-react
playbook: react-frontend
---

# Playbook pack — React frontend

> Applies `UI_CONVENTIONS.md`, `API_DESIGN.md`, and `SECURITY.md` to a React/TypeScript client. Load for frontend work when this playbook is active.

> **Precedence.** Every number, threshold, and preferred choice in this pack is a *default*.
> Where an approved architecture scenario `Measure` or an accepted ADR speaks to the artifact
> being changed, the architecture governs and the default here falls away
> (`PRINCIPLES.md`, Resolving a conflict). Security rules are the exception: an ADR never
> silently overrides one — escalate instead.

## Baseline

- React 18+ with TypeScript in `strict` mode. `any` requires an inline justification.
- One build tool, one router, one server-state library, one styling system — each chosen once and recorded. Parallel solutions for the same job are a defect.
- ESLint (including `react-hooks` and `jsx-a11y`) and Prettier; both commands in `.spec/project.json` `checks`.

## Layout

```
src/
  app/            routes, providers, layout shell
  features/<x>/   components, hooks, api, model  — a feature owns its slice end to end
  shared/ui/      design-system primitives
  shared/lib/     framework-free helpers
  shared/api/     generated API client and types
```

## Rules

- **RX-01** A feature MUST NOT import another feature's internals. Cross-feature use goes through `shared/` or an explicitly exported public surface.
- **RX-02** API types are **generated** from the OpenAPI contract, not hand-written. Hand-maintained duplicates of server types drift and are forbidden (`PRINCIPLES.md` PRIN-02).
- **RX-03** Server state lives in a server-state library (TanStack Query or equivalent) with explicit `queryKey`, staleness, and invalidation. Server data MUST NOT be copied into global client state.
- **RX-04** Client state is local by default: component state → context for a subtree → a store only for genuinely global concerns. A global store holding fetched data is an anti-pattern.
- **RX-05** Every query surface renders loading, empty, and error states (`UI_CONVENTIONS.md` UI-05). An error boundary wraps each route.
- **RX-06** Effects are for synchronising with something outside React. Deriving state in `useEffect` + `setState` is a defect; compute during render or memoise.
- **RX-07** Hook dependency arrays are complete and the lint rule is never disabled without an inline reason.
- **RX-08** List items use a stable domain id as `key`. Array index keys are forbidden for reorderable or mutable lists.
- **RX-09** Tokens MUST NOT be stored in `localStorage` or `sessionStorage` (`SECURITY.md` SEC-25). Use the identity stack's recommended storage; see the Auth0 pack when active.
- **RX-10** `dangerouslySetInnerHTML` requires sanitised input and a reviewer sign-off. User content is rendered as text by default (`SECURITY.md` SEC-11).
- **RX-11** No secret, private key, or backend-only identifier may appear in client code or the bundle — everything shipped is public.
- **RX-12** Routes are code-split; heavy dependencies are lazy-loaded. A bundle-size budget is enforced in CI and named in the proposal when exceeded.
- **RX-13** Forms use a schema-validated form library, validating against the same contract shape the server enforces; server-side validation remains authoritative (`UI_CONVENTIONS.md` UI-04).
- **RX-14** Tests use Testing Library and query by accessible role and name, never by class name or test-id-only. If a query needs a test id, that is usually an accessibility gap.
- **RX-15** Components are not memoised by default. Add `memo`/`useMemo`/`useCallback` against a measured problem, and say what was measured.

## References — load only when the work needs them

| File | Load when |
|---|---|
| `references/data-and-state.md` | adding queries/mutations, caching, optimistic updates, or forms |
| `references/quality-and-performance.md` | accessibility work, bundle/render performance, or test setup |

## Checks

```sh
npm run lint && npx tsc --noEmit
npm test -- --run
npm run build
```
