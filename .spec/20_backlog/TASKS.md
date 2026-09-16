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
