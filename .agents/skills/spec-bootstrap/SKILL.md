---
name: spec-bootstrap
description: Wire a completed ORACE architecture into the SDDF specification store — register routing rows, select playbooks, derive the initial backlog from quality scenarios and ADRs, and validate. Use after /orace-workshop, or when adopting SDDF into a repository that already has architecture artifacts.
trigger: /spec-bootstrap
---

# Spec bootstrap — ORACE to SDDF

The handoff. ORACE produced normative content; SDDF enforces it. Nothing in between happens automatically: an unregistered architecture artifact is invisible, because every agent routes through `.spec/INDEX.md` and is forbidden from reading the store wholesale.

Run this once after the architecture exists, and again whenever the architecture grows a new artifact that has no routing row.

```
/spec-bootstrap                 # use architecture_root from .spec/project.json
/spec-bootstrap <path>          # an architecture folder elsewhere (e.g. ./architecture)
```

## Step 1 — Read what exists

Resolve the architecture root: the argument, else `.spec/project.json` `architecture_root`, else `.spec/15_architecture`, else `./architecture`.

List the tree and read `outcomes.md`, `quality-scenarios.md`, `views/module.md`, `views/deployment.md`, and each ADR title and status. Do not read every file in full — you need the artifact inventory, the scenario ids and their `Artifact` fields, the module names, and the ADR subjects.

Report what you found and what is missing. If `quality-scenarios.md` is absent, stop: there is nothing to derive a backlog from. Send the user back to `/orace-workshop`.

## Step 2 — Check scenario ids and measures

Every scenario needs a stable id of the form `QA-<ATTR>-<NN>` and a `Measure` containing a number.

- A scenario with no id: propose one, show the list, and write the ids into `quality-scenarios.md` after the user confirms. Ids become acceptance criteria and test names; renaming them later breaks traceability.
- A `Measure` with no number ("fast", "reliable", "as quickly as possible"): list these and tell the user plainly that they cannot become acceptance criteria. Offer to run the Phase R questions for just those scenarios. Do **not** invent a number.

## Step 3 — Select playbooks

Read the module and deployment views and the ADRs, and propose the playbook packs the system needs from those registered under `.spec/10_playbooks/`. Match on real evidence — a named language, framework, or provider — not on a guess from the domain.

Show the proposal with the evidence for each, ask for confirmation, then write the confirmed list to `.spec/project.json` `playbooks`.

If the architecture names a technology with no registered playbook (Java, Go, Terraform, a compliance regime), say so and offer:

```sh
python3 scripts/spec.py scaffold java-backend
```

which creates the pack skeleton and prints the routing row to add. Never stretch an existing pack to cover a technology it was not written for — a Python pack applied to a Java service produces confidently wrong rules.

Also set `module_roots` from the module view, so that a file path routes to the right surfaces. Planned directories are fine; they do not need to exist yet.

## Step 4 — Register routing rows

Add one row per artifact to the `.spec/INDEX.md` table. Columns: `ID | Path | Surfaces | Requires | Playbooks`.

Defaults, to be adjusted against what the artifacts actually say:

| Artifact | Surfaces | Requires |
|---|---|---|
| `outcomes.md` | `planning,architecture,governance` | `principles` |
| `quality-scenarios.md` | the union of surfaces its `Artifact` fields name, plus `planning,architecture,review` | `outcomes,nonfunctional` |
| `views/context.md` | `planning,architecture,docs` | `outcomes` |
| `views/module.md` | `architecture,domain` plus the surfaces of the modules it names | `quality-scenarios` |
| `views/runtime.md` | `architecture,backend,api,infra` | `quality-scenarios` |
| `views/deployment.md` | `infra,security,auth,data` | `security,quality-scenarios` |
| `risks/risk-register.md` | `planning,governance,review` | `outcomes` |
| `evidence/evidence-plan.md` | `review,release,observability` | `quality-scenarios,done` |
| `evolution/backlog.md` | `planning` | `outcomes` |
| `decisions/NNN-*.md` | **only** the surfaces the decision actually constrains | `quality-scenarios` plus the policy it specialises |

