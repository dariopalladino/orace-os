## Step 3 — Select playbooks

Use `technology-profile.md` as the primary source and the module/deployment views plus accepted ADRs as cross-checks. For every `Mandated`, `Accepted`, or `Retain` technology row, propose the applicable registered playbook under `.spec/10_playbooks/`. A `Migrate` row may require both current and target playbooks while both code paths are in scope. `Proposed`, `Retire`, and `TBD` rows do not activate a playbook unless implementation work currently depends on them.

Match on recorded evidence—a named language, framework, provider, manifest, or platform configuration—not on a guess from the domain. Report these mismatches before proposing configuration:

- a technology unit with no corresponding module or repository root;
- a module/deployment technology that is absent from the profile;
- an accepted/retained choice whose source-of-truth path is missing;
- a profile row that names a missing playbook;
- a view or accepted ADR that contradicts the profile's lifecycle status or target choice.

Show the proposal with the evidence for each, ask for confirmation, then write the confirmed list to `.spec/project.json` `playbooks`.

If the profile names a technology with no registered playbook (Java, Go, Terraform, a compliance regime), say so and offer:

```sh
python3 scripts/spec.py scaffold java-backend
```

which creates the pack skeleton and prints the routing row to add. Never stretch an existing pack to cover a technology it was not written for — a Python pack applied to a Java service produces confidently wrong rules.

Also propose `module_roots` from the module view, so that a file path routes to the right surfaces. Planned directories are fine; they do not need to exist yet, but must be identified as planned.

Propose `.spec/project.json` `checks` from the Technology Profile's Delivery Toolchain. Use only exact commands backed by a manifest/configuration path or explicitly supplied by the architect. Do not invent a conventional command from a framework name. Show the current and proposed playbooks, module roots, and checks as a diff; ask for confirmation; preserve unrelated manual checks unless the architect explicitly removes them.
