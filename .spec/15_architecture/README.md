# Architecture

This folder holds the ORACE architecture for **this** system. It is empty until you run the workshop:

```
/orace-workshop .spec/15_architecture
```

Expected shape once the workshop completes:

```
outcomes.md                 O — what the system must achieve, what failure it must prevent
quality-scenarios.md        R — measurable quality-attribute scenarios (QA-<ATTR>-<NN>)
approaches.md               A — tactics mapped to scenarios, costs, and status
technology-profile.md       A — component technologies, lifecycle, rationale, evidence, toolchain
decisions/NNN-*.md          A — one ADR per decision that is costly to reverse
views/context.md            C — system boundary and external actors
views/module.md             C — components, responsibilities, owners
views/runtime.md            C — the important flows, sync vs async, failure behaviour
views/deployment.md         C — where things run, trust zones, data residency, AI boundaries
risks/risk-register.md          accepted risks, with owners
evidence/evidence-plan.md   E — the production metrics that prove the architecture works
evolution/backlog.md        E — what to revisit when evidence fails
```

Then run `/spec-bootstrap` to register these artifacts in `.spec/INDEX.md`, derive playbooks and checks from the technology profile, and derive the initial backlog. **Until they are registered, no agent will ever load them** — `scripts/spec.py validate` fails while any artifact here is unregistered, which is how the framework keeps that from happening quietly.

For an architecture created before `approaches.md` and `technology-profile.md` existed, rerun the workshop at this path. Resume detection preserves complete phases and fills the missing Phase A outputs. Later, `/orace-workshop .spec/15_architecture --rerun technology` refreshes only the technology baseline, cross-checks the views, and reports downstream impact before anything else changes.

This folder is canonical: specialists propose changes in their workspace, the supervisor promotes. See `.spec/00_global/GOVERNANCE.md`.
