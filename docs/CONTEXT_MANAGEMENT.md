# Context and model use

Keep one conversation for one coherent task. Start a fresh conversation after a task is closed or when switching to an unrelated request. Within a long task, compact only after a stable checkpoint: write the current plan, changed paths, decisions, blockers, and exact check results to the task workspace first. A summary saves orientation; it does not replace selected specifications or source files. Re-read the selected documents needed for the next step after compaction.

| Host | Mid-task when context is long | New task | Model for the main session |
|---|---|---|---|
| Claude Code | `/compact` | `/clear` | `/model` or start with `claude --model <id>` |
| Codex CLI | `/compact` | `/clear` | `/model` or start with `codex --model <id>` |
| Codex IDE/app | Use the host's compact control where offered | Start a new chat | Model picker |
| Copilot CLI | `/compact` | `/new` or `/clear` | `/model` or start with `copilot --model <id>` |
| Copilot Chat in an IDE | Use its context/compact control if available | Start a new chat | Model picker |

These are host controls, not commands that `orace.py` can run inside an existing conversation. Availability can vary by client version. Use the host's current UI when a command is absent.

## What to carry across a compact

Keep a short checkpoint with the task id, selected routing ids and file paths, the active phase or work package, decisions already made, changed files, exact checks and outcomes, unresolved questions, and the next action. Do not paste full specifications, transcripts, or large tool output into the checkpoint. Persist handoffs and evidence in the task workspace, then re-open only the relevant files. For workshop interviews, each completed phase is an artifact checkpoint; load the next phase reference only after that point.

For subagents, dispatch routing ids, acceptance criteria, and disjoint file ownership. They load selected documents themselves and return a concise handoff. Do not create subagents merely to save the main agent's context; they consume their own tokens.

## Model configuration

`.spec/project.json` stores `models` for `claude`, `codex`, and `copilot`. Each has `workshop`, `supervisor`, and `subagents`; all default to `auto`, which means the active harness chooses its configured model. Model ids are host-specific. During installation, pass `--harness` when supplying explicit ids:

```sh
python3 scripts/orace.py init --target /path/to/project --harness codex \
  --workshop-model <codex-model-id> \
  --supervisor-model <codex-model-id> \
  --subagent-model <codex-model-id>
```

Run `python3 scripts/orace.py launch --harness codex --role workshop` or `--role supervisor` from the installed project to start a CLI session with the selected main-agent model. `auto` starts the CLI without `--model`. The launcher works with Claude Code, Codex, and Copilot CLIs installed on `PATH`; in IDEs/apps, select the corresponding model in the host picker before starting that role. A repository cannot change the model of an already running main session. The workshop may span many turns, so its model must be selected for the main session rather than relying on a one-turn skill override.

Run `python3 scripts/sync_skills.py` after editing model choices. It renders explicit subagent and supervisor models into `.claude/agents/`, `.codex/agents/`, and `.github/agents/`. `auto` leaves the model field absent so each host inherits its default. The supervisor role file affects a spawned supervisor; a main-agent supervisor uses the CLI launcher or host picker. A model id must be available to the configured account and supported by the chosen host.

Host references: [Claude Code commands](https://code.claude.com/docs/en/commands), [Claude Code agents](https://code.claude.com/docs/en/sub-agents), [Codex developer commands](https://learn.chatgpt.com/docs/developer-commands), [Codex agents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Copilot context management](https://docs.github.com/en/copilot/concepts/prompting-and-context/context-management), and [Copilot custom agents](https://docs.github.com/en/copilot/reference/custom-agents-configuration).
