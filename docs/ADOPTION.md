# Adoption

How to put SDDF into a repository. Start with discovery and one task; complete the full architecture model when the system needs it.

## New system

```
1. python3 scripts/orace.py init --target /path/to/repo
2. review .spec/40_workspace/PROJECT_DISCOVERY.json and .spec/project.json
3. python3 scripts/spec.py validate
4. python3 scripts/orace.py task "Fix a narrow bug" --path <affected-path> --surface <confirmed-surface>
5. implement under the recommended Lite, Standard, or Governed mode
```

Baseline policies and registered playbooks support early tasks. The discovery report distinguishes observed files, proposed playbooks, and unknown architecture; review its suggestions before activating them. Run `/orace-workshop` and `/spec-bootstrap` when architectural decisions or measurable quality objectives need to be captured. Unknown measures stay unresolved rather than invented.

The `/` skill examples in this guide use Claude Code syntax. In Codex, use `$orace-workshop`, `$spec-bootstrap`, and the other skill names with `$`; see [Codex setup](CODEX.md).

The completion response includes token usage for that workshop invocation when the host exposes session or turn accounting. It labels the source and accuracy; if usage is unavailable it says so rather than substituting a character estimate. The currently generated final summary is normally outside the count, and the report calls out that boundary. Token usage is operational metadata and is not written into the architecture tree.

## Existing repository

Work on a branch. Nothing here needs to change your source layout.

**1. Copy the framework in.**

```sh
python3 scripts/orace.py init --target /path/to/your/repo
```

It copies a clean specification template and the managed runtime files needed by the CLI and host adapters. It does not copy the framework's internal tests, completed backlog entries, promotion history, or task workspaces. Existing `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` are preserved above an appended SDDF section. Existing project files are not overwritten; a later version is applied with `orace.py upgrade`. The discovery proposal is written under `.spec/40_workspace/` and does not approve architecture.

To choose models at installation, add `--harness claude|codex|copilot` and the three optional `--workshop-model`, `--supervisor-model`, and `--subagent-model` flags. All default to `auto`, which inherits the host model. See [Context and model use](CONTEXT_MANAGEMENT.md) for launch and session controls.

**2. Inspect and confirm what is already present.**

Read `PROJECT_DISCOVERY.json`, confirm the actual stack and paths, and update `.spec/project.json` and `.spec/validation/ROUTING_CASES.json`. When an accepted architectural decision or production measure matters to the work, run `/orace-workshop .spec/15_architecture`. For an existing system this captures the architecture already in use; unresolved measures remain explicit until they can be measured.

The workshop inspects manifests, lockfiles, runtime files, containers, infrastructure, CI, and observability configuration as candidate evidence. It does not equate detection with intent: you confirm whether each observed technology should be retained, migrated, retired, or left TBD. The resulting `technology-profile.md` references the files that own exact versions instead of copying their contents.

If you already have architecture documents elsewhere in the repository, leave them where they are and register those paths in `.spec/INDEX.md` instead. The index takes any repository-relative path. Placement matters far less than registration.

If this repository already has ORACE artifacts from an older framework version, rerun the workshop at the same path. Resume detection skips complete Outcomes and Requirements and fills missing Phase A artifacts. For future stack changes, use:

```sh
/orace-workshop .spec/15_architecture --rerun technology
```

That refreshes the technology baseline and reports affected views, routing rows, and backlog tasks without silently rewriting them.

**3. Validate the confirmed configuration.**

```sh
python3 scripts/spec.py validate
```

When a full ORACE profile exists, `/spec-bootstrap` proposes rather than guesses:

- `playbooks` from accepted/retained technology-profile rows;
- `module_roots` from confirmed module names and repository roots;
- `checks` only when the profile records exact commands and their configuration source;
- backlog work for unresolved technology decisions, migrations, retirements, evidence collection, or missing playbooks.

Review the proposed `.spec/project.json` diff. Keep only playbooks you actually use, ensure every source root maps to the correct surfaces (including `implementation`), preserve intentional manual checks, and choose `supervisor` or `sequential` orchestration for your team.

