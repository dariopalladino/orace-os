# Repository instructions

Follow `AGENTS.md`; read it if it is not already in context.

Use the `spec-workflow` skill for specification-governed work. If skill discovery is unavailable, read `.agents/skills/spec-workflow/SKILL.md` directly.

Entry points:

| Situation | Skill |
|---|---|
| New system, no architecture yet | `/orace-workshop .spec/15_architecture` |
| Architecture exists but is not wired into `.spec/` | `/spec-bootstrap` |
| A decision that is costly to reverse comes up | `/orace-adr` |
| Implementing or changing something | `spec-workflow` |
| A task's handoffs are written and it is ready to close | `/spec-review <task-id>` |

Route ad hoc requests with `python3 scripts/orace.py task "<request>" --path <path>` or registered tasks with `python3 scripts/spec.py select --task <id>`. Confirm inferred surfaces and the minimum Lite, Standard, or Governed mode from the actual change. The canonical planned backlog is `.spec/20_backlog/TASKS.md`; ad hoc work need not be added first. Load complete applicable documents plus their dependencies, and reuse them while scope and context remain valid.

Agent role definitions are in `.claude/agents/`. In supervisor orchestration, dispatch one sub-agent per work package with routing ids rather than specification text.
