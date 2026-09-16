---
description: Record one architecture decision as an ADR and register its routing row
---

Read and follow `.agents/skills/orace-adr/SKILL.md`.

Architecture folder: `$ARGUMENTS` if given, otherwise `architecture_root` from `.spec/project.json`.

One decision per ADR. Seven questions, one at a time. The ADR is not finished until its row is in `.spec/INDEX.md`, the risk is in the register, the promotion is logged, and `python3 scripts/spec.py validate` passes.
