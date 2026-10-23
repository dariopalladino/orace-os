# SDDF — Spec-Driven Development Framework

**An adaptive engineering framework that gives each change relevant architecture context, proportional controls, and inspectable verification evidence.**

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
| Tactics and the project-specific technology baseline | ORACE | `approaches.md`, `technology-profile.md` |
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

## The full architecture pipeline

```
 /orace-workshop          architecture interview          .spec/15_architecture/
        │                 one question at a time          outcomes, scenarios, approaches,
        ▼                                                 technology profile,
                                                          ADRs, views, risks, evidence plan
 /spec-bootstrap          register + derive                INDEX.md rows, playbooks, checks,
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

This is the Governed path for architecture work. Routine fixes can start from an ad hoc task request. Architecture generated from repository discovery stays a proposal until a person accepts and registers it.

---

## Quick start

### Context and model choices

`init` sets each harness's workshop, supervisor, and subagent model to `auto` by default, so the host's own model configuration applies. To choose models for one harness, pass its model ids during initialization:

```sh
python3 scripts/orace.py init --target /path/to/your/repo --harness codex \
  --workshop-model <codex-model-id> --supervisor-model <codex-model-id> \
  --subagent-model <codex-model-id>
```

For a CLI workshop or main supervisor session, start with `python3 scripts/orace.py launch --harness codex --role workshop` (or `--role supervisor`) from the installed project. In an IDE or app, select that role's configured model in the host model picker. Generated Claude, Codex, and Copilot role agents use explicit model settings when configured; `auto` omits the model field. Host-specific model ids, session controls, and limitations are in [Context and model use](docs/CONTEXT_MANAGEMENT.md).

Use one conversation per task. Compact a long session after persisting a concise checkpoint, and start a fresh chat for another task. The ORACE workshop now loads one phase reference at a time, and bootstrap loads one step at a time; their templates stay out of context until needed.

### First useful task

```bash
python3 scripts/orace.py init --target /path/to/your/repo
cd /path/to/your/repo
python3 scripts/spec.py validate
python3 scripts/orace.py task "Fix the submit button spacing" --path web/src/SubmitButton.tsx --surface frontend --output .spec/40_workspace/submit-button/plan.json
```

`init` preserves existing instruction files and writes `.spec/40_workspace/PROJECT_DISCOVERY.json` as a **proposal**. It lists observed manifests, tests, CI, possible decisions, suggested playbooks, and explicit unknowns. A fresh install starts with no active playbooks or module roots; the first task above supplies its surface explicitly. Confirm the proposal and configure `.spec/project.json` before expecting path-based routing to be complete. The discovery report never marks a dependency or inferred architecture as accepted.

### Codex

Open the installed repository in Codex CLI, the IDE extension, or the Codex app. Codex reads `AGENTS.md`, discovers the five skills in `.agents/skills/`, and can use project role agents from `.codex/agents/`. Invoke a skill with `$orace-workshop`, `$spec-bootstrap`, `$spec-workflow`, `$orace-adr`, or `$spec-review`, or ask Codex to work on a task and let the skill description route it. For a supervised task, the main agent coordinates; the `orace_*` agents receive scoped packages. The [Codex guide](docs/CODEX.md) has setup, prompts, and a verification checklist.

The task command selects registered requirements, shows inferred surfaces for confirmation, recommends Lite, Standard, or Governed based on risk, and writes a reviewable execution plan. It does not edit source code. `run --plan <plan.json> --command '<executor command>' --evidence <evidence.json>` can invoke a chosen executable, check its changed-file scope, run configured checks, and produce a review preflight. It does not bundle or install a coding agent. Use `explain` with the same arguments to inspect routing, or `verify --check <group> --task <id> --output <path>` when implementing manually.

For a new enterprise architecture, continue in your agent:

```
/orace-workshop .spec/15_architecture     # capture architecture with stakeholders
/spec-bootstrap                            # register; derive playbooks, checks, and backlog
```

```bash
python3 scripts/spec.py validate
```

The baseline policies and playbooks can route a first task before a full ORACE interview. Unknown quality measures stay unresolved; do not invent numbers to complete onboarding.

During Phase A, the workshop writes the project-specific technology baseline that `/spec-bootstrap` uses to propose playbooks, module roots, and exact checks. At completion it also prints an accuracy-labelled token report for that workshop invocation; the report is operational feedback and is not stored as architecture.

### An existing repository

Use the same `init` command on a branch. It copies a clean specification template and a managed runtime—CLI scripts, skills, host adapters, and the PR check—while leaving the framework's internal tests and task history behind. It **merges** rather than overwrites your `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`. Existing project files are preserved; repeat installations use `upgrade`.

Then:

1. Read the discovery proposal, confirm the actual stack and module roots, and adjust `.spec/project.json` and routing cases.
2. Run `validate`, then try a real ad hoc task and inspect `explain` output.
3. When an accepted architecture decision or measurable quality objective is needed, run `/orace-workshop` and `/spec-bootstrap`. The workshop inspects repository facts as candidates and asks which technologies to retain, migrate, retire, or leave undecided.

For an architecture created by an earlier version, rerun `/orace-workshop .spec/15_architecture`. Resume detection will leave completed Outcomes and Requirements alone and fill the missing `approaches.md` and `technology-profile.md`. Use `--rerun technology` later to refresh only the stack baseline.

Full detail in [`docs/ADOPTION.md`](docs/ADOPTION.md). A complete requirement followed from a stakeholder's sentence to a closed task is in [`examples/WORKED_EXAMPLE.md`](examples/WORKED_EXAMPLE.md).

---

## Task modes and evidence

| Mode | Trigger | Required work |
|---|---|---|
| Lite | Narrow, low-risk repair | Selected specs, scoped change, relevant checks, compact result |
| Standard | Feature or refactor | Concrete criteria, concise plan, verification, structured review |
| Governed | Security, authentication, sensitive data, contracts, irreversible change, accepted architecture impact | Explicit proposal and approvals, stronger evidence, independent review |

`task --mode lite` may escalate to Standard or Governed. Description and filename clues are marked as inferences, and the coding agent must confirm them against the actual behavior. A path with no `module_roots` mapping needs explicit classification. `python3 scripts/orace.py coverage --path <path>` reports mapping; `coverage --diff HEAD` checks changed, deleted, renamed, and untracked paths. In `project.json`, `*` matches one directory segment and `**` matches any depth.

`verify` executes only commands configured in `.spec/project.json`, without a shell, and records exit codes, timestamps, redacted output tails, commit SHA, and a changed-file fingerprint. Add `--authorized-path <path> --base HEAD` to check changed-file scope. `check` and `review` reject evidence when the commit or worktree has changed since verification. The record limits its claim to command execution and optional scope; a passing unit test cannot establish a production recovery target. Review output before sharing it because automated redaction cannot recognize every form of sensitive data.

`task --executor external --external-name <method> --output <plan.json>` exports a JSON execution contract for another coding method. `review --plan <plan.json> --handoff <handoff.json> --evidence <evidence.json>` checks the returned scope and machine evidence; it leaves behavioral claims for a reviewer. The agreement on approval, decision authority, and handoff fields is in [`docs/EXECUTION_ADAPTERS.md`](docs/EXECUTION_ADAPTERS.md).

`run` executes a saved plan through an explicit command, exports `ORACE_PLAN_PATH` to that process, compares the worktree before and after execution, and captures the configured checks. Unmapped plan paths need `--authorize-path`; Governed plans also need a plan-bound `--approval-record`. The run report is ready for human review when the mechanical checks pass; it does not declare behavioral acceptance. See the [execution guide](docs/EXECUTION_ADAPTERS.md) for the command and approval formats.

`impact --path <path>` and `check --diff <base...HEAD>` show affected ADRs, policy selection, routing gaps, and check evidence. `check --run-checks --strict` executes the required configured commands during that invocation, so a strict command gate does not trust a supplied JSON file. The pull request workflow publishes an informational summary; add runtime dependency setup before enabling live application checks in CI. Branch review rules enforce human approval. See [`docs/ARCHITECTURE_CONTINUITY.md`](docs/ARCHITECTURE_CONTINUITY.md).

`upgrade --target <repo>` previews updates from a newer framework checkout. Add `--apply` to replace only managed files whose hashes still match the installed version. Project edits are preserved and reported as conflicts; `doctor` reports routing and managed-file drift. The installed runtime version and hashes live in `.spec/installation.json`.

---

## What's in the box

| Path | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | The operating contract. Short on purpose — it is paid for on every turn |
| `CLAUDE.md`, `.github/copilot-instructions.md` | Thin host adapters pointing at the same contract |
| `.agents/skills/` | Canonical skills: `orace-workshop`, `orace-adr`, `spec-bootstrap`, `spec-workflow`, `spec-review` |
| `.agents/roles/` | Canonical supervisor, planner, specialist, security, and reviewer roles |
| `.claude/skills` | Symlink to the canonical tree, with a copy fallback |
| `.claude/agents/` | Generated Claude role adapter |
| `.claude/commands/` | Slash commands wrapping the skills |
| `.codex/agents/` | Generated Codex role agents (`orace_*`), with no pinned model or permission overrides |
| `.spec/INDEX.md` | The routing registry — the only way agents find anything |
| `.spec/project.json` | Active playbooks, module roots, orchestration, context budget, checks |
| `.spec/00_global/` | 15 policy packs: protocol, principles, governance, clean architecture, DDD, API, data modelling, OWASP security, AI governance, human-in-the-loop, UI, testing, observability, NFR, definition of done |
| `.spec/10_playbooks/` | Technology packs: Python backend, React frontend, Kotlin native, Auth0 identity — plus any you add |
| `.spec/15_architecture/` | This system's ORACE artifacts, including its technology profile (empty until the workshop runs) |
| `.spec/20_backlog/TASKS.md` | Canonical planned backlog; ad hoc tasks may start from a request |
| `.spec/30_delivery/PROMOTION_LOG.md` | Evidence for every canonical change |
| `.spec/40_workspace/<task-id>/` | Task context, proposals, handoffs, reviews |
| `scripts/spec.py` | Validate, select, scaffold |
| `scripts/orace.py` | Init, task, run, explain, coverage, impact, check, verify, review, doctor, upgrade |
| `scripts/architecture.py`, `scripts/distribution.py`, `scripts/benchmark.py` | Architecture links, managed installation, and measurement |
| `.github/workflows/orace-check.yml` | Informational architecture and routing summary for pull requests |
| `benchmarks/` | Routing probes and instructions for recording real comparisons |
| `docs/`, `examples/`, `tests/` | Adoption, integration guidance, a worked example, and framework tests |

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

For Governed changes, the last gate is an independent reviewer. **Reviewer-Agent runs in a fresh context, did not write the code, and judges two things:**

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
python3 -m unittest discover -s tests -v  # framework test suite
python3 scripts/spec.py playbooks         # what is registered, what is active
python3 scripts/spec.py select --task PAY-014
python3 scripts/orace.py doctor            # routing and managed-runtime diagnostics
python3 scripts/benchmark.py run          # synthetic routing measurements
```

