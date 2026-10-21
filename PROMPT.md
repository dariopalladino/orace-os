# Example prompts

These prompts work across hosts. In Codex, prefix a skill name with `$` to invoke it explicitly (for example, `$orace-workshop`); in Claude Code, use its `/` command.

## Start a new system

> Use the orace-workshop skill with `.spec/15_architecture`. I want the architecture documented before we write any code.

Then:

> Use the spec-bootstrap skill. Register the architecture in the routing index, propose playbooks and exact validation checks from the technology profile, cross-check the module and deployment views, and derive the initial backlog from scenarios, ADRs, and unresolved technology work. Show me the proposal before writing anything canonical.

## Adopt SDDF into an existing repository

> Read `docs/ADOPTION.md` and integrate SDDF into this repository on a branch. Merge with the existing `AGENTS.md` and `CLAUDE.md` rather than overwriting them. Run the ORACE workshop so detected technologies are treated as evidence for me to classify, then have bootstrap propose `.spec/project.json`; stop before changing project configuration or deriving a backlog so I can review.

## Refresh technology choices in an existing architecture

> Use the orace-workshop skill with `.spec/15_architecture --rerun technology`. Preserve the other phases and accepted ADRs, confirm observed technologies with me, and report affected views, routing rows, and tasks before proposing any downstream update.

## Implement a task

> Use the spec-workflow skill to implement PAY-014 from `.spec/20_backlog/TASKS.md`. Route with `scripts/spec.py select --task PAY-014`, record the task context, propose, and execute after I approve. Verify against the acceptance criteria and write a handoff.

## Run a work package with sub-agents

> Use supervisor orchestration for work package WP-AUTH. Dispatch one sub-agent per task with routing ids only, keep file ownership disjoint, and bring back handoffs. Do not implement anything yourself.

## Proposal only

> Use the spec-workflow skill to assess <request>. Produce a scoped proposal with a migration plan. This pass is proposal-only: write workspace artifacts, do not change source files or canonical specifications.

## Review before close

> Use the spec-review skill for PAY-014. Judge whether every acceptance criterion is actually evidenced and whether the handoff documents need correction. Give me a verdict and the required actions.

## Resume after a break

> Resume PAY-014 from `.spec/40_workspace/PAY-014/TASK_CONTEXT.md` and the existing handoffs. Recheck scope and re-read the selected specifications; their text is no longer in your context.

## Add a playbook for another technology

> We are adding a Java service. Run `python3 scripts/spec.py scaffold java-backend`, write the pack from our actual conventions, register its routing row, add it to `project.json`, and validate.
