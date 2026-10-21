# Codex host guide

SDDF runs in Codex CLI, the IDE extension, and the Codex app through repository instructions, skills, and project role agents. The framework CLI still needs Python 3; no Python package install is required. Install Codex separately using your organization's normal setup if it is not already available.

## What Codex loads

| Repository path | Purpose |
|---|---|
| `AGENTS.md` | Short operating contract loaded at the start of a Codex session |
| `.agents/skills/*/SKILL.md` | Native Codex skills; use `$skill-name` or let the description select one |
| `.codex/agents/orace_*.toml` | Project scoped planner, specialist, security, reviewer, and supervisor roles |
| `.agents/roles/*.md` | Shared source used to generate both Codex and Claude roles |

Codex does not need a second skill copy under `.codex/skills`. `.claude/commands/` are Claude slash commands; in Codex, invoke the matching skill with `$` or select it from `/skills`. Do not use a Claude slash command name as a Codex command.

## Start a task

From the installed repository root, run:

```sh
python3 scripts/spec.py validate
python3 scripts/sync_skills.py --check
python3 scripts/orace.py task "Fix login validation" --path web/src/login.tsx --surface frontend --surface auth
```

Then ask Codex, for example:

> Use `$spec-workflow` to implement this task. Confirm the task plan's surfaces, read every selected specification in full, follow its required mode, and report the exact checks and evidence.

For architecture work, use `$orace-workshop` and then `$spec-bootstrap`. A costly new decision uses `$orace-adr`. The final independent handoff review uses `$spec-review`.

When `.spec/project.json` sets `"orchestration": "supervisor"`, the main Codex agent coordinates the work. Ask it to delegate independent, disjoint work packages to the appropriate `orace_*` role agents, wait for their handoffs, and use `orace_reviewer` for a Governed final review. `orace_security` reviews sensitive changes. Role agents inherit the parent session's permissions and tools; a role file does not grant extra access. When the project sets `"sequential"` or subagents are unavailable, Codex can complete the roles in sequence with the same artifacts. Governed independent review still needs a separate reviewer context.

## Verify host discovery

1. In Codex, ask: “Summarize the repository instructions you loaded.” Check that it mentions `AGENTS.md` and the `.spec/` routing contract.
2. Run `/skills` or type `$spec-workflow` and confirm the repository skill appears.
3. Ask Codex to list available `orace_*` project agents, or run a bounded read-only exploration with `orace_planner` in a test repository. Keep implementation permissions and approval settings on the parent session.
4. Run `python3 scripts/sync_skills.py --check` and `python3 scripts/spec.py validate` after installation or upgrade.

The repository tests validate the generated TOML and installed files. They do not simulate a live Codex session, so the host discovery check above is still useful on your Codex version.

Codex references: [AGENTS.md discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [local skills](https://learn.chatgpt.com/docs/build-skills), and [project scoped agents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
