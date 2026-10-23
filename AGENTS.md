# Operating contract

This repository uses SDDF specifications in `.spec/`. Apply only the documents routed to the current task and preserve evidence. Explicit user and platform instructions take precedence.

## Before changing files

1. Route an ad hoc request with `python3 scripts/orace.py task "<request>" --path <path>`, or a registered task with `python3 scripts/spec.py select --task <id>`. Check the inferred surfaces and mode against the actual behavior; `.spec/INDEX.md` is the manual fallback. Read `.spec/project.json` for active playbooks, roots, roles, and checks.
2. Read every selected document in full, including routed dependencies. Do not read `.spec/` wholesale or load unselected specifications. Classify by meaning: a UI token-storage change also touches auth and security.
3. Use `.agents/skills/spec-workflow/SKILL.md` for the task lifecycle. Read it directly if skill discovery is unavailable.

Precedence: approved architecture measures and accepted ADRs → global policies → playbook packs → backlog task → code. When an architecture measure displaces a policy or playbook default, record the reason in task context. Never silently override security rules; escalate conflicts.

## Lifecycle and ownership

Choose the minimum safe mode: **Lite** for narrow repairs (route, execute, verify); **Standard** for features or refactors (criteria, plan, execute, verify, review); **Governed** for sensitive, contractual, irreversible, or architecture-significant work (select, propose, approve, execute, handoff, independent review, close). Escalate if scope or risk changes. Inferred modes do not remove security or architecture constraints.

- Governed proposals go only in `.spec/40_workspace/<task-id>/agent_<role>/`; change source only after required approval and within authorised paths.
- Canonical policies, playbooks, architecture, `INDEX.md`, `project.json`, and `TASKS.md` change only by supervisor promotion recorded in `.spec/30_delivery/PROMOTION_LOG.md`.
- For a missing contract, real conflict, or uncovered architecture decision, write `CLARIFICATIONS.md` and stop that work. Do not invent an answer.
- Never weaken a test, lint rule, type check, security control, or acceptance criterion to pass. Report exact commands and actual results.

## Context and roles

Use one conversation per task; start a new one for unrelated work. At a stable checkpoint in a long task, persist decisions, changed paths, check results, and next action, then compact if needed. Reuse source text still in context; re-read after a scope change, new session, or compaction. A hash cannot restore forgotten text. Workshop phases load one at a time. Host commands and model choices are in `docs/CONTEXT_MANAGEMENT.md`.

With `supervisor` orchestration, run independent work packages in parallel through the host's subagents when available; sequence dependent work or packages that touch the same files. Dispatch bounded packages with disjoint ownership to roles in `.agents/roles/` (`.claude/agents/`, `.codex/agents/`, `.github/agents/`). Send routing **ids**, acceptance criteria, and paths, not specification bodies. Subagents load their own documents and return short handoffs. With `sequential` orchestration or no subagents, preserve the same handoffs and gates. A Governed reviewer must be independent of the implementer.

Framework checks: `python3 scripts/spec.py validate`, `python3 scripts/sync_skills.py --check`, `python3 -m unittest discover -s tests -v`. Application checks come from `.spec/project.json` when the affected application exists.
