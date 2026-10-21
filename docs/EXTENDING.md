# Extending the framework

The two things you will most often add: a playbook pack for a technology the framework does not ship, and a rule to an existing pack.

## Add a playbook pack

A playbook pack is any body of guidance that applies to *some* projects: a language (Java, Go, Rust), a platform (iOS, Terraform, Kafka), a provider (Stripe, Snowflake), or a compliance regime (PCI-DSS, HIPAA, EU AI Act). The mechanism is the same for all of them.

```sh
python3 scripts/spec.py scaffold java-backend
```

That creates `.spec/10_playbooks/java-backend/PACK.md` and a `references/` folder, and prints the routing row to add.

Then:

1. **Write `PACK.md`.** Aim for 60–150 lines of enforceable rules. Anything longer belongs in `references/`.
2. **Register it** in `.spec/INDEX.md` with the narrowest correct surfaces, and a `Requires` list naming the global policies it specialises.
3. **Activate it** in `.spec/project.json` `playbooks`.
4. **Add routing cases** to `.spec/validation/ROUTING_CASES.json` asserting it loads for its own surfaces and stays out of others.
5. **Validate.** `python3 scripts/spec.py validate`.

### What makes a pack worth loading

Write **rules, not tutorials**. Every line should be something a reviewer could cite in a rejection.

- Each rule gets a stable id (`JAV-07`) so handoffs and review reports can reference it. Ids are permanent; renumbering breaks every citation in the workspace history.
- Prefer MUST and MUST NOT. A pack of "considers" and "prefers" changes nothing.
- Specialise, do not duplicate. If `SECURITY.md` already says parameterise queries, the Java pack says *how that is done here* and cites `SEC-10` — it does not restate the principle.
- State the exception where one genuinely exists, and what evidence justifies it. A rule with no stated exception gets ignored the first time reality does not fit.
- Numbers in a pack are **defaults**. Say so — the architecture governs where it speaks.
- Push depth into `references/`, each with a one-line "load when" condition. The pack is paid for on every matching task; a reference is paid for only when someone needs it.

### Surfaces

Give a pack only the surfaces its rules actually constrain. A Java backend pack is `backend,api,data` — not `implementation`, which would load it on every frontend task too. Getting this wrong is the main way a selective framework becomes an expensive one.

If you need a surface that does not exist, add it to `SURFACES` in `scripts/spec.py` and to the list in `.spec/INDEX.md`. Do this rarely: twenty-one surfaces already cover most systems, and each new one makes classification harder for every agent.

## Add a rule to an existing pack

Edit the pack, give the rule the next id in its sequence, and log the change in `.spec/30_delivery/PROMOTION_LOG.md`. This is a canonical change: propose, promote, log.

If the rule only applies to your project rather than to the technology in general, it probably belongs in your architecture as an ADR instead — that is what makes it project-specific, traceable, and able to outrank the generic default.

## Add a global policy document

Rare, and worth resisting. `00_global/` is for policy that outlives any single system and applies regardless of technology. Before adding one, check whether the content is really:

- a playbook rule (technology-specific) → `10_playbooks/`
- a project decision (this system only) → an ADR in the architecture
- a task requirement (this change only) → acceptance criteria in the backlog

If it genuinely is global policy, add the file, register it, give its rules an id prefix, and add routing cases. `validate` will fail until it is registered — that check exists precisely so a policy nobody routes to cannot be added quietly.

## Add an agent role

Drop a definition in `.agents/roles/` with YAML `name` and `description` frontmatter. Keep it to what the role **owns**, what it **must not** do, and which surfaces it selects. Do not restate policy in a role definition — the role routes to the policy, which is the whole point of the index. Roles are hints for dispatch; they never exclude a requirement. Run `python3 scripts/sync_skills.py` to generate `.claude/agents/` and `.codex/agents/` adapters; do not edit those generated files directly.

## Add a skill

Put it in `.agents/skills/<name>/SKILL.md` — the canonical tree — then run `python3 scripts/sync_skills.py`. Never edit `.claude/skills` directly; it is generated, and `--check` will fail on drift.
