---
name: orace-workshop
description: "Guides an architect through the ORACE framework interview to generate architecture artifacts (outcomes, quality-attribute scenarios, approaches, technology profile, ADRs, views, risk register, evidence plan, evolution backlog) suitable as input for AI coding agents. Use when the user wants to document or refresh the architecture of a new or existing system using the ORACE method."
trigger: /orace-workshop
---

# /orace-workshop

Conduct a structured ORACE architecture interview with the architect and generate a complete set of machine-readable artifacts in a local folder. The artifacts are designed to be fed directly to AI coding agents as architecture context.

## Usage

```
/orace-workshop                        # run in ./architecture/ (creates folder if absent)
/orace-workshop <path>                 # run in a specific folder
/orace-workshop <path> --reset         # ignore existing files and start from scratch
/orace-workshop <path> --rerun A       # rerun one completed phase (O, R, A, C, or E)
/orace-workshop <path> --rerun technology  # refresh only the technology baseline and its impacts
```

`--rerun` is the safe path for an existing architecture. It preserves every phase not named, reports the downstream artifacts and backlog tasks that may be invalidated, and asks before overwriting each affected file. `--reset` remains the destructive full restart and requires confirmation.

### Token accounting

Before the resume scan, capture host-reported cumulative usage or the workshop start turn if the host exposes usage; otherwise record that usage is unavailable. Keep the boundary in session state, outside architecture artifacts. Read `references/usage.md` now for accounting rules, then `references/completion.md` only at completion. Never guess consumed tokens.

## What You Must Do When Invoked

### Resolve the output path

If a path argument was given, use it. Otherwise:

- If `.spec/project.json` exists, read its `architecture_root` (default `.spec/15_architecture`) and use that. This keeps the ORACE tree inside the governed specification store so the SDDF routing index can register it.
- Otherwise default to `./architecture/` relative to the current working directory.

Keep the whole ORACE tree in one folder. Splitting outcomes and decisions into different roots is conceptually tidier and breaks `/orace-adr`, which derives the next sequence number from `decisions/` in the same folder it reads `quality-scenarios.md` from.

Create the folder and its subfolders if they do not exist:

```
<path>/
  views/
  decisions/
  risks/
  evidence/
  evolution/
```

### Check resume state (unless --reset was given)

Before asking anything, scan the output folder for existing files and report the status:

```
ORACE Workshop — resume check
──────────────────────────────
[O] Outcomes      → outcomes.md              ✓ done  /  ✗ missing
[R] Requirements  → quality-scenarios.md     ✓ done  /  ✗ missing
[A] Approaches    → approaches.md + technology-profile.md + decisions/ (N files)  ✓ done  /  ✗ missing
[C] Communication → views/ (context/module/runtime/deployment)  ✓ done  /  ✗ missing
[E] Evidence      → evidence/evidence-plan.md  ✓ done  /  ✗ missing
──────────────────────────────
Resuming from Phase X.
```

A phase is **done** when its primary output file exists and is non-empty.
- O is done when `outcomes.md` exists
- R is done when `quality-scenarios.md` exists
- A is done when `approaches.md` and `technology-profile.md` exist and are non-empty. The decision count is reported but zero ADRs is valid when no costly-to-reverse decision was identified.
- C is done when `views/context.md`, `views/module.md`, `views/runtime.md`, and `views/deployment.md` all exist
- E is done when `evidence/evidence-plan.md` exists

Skip completed phases entirely unless explicitly named by `--rerun`. An architecture produced by an older workshop will therefore resume at A when `approaches.md` or `technology-profile.md` is absent, without forcing Outcomes or Requirements to be repeated.

### Targeted reruns

Before a rerun, list the files that phase owns, whether each exists, the registered routing rows that point to them, and the open or completed backlog tasks that cite those rows. Explain that changed architecture may reopen those tasks. Do not write until the architect confirms the rerun scope.

- `--rerun O`, `R`, `A`, `C`, or `E`: rerun only that phase. Do not automatically rerun later phases; report which later artifacts may now be stale and offer them one at a time.
- `--rerun technology`: run Phase A's Technology Baseline step, reassess only new or changed technology choices for ADRs, then perform the Communication cross-check described below. Preserve `approaches.md`, existing ADRs, views, and evidence unless the architect separately approves their update.
- If all phases are done and no `--rerun` target was supplied, report completion and offer `--rerun technology`, another specific phase, or `/orace-adr` for one new decision.

## Load one phase at a time

Read only the reference for the active phase, in order: `references/phase-o.md`, `phase-r.md`, `phase-a.md`, `phase-c.md`, `phase-e.md`. Read `references/behaviour.md` before the first interview question and retain its rules. Read `references/completion.md` only when finishing the invocation. For `--rerun technology`, load Phase A and Phase C only. Never preload later phase templates.

At each phase boundary, write the phase artifact, record the next phase and unresolved questions in a short checkpoint, then use the host's compaction command if context is long. After compaction, re-read this controller, the behavior rules, the next phase reference, and only the relevant persisted artifacts. A compacted summary is not a substitute for source text.
