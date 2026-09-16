# Adoption

How to put SDDF into a repository. Two paths: a new system, and one that already has code.

## New system

```
1. /orace-workshop .spec/15_architecture      half a day with real stakeholders
2. /spec-bootstrap                            register rows, pick playbooks, derive the backlog
3. python3 scripts/spec.py validate           must be clean before the first task
4. one proposal-only task in each host you use — inspect what it selected
5. one real task end to end, through /spec-review
```

Do the workshop **first**. There is nothing for the framework to route until the architecture exists, and a backlog derived from guesses is worse than no backlog.

## Existing repository

Work on a branch. Nothing here needs to change your source layout.

**1. Copy the framework in.**

```sh
python3 scripts/init_project.py --target /path/to/your/repo
```

It copies `.spec/`, `.agents/`, `.claude/`, `scripts/`, and `tests/`, and **merges** rather than overwrites `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` — your existing instructions are preserved above an appended SDDF section. It refuses to clobber an existing `.spec/`; use `--force` only when you mean it.

**2. Configure `.spec/project.json`.**

- `playbooks` — only the packs you actually use. A pack you activate but do not follow is noise on every task.
- `module_roots` — map your real directories to surfaces. This is what turns a file path into a routing decision, so it is worth getting right. Include a source root under `implementation`.
- `checks` — your real commands. Do not leave the defaults if they are not what you run.
- `orchestration` — `supervisor` for multi-package work, `sequential` for a single agent doing the stages in order. The gates are identical.

**3. Capture the architecture you already have.**

You almost certainly have decisions, none of them written down in a form an agent can load. Run `/orace-workshop .spec/15_architecture`. For an existing system it is a documentation exercise rather than a design one, and it goes faster — but the `Measure` fields still need real numbers, and this is the moment to discover you do not have them.

If you already have architecture documents elsewhere in the repository, leave them where they are and register those paths in `.spec/INDEX.md` instead. The index takes any repository-relative path. Placement matters far less than registration.

**4. Bootstrap and validate.**

```sh
/spec-bootstrap
python3 scripts/spec.py validate
```

**5. Calibrate the routing before you trust it.**

```sh
python3 scripts/spec.py select --surface frontend --surface auth --path web/src/login.tsx
```

Read the output. Did the deployment view arrive for an auth change? Did an unrelated playbook stay out? Did the estimate land inside your budget? Fix surfaces now, not after ten tasks have been routed wrongly. Add the cases you care about to `.spec/validation/ROUTING_CASES.json` so a future edit cannot break them silently.

**6. Start small.**

One proposal-only task. Read what it selected and what it wrote. Then one real task through the full lifecycle including `/spec-review`. Do not convert the whole backlog on day one.

## Adapting the packs to your conventions

The packs in `.spec/00_global/` and `.spec/10_playbooks/` are opinionated on purpose — vague policy produces vague compliance. Where a rule contradicts a convention your team has already settled, **change the rule** rather than tolerating a spec nobody follows. Edit it, log the change in `.spec/30_delivery/PROMOTION_LOG.md`, and keep the rule id so handoffs stay citable.

Deleting a rule you do not want is better than keeping one you will not enforce.

## Rollback

Everything SDDF adds lives in `.spec/`, `.agents/`, `.claude/`, `scripts/`, `tests/`, and appended sections of the three instruction files. Removing those directories and the appended sections leaves your repository as it was. Nothing in your source tree depends on the framework.

## Host support

| Host | Discovery | Fallback |
|---|---|---|
| Claude Code | `.claude/skills` (synced from `.agents/skills`), `.claude/agents`, `.claude/commands` | read `SKILL.md` directly |
| Codex | `AGENTS.md` | read `SKILL.md` directly |
| GitHub Copilot | `.github/copilot-instructions.md` | read `SKILL.md` directly |
| Anything else | point it at `AGENTS.md` | — |

Run `python3 scripts/sync_skills.py` after adding a skill, and `--check` in CI. Verify discovery in each host you actually use rather than assuming it; a direct instruction to read the skill file always works.
