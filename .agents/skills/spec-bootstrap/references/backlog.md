## Step 5 — Derive the initial backlog

Write tasks into `.spec/20_backlog/TASKS.md`. This is where the two frameworks actually join: **an ORACE `Measure` is already an acceptance criterion** — specific, numeric, testable. Copy it across verbatim. Do not paraphrase it and do not soften it.

For each scenario, each ADR that requires implementation work, and each unresolved technology-profile item that requires a spike, migration, retirement, evidence collection, or missing playbook, propose a task. Do not turn every accepted technology row into a task.

```markdown
## <ID> — <objective in one line>

- Status: ready
- Priority: <1-3>
- Package: <WP-ID>
- Owner: <role>
- Authorization: <the request or approval that authorises this work>
- Surfaces: <comma-separated>
- Paths: <planned or affected module roots>
- Specifications: <routing ids, comma-separated>
- Objective: <what must become true, referencing the scenario, ADR, or technology-profile entry>
- Acceptance criteria:
  - <Measure field, verbatim>
  - Test `test_<scenario_id_lowercased>_<slug>` exercises the scenario and asserts each measure.
  - Metrics `<names from the evidence plan>` are instrumented with the thresholds recorded there.
```

**Work packages.** Group tasks that share surfaces, playbooks, and file ownership into a package (`WP-AUTH`, `WP-ORDERS-API`, `WP-MOBILE-SHELL`). One package is one sub-agent's assignment, so packages dispatched together must have disjoint file ownership. A package that spans three playbooks and every module is not a package; split it.

Include the `technology-profile` routing id and applicable playbook id in a task's `Specifications` when the task implements, migrates, or retires that technology choice. The profile says what this project uses and why; the playbook says how to use it correctly.

Name each scenario's test after its id (`QA-AVAIL-01` → `test_qa_avail_01_screening_outage`). This is the one naming convention worth enforcing: it makes the requirement greppable from the test suite and the test greppable from the architecture, for a human six months later and for an agent in a fresh context.

Present the derived backlog for approval before writing it. The user decides priority and sequence; you propose.
