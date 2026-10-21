# Specification routing index

The single routing registry. Every agent selects documents through this table and is forbidden from reading the specification store wholesale. **An artifact with no row here is invisible.**

Paths are repository-relative. `*` in Surfaces means baseline (always selected). `*` in Playbooks means any project. Commas mean union; `-` means no dependencies.

`project.json` `module_roots` are directory prefixes ending in `/`. A `*` segment matches exactly one directory; `**` matches zero or more directories. For example, `services/*/migrations/` matches `services/payments/migrations/001.py` but not a deeper `services/payments/src/migrations/001.py`. Candidate source paths may use `/` or `\`; configured roots use `/`. A path outside all roots requires explicit semantic classification.

## How to select

1. Read `.spec/project.json` for active playbooks and module roots.
2. Classify the task's semantic surfaces — what the change *means*, not which folder it lives in. A token-storage change in a React component is `frontend`, `auth`, and `security`.
3. Select every row whose Surfaces intersect the task's, plus every baseline row, plus any explicitly referenced id, then close over `Requires`.
4. Drop rows whose Playbooks do not include an active playbook. An explicit reference to an inactive playbook's row is a decision to make, not a row to silently omit.

Deterministic equivalent:

```sh
python3 scripts/spec.py select --surface backend --surface auth --path src/app/login.py
python3 scripts/spec.py select --task PAY-014
```

## Registry

| ID | Path | Surfaces | Requires | Playbooks |
| --- | --- | --- | --- | --- |
| protocol | .spec/00_global/AGENT_EXECUTION_PROTOCOL.md | * | - | * |
| principles | .spec/00_global/PRINCIPLES.md | * | - | * |
| governance | .spec/00_global/GOVERNANCE.md | governance,architecture,api,data,auth,security,infra,release,review | protocol | * |
| done | .spec/00_global/DEFINITION_OF_DONE.md | review,release | principles | * |
| clean-architecture | .spec/00_global/CLEAN_ARCHITECTURE.md | architecture,backend,frontend,native,domain | principles | * |
| ddd | .spec/00_global/DDD.md | domain,data,architecture | principles | * |
| api-design | .spec/00_global/API_DESIGN.md | api | security | * |
| data-modelling | .spec/00_global/DATA_MODELLING.md | data | ddd,security,governance | * |
| security | .spec/00_global/SECURITY.md | security,auth,backend,api,data,infra,native | principles | * |
| ai-governance | .spec/00_global/AI_GOVERNANCE.md | ai,governance,review,implementation | protocol,principles | * |
| hitl | .spec/00_global/HUMAN_IN_THE_LOOP.md | hitl,ai,governance | ai-governance | * |
| ui | .spec/00_global/UI_CONVENTIONS.md | frontend,native | principles | * |
| testing | .spec/00_global/TESTING.md | testing,review,implementation | principles | * |
| observability | .spec/00_global/OBSERVABILITY.md | observability,backend,infra,release | principles | * |
| nonfunctional | .spec/00_global/NONFUNCTIONAL.md | planning,api,backend,frontend,native,infra | principles | * |
| play-python | .spec/10_playbooks/python-backend/PACK.md | backend,api,data | clean-architecture,security | python-backend |
| play-react | .spec/10_playbooks/react-frontend/PACK.md | frontend | ui,api-design | react-frontend |
| play-kotlin | .spec/10_playbooks/kotlin-native/PACK.md | native | clean-architecture,ui,security | kotlin-native |
| play-auth0 | .spec/10_playbooks/auth0-identity/PACK.md | auth | security,api-design | auth0-identity |

Architecture rows produced by ORACE are added by `/spec-bootstrap` and `/orace-adr`, one row per artifact and one row per ADR. They are registered below this line.

<!-- architecture rows start -->
<!-- architecture rows end -->

## Surfaces

`docs`, `planning`, `architecture`, `domain`, `backend`, `frontend`, `native`, `api`, `data`, `auth`, `security`, `infra`, `release`, `governance`, `ai`, `hitl`, `implementation`, `review`, `testing`, `observability`, `example`.

Any task that writes code declares `implementation`. Module roots in `project.json` add it automatically for paths under a source tree, but a task planning work in a directory that does not exist yet should declare it explicitly.

`docs` selects only the baseline — unless the documentation concerns a contract or a sensitive behaviour, in which case select that subject too.

## Rules for this file

- One row per document. Never register a folder: at fifteen ADRs a folder row drags every decision into every task, which converts selective loading back into read-everything.
- Give each row the narrowest surfaces that are still correct. A row that is too wide costs context on every unrelated task; a row that is too narrow ships a violation.
- Role is a hint and never an exclusion. Path matching cannot infer every security implication — add `security` and `auth` deliberately.
- Reference bodies hold the requirements. Selection order does not change authority; precedence is defined in `PRINCIPLES.md`.
- This index is a routing catalog, not a context cache. Re-select after scope, path, playbook, or architecture changes.
