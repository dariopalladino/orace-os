### PROPOSED_CHANGES
- Task: `ORACE-USAGE-001`
- Intent: Give architects a transparent, workshop-scoped token-consumption report without inventing precision on hosts that do not expose usage metadata.
- Files to modify: `.agents/skills/orace-workshop/SKILL.md`; `.spec/20_backlog/TASKS.md`; `.spec/30_delivery/PROMOTION_LOG.md`; `README.md`; `docs/ADOPTION.md`; `tests/test_orace_workflow.py`; task workspace artifacts.
- Implementation plan:
  1. Capture an in-memory usage baseline before the first workshop question or targeted-rerun work.
  2. Define a measurement hierarchy: host cumulative-usage delta, attributed per-turn sum, explicitly labeled estimate, or unavailable.
  3. Add a final report template with scope, source, input/cached/output/reasoning/total fields and non-double-counting rules.
  4. State the temporal boundary: usage through the last completed turn; the final summary itself is excluded unless the host can inject post-response usage.
  5. Keep usage out of ORACE architecture artifacts and avoid automatic cost claims.
  6. Document the behavior and add contract tests for all accuracy modes and accounting invariants.
- Requirements applied: PROTO-01 through PROTO-05, PROTO-08, PROTO-11; AIG-01, AIG-02, AIG-03, AIG-09; PRIN-02, PRIN-10; GOV-02, GOV-07; TEST-06, TEST-08, TEST-13.
- Risks: Hosts expose different usage surfaces; mitigate with an explicit measurement source and `Unavailable` fallback. The current final response cannot normally count itself; disclose the boundary. Cached/reasoning fields can be double-counted; define them as included subtotals. Usage can settle later; label it best-effort and not billing evidence.
- Cost and scale notes: Instruction/documentation-only behavior; no API call is added. The final report adds a small fixed amount of output. No pricing or monetary estimate is calculated.
- Test plan: Extend deterministic skill-contract tests, then run framework validation, adapter synchronization, targeted tests, full tests, and whitespace validation.
- Approval: Approved for execution by the user's explicit implementation request on 2026-09-28; primary agent acts as supervisor and promotion owner.
