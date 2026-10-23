## Step 4 — Register routing rows

Add one row per artifact to the `.spec/INDEX.md` table. Columns: `ID | Path | Surfaces | Requires | Playbooks`.

Defaults, to be adjusted against what the artifacts actually say:

| Artifact | Surfaces | Requires |
|---|---|---|
| `outcomes.md` | `planning,architecture,governance` | `principles` |
| `quality-scenarios.md` | the union of surfaces its `Artifact` fields name, plus `planning,architecture,review` | `outcomes,nonfunctional` |
| `approaches.md` | `planning,architecture` plus the surfaces of the scenario artifacts it addresses | `quality-scenarios` |
| `technology-profile.md` | `architecture,implementation` plus only the component/toolchain surfaces its rows govern | `approaches,quality-scenarios` |
| `views/context.md` | `planning,architecture,docs` | `outcomes` |
| `views/module.md` | `architecture,domain` plus the surfaces of the modules it names | `quality-scenarios,technology-profile` |
| `views/runtime.md` | `architecture,backend,api,infra` adjusted to the flows it contains | `quality-scenarios,technology-profile` |
| `views/deployment.md` | `infra,security,auth,data` adjusted to the deployed system | `security,quality-scenarios,technology-profile` |
| `risks/risk-register.md` | `planning,governance,review` | `outcomes` |
| `evidence/evidence-plan.md` | `review,release,observability` | `quality-scenarios,done` |
| `evolution/backlog.md` | `planning` | `outcomes` |
| `decisions/NNN-*.md` | **only** the surfaces the decision actually constrains | `quality-scenarios` plus the policy it specialises |

Three of these carry most of the value:

- **`quality-scenarios` is deliberately wide.** The scenarios are what the system must prove it can do, and almost any change can violate one. It depends on `nonfunctional` so the generic defaults and the governing numbers always arrive together — and the agent can see which one displaces which.
- **ADR continuity metadata.** For each accepted ADR, confirm `status`, `owner`, `affected_paths`, `scenarios_addressed`, and `supersedes` in its frontmatter. Missing fields stay explicit; do not invent an owner or a path. `orace.py impact` uses these fields to propose affected decisions during later changes.
- **`view-deployment` carries `security` and `auth`.** It holds trust zones, data residency, and the AI capability boundary. That mapping is what makes a frontend task touching token storage pull in the trust-zone document. It prevents a recurring and expensive class of mistake.
- **One row per ADR, never one row for the folder.** A folder row means that at fifteen ADRs every task drags in every decision ever made, which converts selective loading back into read-everything. Give each ADR only the surfaces its decision constrains: an audit-log persistence decision is `data`, not `data,backend`.

`technology-profile.md` is intentionally compact but not automatically universal. Give it the union of the implementation surfaces it actually describes; do not add security, data, infra, frontend, or native merely because those categories could exist. If the profile becomes large enough that every implementation task loads unrelated stacks, split it by stable component boundary and register each resulting artifact separately.

Use the `Playbooks` column to scope a row that only applies to one technology. Architecture artifacts are almost always `*`.