Python 3.10+, standard library only. No virtualenv or package installation is required for the framework CLI. `run` needs the executor command you choose, and application checks need that application's dependencies. The framework CI runs validation, skill sync, tests, and a pull request change summary. Installed projects receive a separate informational PR workflow; teams can opt into strict live command gating after configuring their roots, checks, and CI environment.

`validate` fails on: an unregistered global policy, an unregistered playbook pack, an **unregistered architecture artifact**, a missing or cyclic dependency, an unknown surface or playbook, an unsafe path, a duplicate id, an active playbook with no routing row, a broken routing assertion, or a selection over its hard token budget.

---

## Honest limits

The routing index is maintained by hand. It grows a row per ADR. `impact` and `validate` detect missing machine-readable scenario links and affected path gaps, but they cannot prove that an ADR's prose still agrees with a quality scenario. A reviewer must judge that relationship.

Surface mapping is human judgement. Path and role matching are hints; they cannot infer every security implication, which is why the framework pushes you to attach `security` and `auth` deliberately rather than hope.

The token figures above are `characters ÷ 4` estimates of what a compliant agent *should* load. They are not measured host traces, and the selector does not load anything into a context window — use them to compare task shapes and to catch a bad surface mapping, not as a benchmark.

The benchmark harness ships synthetic routing probes and a format for recording real comparative runs. It does not claim productivity gains or measured comparisons with other coding methods until those runs are supplied.

