### PROPOSED_CHANGES

- Task: `ORACE-README-001`
- Intent: Make the README the clear user-facing entry point for the already implemented technology-profile and token-usage features.
- Files to modify: `README.md`; README assertions in `tests/test_orace_workflow.py`; `.spec/20_backlog/TASKS.md`; `.spec/30_delivery/PROMOTION_LOG.md`; task workspace artifacts.
- Implementation plan:
  1. Add a quick-start bridge from Phase A technology capture to bootstrap and the completion usage report.
  2. Add a technology section covering ORACE phase ownership, new versus existing/hybrid discovery, artifact sources of truth, targeted reruns, and bootstrap consumption.
  3. Add a token section covering invocation scope, accuracy modes, category accounting, subagents, final-response boundaries, billing limitations, and non-persistence.
  4. Explicitly distinguish selector `characters ÷ 4` context estimates from consumed-token reporting.
  5. Add deterministic documentation contract tests and run all framework checks.
- Requirements applied: PROTO-01 through PROTO-05 and PROTO-08; AIG-01, AIG-02, and AIG-09; PRIN-02 and PRIN-10; GOV-02 and GOV-07; TEST-06, TEST-08, and TEST-13.
- Risks: Documentation could drift from skill behavior; mitigate with assertions over the stable user-facing contract. A sample usage block could imply billing precision; mitigate with explicit best-effort, temporal-boundary, and non-billing language.
- Test plan: Run focused ORACE workflow tests, framework validation, adapter synchronization, whitespace checks, the full test suite, and task routing.
- Approval: Approved for execution by the user's explicit documentation request on 2026-09-28; the primary agent acts as supervisor and promotion owner.
