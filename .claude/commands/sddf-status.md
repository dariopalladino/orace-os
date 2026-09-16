---
description: Show the current state of the specification store, backlog, and routing
---

Report, without loading specification bodies:

1. `python3 scripts/spec.py validate` and `python3 scripts/spec.py playbooks`.
2. Whether the architecture root has artifacts and whether they are all registered in `.spec/INDEX.md`.
3. Open tasks in `.spec/20_backlog/TASKS.md` grouped by `Package`, with status and owner.
4. Task workspaces under `.spec/40_workspace/` whose latest artifact is a handoff with no `REVIEW_REPORT.md` — these are waiting on `/spec-review`.
5. Anything blocked: tasks with status `blocked`, and any `CLARIFICATIONS.md` with `Blocking: yes` and no resolution in the promotion log.

Keep it to a short table per section. Do not read the specifications themselves.
