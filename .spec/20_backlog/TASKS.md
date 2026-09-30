# Task backlog

The canonical task source. `/spec-bootstrap` derives the initial entries from the architecture; the supervisor records subsequent authorised work here. Workspace artifacts support tasks but never become requirements on their own.

Acceptance criteria that come from a quality-attribute scenario are copied **verbatim** from its `Measure` field, and the test that defends each one is named after the scenario id.

## Template

```markdown
## <ID> — <objective in one line>

- Status: ready | in_progress | blocked | complete
- Priority: 1 | 2 | 3
- Package: <WP-ID — the sub-agent assignment this belongs to>
- Owner: <agent role>
- Authorization: <the request or approval that authorises this work>
- Surfaces: <comma-separated semantic surfaces>
- Paths: <affected or planned paths>
- Specifications: <routing ids from .spec/INDEX.md>
- Objective: <what must become true; note which requirement governs where a default is displaced>
- Dependencies: <task ids that must complete first>
- Acceptance criteria:
  - <observable outcome, with the scenario Measure verbatim where one applies>
  - Test `test_<scenario_id>_<slug>` asserts each measure above.
  - Metrics `<names>` instrumented per `evidence/evidence-plan.md`.
```

`Surfaces`, `Paths`, and `Specifications` are read by `python3 scripts/spec.py select --task <ID>`. A task without them cannot be routed deterministically.

---

<!-- tasks start -->

## ORACE-TECH-001 — Add an evidence-backed technology profile to the ORACE workflow

- Status: complete
- Priority: 1
- Package: WP-ORACE-TECHNOLOGY
- Owner: framework supervisor
- Authorization: User request on 2026-09-28 to make the changes necessary for new and existing projects to benefit when rerunning the ORACE workshop.
- Surfaces: architecture, planning, governance, docs, testing
- Paths:
- Specifications: protocol, principles, governance, testing
- Objective: The workshop must capture project-specific technology constraints, choices, rationale, lifecycle, and evidence without making quality requirements implementation-dependent; bootstrap must route that profile into playbooks, checks, and task context.
- Dependencies: none
- Acceptance criteria:
  - New projects can produce `approaches.md` and `technology-profile.md` with planned choices, version policy, rationale, source of truth, and playbook mapping.
  - Existing projects can rerun only technology discovery, classify observed choices as retain/migrate/retire/TBD, and receive downstream impact reporting without silent overwrites.
  - Bootstrap treats the technology profile as the primary source for evidenced playbooks and checks and registers it selectively.
  - User-facing adoption and initialization guidance uses the same workshop-first workflow.
  - Framework validation, skill synchronization, and unit tests pass.

## ORACE-USAGE-001 — Report workshop-scoped token consumption

- Status: complete
- Priority: 2
- Package: WP-ORACE-USAGE
- Owner: framework supervisor
- Authorization: User request on 2026-09-28 to add a final consumed-token count to the ORACE workshop.
- Surfaces: architecture, governance, docs, testing
- Paths:
- Specifications: protocol, principles, governance, ai-governance, testing
- Objective: Every completed workshop or targeted rerun reports host-measured token usage when available, otherwise labels an evidenced estimate or unavailable data honestly, with an explicit invocation boundary and no category double-counting.
- Dependencies: ORACE-TECH-001
- Acceptance criteria:
  - A usage boundary is captured before workshop discovery or interview work.
  - The final report distinguishes measured, estimated, and unavailable usage and names its source and scope.
  - Cached input remains included in input; reasoning remains included in output; total is input plus output.
  - The report discloses the final-response boundary, best-effort accounting, subagent inclusion, and the absence of billing claims.
  - Usage is not persisted as normative architecture.
  - Framework validation, skill synchronization, and unit tests pass.

## ORACE-README-001 — Document the latest ORACE technology and token-usage workflow

- Status: complete
- Priority: 2
- Package: WP-ORACE-README
- Owner: framework supervisor
- Authorization: User request on 2026-09-28 to update `README.md` with the technology step and token consumption tracking.
- Surfaces: docs, architecture, governance, testing
- Paths:
- Specifications: protocol, ai-governance, clean-architecture, ddd, governance, hitl, principles, testing
- Objective: The top-level README must accurately explain the completed technology-profile lifecycle and workshop-scoped token accounting so architects can apply both features without inspecting skill internals.
- Dependencies: ORACE-TECH-001, ORACE-USAGE-001
- Acceptance criteria:
  - The README covers technology capture across ORACE phases, greenfield and brownfield behavior, artifact ownership, targeted reruns, and bootstrap consumption.
  - The README covers measured, trace-counted, and unavailable token reporting; accounting and scope boundaries; billing limitations; and non-persistence.
  - The README explicitly distinguishes selector context estimates from workshop consumption reports.
  - Content-contract tests and all framework checks pass.