Three of these carry most of the value:

- **`quality-scenarios` is deliberately wide.** The scenarios are what the system must prove it can do, and almost any change can violate one. It depends on `nonfunctional` so the generic defaults and the governing numbers always arrive together — and the agent can see which one displaces which.
- **`view-deployment` carries `security` and `auth`.** It holds trust zones, data residency, and the AI capability boundary. That mapping is what makes a frontend task touching token storage pull in the trust-zone document. It prevents a recurring and expensive class of mistake.
- **One row per ADR, never one row for the folder.** A folder row means that at fifteen ADRs every task drags in every decision ever made, which converts selective loading back into read-everything. Give each ADR only the surfaces its decision constrains: an audit-log persistence decision is `data`, not `data,backend`.

Use the `Playbooks` column to scope a row that only applies to one technology. Architecture artifacts are almost always `*`.

## Step 5 — Derive the initial backlog

Write tasks into `.spec/20_backlog/TASKS.md`. This is where the two frameworks actually join: **an ORACE `Measure` is already an acceptance criterion** — specific, numeric, testable. Copy it across verbatim. Do not paraphrase it and do not soften it.

For each scenario, and for each ADR that requires implementation work, propose a task:

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
- Objective: <what must become true, referencing the scenario or ADR>
- Acceptance criteria:
  - <Measure field, verbatim>
  - Test `test_<scenario_id_lowercased>_<slug>` exercises the scenario and asserts each measure.
  - Metrics `<names from the evidence plan>` are instrumented with the thresholds recorded there.
```

**Work packages.** Group tasks that share surfaces, playbooks, and file ownership into a package (`WP-AUTH`, `WP-ORDERS-API`, `WP-MOBILE-SHELL`). One package is one sub-agent's assignment, so packages dispatched together must have disjoint file ownership. A package that spans three playbooks and every module is not a package; split it.

Name each scenario's test after its id (`QA-AVAIL-01` → `test_qa_avail_01_screening_outage`). This is the one naming convention worth enforcing: it makes the requirement greppable from the test suite and the test greppable from the architecture, for a human six months later and for an agent in a fresh context.

Present the derived backlog for approval before writing it. The user decides priority and sequence; you propose.

## Step 6 — Check the precedence surface

Compare each scenario `Measure` against the defaults in `.spec/00_global/NONFUNCTIONAL.md` and any active playbook pack. Where a scenario is stricter *or looser* than a default, note it explicitly in the task's `Objective` line:

```
governed by QA-PERF-02 (p99 ≤ 500 ms); NONFUNCTIONAL 300 ms default not applicable
```

The framework already resolves this in favour of the architecture (`PRINCIPLES.md`, Resolving a conflict), so no policy edit is needed — but an agent that has not been told which number governs will read both and guess. Writing it into the task removes the guess.

If a scenario or ADR conflicts with a **security** rule rather than a performance default, do not record a precedence note. Raise it: security rules are not overridden by an ADR without an explicit, logged risk acceptance.

## Step 7 — Validate and report

```sh
python3 scripts/spec.py validate
python3 scripts/spec.py select --task <first task id>
```

`validate` fails while any architecture artifact is unregistered — that check is the reason this step exists. Fix the registry until it passes.

Then show the user the selection for one real task: which documents it pulled, why each one, and the token estimate. That output is the evidence that the wiring works, and it is worth reading carefully — if a task about a login form is not pulling the deployment view, a surface mapping is wrong.

Finally, record the bootstrap in `.spec/30_delivery/PROMOTION_LOG.md`: what was registered, which playbooks were activated, how many tasks were derived, and the validation result.

## Rules

- Propose, then write. The user approves ids, playbooks, surfaces, and the backlog before anything canonical changes.
- Never invent a `Measure`, a threshold, a scenario, or an ADR. Missing content goes back to the architecture interview.
- Never register a folder as one row.
- Never copy ORACE content into `.spec/00_global/`. The global folder holds policy that outlives any single system; duplicating a scenario there creates two sources of truth with different change-control paths.
- An ADR added later is not finished until its row exists and `validate` passes.
