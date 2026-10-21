---
name: spec-workflow
description: Plan, implement, or review a change in a repository governed by .spec specifications. Routes applicable requirements, selects Lite, Standard, or Governed execution by risk, and preserves proportional evidence.
---

# Spec workflow

Use this for work that changes or reviews the repository. An ordinary question needs no task ceremony.

Paths are repository-relative.

## 1. Select

```sh
python3 scripts/spec.py select --task <task-id>            # routing metadata from the backlog
python3 scripts/spec.py select --surface auth --path web/src/login.tsx
python3 scripts/orace.py task "Fix login validation" --path web/src/login.tsx
```

Without Python, read `.spec/INDEX.md` and apply the table by hand.

Classify honestly before selecting. Surfaces come from **what the change means**, not from which folder the file sits in. A token-storage change in a React component is `frontend` *and* `auth` *and* `security`. Role and path are hints; they cannot identify every security implication, so add the surface a reviewer would ask about.

Read every selected document **in full** before work that depends on it. The index routes to requirements; it does not summarise them. Do not load anything routing did not select — if the selection looks wrong, fix the surfaces and re-run, do not widen the read.

The task command infers candidate surfaces from the description and selects a minimum mode. Confirm candidate surfaces against the actual change; add any missed semantics. A lower requested mode never bypasses escalation. For Standard and Governed work, record selected ids, reasons, token estimate, active playbooks, and conflicts in `.spec/40_workspace/<task-id>/TASK_CONTEXT.md`. For Lite, include these in the compact result.

When another execution method will implement the change, export the JSON contract with `task --executor external --external-name <method> --output <plan.json>`. The external method receives selected ids, authorised paths, approval gate, decision authority, and required checks. Its handoff can be preflighted with `orace.py review --plan <plan.json> --handoff <handoff.json> --evidence <evidence.json>`. The external method never changes accepted architecture or approval authority. See `docs/EXECUTION_ADAPTERS.md`.

## 2. Choose the execution level

- **Lite:** a narrow, low-risk correction. No backlog registration, separate proposal, or independent review is required. Read selected documents, implement in the authorised scope, verify, and return changed files plus exact results.
- **Standard:** a feature or refactor without Governed triggers. Record concrete acceptance criteria, scope, and a concise plan before implementation. Verify each criterion and review the evidence.
- **Governed:** authentication, security, sensitive data, schema or public contract change, irreversible operation, or accepted architecture impact. Follow the full proposal, approval, handoff, independent review, and close lifecycle below. Security review remains required for sensitive work.

Reclassify when paths or meaning change. A configured check passing covers that check; it does not prove an end-to-end or production quality measure.

For a diff or architecture-sensitive change, run `python3 scripts/orace.py check --diff <base...HEAD>` or `impact --path <path>`. Treat affected ADRs and drift findings as review candidates; never rewrite an accepted decision automatically.

## 3. Propose (Governed)

Write `agent_<role>/PROPOSED_CHANGES.md`: intent, files to modify, ordered plan, risks, and test plan. Nothing outside the workspace changes in this phase.

Stop and write `CLARIFICATIONS.md` instead of guessing when a contract is missing, two selected documents genuinely conflict, or the work requires an architectural decision no ADR covers. The supervisor's answer to the last case is `/orace-adr`, then a routing row, then the task resumes. An agent that picks silently is the failure this framework exists to prevent.

In supervisor mode, wait for approval. In sequential mode, record the self-approval and continue — the same gates still apply.

## 4. Execute

Implement only the authorised scope and file set. In Governed mode wait for required approval. Adjacent problems you discover become backlog entries when they need future work, not extra commits.

Apply the selected documents as written. When a playbook default and an architecture `Measure` both speak to what you are changing, the architecture governs — and the handoff says so by id.

## 5. Verify and hand off

Run the checks from `.spec/project.json` that the change actually warrants, plus any the selected specifications require. `python3 scripts/orace.py verify --check <group> --task <id> --output .spec/40_workspace/<id>/evidence.json` captures commands, exit codes, output tails, timestamps, and commit SHA. Inspect the output and report what it actually establishes. Standard and Governed tasks write a handoff using the [artifact templates](references/artifacts.md); Lite reports the same essential facts compactly.

Evidence means the command and its real output, a file and line, or a specification rule id. Never report a check you did not run; never report a passing suite while hiding new skips (`AI_GOVERNANCE.md` AIG-02, `TESTING.md` TEST-13).

Name the governing requirement beside each acceptance criterion — `QA-AVAIL-01`, `SEC-03`, `PY-08` — so the reviewer can check the claim without re-deriving the routing.

## 6. Review

A sensitive change needs `agent_security/SECURITY_REVIEW.md` before close. Governed tasks end with `spec-review` judging the handoffs independently, then the supervisor closes against the Definition of Done. Standard tasks receive a structured review of criteria and evidence. Lite tasks may close on the compact result when relevant checks pass.

## Refresh

Re-run selection when scope, affected paths, playbooks, or the architecture change, and load newly relevant documents before dependent work.

After a new session, a compaction, or a sub-agent start, recover scope from `TASK_CONTEXT.md` and re-read the selected sources. A file hash proves a file is unchanged; it never proves the text is still in the model's context. Do not mechanically re-read unchanged documents you still hold.

## Working as a sub-agent

You were given a package brief with task ids, authorised paths, routing ids, and acceptance criteria — not specification bodies. Load the documents yourself from the recorded ids.

Stay inside the package's file ownership; another package may hold the file you want. Return a `HANDOFF.md` and a short result message. Do not return specification text, full file contents, or reasoning transcripts — the supervisor's context is a shared resource.
