---
id: ui
---

# UI conventions

> Stack-neutral rules for anything a person looks at. Load for frontend and native work.

## Structure

- **UI-01** Screens compose from a shared design system. A one-off component that duplicates an existing one is a defect; extend the system or record why it cannot be extended.
- **UI-02** Design tokens (colour, spacing, radius, typography, motion) are defined once and referenced. Hard-coded hex values, pixel spacing, and font sizes in components are forbidden.
- **UI-03** Components are presentational by default. Data fetching, navigation, and business rules live in containers, hooks, or view models — not inside a rendering component.
- **UI-04** No business rule is implemented only on the client. Client-side validation is a convenience; the server decides.

## State

- **UI-05** Every asynchronous view models four states explicitly: loading, empty, error, and success. A screen with no empty state and no error state is incomplete.
- **UI-06** Errors are shown in the user's language with a recovery action. Never surface raw status codes, stack traces, or backend messages.
- **UI-07** Destructive actions require confirmation and, where feasible, an undo window. Confirmation text names the specific object.
- **UI-08** Optimistic updates MUST have a defined rollback and a visible failure path.
- **UI-09** Forms preserve user input across failures. Losing typed data on a validation error is a defect.

## Accessibility

- **UI-10** Target WCAG 2.2 AA. Text contrast ≥ 4.5:1 (≥ 3:1 for large text and meaningful non-text).
- **UI-11** Every interactive element is reachable and operable by keyboard, with a visible focus indicator. Focus is managed on route change, dialog open, and dialog close.
- **UI-12** Semantic elements first; ARIA only to fill a genuine gap. A `div` with a click handler is not a button.
- **UI-13** Every input has a programmatically associated label; every meaningful image has alt text; decorative images are hidden from assistive technology.
- **UI-14** Colour is never the only carrier of meaning. Errors, statuses, and chart series carry a second signal.
- **UI-15** Motion respects `prefers-reduced-motion`, and no content flashes more than three times per second.
- **UI-16** Live regions announce asynchronous changes that matter (submission result, validation summary, background completion).

## Performance and resilience

- **UI-17** Interaction feedback appears within 100 ms; anything past ~1 s shows determinate or indeterminate progress. Skeletons replace layout, they do not shift it.
- **UI-18** Layout is responsive from the smallest supported width up, with no horizontal scroll on the page body and touch targets ≥ 44 px.
- **UI-19** Images and media declare intrinsic dimensions or an aspect ratio to prevent layout shift.
- **UI-20** The interface works in both light and dark themes when the product supports them; every colour is defined in both.
- **UI-21** Copy is consistent: sentence case for labels, no jargon, no blame, one term per concept across the whole product.

## Review checks

- Keyboard-only pass through the changed flow.
- Contrast checked on new colour pairings.
- Loading, empty, and error states demonstrated.
- No new hard-coded design values.