**4. Calibrate the routing before you trust it.**

```sh
python3 scripts/spec.py select --surface frontend --surface auth --path web/src/login.tsx
```

Read the output. Did the deployment view arrive for an auth change? Did an unrelated playbook stay out? Did the estimate land inside your budget? Fix surfaces now, not after ten tasks have been routed wrongly. Add the cases you care about to `.spec/validation/ROUTING_CASES.json` so a future edit cannot break them silently.

**5. Start small.**

Use `python3 scripts/orace.py task "<request>" --path <path>` and confirm its inferred surfaces. A narrow repair can finish with a compact result; a feature uses a concise plan and review; a sensitive or architecture-significant change follows the full Governed lifecycle with independent review. `python3 scripts/orace.py verify --check <group> --task <id> --output .spec/40_workspace/<id>/evidence.json` records actual check invocations, exit codes, output tails, timestamps, commit SHA, and changed-file fingerprint. Later checks reject evidence after relevant worktree changes. The record proves command execution only; acceptance and production measures need their own observations.

For a change in a pull request, `python3 scripts/orace.py check --diff origin/main...HEAD` reports selected policies, possible ADR impact, unmapped paths, and missing or contradicted check records. The installed `.github/workflows/orace-check.yml` writes this as an informational summary. After CI installs the project's dependencies, use `--run-checks --strict` to execute configured commands in the check job; supplied JSON evidence alone is not a strict gate. Configure host branch rules for human review. Accepted ADRs can declare `owner`, `affected_paths`, `scenarios_addressed`, and `supersedes`; `orace.py impact` reports possible drift without rewriting them.

For an external coding method, export a task plan with `--executor external --external-name <method> --output <plan.json>`. `orace.py review` preflights its JSON handoff against captured evidence. If that method has an executable, `orace.py run --plan <plan.json> --command '<executor command>' --evidence <new-evidence.json>` can invoke it, enforce changed-file scope, and run configured checks. Governed plans require a plan-bound approval record. The contract and limits are in [`EXECUTION_ADAPTERS.md`](EXECUTION_ADAPTERS.md).

For later framework versions, run the newer checkout's `python3 scripts/orace.py upgrade --target /path/to/repo` to preview file changes, then repeat with `--apply`. Managed files edited by the project are preserved as conflicts. Run `doctor` and `spec.py validate` after an upgrade.

## Adapting the packs to your conventions

The packs in `.spec/00_global/` and `.spec/10_playbooks/` are opinionated on purpose — vague policy produces vague compliance. Where a rule contradicts a convention your team has already settled, **change the rule** rather than tolerating a spec nobody follows. Edit it, log the change in `.spec/30_delivery/PROMOTION_LOG.md`, and keep the rule id so handoffs stay citable.

Deleting a rule you do not want is better than keeping one you will not enforce.

## Rollback

Everything SDDF adds lives in `.spec/`, `.agents/`, `.claude/`, `.codex/`, `scripts/`, `benchmarks/`, the optional PR workflow, and appended sections of the three instruction files. The installation manifest lists managed files. Review it before removing files in a repository that had pre-existing content in those paths.

## Host support

| Host | Discovery | Fallback |
|---|---|---|
| Claude Code | `.claude/skills` (synced from `.agents/skills`), `.claude/agents`, `.claude/commands` | read `SKILL.md` directly |
| Codex | `AGENTS.md`, `.agents/skills`, `.codex/agents` | read `SKILL.md` directly |
| GitHub Copilot | `.github/copilot-instructions.md`, `.github/agents/` | read `SKILL.md` directly |
| Anything else | point it at `AGENTS.md` | — |

Run `python3 scripts/sync_skills.py` after adding a skill or role, and `--check` in CI. See the [Codex guide](CODEX.md) for Codex setup and smoke checks. Verify discovery in each host you actually use rather than assuming it; a direct instruction to read the skill file always works.
