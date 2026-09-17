# Contributing to SDDF

SDDF is a specification and governance layer, not an application — most contributions are text: policy packs, playbook packs, skill definitions, and the scripts that validate them. The bar for merging is the same bar the framework holds coding agents to: **rules, not tutorials**, each one registered so nothing gets loaded that nothing routes to.

Before opening a PR, read [`AGENTS.md`](AGENTS.md) (the operating contract) and, if you're touching architecture guidance, the relevant section of [`README.md`](README.md#extending-it). [`docs/EXTENDING.md`](docs/EXTENDING.md) is the detailed guide for the two most common contributions below.

## Ways to contribute

### Add a playbook pack

A playbook is technology- or provider-specific guidance (a language, a platform, a compliance regime) that some projects need and others don't.

```bash
python3 scripts/spec.py scaffold <pack-name>
```

This scaffolds `.spec/10_playbooks/<pack-name>/PACK.md` and prints the routing row to add. Then:

1. Write `PACK.md` — aim for 60–150 enforceable lines; push depth into `references/` with a stated "load when" condition.
2. Register the pack in `.spec/INDEX.md` with the narrowest correct surfaces and a `Requires` list of the global policies it specialises.
3. Add it to `.spec/project.json`'s active `playbooks` (in your example project or test fixture, not the framework's own baseline unless it should ship active by default).
4. Add routing cases to `.spec/validation/ROUTING_CASES.json` proving it loads for its own surfaces and stays out of others.
5. Run `python3 scripts/spec.py validate`.

### Add or change a rule in an existing pack or global policy

Give the rule the next stable id in its sequence (ids are permanent — never renumber; it breaks every past citation). State MUST/MUST NOT, not "consider" or "prefer". If the rule only applies to one project rather than to the technology in general, it belongs in that project's architecture as an ADR, not in a shared pack.

### Add a skill or agent role

Skills live in `.agents/skills/` (canonical) with adapters synced to `.claude/skills/`; agent role definitions live in `.claude/agents/`. A role should state what it owns and must not do, and route to policy rather than restate it — see the existing ten roles for the level of compression expected.

### Fix or extend the scripts

`scripts/spec.py`, `scripts/init_project.py`, and `scripts/sync_skills.py` are standard-library Python 3.10+ — no new runtime dependencies. If you add a surface, register it in both `SURFACES` in `scripts/spec.py` and the list in `.spec/INDEX.md`.

## Before opening a PR

Run the same three checks CI runs:

```bash
python3 scripts/spec.py validate          # registry, coverage, routing cases, budgets
python3 scripts/sync_skills.py --check    # host adapters match the canonical skill tree
python3 -m unittest discover -s tests -v  # framework tests
```

`validate` will fail on an unregistered pack, policy, or architecture artifact — that's intentional. It's the mechanism that stops guidance from being added without anything routing to it. If you're adding routing cases, add at least one asserting your new content loads where it should and at least one asserting it stays out where it shouldn't.

If your change affects the numbers in the [selective-loading table](README.md#how-selective-loading-works) or the pipeline diagram, update them — they're read from this repository, not aspirational.

## Pull requests

- Keep a PR to one pack, one policy change, or one script fix where possible — reviewers cite rule ids, and a mixed PR makes that harder.
- Describe what surfaces the change should and shouldn't load for, and how you verified it (the `select` command output is good evidence).
- Note any deviation from the "rules not tutorials" guidance and why, if there is one.

## Reporting issues

Open an issue with the command you ran, its output, and what you expected instead. For a routing problem, include the `scripts/spec.py select` output — it's usually faster to diagnose than a description of the symptom.

## License

By contributing, you agree your contribution is licensed under the [MIT License](LICENSE) that covers this repository.
