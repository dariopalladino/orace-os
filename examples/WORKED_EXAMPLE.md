# Worked example — one requirement, end to end

A payment system, followed from a stakeholder's sentence to a closed task. Nothing here is normative; it exists to show the shape of the artifacts and how they connect.

---

## 1. ORACE — Phase O, the failure to prevent

From the workshop interview, in `outcomes.md`:

> **Business failure to prevent:** a payment is confirmed to the customer without having been screened for sanctions. Impact: regulatory breach, licence risk, per-incident fines.

Note what this is *not*: it is not "the screening service should be reliable". It names a specific business failure with a consequence, which is what makes the next step possible.

## 2. ORACE — Phase R, the measurable scenario

In `quality-scenarios.md`:

```markdown
## QA-AVAIL-01 — Availability

| Field | Value |
|-------|-------|
| **Source** | The third-party sanctions-screening provider |
| **Stimulus** | The provider becomes unreachable (connection refused or > 10 s timeout) |
| **Environment** | Normal production load, 3,000 transactions per second |
| **Artifact** | Payment Orchestration service |
| **Response** | Stop confirming payments that depend on screening; queue them durably; degrade to a "pending review" state visible to the customer; recover automatically when the provider returns |
| **Measure** | Unreachability detected in ≤ 5 s. Recovery completes in ≤ 30 s after the provider returns. Zero transactions permanently lost; dead-letter depth returns to zero within 30 s of recovery. No payment is confirmed without a screening result under any condition. |
```

The `Measure` field is the whole point. "Recovers quickly" would have produced nothing downstream.

## 3. ORACE — Phase A, the decision

`decisions/001-circuit-breaker-dlq.md`, written through `/orace-adr`:

> **Decision:** wrap screening calls in a circuit breaker with a dead-letter queue for failed screenings. Explicitly **not** chosen: failing the payment outright (loses transactions), or confirming optimistically and screening later (the exact failure Phase O forbids).
>
> **Risk accepted:** customers see a "pending review" state during a provider outage. Owner: Head of Payments.

## 4. `/spec-bootstrap` — registration

The rows added to `.spec/INDEX.md`:

```markdown
| outcomes | .spec/15_architecture/outcomes.md | planning,architecture,governance | principles | * |
| quality-scenarios | .spec/15_architecture/quality-scenarios.md | planning,architecture,backend,api,infra,review | outcomes,nonfunctional | * |
| view-runtime | .spec/15_architecture/views/runtime.md | architecture,backend,api,infra | quality-scenarios | * |
| view-deployment | .spec/15_architecture/views/deployment.md | infra,security,auth,data | security,quality-scenarios | * |
| evidence-plan | .spec/15_architecture/evidence/evidence-plan.md | review,release,observability | quality-scenarios,done | * |
| adr-001-circuit-breaker | .spec/15_architecture/decisions/001-circuit-breaker-dlq.md | backend,infra | quality-scenarios,architecture | * |
```

Three details carry the weight:

- `quality-scenarios` is on many surfaces because almost any change can violate a scenario, and it requires `nonfunctional` so the generic defaults and the governing numbers always arrive together.
- `view-deployment` carries `security` and `auth`, which is what makes a *frontend* task touching token storage pull in the trust-zone document.
- ADR-001 gets `backend,infra` — the surfaces its decision actually constrains. Not `*`, and not a single row for the whole `decisions/` folder.

## 5. The derived task

In `.spec/20_backlog/TASKS.md`:

```markdown
## PAY-014 — Screening outage degradation for payment orchestration

- Status: ready
- Priority: 1
- Package: WP-PAYMENTS-RESILIENCE
- Owner: Backend-Agent
- Authorization: User approved implementation of QA-AVAIL-01.
- Surfaces: backend, infra, security, implementation, review
- Paths: services/payments/
- Specifications: quality-scenarios, adr-001-circuit-breaker, view-runtime, view-deployment, evidence-plan, security
- Objective: Implement circuit-breaker + dead-letter degradation in the Payment Orchestration
  service per ADR-001, so a screening outage never confirms an unscreened payment and never
  loses a transaction. Governed by QA-AVAIL-01; NONFUNCTIONAL availability default not applicable.
- Acceptance criteria:
  - Screening unreachability is detected in ≤ 5 seconds under 3,000 TPS.
  - Recovery completes in ≤ 30 seconds after screening returns.
  - Zero transactions permanently lost; dead-letter depth is zero 30 s after recovery.
  - No payment is confirmed without a screening result under any condition.
  - Chaos test `test_qa_avail_01_screening_outage` exercises the scenario and asserts each measure.
  - Metrics `circuit_breaker_open_rate` and `dlq_depth` are instrumented with the alert
    thresholds recorded in `evidence/evidence-plan.md`.
```

Every criterion is traceable: to the scenario, to the ADR that chose the tactic, to the evidence plan that will watch it in production. The measures were copied, not paraphrased.

## 6. Routing

```sh
python3 scripts/spec.py select --task PAY-014
```

Selects the baseline, the policies for those surfaces, the Python pack, and — from the architecture — the scenarios, the runtime and deployment views, the evidence plan, and ADR-001. It leaves out the context view, the UI conventions, the React and Kotlin packs, and every other ADR.

## 7. Where the frameworks interlock mid-task

The agent discovers that the dead-letter queue needs an ordering guarantee ADR-001 never addressed.

It does not choose one. `AI_GOVERNANCE.md` AIG-01 and `AGENT_EXECUTION_PROTOCOL.md` PROTO-07 both forbid that: it writes `CLARIFICATIONS.md` and stops.

The supervisor's resolution is `/orace-adr` → `decisions/003-dlq-ordering.md` → a routing row → a promotion entry → the task unblocks. This is the neatest fit between the two halves: **an ORACE decision record is the answer to an SDDF clarification.** The alternative — the agent silently picking an ordering strategy — is exactly the invisible assumption both frameworks exist to prevent.

## 8. Review

`/spec-review PAY-014` reads the task context and the handoffs, and checks the claims that matter:

- The criterion says recovery in ≤ 30 s. The handoff cites `test_qa_avail_01_screening_outage`. Does that test actually assert 30 s, or does it mock the recovery and assert a flag? → **covered** or **unproven**.
- The evidence plan names `dlq_depth`. Is that exact name emitted? → spot-check.
- Was the 500 ms figure in the scenario quietly replaced by the 300 ms default from `NONFUNCTIONAL.md`? → precedence check.
- Did anything outside `services/payments/` change? → scope check.

Verdict `accept`, `revise`, or `reopen`, with ordered required actions.

## 9. When production disagrees

`evidence/evidence-plan.md` says `circuit_breaker_open_rate` should stay under 0.5%. It runs at 4%. The architecture's assumption — that provider outages are rare — was wrong.

ORACE's evolution phase says return to the *correct* level, not reflexively to the top:

| What failed | Revisit level | What actually happens |
|---|---|---|
| Implementation drifted from ADR-001 | Communication | New backlog task; existing criteria reopen; no promotion |
| The circuit breaker cannot meet the measure | Approaches | `/orace-adr` supersedes ADR-001; new row; promotion entry |
| The 30 s measure is not achievable or not meaningful | Requirements | Amend the scenario under promotion; every task citing it reopens |
| Regulation changed what "screened" means | Outcomes | Re-run the affected workshop phases; re-derive downstream |

Because the architecture is registered, it is canonical: an agent may *propose* a change to `quality-scenarios.md`, but only the supervisor promotes it, with a log entry. An agent cannot weaken a scenario to make its test pass.
