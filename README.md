# SDDF — Spec-Driven Development Framework

**Architecture that AI coding agents actually read, and a lifecycle that makes them prove they read it.**

SDDF is a portable governance layer for coding agents — Claude Code, Codex, GitHub Copilot, or anything you can point at a file. It wraps [ORACE](#orace-the-front-door), an architecture method that produces a traceable chain from business outcome to production metric, and turns that architecture into constraints an agent is handed at the moment it writes code.

Two halves, one line between them:

> **ORACE is normative content. SDDF is normative process.**
> ORACE says *the payment orchestrator must recover within 30 seconds*.
> SDDF makes sure the agent editing the orchestrator has read that sentence, cannot close the task without evidence against it, and cannot quietly change it.

Each half has a hole exactly the shape of the other. ORACE produces requirements and has no mechanism for delivering them — the artifacts sit in a folder, and "paste the file list into your prompt" stops working at twelve ADRs. SDDF knows how to route, gate, and evidence requirements it does not itself have.

---

## The division of labour

| Concern | Owner | Lives in |
|---|---|---|
| Why the system exists; what business failure it must prevent | ORACE | `outcomes.md` |
| Measurable quality-attribute scenarios | ORACE | `quality-scenarios.md` |
| Why each costly decision was made, and what was rejected | ORACE | `decisions/NNN-*.md` |
| Component ownership, runtime flows, trust zones, AI boundaries | ORACE | `views/` |
| What proves it works in production | ORACE | `evidence/evidence-plan.md` |
| Engineering policy that outlives any one system | SDDF | `.spec/00_global/` |
| Technology and domain guidance (Python, React, Kotlin, Auth0, …) | SDDF | `.spec/10_playbooks/` |
| Which documents *this* task needs | SDDF | `.spec/INDEX.md` |
| Who may approve and change what | SDDF | `GOVERNANCE.md`, `AGENT_EXECUTION_PROTOCOL.md` |
| Task scope, acceptance criteria, ownership | SDDF | `20_backlog/TASKS.md`, `40_workspace/<id>/TASK_CONTEXT.md` |
| Evidence that the agent did what it claimed | SDDF | `agent_<role>/HANDOFF.md`, `REVIEW_REPORT.md`, `PROMOTION_LOG.md` |

---

## The pipeline

```
 /orace-workshop          architecture interview          .spec/15_architecture/
        │                 one question at a time          outcomes, scenarios, ADRs,
        ▼                                                 views, risks, evidence plan
 /spec-bootstrap          register + derive                INDEX.md rows, playbooks,
        │                                                  backlog with verbatim measures
        ▼
  spec-workflow           select → propose → execute       one sub-agent per work package
        │                 → handoff                        loading only what it routed to
        ▼
 /spec-review             judge evidence and handoffs      accept / revise / reopen
        │
        ▼
    supervisor            promote + close on evidence      PROMOTION_LOG.md
        │
        └──── production evidence fails ──▶ /orace-adr or a workshop phase ──▶ back to the top
```

Nothing between those steps is automatic, and that is deliberate. The one step people skip — registering the architecture in the routing index — is the step `scripts/spec.py validate` refuses to let you skip.

---

## Quick start

### A new system

```bash
python3 scripts/init_project.py --target /path/to/your/repo
cd /path/to/your/repo
```

Then, in your agent:

```
/orace-workshop .spec/15_architecture     # half a day, with real stakeholders
/spec-bootstrap                            # register, pick playbooks, derive the backlog
```

```bash
python3 scripts/spec.py validate           # must be clean before the first task
```

Run the workshop **first**. There is nothing to route until the architecture exists, and a backlog derived from guesses is worse than no backlog.

### An existing repository

Same installer, on a branch. It copies `.spec/`, `.agents/`, `.claude/`, `scripts/`, `tests/`, and **merges** rather than overwrites your `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` — your conventions stay, an SDDF section is appended below them. It refuses to overwrite an existing `.spec/`.

Then:

1. Edit `.spec/project.json` — active `playbooks`, `module_roots` mapped to your real directories, your real `checks`.
2. Run `/orace-workshop`. For an existing system this is documentation rather than design, and it goes faster — but the `Measure` fields still need real numbers, and this is where you find out you do not have them.
3. Run `/spec-bootstrap`, then `validate`.
4. Calibrate the routing before you trust it (below), then run **one** proposal-only task and read what it selected.

Full detail in [`docs/ADOPTION.md`](docs/ADOPTION.md). A complete requirement followed from a stakeholder's sentence to a closed task is in [`examples/WORKED_EXAMPLE.md`](examples/WORKED_EXAMPLE.md).

---

## What's in the box

| Path | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | The operating contract. Short on purpose — it is paid for on every turn |
| `CLAUDE.md`, `.github/copilot-instructions.md` | Thin host adapters pointing at the same contract |
| `.agents/skills/` | Canonical skills: `orace-workshop`, `orace-adr`, `spec-bootstrap`, `spec-workflow`, `spec-review` |
| `.claude/skills` | Symlink to the canonical tree, with a copy fallback |
| `.claude/agents/` | Ten compact role definitions, supervisor through reviewer |
| `.claude/commands/` | Slash commands wrapping the skills |
| `.spec/INDEX.md` | The routing registry — the only way agents find anything |
| `.spec/project.json` | Active playbooks, module roots, orchestration, context budget, checks |
| `.spec/00_global/` | 15 policy packs: protocol, principles, governance, clean architecture, DDD, API, data modelling, OWASP security, AI governance, human-in-the-loop, UI, testing, observability, NFR, definition of done |
| `.spec/10_playbooks/` | Technology packs: Python backend, React frontend, Kotlin native, Auth0 identity — plus any you add |
| `.spec/15_architecture/` | This system's ORACE artifacts (empty until the workshop runs) |
| `.spec/20_backlog/TASKS.md` | The only task list |
| `.spec/30_delivery/PROMOTION_LOG.md` | Evidence for every canonical change |
| `.spec/40_workspace/<task-id>/` | Task context, proposals, handoffs, reviews |
| `scripts/spec.py` | Validate, select, scaffold |
| `docs/`, `examples/`, `tests/` | Adoption, extension, a worked example, 24 tests |

Every rule in every pack has a stable id — `SEC-03`, `CA-02`, `PY-08`, `KT-12` — so a handoff, a review finding, or a rejection can cite it and a human can look it up.

---

## How selective loading works

Every agent routes through `.spec/INDEX.md` and is **forbidden from reading the specification store wholesale**. A row maps a document to the semantic surfaces it governs, its dependencies, and the playbooks it belongs to.

```bash
python3 scripts/spec.py select --surface frontend --surface auth --path web/src/login.tsx
```

```
security    .spec/00_global/SECURITY.md      surface:auth; required by:play-auth0; required by:api-design
ui          .spec/00_global/UI_CONVENTIONS.md  path:web/src/login.tsx -> frontend; required by:play-react
play-auth0  .spec/10_playbooks/auth0-identity/PACK.md  surface:auth
…
Selected 12 of 19 registered specifications (7 not loaded); ~11484 tokens
```

A change to a login form pulled in the identity pack and the security baseline because `auth` was on the task, while the Kotlin pack, the data-modelling rules, and the observability policy stayed out.

**Real numbers from this repository** (`characters ÷ 4`, not measured tokens; the full store is 19 documents):

| Task shape | Loaded | Estimate |
|---|---|---|
| Documentation only | 2 of 19 | ~2,100 |
| Review / close-out | 6 of 19 | ~5,000 |
| Database migration | 8 of 19 | ~7,700 |
| AI feature with a human gate | 9 of 19 | ~8,300 |
| Mobile screen touching tokens | 10 of 19 | ~9,900 |
| Backend endpoint | 11 of 19 | ~10,000 |
| Frontend login form | 12 of 19 | ~11,500 |
| Everything at once | 19 of 19 | ~17,300 |

A further ~29,000 tokens of playbook `references/` sit behind explicit "load when" conditions and are **never** selected automatically.

Four mechanisms keep this from drifting:

1. **Per-document rows, never per-folder.** One row for `decisions/` means that at fifteen ADRs every task drags in every decision ever made. One row per ADR, with only the surfaces that decision constrains, means the agent building a React form never loads the dead-letter-queue rationale.
2. **Two-level packs.** A pack is 60–150 lines of enforceable rules; depth lives in `references/` with a stated condition for loading it.
3. **A context budget.** `project.json` sets `warn_tokens` and `hard_tokens`; a selection that blows the hard limit fails, which is a signal to split the work package, not to raise the number.
4. **Sub-agents get ids, not bodies.** A supervisor dispatches routing **ids** and acceptance criteria; the sub-agent loads the documents itself and returns a handoff — never specification text or reasoning transcripts.

Calibrate before you trust it. Read the selector output for the tasks you actually run: did the deployment view arrive for an auth change? Did an unrelated pack stay out? Then freeze what matters into `.spec/validation/ROUTING_CASES.json`, which `validate` enforces — one of the shipped cases already caught a wrong assertion while this framework was being built.

---

## Precedence: the architecture wins

The collision is guaranteed and it bites quietly. `NONFUNCTIONAL.md` says *p95 < 300 ms for standard operations*. Your ORACE scenario `QA-PERF-02` says *p99 ≤ 500 ms end to end for the payment orchestrator*, because that number came from a business outcome and is measured in production every day.

An agent that resolves this mechanically — global policy outranks everything, so 300 ms — gets it backwards, and ships a budget nobody asked for.

SDDF fixes it at the top, in the always-loaded baseline:

```
architecture  →  global policy  →  playbook packs  →  backlog task  →  existing code
```

1. Is there an approved scenario whose `Artifact` field names what I am changing? **Its `Measure` governs.**
2. Is there an accepted ADR covering this decision? **It governs** over any generic guidance — a pack's preferred library, pattern, or structure included.
3. Otherwise a global policy rule governs over a playbook pack.
4. Otherwise the pack's default applies.
5. **Security is the exception.** An ADR never silently overrides a security rule. That is not a precedence question — stop, write `CLARIFICATIONS.md`, and escalate. An accepted risk is explicit, owned, and logged.

Every number in every pack is marked as a default, in a banner the validator asserts is present. The agent records the resolution in its task context — *governed by QA-PERF-02 (p99 ≤ 500 ms); NONFUNCTIONAL 300 ms default not applicable* — and the reviewer checks it. An unrecorded conflict resolution is treated as an unresolved conflict.

The rule of thumb behind all of it: **global policy and playbooks say what kind of thing must be true; the architecture says what is true for this system.**

---

## Sub-agents, work packages, and the reviewer

A **work package** is the unit of delegation: tasks sharing surfaces, playbooks, and file ownership. One package, one sub-agent.

The supervisor hands over a brief with task ids, authorised paths, routing ids, acceptance criteria, and required checks — and no specification bodies. Packages dispatched in parallel must have **disjoint file ownership**; a package spanning three playbooks and every module is not a package, it is a plan that needs splitting. Sub-agents return a handoff and a short message, so the supervisor's context stays free for coordination.

Then the last gate, and the one most frameworks omit. **Reviewer-Agent runs in a fresh context, did not write the code, and judges two things:**

- **The work.** Is every acceptance criterion *covered* by evidence a sceptic would accept, *unproven*, or *contradicted*? A criterion saying "recovery completes in ≤ 30 s" is not covered by a unit test that mocks the recovery.
- **The handoff documents themselves.** Vague evidence ("tests pass"), missing commands, unreported skips, silent deviations from the approved proposal, an empty residual-risk section on a non-trivial change, undocumented new configuration. Each becomes a required correction.

It also checks scope against the authorised file set, checks that no test or control was weakened to make the work pass, and checks that an architecture measure was not displaced by a generic default. Verdict: `accept`, `revise`, or `reopen`. It does not fix the code — finding and fixing in the same pass destroys the independence that makes the review worth running.

---

## Extending it

The packs that ship cover Python, React, Kotlin, and Auth0. Anything else — Java, Go, Rust, Terraform, iOS, Kafka, Stripe, or a compliance regime like PCI-DSS — drops in the same way:

```bash
python3 scripts/spec.py scaffold java-backend
```

That creates the pack skeleton and prints the routing row to add. Then write 60–150 lines of enforceable rules with stable ids, register the row with the narrowest correct surfaces, add it to `project.json`, add routing cases, and validate. `validate` **fails** while the pack is unregistered — the framework will not let you add guidance nobody routes to.

What makes a pack worth its context: rules a reviewer could cite in a rejection, not a tutorial. Specialise the global policy rather than restating it. State the exception where one genuinely exists. Push depth into `references/`. [`docs/EXTENDING.md`](docs/EXTENDING.md) has the full guidance, including when something belongs in an ADR instead of a pack.

The packs are opinionated on purpose — vague policy produces vague compliance. Where a rule contradicts a convention your team has already settled, **change the rule** and log it. Deleting a rule you will not enforce is better than keeping one nobody follows.

---

## Validation

```bash
python3 scripts/spec.py validate          # registry, coverage, routing cases, budgets
python3 scripts/sync_skills.py --check    # host adapters match the canonical skill tree
python3 -m unittest discover -s tests -v  # 24 tests
python3 scripts/spec.py playbooks         # what is registered, what is active
python3 scripts/spec.py select --task PAY-014
```

Python 3.10+, standard library only. No virtualenv, no install step, nothing to run in CI beyond the three commands above — the workflow in `.github/workflows/validate.yml` runs exactly those.

`validate` fails on: an unregistered global policy, an unregistered playbook pack, an **unregistered architecture artifact**, a missing or cyclic dependency, an unknown surface or playbook, an unsafe path, a duplicate id, an active playbook with no routing row, a broken routing assertion, or a selection over its hard token budget.

---

## Honest limits

The routing index is maintained by hand. It grows a row per ADR, and nothing detects an ADR that has quietly gone stale relative to the scenario it serves — `validate` checks that references and dependencies resolve, not that the content still agrees.

Surface mapping is human judgement. Path and role matching are hints; they cannot infer every security implication, which is why the framework pushes you to attach `security` and `auth` deliberately rather than hope.

The token figures above are `characters ÷ 4` estimates of what a compliant agent *should* load. They are not measured host traces, and the selector does not load anything into a context window — use them to compare task shapes and to catch a bad surface mapping, not as a benchmark.

And no framework can rescue a bad interview. If the `Measure` fields come back as "fast" and "reliable", routing them perfectly achieves nothing. `/orace-workshop` probes once for a number; it cannot supply one.

What this combination reliably buys is not a smaller context window — it is a **correct** one: the agent holding the two ADRs and the one scenario that govern the file it is editing, with an approval gate in front of it and an evidence trail behind it.

---

## ORACE: the front door

Five phases, interviewed one question at a time, each writing its output before the next begins.

| Phase | Produces | Asks |
|---|---|---|
| **O** — Outcomes | `outcomes.md` | What must this system achieve, and which business failures must it prevent? |
| **R** — Requirements | `quality-scenarios.md` | Turn each failure into a scenario with source, stimulus, environment, artifact, response, and a **measure containing a number** |
| **A** — Approaches | `decisions/`, `risks/` | Which tactics address each scenario, and which decisions are costly enough to reverse that they need an ADR? |
| **C** — Communication | `views/` | Context, module, runtime, and deployment views — including trust zones and what an AI component may read, propose, and never execute |
| **E** — Evidence | `evidence/`, `evolution/` | Which production metrics prove the architecture works, and what gets revisited when they fail? |

The version vendored here differs from standalone ORACE in three ways: it writes into `.spec/15_architecture` by default, it assigns each scenario a stable `QA-<ATTR>-<NN>` id that becomes an acceptance criterion and a test name, and it hands off to `/spec-bootstrap` instead of stopping at a file listing. `/orace-adr` records one decision at a time afterwards — and is the supervisor's answer when a task escalates a decision no ADR covers.

That last point is the neatest fit between the two halves: **an ORACE decision record is the answer to an SDDF clarification.** The agent that hits an undecided question does not choose. It stops, the decision gets made and recorded by a human, the row gets registered, and the task resumes — which is how an architecture stays true six months after the workshop.
