# Architecture impact and evolution

Accepted ADRs can declare machine-readable lifecycle links in their frontmatter:

```yaml
status: Accepted
owner: Payments team
affected_paths:
  - services/payments/
scenarios_addressed:
  - QA-AVAIL-01
supersedes: none
```

`affected_paths` uses repository-relative directory prefixes ending in `/` or exact file paths. `*` matches one directory segment and `**` matches any depth. Existing ADRs without these fields remain readable; the impact report marks their scope or owner as unknown.

```sh
python3 scripts/orace.py impact --path services/payments/handler.py
python3 scripts/orace.py check --diff origin/main...HEAD
```

`impact` identifies accepted decisions that match changed paths or selected semantic surfaces. It also reports missing scenario links, missing superseded ADRs, unknown owners, and unknown path scope. `check` adds routing, recommended mode, configured check evidence, and possible gaps where an ADR's path scope applies but the routing index did not select it. These are candidates for review, not automatic amendments to accepted architecture.

The repository's `orace-check.yml` workflow writes an informational pull-request summary. `check --run-checks --strict` runs the configured commands during the check and fails on deterministic routing gaps or failed required checks when a team wants a merge gate. Install application dependencies in the CI job before enabling live application checks. Supplied JSON evidence is informational in strict mode. Human approval is enforced by the host's review and branch rules; a file committed by the PR author is not a trusted approval signal.
