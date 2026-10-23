## Phase E — Evidence & Evolution

**Goal**: define how the architecture will be proven to work in production, and how evidence failures drive evolution. Output: `evidence/evidence-plan.md`, `evolution/backlog.md`.

Ask:

"We're building the evidence plan — the production metrics that prove the architecture is actually working.

For each quality-attribute scenario we defined, I need:
1. The metric name
2. What it proves (one sentence)
3. The target value (the architecture is healthy when this holds)
4. The alert threshold (investigate when this is crossed)
5. How it is collected (APM tool, log aggregation, custom counter, chaos test, etc.)

Let's go through each scenario."

For each scenario in `quality-scenarios.md`, ask the five questions above.

Then ask:

"Beyond the per-scenario metrics, are there any one-time validation tests or drills needed before the first production release? Examples: load test at 2× peak volume, chaos test killing a dependency, regulatory retrieval drill, provider-switch drill."

Review `technology-profile.md` and ask one at a time about any architectural technology assumption that still needs proof: capacity, driver or protocol compatibility, migration safety, provider portability, operability, licensing, or support lifetime. Add a validation test only when it has a measurable pass criterion. Routine dependency-update checks do not belong in the architecture evidence plan.

Finally ask:

"When evidence fails and the architecture needs to evolve, what are the known improvement candidates — things you expect to revisit? These go into the evolution backlog."

Write `evidence/evidence-plan.md` and `evolution/backlog.md` using these templates:

```markdown
---
orace_phase: E
generated_by: orace-workshop
generated_at: YYYY-MM-DD
---

# Evidence Plan — [System Name]

> Evidence converts the architecture from a hypothesis into a proven design.
> These metrics run continuously in production. A metric in the red means the architecture assumption it validates is failing.

## Production Metrics

| Metric | Proves | Target | Alert at | How collected |
|--------|--------|--------|----------|---------------|
| [metric name] | [what it proves — one sentence] | [target value] | [alert threshold] | [collection method] |

## Pre-Release Validation Tests

| Test | Scenario Validated | Pass Criterion | Owner |
|------|--------------------|---------------|-------|
| [test name] | [scenario] | [measurable pass/fail] | [team] |

## Technology Assumption Tests

| Assumption | Profile entry / ADR | Validation | Pass criterion | Owner |
|------------|---------------------|------------|----------------|-------|
| [architecturally significant technology assumption] | [unit/category or ADR] | [spike, compatibility test, migration rehearsal, capacity test] | [measurable result] | [team] |

## Governance Signals (for AI components, if present)

| Signal | Healthy range | Action if outside range |
|--------|--------------|------------------------|
| Human override rate on AI proposals | 5%–25% (stable) | < 2%: audit for rubber-stamping; > 40%: retrain or remove |
| AI grounded-claim rate | ≥ 95% with evidence references | < 90%: review model outputs before next deployment |
| Unauthorized capability attempts | 0 | Any non-zero: security incident |
```

```markdown
---
orace_phase: E
generated_by: orace-workshop
generated_at: YYYY-MM-DD
---

# Evolution Backlog — [System Name]

> Items to revisit when evidence signals the architecture needs to change.
> Each item links back to the evidence signal that would trigger it.

| ID | Item | Trigger signal | Revisit level | Owner | Status |
|----|------|---------------|---------------|-------|--------|
| E-001 | [improvement] | [metric or signal] | Outcomes / Requirements / Approaches / Communication | [team] | Pending |
```
