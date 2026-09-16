# Specification store

| Folder | Holds | Changed by |
|---|---|---|
| `00_global/` | Reusable engineering and governance policy that outlives any one system | promotion |
| `10_playbooks/` | Technology and domain playbook packs, activated per project | promotion |
| `15_architecture/` | This system's ORACE architecture: outcomes, scenarios, ADRs, views, risks, evidence | promotion (`/orace-workshop`, `/orace-adr`) |
| `20_backlog/TASKS.md` | The only task list | supervisor |
| `30_delivery/PROMOTION_LOG.md` | Evidence for every canonical change | supervisor |
| `40_workspace/<task-id>/` | Task context, proposals, handoffs, reviews | the owning agent |
| `50_archive/` | Superseded material kept for the record | supervisor |
| `INDEX.md` | The routing registry — the only way agents find any of the above | promotion |
| `project.json` | Active playbooks, module roots, orchestration, context budget, checks | promotion |

Nothing here is loaded wholesale. Agents select through `INDEX.md`.
