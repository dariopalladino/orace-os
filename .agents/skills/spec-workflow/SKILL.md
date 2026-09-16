---
name: spec-workflow
description: Plan, implement, or review a change in a repository governed by .spec specifications. Selects the applicable requirements for the task, runs the proposal-execution-handoff lifecycle, and keeps evidence — without loading the whole specification library.
---

# Spec workflow

Use this for work that changes or reviews the repository. An ordinary question needs no task ceremony.

Paths are repository-relative.

## 1. Select

```sh
python3 scripts/spec.py select --task <task-id>            # routing metadata from the backlog
python3 scripts/spec.py select --surface auth --path web/src/login.tsx
```

Without Python, read `.spec/INDEX.md` and apply the table by hand.

Classify honestly before selecting. Surfaces come from **what the change means**, not from which folder the file sits in. A token-storage change in a React component is `frontend` *and* `auth` *and* `security`. Role and path are hints; they cannot identify every security implication, so add the surface a reviewer would ask about.

Read every selected document **in full** before work that depends on it. The index routes to requirements; it does not summarise them. Do not load anything routing did not select — if the selection looks wrong, fix the surfaces and re-run, do not widen the read.

Record in `.spec/40_workspace/<task-id>/TASK_CONTEXT.md`: the selected ids, the reason for each, the token estimate, the active playbooks, and — where two selected documents disagree — which requirement governs and which default it displaced (`PRINCIPLES.md`, Resolving a conflict; `AGENT_EXECUTION_PROTOCOL.md` PROTO-10).

## 2. Propose

Write `agent_<role>/PROPOSED_CHANGES.md`: intent, files to modify, ordered plan, risks, and test plan. Nothing outside the workspace changes in this phase.

Stop and write `CLARIFICATIONS.md` instead of guessing when a contract is missing, two selected documents genuinely conflict, or the work requires an architectural decision no ADR covers. The supervisor's answer to the last case is `/orace-adr`, then a routing row, then the task resumes. An agent that picks silently is the failure this framework exists to prevent.

In supervisor mode, wait for approval. In sequential mode, record the self-approval and continue — the same gates still apply.

## 3. Execute

Implement only the approved scope, only inside the authorised file set. Adjacent problems you discover become backlog entries, not extra commits.

Apply the selected documents as written. When a playbook default and an architecture `Measure` both speak to what you are changing, the architecture governs — and the handoff says so by id.

## 4. Verify and hand off

Run the checks from `.spec/project.json` that the change actually warrants, plus any the selected specifications require. Then write `agent_<role>/HANDOFF.md` using the [artifact templates](references/artifacts.md).

Evidence means the command and its real output, a file and line, or a specification rule id. Never report a check you did not run; never report a passing suite while hiding new skips (`AI_GOVERNANCE.md` AIG-02, `TESTING.md` TEST-13).

Name the governing requirement beside each acceptance criterion — `QA-AVAIL-01`, `SEC-03`, `PY-08` — so the reviewer can check the claim without re-deriving the routing.

## 5. Review

A sensitive change needs `agent_security/SECURITY_REVIEW.md` before close. Every task ends with the `spec-review` skill judging the handoffs, then the supervisor closing against the Definition of Done.

## Refresh

Re-run selection when scope, affected paths, playbooks, or the architecture change, and load newly relevant documents before dependent work.

After a new session, a compaction, or a sub-agent start, recover scope from `TASK_CONTEXT.md` and re-read the selected sources. A file hash proves a file is unchanged; it never proves the text is still in the model's context. Do not mechanically re-read unchanged documents you still hold.

## Working as a sub-agent

You were given a package brief with task ids, authorised paths, routing ids, and acceptance criteria — not specification bodies. Load the documents yourself from the recorded ids.

Stay inside the package's file ownership; another package may hold the file you want. Return a `HANDOFF.md` and a short result message. Do not return specification text, full file contents, or reasoning transcripts — the supervisor's context is a shared resource.
