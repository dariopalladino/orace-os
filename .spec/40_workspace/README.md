# Workspace

One folder per task: `.spec/40_workspace/<task-id>/`.

```
TASK_CONTEXT.md          scope, routing result, governing requirements, progress  (supervisor)
REVIEW_REPORT.md         final verdict over the handoffs                          (reviewer)
agent_<role>/
  PROPOSED_CHANGES.md    the plan, before any source file changes
  CLARIFICATIONS.md      only when genuinely blocked
  HANDOFF.md             what changed, with evidence
  SECURITY_REVIEW.md     for sensitive changes
```

These are **evidence of work**, never policy. Do not load a historical workspace to learn what the rules are — read the specifications the index selects. Inspect a prior workspace only for continuity on the same task.

Nothing here is deleted or rewritten. Superseded artifacts are marked superseded and kept; the audit trail is the point.

Templates live in `.agents/skills/spec-workflow/references/artifacts.md`.