Saved evidence JSON is inspectable but can be edited; `check --strict` therefore requires live command execution for a check gate. A plan-bound approval record catches accidental plan mismatch but cannot establish the approver's identity. Independent review and host branch rules remain the acceptance and approval authority.

And no framework can rescue a bad interview. If the `Measure` fields come back as "fast" and "reliable", routing them perfectly achieves nothing. `/orace-workshop` probes once for a number; it cannot supply one.

What this combination reliably buys is not a smaller context window — it is a **correct** one: the agent holding the two ADRs and the one scenario that govern the file it is editing, with an approval gate in front of it and an evidence trail behind it.

---

## ORACE: the front door

Five phases, interviewed one question at a time, each writing its output before the next begins.

| Phase | Produces | Asks |
|---|---|---|
| **O** — Outcomes | `outcomes.md` | What must this system achieve, and which business failures must it prevent? |
| **R** — Requirements | `quality-scenarios.md` | Turn each failure into a scenario with source, stimulus, environment, artifact, response, and a **measure containing a number** |
| **A** — Approaches | `approaches.md`, `technology-profile.md`, `decisions/`, `risks/` | Which tactics address each scenario, which technologies realize them, and which choices are costly enough to reverse that they need an ADR? |
| **C** — Communication | `views/` | Context, module, runtime, and deployment views — including trust zones and what an AI component may read, propose, and never execute |
| **E** — Evidence | `evidence/`, `evolution/` | Which production metrics prove the architecture works, and what gets revisited when they fail? |

