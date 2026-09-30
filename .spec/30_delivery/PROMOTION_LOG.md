# Promotion log

Every canonical change — global policy, playbook packs, the architecture tree, the routing index, the project configuration, the backlog — is recorded here by the supervisor.

```markdown
## <date> — <task id> — <what changed>
- Approver: <who authorised it>
- Change: <canonical paths and the substance of the change>
- Reason: <why, referencing the clarification, ADR, or evidence signal that prompted it>
- Impact: <tasks reopened, contracts affected, migration required>
- Validation: <commands run and result>
```

---

## 2026-09-28 — ORACE-TECH-001 — Add the ORACE technology-profile workflow
- Approver: User, via the explicit request to make the necessary changes for new and existing projects rerunning the workshop.
- Change: Promoted the framework task in `.spec/20_backlog/TASKS.md`, clarified technology-derived configuration in `.spec/project.json`, and updated `.spec/15_architecture/README.md` for the new `approaches.md` and `technology-profile.md` artifacts. The canonical ORACE/bootstrap skills, adoption documentation, initializer guidance, prompt examples, and regression tests now support evidence-backed greenfield discovery and non-destructive brownfield technology reruns.
- Reason: ORACE previously left technology choices scattered across ADRs and views, forcing bootstrap to infer the stack and losing tactic-level content that Phase A claimed to persist.
- Impact: Existing architecture content is not migrated automatically. On the next workshop invocation, an architecture without `approaches.md` or `technology-profile.md` resumes at Phase A; `--rerun technology` refreshes only the baseline and reports affected views, routing rows, and tasks. No application contract, schema, or runtime migration is introduced.
- Validation: `python3 scripts/spec.py validate` — passed (`19` specifications, `4` active playbooks); `python3 scripts/sync_skills.py --check` — passed (`1` adapter); `python3 -m unittest discover -s tests -v` — passed (`33` tests); `git diff --check` — passed with no output; `python3 scripts/spec.py select --task ORACE-TECH-001` — passed (`9` specifications, approximately `7,481` tokens).

## 2026-09-28 — ORACE-TECH-001 — Close after independent review
- Approver: User authorised the implementation; fresh Reviewer-Agent verdict `accept` in `.spec/40_workspace/orace-technology-profile/REVIEW_REPORT.md`.
- Change: Marked `ORACE-TECH-001` complete after adding the two contract-test assertion groups requested by the first review. Preserved the superseded handoff and reopen report as audit history.
- Reason: Close the task only after every acceptance criterion was directly evidenced and the second independent review found no remaining criterion, handoff, scope, precedence, or security issue.
- Impact: No additional architecture or application migration. The framework technology-profile workflow is ready for use; a live greenfield/brownfield usability exercise remains a disclosed, non-blocking residual risk.
- Validation: Final close-out run: `python3 scripts/spec.py validate` passed (`19` specifications, `4` active playbooks); `python3 scripts/sync_skills.py --check` passed (`1` adapter); `python3 -m unittest discover -s tests -v` passed (`33` tests, no skips or expected failures); `git diff --check` passed with no output.

## 2026-09-28 — ORACE-USAGE-001 — Add workshop token-usage reporting
- Approver: User, via the explicit request to add a final consumed-token count to the ORACE workshop.
- Change: Added a workshop-invocation usage boundary and final accuracy-labeled token report to `.agents/skills/orace-workshop/SKILL.md`; documented the behavior in `README.md` and `docs/ADOPTION.md`; added `ORACE-USAGE-001` to `.spec/20_backlog/TASKS.md`; extended contract tests for measurement modes, accounting invariants, scope, final-response boundaries, and non-persistence.
- Reason: Architects need visibility into workshop context consumption, but hosts expose different telemetry and missing usage must not be replaced with a plausible estimate.
- Impact: No architecture artifact, application contract, schema, or runtime migration. Completed workshops and targeted reruns now end with a measured, trace-counted, or unavailable usage block. Existing workshop artifacts are untouched.
- Validation: `python3 scripts/spec.py validate` passed (`19` specifications, `4` active playbooks); `python3 scripts/sync_skills.py --check` passed (`1` adapter); `python3 -m unittest tests.test_orace_workflow -v` passed (`13` tests); `python3 -m unittest discover -s tests -v` passed (`37` tests, no skips or expected failures); `git diff --check` passed with no output; `python3 scripts/spec.py select --task ORACE-USAGE-001` passed (`8` specifications, approximately `6,827` tokens).

## 2026-09-28 — ORACE-USAGE-001 — Close after independent review
- Approver: User authorised the implementation; fresh Reviewer-Agent verdict `accept` in `.spec/40_workspace/orace-token-usage/REVIEW_REPORT.md`.
- Change: Marked `ORACE-USAGE-001` complete after independent verification of the usage-boundary, accuracy-mode, non-double-counting, final-response-boundary, subagent, billing, and non-persistence contracts.
- Reason: Close only after the reviewer confirmed every acceptance criterion and found no handoff, scope, precedence, control-weakening, or security issue.
- Impact: No additional migration or behavior change beyond the promoted reporting contract. Hosts without workshop-scoped usage telemetry will truthfully report `Unavailable`.
- Validation: Independent review reran specification validation, adapter synchronization, 13 targeted tests, 37 full-suite tests with no skips or expected failures, and `git diff --check`; all passed.

## 2026-09-28 — ORACE-README-001 — Document technology and token-usage workflow

- Approver: User, via the explicit request to update `README.md` with the latest technology-step and token-consumption changes.
- Change: Added detailed README guidance for technology capture across ORACE, new and existing project handling, source-of-truth ownership, targeted technology reruns, bootstrap consumption, and workshop-scoped token reporting. Added two README content-contract tests and registered the documentation task and its evidence workspace.
- Reason: The implementation existed, but the top-level README only summarized it; architects needed a complete operational explanation at the framework entry point.
- Impact: Documentation and deterministic documentation tests only. No workshop behavior, architecture artifact, application contract, schema, generated adapter, or runtime is changed.
- Validation: `python3 scripts/spec.py validate` passed (`19` specifications, `4` active playbooks); `python3 scripts/sync_skills.py --check` passed (`1` adapter); `python3 -m unittest tests.test_orace_workflow -v` passed (`15` tests); `python3 -m unittest discover -s tests -v` passed (`39` tests, no skips or expected failures); `git diff --check` passed with no output; `python3 scripts/spec.py select --task ORACE-README-001` passed (`8` specifications, approximately `6,827` tokens).

## 2026-09-28 — ORACE-README-001 — Close after independent review

- Approver: User authorised the documentation update; fresh Reviewer-Agent verdict `accept` in `.spec/40_workspace/orace-readme-latest/REVIEW_REPORT.md`.
- Change: Marked `ORACE-README-001` complete after independent verification of all four README and validation acceptance criteria.
- Reason: Close only after the reviewer confirmed technology lifecycle coverage, token-accounting coverage, the selector-versus-consumption distinction, exact validation evidence, clean scope, and no weakened controls.
- Impact: No additional behavior or migration. The top-level README is now the complete user-facing guide to both features.
- Validation: Independent review reran 15 focused tests, specification validation, adapter synchronization, 39 full-suite tests with no skips or expected failures, `git diff --check`, and task routing; all passed.
