---
id: principles
tier: baseline
---

# Engineering principles

> The non-negotiables. Loaded on every task because almost every change can violate one.

- **PRIN-01 Separation of concerns.** Business rules, transport, persistence, and presentation live in different units and do not import each other's internals.
- **PRIN-02 One source of truth.** A fact is defined once — in the schema, the contract, or the domain model — and referenced everywhere else. Duplicated logic across layers is a defect, not a convenience.
- **PRIN-03 Explicit contracts.** Every boundary (HTTP, event, database, module) has a written, versioned contract. Implicit coupling through shared structures is forbidden.
- **PRIN-04 Compatibility first.** Breaking a published contract requires a version, a migration path, a deprecation window, and recorded approval.
- **PRIN-05 Secure by default.** Endpoints are authenticated unless explicitly declared public. Input is untrusted. Authorisation is explicit and enforced server-side.
- **PRIN-06 Observability is part of the feature.** A change that cannot be observed in production is not finished. See `OBSERVABILITY.md`.
- **PRIN-07 Test what breaks.** Deterministic tests on domain rules, contract boundaries, and error paths. Coverage percentage is not a goal; untested critical paths are a defect.
- **PRIN-08 Predictable side effects.** Write operations are idempotent where the contract allows, retries are safe, and every side effect is documented in the contract that triggers it.
- **PRIN-09 Reversibility.** Prefer the change that is cheap to undo. When a decision is expensive to reverse, it needs an ADR before code.
- **PRIN-10 Smallest sufficient change.** Refactors that are not required by the task go to the backlog. Scope creep destroys reviewability.

## Precedence

Within project artifacts, authority runs in this order:

1. **Architecture requirements** — an approved quality-attribute scenario's `Measure`, and an accepted ADR, for the artifact they name.
2. **Global policy** — this folder.
3. **Stack packs** — `.spec/10_stacks/`.
4. **Backlog task** definitions.
5. **Existing code** and agent interpretation.

Global policy and playbook packs state *what kind of thing must be true*. The architecture states *what is true for this system*. Where both speak to the same artifact, the architecture governs and the generic default falls away. Platform and explicit user instructions always outrank all of the above.

### Resolving a conflict

When two selected documents disagree about the same artifact, an agent MUST NOT pick the stricter one, the looser one, or the one it read most recently. It applies this procedure:

1. **Is there an approved quality-attribute scenario whose `Artifact` field names what I am changing?** Its `Measure` governs. Record the scenario id in the handoff beside the criterion it settles.
2. **Is there an accepted ADR covering this decision?** Its decision governs over any generic guidance, including a playbook pack's preferred library, pattern, or structure.
3. **Otherwise, is this a global policy rule (`00_global/`)?** It governs over a playbook pack.
4. **Otherwise the playbook pack's default applies.**
5. **If the architecture and a global *security* or *governance* rule genuinely conflict** — an ADR that requires storing a token in `localStorage`, say — that is not a precedence question. Stop, write `CLARIFICATIONS.md`, and escalate. Security rules are never silently overridden by an ADR; the ADR is amended or the risk is accepted explicitly and logged.

**Worked example.** `NONFUNCTIONAL.md` sets a default of p95 < 300 ms. Scenario `QA-PERF-02` sets p99 ≤ 500 ms end to end for the payment orchestrator. For the payment orchestrator, 500 ms p99 is the requirement and the 300 ms default does not apply; it still applies to every endpoint no scenario names. The agent writes `governed by QA-PERF-02 (p99 ≤ 500 ms); NONFUNCTIONAL default not applicable` in `TASK_CONTEXT.md`, and the acceptance criterion and its test both use 500 ms.

Silently shipping the 300 ms budget over a 500 ms scenario, or the reverse, is a governance failure even when the code works.