### Technology baseline: project truth, not generic guidance

Technology enters the workshop deliberately, without contaminating the requirements with implementation choices:

- **Phase O** records whether the project is `New`, `Existing`, or `Hybrid`, plus technologies that are present, mandated, preferred, or prohibited and the source of each constraint.
- **Phase R** remains implementation-neutral. A quality scenario says what the system must do and how success is measured, not which framework must do it.
- **Phase A** maps tactics to those scenarios in `approaches.md`, then writes the choices that realize them to `technology-profile.md`. A costly-to-reverse choice also gets an ADR; routine library selection does not need ceremonial decision records.
- **Phase C** reconciles component names, protocols, hosting, managed services, and trust-boundary providers with the module, runtime, and deployment views. The views reference the profile instead of becoming a second stack inventory.
- **Phase E** adds measurable tests for architectural technology assumptions such as capacity, compatibility, migration safety, portability, operability, licensing, or support lifetime.

For a **new** project, the profile records planned implementation units, proposed or accepted choices, version policies, rationale, and planned source-of-truth paths—even before those paths exist. For an **existing or hybrid** project, manifests, lockfiles, runtime files, containers, infrastructure, CI, and observability configuration are candidate evidence only. The architect classifies each observed choice as `Retain`, `Migrate`, `Retire`, or `TBD`; discovery never silently turns an installed dependency into architectural intent.

Each artifact owns a different part of the answer:

