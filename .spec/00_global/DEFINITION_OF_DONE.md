---
id: done
---

# Definition of done

> The closing gate. A task is done when each applicable gate has evidence — not an assertion.

| # | Gate | Evidence required |
|---|---|---|
| DOD-01 | Acceptance criteria satisfied | Each criterion named, with the observation that proves it |
| DOD-02 | Approved scope respected | Changed-file list is a subset of the package's authorised paths |
| DOD-03 | Build and type checks pass | Exact command and its real output |
| DOD-04 | Relevant tests pass | Test ids traceable to the criteria and scenarios they defend |
| DOD-05 | Lint and format clean | Exact command and result |
| DOD-06 | Sensitive change reviewed | `SECURITY_REVIEW.md` with verdict `approved` |
| DOD-07 | Contract compatibility preserved | Contract diff, version bump, or recorded approval to break |
| DOD-08 | Migration is reversible | Forward and rollback path both exercised |
| DOD-09 | Observability in place | Metric, log, and trace names as specified in the evidence plan |
| DOD-10 | Specifications current | Affected specs updated by promotion, or confirmed unaffected |
| DOD-11 | No new dead code or blocking TODOs | Grep result or reviewer confirmation |
| DOD-12 | Evidence reported at the required level | Lite: compact result; Standard: concise handoff and review; Governed: `HANDOFF.md` plus independent `REVIEW_REPORT.md` verdict `accept` |

## Rules

- **DOD-13** A gate that does not apply MUST be recorded as not applicable *with a reason*. Silence is not a waiver.
- **DOD-14** A gate that could not run (missing environment, unavailable dependency) leaves its acceptance criterion **open**. The task cannot close on it.
- **DOD-15** Never claim a check passed that was not run. This is the single fastest way for an agent to lose the right to close its own work.
- **DOD-16** Future backlog items and documented examples are not unresolved work in the current task.
- **DOD-17** Commands come from `.spec/project.json` `checks`. Application checks apply only when the affected application exists in this repository.
