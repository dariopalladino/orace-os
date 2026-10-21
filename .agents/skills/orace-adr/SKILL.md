---
name: orace-adr
description: Record a single architecture decision as an ADR in an existing ORACE architecture folder, append its risk to the register, and register its routing row so agents actually load it. Use when a decision that is costly to reverse comes up mid-project, or to resolve a blocking clarification from a task.
trigger: /orace-adr
---

# /orace-adr

One decision, one interview, one file, one routing row. This is the standing habit that keeps an ORACE architecture alive after the workshop — and it is the supervisor's answer when a task escalates a decision no ADR covers.

```
/orace-adr                 # architecture_root from .spec/project.json, else ./architecture
/orace-adr <path>          # an architecture folder elsewhere
```

## Before asking anything

Resolve the architecture folder, then read `quality-scenarios.md` and list `decisions/`. You need the scenario ids (to link the decision to what it serves) and the highest existing sequence number.

If the folder has no `quality-scenarios.md`, say so and ask whether to proceed anyway — an ADR that serves no stated requirement usually means the requirement was never written down.

## Interview

Ask **one question at a time** and wait for each answer. Do not batch.

1. "What is the title of this decision? Use an imperative phrase — 'Use synchronous screening calls', 'Adopt event sourcing for the audit log'."
2. "What is the context — what situation made this decision necessary, and what forces are in tension? What happens if no decision is made?"
3. "Which quality-attribute scenarios does this decision serve?" *(Offer the ids from `quality-scenarios.md`. If none apply, ask what requirement it does serve.)*
4. "What alternatives did you consider? For each: what does it give you, and what does it cost?" *(Press for at least two. A decision with one option considered is a preference, not a decision.)*
5. "What did you decide — and what did you explicitly decide **not** to do?"
6. "What are the consequences? What becomes easier, what becomes harder, and what risk are you now accepting?"
7. "Status: Proposed or Accepted? And who owns the accepted risk?"
8. "Which repository paths or component roots does this decision govern? Name directory prefixes ending in `/`, or exact files; use `*` for one directory and `**` for any depth."

If an answer is vague ("the backend team", "it should be fast"), reflect it back once and ask for the specific name or number. If the architect says they will fill something in later, record `[TBD — owner: <name>]` and continue.

## Write the ADR

Next number = highest existing `decisions/NNN-*.md` + 1, zero-padded to three digits. Slug from the title.

```markdown
---
orace_phase: A
generated_by: orace-adr
generated_at: YYYY-MM-DD
status: [Proposed | Accepted | Deprecated | Superseded]
owner: [person or accountable role]
affected_paths:
  - [repository-relative directory prefix or exact file]
scenarios_addressed:
  - QA-XXXX-NN
supersedes: [ADR-NNN or none]
---

# ADR-[NNN]: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded] — [date]

## Context
[The situation that made this decision necessary. The forces in tension.]

## Alternatives Considered

| Option | Benefit | Cost |
|--------|---------|------|
| [A] | [benefit] | [cost] |
| [B] | [benefit] | [cost] |

## Decision
[What was decided, stated directly. What was explicitly not chosen.]

## Consequences

**Easier**: [what this makes easier]
**Harder**: [what this makes harder]
**Risk accepted**: [residual risk, and who owns it]
```

Then append the accepted risk to `risks/risk-register.md`, creating it if absent, with the ADR as its source.

**Superseding.** If this decision replaces an earlier one, set the old ADR's status to `Superseded by ADR-NNN` — do not delete it. The rejected path and the reason it was rejected are the most valuable content in an architecture folder.

## Register the routing row

**An ADR is not finished until its row exists.** Unregistered, no agent will ever load it, because every agent routes through `.spec/INDEX.md` and is forbidden from reading the store wholesale.

Add one row to the `.spec/INDEX.md` table:

```markdown
| adr-003-dlq-ordering | .spec/15_architecture/decisions/003-dlq-ordering.md | data | quality-scenarios,architecture | * |
```

Give it **only the surfaces the decision actually constrains**. An audit-log persistence decision is `data`. Adding `backend` as well means it loads on every backend task, which is how a selective-loading framework quietly becomes a read-everything one. Set `Playbooks` to `*` unless the decision applies to one technology only.

Then:

```sh
python3 scripts/spec.py validate
```

## Close the loop

- Append an entry to `.spec/30_delivery/PROMOTION_LOG.md`: the ADR, its approver, what it changes, and which tasks it affects.
- If this ADR resolves a blocking `CLARIFICATIONS.md` in a task workspace, say so in the promotion entry and tell the supervisor the task is unblocked.
- If it invalidates work already done or in flight, name those tasks. An ADR that silently contradicts shipped code is worse than no ADR.

Report:

```
ADR-[NNN] written    decisions/[NNN]-[slug].md
Risk appended        risks/risk-register.md  (R-NNN)
Routing row added    .spec/INDEX.md          surfaces: [...]
Validation           ok
Unblocks             [task ids, or none]
```

## Rules

- One decision per ADR. A file deciding three things cannot be superseded cleanly.
- Never invent context, alternatives, or consequences. Missing answers are `[TBD]` with an owner.
- Never edit an accepted ADR's decision in place. Supersede it with a new one.
- This is a canonical change: it goes through promotion, and a specialist agent proposes it rather than running it directly (`GOVERNANCE.md` GOV-01/GOV-03).
