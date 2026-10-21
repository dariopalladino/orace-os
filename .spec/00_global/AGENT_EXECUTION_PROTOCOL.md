---
id: protocol
tier: baseline
---

# Agent execution protocol

> Route every change, then use the least ceremony consistent with its risk. Loaded on every task.

## Adaptive execution

`python3 scripts/orace.py task "<request>" --path <path>` recommends a minimum mode and explains escalation. Description-based surfaces are suggestions; the agent confirms them against the affected behavior and paths before implementation. A requested mode may increase controls but cannot lower the recommended minimum. Authentication, security, data migrations, public contracts, irreversible changes, and accepted architecture decisions require Governed handling. Unknown paths require explicit semantic classification.

| Mode | Appropriate work | Required record and review |
|---|---|---|
| Lite | Narrow, low-risk repair | Read selected specs, implement within scope, run relevant checks, report changed files and exact evidence in one compact result. No separate proposal, backlog entry, or independent review is required. |
| Standard | Features and refactoring without governed triggers | Record acceptance criteria, paths and a concise plan before implementation; verify and hand off; review criteria and evidence. |
| Governed | Sensitive, contractual, irreversible, or architecture-significant change | Use the full phase table below, explicit approval where required, security review when applicable, and an independent reviewer. |

Escalate when scope or meaning changes. No mode waives an applicable security rule, accepted ADR, architecture measure, or required check. A check result is evidence for that check only; production measures remain unproven until measured.

## Phases

| Phase | Who | Writes | Gate to leave |
|---|---|---|---|
| `select` | assigned agent | `TASK_CONTEXT.md` | routing recorded with reasons and token estimate |
| `propose` | specialist | `agent_<role>/PROPOSED_CHANGES.md` | supervisor approval (supervisor mode) or recorded self-approval (sequential mode) |
| `execute` | specialist | source files in the approved ownership set | approved scope implemented, checks run |
| `handoff` | specialist | `agent_<role>/HANDOFF.md` | evidence present for every acceptance criterion |
| `review` | Reviewer-Agent | `REVIEW_REPORT.md` | verdict `accept`, `revise`, or `reopen` |
| `close` | supervisor | `TASK_CONTEXT.md`, `PROMOTION_LOG.md` | Definition of Done gates evidenced or explicitly waived with reason |

## Rules

- **PROTO-01** An agent MUST perform routing (`scripts/orace.py task`, `scripts/spec.py select`, or the `.spec/INDEX.md` table by hand) before dependent work. Standard and Governed work records selected ids, reasons, and token estimate in `TASK_CONTEXT.md`; Lite work includes them in its compact result.
- **PROTO-02** An agent MUST read every selected normative document in full before work that depends on it. The index routes to requirements; it does not summarise them.
- **PROTO-03** An agent MUST NOT read the whole specification store to start a task, and MUST NOT load a document that routing did not select. If routing looks wrong, fix the routing, do not widen the read.
- **PROTO-04** In Governed `propose`, an agent MUST write only inside `.spec/40_workspace/<task-id>/agent_<role>/`. Source files change only in `execute`, and only inside the approved ownership set. Lite and Standard may implement within the scope authorised by the request after recording their required plan, if any.
- **PROTO-05** An agent MUST re-run routing when scope, affected paths, active stacks, or the architecture change. A file hash proves a file is unchanged; it never proves the model still holds its text.
- **PROTO-06** After a new session, a compaction, or a sub-agent start, an agent MUST recover scope from the task record or current request and re-read the selected sources before dependent work.
- **PROTO-07** An agent MUST escalate rather than invent: a missing contract, a conflict between two selected documents, or an architectural decision not covered by an ADR goes to `CLARIFICATIONS.md`, not into the code.
- **PROTO-08** An agent MUST report the exact commands it ran and their real output. Claiming an unrun check is a governance failure, not a reporting style.
- **PROTO-09** An agent MUST NOT edit canonical specifications (`00_global/`, `10_playbooks/`, the architecture root) during task execution. It proposes; the supervisor promotes.
- **PROTO-10** When two selected documents disagree, an agent MUST resolve the conflict by the precedence procedure in `PRINCIPLES.md` and MUST record in `TASK_CONTEXT.md` which requirement governs, which default it displaced, and why. An unrecorded conflict resolution is treated as an unresolved conflict at review.
- **PROTO-11** Work MUST stay inside the authorised scope. Discovered adjacent problems become backlog entries, not silent extra commits.

## Sub-agent dispatch

A **work package** is the unit of delegation: a set of backlog tasks sharing surfaces, stacks, and file ownership. One sub-agent owns one work package.

- **PROTO-12** A supervisor MUST give a sub-agent a package brief containing: task ids, objective, authorised paths, the routing result (ids, not bodies), acceptance criteria, and required checks. It MUST NOT paste specification bodies into the brief — the sub-agent loads them itself from the recorded ids.
- **PROTO-13** Work packages dispatched in parallel MUST have disjoint file ownership. Shared files are sequenced by the supervisor or moved into their own package.
- **PROTO-14** A sub-agent returns a `HANDOFF.md` and a short result message. It MUST NOT return specification text, full file contents, or reasoning transcripts to the supervisor.

## Authorisation

A user request authorises its own scope for the session. Existing approval persists — do not re-ask for permission already given. Promotion of canonical specifications, schema changes, public contract changes, and anything touching authorisation always require an explicit approval step recorded in `.spec/30_delivery/PROMOTION_LOG.md`.
