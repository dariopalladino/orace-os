---
id: governance
---

# Governance and promotion

> Who may change what, and what evidence that change leaves behind.

## Canonical vs workspace

**Canonical** (changed only by promotion): `.spec/00_global/`, `.spec/10_stacks/`, the architecture root, `.spec/20_backlog/TASKS.md`, `.spec/INDEX.md`, `.spec/project.json`.

**Workspace** (freely written by the owning agent): `.spec/40_workspace/<task-id>/`.

## Rules

- **GOV-01** A specialist agent MUST NOT write to a canonical path. It proposes the change in its workspace; the supervisor promotes it.
- **GOV-02** Every canonical change MUST have an entry in `.spec/30_delivery/PROMOTION_LOG.md` recording: date, task id, approver, what changed, why, migration impact, and validation evidence.
- **GOV-03** A new or superseded ADR is not finished until its routing row exists in `.spec/INDEX.md` and `python3 scripts/spec.py validate` passes. An unregistered artifact is invisible to every future task.
- **GOV-04** An agent MUST NOT weaken a quality-attribute scenario, an acceptance criterion, or a security rule to make its own work pass. Detecting that a requirement is wrong is a clarification, not a licence to edit it.
- **GOV-05** Changes to authentication, authorisation, data exposure, cryptography, payment paths, or personal data require security review before close, regardless of which agent made them.
- **GOV-06** Schema and public API contract changes are promoted **before** the dependent implementation task starts, not alongside it.
- **GOV-07** `.spec/20_backlog/TASKS.md` is the only task list. Any other list is a pointer to it.
- **GOV-08** Deleting or rewriting history in `40_workspace/` is forbidden. Superseded artifacts are marked superseded and kept; the audit trail is the point.

## Change classes

| Class | Examples | Required path |
|---|---|---|
| Routine | Bug fix inside one module, test addition, copy change | Proposal → approval → execute → handoff → review |
| Contract | New endpoint, response shape change, event payload | Contract promotion first, then implementation task |
| Structural | Schema migration, module boundary move, dependency swap | ADR (`/orace-adr`) → index row → promotion → implementation |
| Architectural | New quality-attribute scenario, changed `Measure`, new outcome | ORACE phase re-run → promotion → downstream tasks reopened |

## Escalation to architecture

When a task reveals that no ADR covers a decision the implementation requires, the agent stops and writes `CLARIFICATIONS.md`. The supervisor's resolution is to run `/orace-adr`, register the row, log the promotion, then unblock the task. An agent that picks silently is the exact failure this framework exists to prevent.
