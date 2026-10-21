# Copilot instructions

This repository is governed by SDDF. Follow `AGENTS.md`, and read `.agents/skills/spec-workflow/SKILL.md` before making a change — Copilot does not discover skills automatically, so read that file directly.

Do not read the whole `.spec/` store. Select what the task needs through `.spec/INDEX.md`:

```sh
python3 scripts/spec.py select --surface backend --surface auth --path api/src/login.py
python3 scripts/orace.py task "Fix login validation" --path api/src/login.py
```

Read every selected document in full. Confirm inferred surfaces and the task command's minimum Lite, Standard, or Governed mode. Lite returns a compact verified result; Standard records criteria and a concise plan; Governed uses a proposal in `.spec/40_workspace/<task-id>/agent_<role>/PROPOSED_CHANGES.md`, required approval, handoff, and independent review. Implement only inside the authorised file set and report exact commands and real output.

Architecture requirements in the architecture root outrank the generic defaults in `.spec/00_global/` and `.spec/10_playbooks/` for the artifact they name. Never edit a canonical specification during a task; propose it instead.