| Source | Owns |
|---|---|
| `technology-profile.md` | Project-specific choice, current and target state, lifecycle status, version policy, rationale, evidence, and playbook mapping |
| `decisions/NNN-*.md` | Why a costly-to-reverse choice was accepted, its alternatives, and its consequences |
| `views/` | Where components live and how they interact, execute, and deploy |
| `.spec/10_playbooks/` | Reusable rules for implementing a technology correctly |
| Manifests and lockfiles | Exact direct and transitive dependency versions |
| `.spec/project.json` | Active playbooks, module roots, orchestration, and exact repository checks |

Older architectures do not need a new workshop from scratch. Refresh only the technology baseline with:

```text
/orace-workshop .spec/15_architecture --rerun technology
```

The rerun preserves Outcomes, Requirements, approaches, accepted ADRs, views, and evidence unless the architect explicitly changes them. It reports downstream artifacts and tasks that may now be stale rather than silently rewriting them. `/spec-bootstrap` then treats the confirmed profile as the primary source for proposed playbooks, module roots, checks, and selective routing; it flags missing packs and contradictions with views or accepted ADRs for review.

### Workshop token consumption

Every completed workshop or targeted rerun ends with a token-usage block for **that invocation only**. Its boundary is established before resume detection, repository discovery, or the first interview question. Root-agent turns and attributable workshop subagent turns are included when the host exposes enough telemetry.

| Accuracy | When it is used |
|---|---|
| **Measured (host-reported, best-effort)** | The host exposes cumulative session snapshots or per-turn usage that can be attributed to the invocation |
| **Estimated (trace-counted)** | A named, model-aware tokenizer actually counts an exported workshop trace; the counter, counted content, and exclusions are disclosed |
| **Unavailable** | Neither suitable host telemetry nor a trace-counted estimate exists; the workshop reports why instead of printing zero or a plausible substitute |

The accounting identity is `total_tokens = input_tokens + output_tokens`. Cached input is already included in input, and reasoning tokens are already included in output; both may be displayed as subsets but are never added twice. A category the host omits is shown as `not reported`, not zero.

A typical measured block looks like this:

```text
Token usage — this ORACE workshop invocation
Accuracy: Measured (host-reported, best-effort)
Source: <host session usage | summed turn usage | named source>
Scope: <start boundary> through the last completed turn before this summary
Input tokens: <N>
  Cached input tokens: <N | not reported> (included in input)
Output tokens: <N>
  Reasoning tokens: <N | not reported> (included in output)
Total tokens: <input + output>
Includes workshop subagents: <yes, N turns | none used | attribution unavailable>
Final-summary tokens included: <yes via post-response accounting | no — not knowable while generating this response>
Billing note: best-effort usage; not a final bill
```

Unless the host can inject usage after the response, a model cannot count the final summary while it is still generating it, so the scope ends at the last completed turn and says so. The workshop does not infer monetary cost, and host figures may settle later. This is operational session metadata, not architectural truth, so it is not persisted in `outcomes.md`, `technology-profile.md`, ADRs, or evidence artifacts.

The `characters ÷ 4` figures in [How selective loading works](#how-selective-loading-works) are rough selector context estimates. They describe what a compliant agent should load; they are never reported as consumed workshop tokens.

The version vendored here writes into `.spec/15_architecture` by default, assigns each scenario a stable `QA-<ATTR>-<NN>` id that becomes an acceptance criterion and a test name, records a project-specific technology profile, supports targeted phase and technology reruns, and hands off to `/spec-bootstrap` instead of stopping at a file listing. `/orace-adr` records one decision at a time afterwards—and is the supervisor's answer when a task escalates a decision no ADR covers.

That last point is the neatest fit between the two halves: **an ORACE decision record is the answer to an SDDF clarification.** The agent that hits an undecided question does not choose. It stops, the decision gets made and recorded by a human, the row gets registered, and the task resumes — which is how an architecture stays true six months after the workshop.
