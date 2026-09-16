---
name: spec-review
description: Final review of a task's handoff documents before close — judge whether each acceptance criterion is actually evidenced, whether the handoffs themselves need correction, and whether the work stayed in scope. Use at the end of a task or work package, after specialists have written their handoffs.
trigger: /spec-review
---

# Spec review

The last gate. You are reviewing **the evidence and the handoff documents**, not re-implementing the work. Your output is a verdict the supervisor can act on.

You run in a fresh context on purpose. You did not write this code and you have no stake in it passing.

```
/spec-review <task-id>
```

## What to load, and nothing more

1. `.spec/40_workspace/<task-id>/TASK_CONTEXT.md` — scope, acceptance criteria, selected specifications, ownership, governing requirements.
2. Every `agent_<role>/HANDOFF.md` and `SECURITY_REVIEW.md` under that task.
3. The backlog task entry.
4. The **acceptance-bearing** specifications only: the ones whose rules a criterion names. Use `python3 scripts/spec.py select --task <task-id>` to see what the implementer should have held; read the subset the criteria actually depend on.

Read source files only where a specific claim needs checking (step 3). Reading the whole diff makes you a second implementer and blows the context this role exists to conserve.

## Step 1 — Criterion coverage

For every acceptance criterion, classify:

- **covered** — the handoff names an observation that would convince a sceptic: a command and its output, a test id that exercises it, a metric now emitted, a contract diff.
- **unproven** — the handoff asserts it without evidence, or the evidence does not actually test the criterion. A criterion saying "recovery completes in ≤ 30 s" is not covered by a unit test that mocks the recovery.
- **contradicted** — the evidence shows something different from the claim.

A criterion whose check could not run is **open**, not satisfied (`DEFINITION_OF_DONE.md` DOD-14). Say which check and why.

## Step 2 — Judge the handoff documents themselves

This is the part that is usually skipped, and it is half the value of the role. Handoffs are what the next agent, and the next human, will rely on. A thin handoff over good work still leaves the task unmaintainable.

Flag each of these as a required correction:

- **Vague evidence.** "Tests pass", "verified manually", "works as expected" — no command, no output, no test name.
- **Missing commands.** Checks claimed with no exact invocation.
- **Unreported gaps.** Skipped, quarantined, or newly flaky tests not mentioned (`TESTING.md` TEST-13). A green suite hiding twelve skips is a false signal.
- **Silent deviations.** The implementation differs from the approved proposal and the handoff does not say so or why.
- **Unattributed requirements.** A criterion closed without naming the rule or scenario id that governs it, when the task context recorded one.
- **Empty residual risk.** Any non-trivial change with "none" here is almost always incomplete thinking, not perfection. Ask what was not verified.
- **Undocumented new behaviour.** New configuration, metric, flag, or migration with no note of how to operate it.
- **Leaked secrets or personal data** in the handoff text (`AI_GOVERNANCE.md` AIG-07). Treat as blocking.

Write each finding as *what is missing* plus *the correction required* — not as a style note.

## Step 3 — Spot-check the claims that matter

Pick the two or three highest-consequence claims and check them against the repository:

- A test named as evidence — does it exist, and does it assert the number in the criterion?
- A negative authorisation case — is there a test for the wrong tenant, wrong role, no credentials (`TESTING.md` TEST-15)?
- A metric named in the evidence plan — is that exact name emitted?
- A migration — is there a rollback path?

Report what you checked and what you did not. A review that claims more coverage than it performed is the same failure it is meant to catch.

## Step 4 — Scope and precedence

- **Scope.** Compare the changed-file list against the package's authorised ownership. Files outside it are a finding even when the change is good.
- **Precedence.** Where a playbook or policy default and an architecture `Measure` both applied, check that the architecture governed and that the handoff says so by id. A task that shipped a 300 ms default over a 500 ms scenario — or the reverse — is a governance failure even if the code works (`PRINCIPLES.md`, Resolving a conflict).
- **Weakening.** Check that no test, lint rule, type check, or security control was disabled, narrowed, or annotated away to make the work pass (`AI_GOVERNANCE.md` AIG-03). Look for new suppressions, changed thresholds, and removed assertions.
- **Canonical edits.** Check that no specialist wrote to a canonical path without promotion (`GOVERNANCE.md` GOV-01).

## Step 5 — Verdict

Write `.spec/40_workspace/<task-id>/REVIEW_REPORT.md` using the template in the `spec-workflow` skill's [artifact templates](../spec-workflow/references/artifacts.md).

| Verdict | Use when |
|---|---|
| `accept` | Every criterion covered, handoffs sufficient, scope clean |
| `revise` | The work is sound but a handoff needs correction or a check needs running — the specialist fixes the document or runs the check, nothing is re-implemented |
| `reopen` | A criterion is unproven or contradicted, scope was exceeded, a control was weakened, or a sensitive change has no security review |

Then report to the supervisor in a short message: the verdict, the number of findings by class, and the ordered required actions. Do not paste the report body into the message — the supervisor reads the file.

## Rules

- Judge against the recorded criteria and the selected specifications. Do not invent new requirements at review time; a genuinely missing requirement is a backlog item you name, not a reason to block.
- Do not fix the code. Finding and fixing in the same pass destroys the independence that makes this review worth running.
- Be specific and be brief. "HANDOFF.md line 12: 'tests pass' — name the command and paste its output" is actionable. "Improve the handoff quality" is not.
- An `accept` you are not confident in is worse than a `revise`. Say what you could not verify.
