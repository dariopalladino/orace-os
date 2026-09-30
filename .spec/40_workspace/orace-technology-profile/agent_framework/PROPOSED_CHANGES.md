### PROPOSED_CHANGES
- Task: `orace-technology-profile`
- Intent: Close the gap between project-specific architecture and reusable technology playbooks by making the workshop produce an explicit, evidence-backed technology profile that works for greenfield discovery and brownfield reruns.
- Files to modify: `.agents/skills/orace-workshop/SKILL.md`; `.agents/skills/spec-bootstrap/SKILL.md`; `.spec/project.json`; `.spec/15_architecture/README.md`; `.spec/20_backlog/TASKS.md`; `.spec/30_delivery/PROMOTION_LOG.md`; `README.md`; `PROMPT.md`; `docs/ADOPTION.md`; `scripts/init_project.py`; existing or new tests under `tests/`; task workspace artifacts.
- Implementation plan:
  1. Add explicit rerun targeting and resume rules so completed workshops can rerun Technology and affected Communication views without `--reset`.
  2. Extend Outcomes with current/mandated/prohibited technology constraints while keeping Requirements implementation-neutral.
  3. Make Approaches persist its collected tactics in `approaches.md`, add a greenfield/brownfield technology-mapping interview, write `technology-profile.md`, and elevate costly choices to ADRs.
  4. Make Communication views consume and cross-check the profile rather than duplicate it, and add relevant technology assumptions to Evidence/Evolution.
  5. Update `/spec-bootstrap` to read the profile first, derive playbooks and validation checks with confirmation, register both new Phase A artifacts with selective surfaces, and identify missing playbooks or evidence.
  6. Align README, adoption, architecture-folder, and initializer guidance with the workshop-first/bootstrap-derived workflow.
  7. Add regression tests over the skill and documentation contracts, run all required checks, write handoff/review evidence, and log canonical promotion.
- Requirements applied: PROTO-01 through PROTO-05, PROTO-08, PROTO-11; AIG-01 through AIG-05; PRIN-02, PRIN-03, PRIN-04, PRIN-09, PRIN-10; CA-08, CA-09; GOV-02, GOV-07; TEST-06, TEST-08, TEST-13.
- Risks: A monolithic technology inventory could over-route context; mitigate with compact tables and selective surfaces. Reruns could overwrite accepted architecture; mitigate with explicit target selection, impact reporting, and per-file confirmation/promotion. Exact versions could duplicate lockfiles; mitigate by recording version policy plus source-of-truth paths. Bootstrap inference could invent commands; require evidence from profile/manifests and user confirmation.
- Cost and scale notes: Documentation/skill-only change; no runtime resource, query, model-call, or production cost impact. Added routed context is one compact architecture artifact, expected to remain in the low-thousands of characters.
- Test plan: Add deterministic content-contract tests; run `python3 scripts/spec.py validate`, `python3 scripts/sync_skills.py --check`, and `python3 -m unittest discover -s tests -v`.
- Approval: Approved for execution by the user’s explicit implementation request on 2026-09-28; primary agent is acting as supervisor and promotion owner.
