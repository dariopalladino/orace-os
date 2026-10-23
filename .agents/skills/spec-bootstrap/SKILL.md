---
name: spec-bootstrap
description: Wire a completed ORACE architecture into the SDDF specification store — register routing rows, select playbooks, derive the initial backlog from quality scenarios and ADRs, and validate. Use after /orace-workshop, or when adopting SDDF into a repository that already has architecture artifacts.
trigger: /spec-bootstrap
---

# Spec bootstrap — ORACE to SDDF

The handoff. ORACE produced normative content; SDDF enforces it. Nothing in between happens automatically: an unregistered architecture artifact is invisible, because every agent routes through `.spec/INDEX.md` and is forbidden from reading the store wholesale.

Run this once after the architecture exists, and again whenever the architecture grows a new artifact that has no routing row.

```
/spec-bootstrap                 # use architecture_root from .spec/project.json
/spec-bootstrap <path>          # an architecture folder elsewhere (e.g. ./architecture)
```

## Step 1 — Read what exists

Resolve the architecture root: the argument, else `.spec/project.json` `architecture_root`, else `.spec/15_architecture`, else `./architecture`.

List the tree and read `outcomes.md`, `quality-scenarios.md`, `approaches.md`, `technology-profile.md`, `views/module.md`, `views/deployment.md`, and each ADR title and status. Do not read every file in full—you need the artifact inventory, scenario ids and `Artifact` fields, approach mappings, technology rows and evidence, module names, and ADR subjects.

Report what you found and what is missing. If `quality-scenarios.md` is absent, stop: there is nothing to derive a backlog from. Send the user back to `/orace-workshop`.

If `technology-profile.md` is absent, do not infer a complete stack from scattered prose. Send the user to `/orace-workshop <path> --rerun technology`; an older architecture can add the profile without resetting Outcomes, Requirements, existing ADRs, or Evidence. If `approaches.md` is absent, offer `/orace-workshop <path> --rerun A` and explain that tactic traceability is incomplete.

When bootstrap has run before, inventory existing routing rows, active playbooks, module roots, checks, and backlog references before proposing changes. Update matching rows in place; never add duplicate ids or discard manually configured checks without explicit approval.

## Step 2 — Check scenario ids and measures

Every scenario needs a stable id of the form `QA-<ATTR>-<NN>` and a `Measure` containing a number.

- A scenario with no id: propose one, show the list, and write the ids into `quality-scenarios.md` after the user confirms. Ids become acceptance criteria and test names; renaming them later breaks traceability.
- A `Measure` with no number ("fast", "reliable", "as quickly as possible"): list these and tell the user plainly that they cannot become acceptance criteria. Offer to run the Phase R questions for just those scenarios. Do **not** invent a number.

## Rules

- Propose, then write. The user approves ids, playbooks, surfaces, and the backlog before anything canonical changes.
- Never invent a `Measure`, a threshold, a scenario, or an ADR. Missing content goes back to the architecture interview.
- Never invent a technology, version, lifecycle status, repository root, source-of-truth path, playbook mapping, or validation command. Missing content goes back to `/orace-workshop --rerun technology` or becomes an explicitly owned backlog item.
- Never register a folder as one row.
- Never copy ORACE content into `.spec/00_global/`. The global folder holds policy that outlives any single system; duplicating a scenario there creates two sources of truth with different change-control paths.
- An ADR added later is not finished until its row exists and `validate` passes.

## Progressive loading

After the inventory and measure checks, load only the next step reference: `references/technology.md`, `routing.md`, `backlog.md`, `precedence.md`, then `validation.md`. Do not preload all routing defaults or backlog templates. Persist confirmed changes and a brief checkpoint before compacting a long session; after compaction, re-read this controller and the reference for the active step plus the relevant persisted architecture artifacts.
