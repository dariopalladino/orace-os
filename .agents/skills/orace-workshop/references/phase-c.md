## Phase C — Communication (Four Views)

**Goal**: capture the three architectural views so that different stakeholders can read what is relevant to them. Output: `views/context.md`, `views/module.md`, `views/runtime.md`, `views/deployment.md`.

### Context View

Ask: "Let's start with the Context View — the system in its environment.

Tell me:
- What is the system's boundary — what is inside vs outside?
- What external actors or systems interact with it?
- What data flows in and out?

You can describe it in prose — I will structure it."

Write `views/context.md`.

### Module View

Ask: "Now the Module View — who is responsible for what.

List the major components or services in this system. For each, tell me:
- Its name
- Its single responsibility (one sentence)
- Which team or person owns it
- Its planned or existing repository root
- Its main dependencies (what it calls or consumes)
- Its persistence boundary and relationship to neighbouring modules, when applicable"

Use the exact unit names from `technology-profile.md`. For each module, reference its technology-profile rows rather than copying the stack into the view. If the module list and profile disagree, stop and ask which name or boundary is authoritative before writing either file.

Write `views/module.md`.

### Runtime View

Ask: "Now the Runtime View — how components communicate at runtime.

Describe 1–3 of the most important flows in the system. For each flow:
- Give it a name
- List the steps in order: [component] → [action] → [component]
- Note which calls are synchronous and which are asynchronous
- Note any timeouts, retries, or failure behaviours"

Cross-check each protocol and format against `technology-profile.md` Integration Technology. The runtime view owns interaction order and failure behaviour; the profile owns the selected protocol technology and compatibility policy.

Write `views/runtime.md`.

### Deployment View

Ask: "Finally, the Deployment View — where things run and what the trust boundaries are.

Tell me:
1. Where does each component run? (cloud provider, region, container, on-premise, edge)
2. What are the trust zones? (public internet, DMZ, internal network, restricted zone)
3. Which components cross a trust boundary when they communicate?
4. Where does sensitive data live, and where is it NOT allowed to go?
5. If there is an AI component: what can it read, what can it propose, and what can it never execute directly?"

Reference the hosting, orchestration, identity, data, and observability entries from `technology-profile.md`; do not create a second technology inventory in the deployment view. Write `views/deployment.md`.

### Communication cross-check

After all views are drafted—or immediately after `--rerun technology` updates the profile—compare unit names, repository roots, integration protocols, hosting locations, managed services, and trust-boundary providers across `technology-profile.md` and the three views. Report mismatches individually. During a technology-only rerun, do not silently edit a view: offer `--rerun C`, explain which routing rows and tasks may be affected, and wait for approval.

Use the following templates for each view:

```markdown
---
orace_phase: C
view: [context | module | runtime | deployment]
generated_by: orace-workshop
generated_at: YYYY-MM-DD
---

# [View Name] — [System Name]

> [One-line description of what this view answers]

[Content per view]
```

After all views are written, tell the architect: "Phase C complete — views written. Moving to Phase E."
