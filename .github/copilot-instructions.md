# Copilot instructions

This repository is governed by SDDF. Follow `AGENTS.md`, and read `.agents/skills/spec-workflow/SKILL.md` before making a change — Copilot does not discover skills automatically, so read that file directly.

Do not read the whole `.spec/` store. Select what the task needs through `.spec/INDEX.md`:

```sh
python3 scripts/spec.py select --surface backend --surface auth --path api/src/login.py
```

Read every selected document in full, then follow the lifecycle: proposal in `.spec/40_workspace/<task-id>/agent_<role>/PROPOSED_CHANGES.md`, implementation only inside the approved file set, handoff with exact commands and real output.

Architecture requirements in the architecture root outrank the generic defaults in `.spec/00_global/` and `.spec/10_playbooks/` for the artifact they name. Never edit a canonical specification during a task; propose it instead.
