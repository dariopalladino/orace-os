# Shared artifact templates

Use only the template for the phase you are in. Replace placeholders with concrete evidence; omit optional sections that are empty. Paths are repository-relative.

## Task context — supervisor or sequential coordinator

`.spec/40_workspace/<task-id>/TASK_CONTEXT.md`. Specialists read this and report updates to its owner.

```markdown
# Task context
- Task: <id and objective>
- Package: <work package id, when dispatched as one>
- Scope: <authorised behaviour and explicit exclusions>
- Phase: select | propose | execute | handoff | review | complete
- Authorization: <the request and any applicable existing approval>
- Playbooks: <active playbook packs>
- Selected specifications: <id — path — reason, one per line>
- Context estimate: <tokens reported by scripts/spec.py select>
- Governing requirements: <where documents disagreed: what governs, what it displaced, why>
- Ownership: <role — files this package may change>
- Acceptance criteria: <observable outcomes, each naming what proves it>
- Validation: <required checks>
- Progress: <done, open, next action>
```

## Proposal

`.spec/40_workspace/<task-id>/agent_<role>/PROPOSED_CHANGES.md`.

```markdown
### PROPOSED_CHANGES
- Task: <reference>
- Intent: <the problem being solved>
- Files to modify: <list — must be inside the authorised ownership set>
- Implementation plan: <ordered changes>
- Requirements applied: <rule ids this plan satisfies, e.g. CA-02, SEC-03, QA-PERF-02>
- Risks: <regressions, edge cases, blast radius>
- Cost and scale notes: <new resource, model call, or query pattern with an order-of-magnitude estimate>
- Test plan: <commands and the behaviour each asserts>
```

## Clarifications — only when blocked

`.spec/40_workspace/<task-id>/agent_<role>/CLARIFICATIONS.md`. Routine implementation choices are resolved from the selected requirements without a clarification.

```markdown
### CLARIFICATIONS
- Task: <reference>
#### Q1: <the decision needed>
- Context: <the missing or conflicting evidence, with document ids>
- Options: <viable alternatives, each with a consequence>
- Impact: <behaviour, contract, architecture, or authorisation affected>
- Recommendation: <preferred option and why>
- Blocking: yes | no
```

## Handoff

`.spec/40_workspace/<task-id>/agent_<role>/HANDOFF.md`. This is the document the reviewer judges.

```markdown
### HANDOFF
- Task: <reference>
- Status: done | blocked | needs_review
- Summary: <3–6 concrete bullets: what changed and why>
- Files changed: <list>
- Commands run: <exact commands>
- Evidence:
  - <acceptance criterion> — <governing requirement id> — <observation that proves it>
- Requirements applied: <rule ids>
- Deviations: <any place the implementation differs from the proposal, and why>
- Checks not run: <check — reason — which criterion it leaves open>
- Risks and edge cases: <what could still break>
- Residual risk: <what was not verified>
- Next steps: <remaining actions, or none>
```

## Security review

`.spec/40_workspace/<task-id>/agent_security/SECURITY_REVIEW.md`, required for sensitive changes.

```markdown
### SECURITY_REVIEW
- Task: <reference>
- Status: approved | changes_required | blocked
- Scope: <files, behaviour, and the security requirements selected>
- Findings: <severity — location — impact — remediation; or "none found" with what was examined>
- Negative tests: <the authorisation and validation cases actually exercised>
- Checks run: <exact commands and results>
- Residual risks: <unverified behaviour>
- Required follow-up: <blocking fixes, or none>
```

## Review report

`.spec/40_workspace/<task-id>/REVIEW_REPORT.md`, written by the reviewer over all handoffs in the task.

```markdown
### REVIEW_REPORT
- Task: <reference>
- Handoffs reviewed: <paths>
- Verdict: accept | revise | reopen
- Criterion coverage:
  - <criterion> — covered | unproven | contradicted — <the evidence, or what is missing>
- Handoff quality findings:
  - <handoff path> — <what is missing, vague, or unsupported> — <required correction>
- Requirement conflicts: <cases where a default was applied over a governing architecture measure, or the reverse>
- Scope findings: <changes outside the authorised set>
- Required actions before close: <ordered list, or none>
```

## Promotion entry

Append to `.spec/30_delivery/PROMOTION_LOG.md` for every canonical change.

```markdown
## <date> — <task id> — <what changed>
- Approver: <who authorised it>
- Change: <canonical paths and the substance of the change>
- Reason: <why, referencing the clarification, ADR, or evidence signal that prompted it>
- Impact: <tasks reopened, contracts affected, migration required>
- Validation: <commands run and result>
```
