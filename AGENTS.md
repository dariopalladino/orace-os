# Operating contract

This repository is governed by **SDDF** — specifications in `.spec/`, selected per task, with evidence preserved. This file is the short contract; it is loaded on every turn, so it stays short.

## Before you change anything

1. Route. For an ad hoc request use `python3 scripts/orace.py task "<request>" --path <path>`; for a registered task use `python3 scripts/spec.py select --task <id>`. Confirm inferred surfaces and mode from the behavior, or apply `.spec/INDEX.md` by hand. Read `.spec/project.json` for active playbooks, module roots, orchestration, and checks.
2. Read every selected document **in full**. Never read the specification store wholesale, and never load what routing did not select.
3. Classify by meaning, not by folder. A token-storage change inside a UI component is `frontend`, `auth`, **and** `security`. Role and path are hints; they cannot infer every security implication.
4. Use the `spec-workflow` skill at `.agents/skills/spec-workflow/SKILL.md`. Read it directly if skill discovery is unavailable.

## Precedence

Architecture (an approved quality-attribute scenario `Measure`, an accepted ADR) → global policy in `.spec/00_global/` → playbook packs in `.spec/10_playbooks/` → the backlog task → existing code.

Where a playbook or policy default and an architecture measure both speak to what you are changing, **the architecture governs** and the default falls away — record which, and why, in the task context. A security rule is the exception: it is never silently overridden by an ADR. Escalate instead. Platform and explicit user instructions outrank everything here.

## Lifecycle

Use the minimum safe mode from `scripts/orace.py task`:

- **Lite:** route → execute → verify → compact result. Narrow, low-risk fixes need no separate proposal, backlog entry, or independent review.
- **Standard:** route → criteria and concise plan → execute → verify → review. Features and refactoring use this path.
- **Governed:** select → propose → approve → execute → handoff → independent review → close. Sensitive, contractual, irreversible, and architecture-significant work uses this path.

Escalate when scope or risk changes. Description-based classification is a hint; applicable security and architecture constraints never disappear because a mode was requested.

- Governed proposal phases write only in `.spec/40_workspace/<task-id>/agent_<role>/`. Source files change only after required approval, only inside the authorised file set.
- Canonical paths — `00_global/`, `10_playbooks/`, the architecture root, `INDEX.md`, `project.json`, `TASKS.md` — change only by supervisor promotion with a `.spec/30_delivery/PROMOTION_LOG.md` entry.
- Missing contract, real conflict, or a decision no ADR covers: stop and write `CLARIFICATIONS.md`. Do not invent it.
- Never weaken a test, lint rule, type check, security control, or acceptance criterion to make your work pass.
- Report exact commands and real output. Never claim a check you did not run.

## Context

Reuse source text you still hold; re-read after a scope change, a new session, or a compaction. A file hash proves the file is unchanged — it never proves the text is still in your context.

As a sub-agent you receive routing **ids**, not bodies: load the documents yourself, stay inside your package's file ownership, and return a handoff plus a short message — not specification text or transcripts.

## Host roles

Role definitions live in `.agents/roles/`. When `project.json` chooses `supervisor` orchestration, the main agent coordinates scoped work packages and uses host role agents when available. Codex uses `orace_*` agents from `.codex/agents/`; Claude Code uses `.claude/agents/`. Dispatch only bounded packages with disjoint file ownership, and give each agent routing ids and acceptance criteria. In `sequential` mode or without subagents, fulfill the same roles in order and preserve the same handoffs and review gates. The final reviewer must not be the implementer for Governed work.

## Framework checks

```sh
python3 scripts/spec.py validate
python3 scripts/sync_skills.py --check
python3 -m unittest discover -s tests -v
```

Application checks come from `.spec/project.json` and run when the affected application exists here.
