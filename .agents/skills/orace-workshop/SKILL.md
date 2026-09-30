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

### Token accounting for this invocation

At the start of every workshop invocation—before the resume scan, repository discovery, or first interview question—establish a token-usage boundary:

1. If the host exposes cumulative session usage, capture the current input, cached-input, output, reasoning, and total counters plus the measurement source.
2. Otherwise, if the host exposes usage per completed turn, record the workshop start turn and plan to sum root-agent turns and any subagent turns attributable to this workshop.
3. Otherwise record that measured usage is unavailable. Do not interrupt the interview to ask the architect for telemetry they do not have.

Keep the boundary in session working state. It is operational metadata, not architecture: do not write it to `outcomes.md`, `technology-profile.md`, evidence artifacts, ADRs, or another file under the architecture root.

At completion of a full workshop or a targeted rerun, report usage for **this invocation only** using the hierarchy below:

- **Measured (host-reported, best-effort):** subtract the cumulative start snapshot from the latest completed-turn snapshot, or sum attributed per-turn usage. Include root-agent and workshop-related subagent turns. Reject negative deltas and fall back to `Unavailable` instead of guessing.
- **Estimated (trace-counted):** use only when an actual model-aware token counter was run over an exported workshop trace. Name the counter, content counted, and exclusions. Never present `characters ÷ 4`, a selector context estimate, visible-text length, or intuition as consumed tokens.
- **Unavailable:** use when neither measured usage nor a trace-counted estimate exists. State why; do not print zero or a plausible substitute.

Accounting invariants:

- `total_tokens = input_tokens + output_tokens`.
- Cached input is already included in input tokens; show it as an indented subset and never add it again.
- Reasoning tokens are already included in output tokens; show them as an indented subset and never add them again.
- If the host omits a category, print `not reported` rather than treating it as zero.
- Do not calculate monetary cost unless the architect separately asks and current model-specific pricing and cache treatment are available.
- Host/session usage may be best-effort, may settle later, and is not a final bill.
- A model normally cannot know the tokens used by the final response while generating that response. Unless the host supports post-response usage injection, the scope ends at the last completed turn immediately before the final summary; say so explicitly.

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

---

## Phase O — Outcomes

**Goal**: understand what the system must achieve and which business failures it must prevent. Output: `outcomes.md`.

Ask the following questions **one at a time**, in order. Wait for the answer before asking the next. Do not batch them.

1. **System name and purpose**: "What is the name of the system, and what does it do in one or two sentences?"

2. **Project state**: "Is this a new system, an existing system, or a hybrid where new components will coexist with existing ones?" Record exactly one of `New`, `Existing`, or `Hybrid` and a one-sentence explanation.

3. **Stakeholders**: "Who are the primary stakeholders? List each one and their main concern about the system." *(Prompt if vague: "Think about the people who would be in an architecture review: business owner, tech lead, compliance, security, operations. Who from that list applies here?")*

4. **Business outcomes**: "What are the 2–3 most critical business outcomes this system must deliver? Frame each as: 'The system must enable [who] to [do what] [under what condition]'."

5. **Failure risks**: "Which business failures must this system prevent? For each, describe the impact on the business, the users, or the regulatory position."

6. **Regulatory and contractual constraints**: "Are there regulatory, compliance, or contractual constraints? Examples: GDPR, PCI-DSS, HIPAA, SOC 2, data residency requirements, SLA commitments." *(If none, record 'None identified'.)*

7. **Technology constraints**: "Which technologies are already present or mandated, preferred, or prohibited—and what is the source of each constraint? Include organization standards, team capabilities, licensing, support windows, hosting commitments, and procurement decisions. Do not list a preference as a mandate." *(If none, record `None identified`; the complete technology inventory belongs to Phase A.)*

8. **External dependencies**: "What external systems, APIs, or third-party providers does this system depend on or integrate with? List each and classify it as: critical (failure of this dependency fails the system) or non-critical."

After all answers are collected, write `outcomes.md` using the template below. Do not ask for confirmation before writing.

### outcomes.md template

```markdown
---
orace_phase: O
generated_by: orace-workshop
generated_at: YYYY-MM-DD
---

# Outcomes — [System Name]

## One-Line Description
[One sentence from Q1]

## Project State
[New | Existing | Hybrid] — [one-sentence explanation]

## Stakeholders

| Stakeholder | Primary Concern |
|-------------|----------------|
| [name/role] | [concern]      |

## Business Outcomes

1. [Outcome 1]
2. [Outcome 2]
3. [Outcome 3 if present]

## Business Failures to Prevent

| Failure | Business Impact |
|---------|----------------|
| [failure] | [impact]     |

## Constraints

| Constraint | Type | Source |
|------------|------|--------|
| [name] | Regulatory / Contractual / SLA | [regulation or agreement] |

## Technology Constraints

| Constraint | Classification | Source | Consequence |
|------------|----------------|--------|-------------|
| [technology or constraint] | Existing / Mandated / Preferred / Prohibited | [policy, repository evidence, owner, or agreement] | [what it enables or excludes] |

## External Dependencies

| System / Provider | Classification | Notes |
|-------------------|---------------|-------|
| [name] | critical / non-critical | [notes] |
```

After writing, tell the architect: "Phase O complete — `outcomes.md` written. Moving to Phase R."

---

## Phase R — Requirements (Quality-Attribute Scenarios)

**Goal**: turn the failure risks identified in Phase O into measurable quality-attribute scenarios. Output: `quality-scenarios.md`.

Keep Phase R implementation-neutral. A scenario describes required behaviour and a measurable outcome, not a preferred framework, database, cloud service, or vendor. If the architect answers with a technology, ask what behaviour or constraint that technology is meant to satisfy and record the technology later in Phase A.

### Step R-1: Identify quality attributes

Say: "Based on the failure risks you described, I'll propose which quality attributes likely need scenarios. Tell me which ones resonate and add any I missed."

Map each failure risk from Phase O to one or more quality attributes from this list:

| Quality Attribute | Relevant when... |
|-------------------|-----------------|
| Availability | failure risk involves downtime, outages, or dependency failure |
| Performance | failure risk involves latency, throughput, or user experience under load |
| Modifiability | failure risk involves slow response to change, vendor lock-in, or team coupling |
| Security | failure risk involves unauthorized access, data breach, or injection |
| Auditability | failure risk involves compliance gaps, inability to explain decisions, or missing audit trail |
| Scalability | failure risk involves capacity limits, growth inability, or cost explosion under load |
| Recoverability | failure risk involves data loss, corruption, or inability to restore service |
| Interoperability | failure risk involves integration failures with external systems |

Present the proposed list and ask: "Does this list capture what matters most? What would you add or remove?"

Confirm the final list of 3–6 quality attributes before proceeding.

### Step R-2: Write each scenario

For each confirmed quality attribute, ask the architect to fill in the six-field scenario template. Ask the fields **one at a time**:

1. **Source**: "Who or what generates the trigger? (Example: a user, a batch job, an external system failure, a calendar event)"
2. **Stimulus**: "What specific event or condition triggers the response? Be concrete — not 'high load' but 'a spike to 10,000 concurrent users'."
3. **Environment**: "Under what operating conditions does this happen? Normal load? Peak? Degraded mode? During a deployment?"
4. **Artifact**: "Which part of the system must respond? Name the specific component, service, or layer."
5. **Response**: "What should the system do when this happens? Describe the behavior, not the implementation."
6. **Measure**: "How do you know the response was adequate? Give a number. If you write 'quickly' or 'reliably', I will ask again." *(If the answer has no numbers, probe once: "Can you put a specific number on this — milliseconds, percentage, count, duration?")*

After all six fields are filled for a quality attribute, summarize the completed scenario and ask: "Does this accurately capture the requirement? Any adjustments?"

Repeat for each quality attribute.

### Step R-3: Write quality-scenarios.md

After all scenarios are complete, write `quality-scenarios.md` using the template below.

### quality-scenarios.md template

```markdown
---
orace_phase: R
generated_by: orace-workshop
generated_at: YYYY-MM-DD
system: [System Name]
---

# Quality-Attribute Scenarios — [System Name]

> These scenarios define the architecturally significant requirements for this system.
> Each scenario is testable: if you cannot write a test or metric for the Measure field, the scenario is not finished.

---

## QA-[ATTR]-[NN] — [Quality Attribute]

> Scenario id format: `QA-<ATTRIBUTE-ABBREVIATION>-<NN>`, for example `QA-AVAIL-01`, `QA-PERF-02`.
> This id is copied verbatim into backlog acceptance criteria and into the name of the test that
> defends it (`test_qa_avail_01_*`), so it must be stable once written.

| Field | Value |
|-------|-------|
| **Source** | [source] |
| **Stimulus** | [stimulus] |
| **Environment** | [environment] |
| **Artifact** | [artifact] |
| **Response** | [response] |
| **Measure** | [measure — must contain numbers] |

---
```

Repeat the table block for each scenario.

After writing, tell the architect: "Phase R complete — `quality-scenarios.md` written with [N] scenarios. Moving to Phase A."

---

## Phase A — Approaches (Tactics, Technology, and Architecture Decisions)

**Goal**: identify the tactics that address each scenario, declare the technology baseline that realizes them, and record costly-to-reverse decisions. Outputs: `approaches.md`, `technology-profile.md`, zero or more ADRs in `decisions/`, and the risk register.

### Step A-1: Tactics per scenario

For each scenario in `quality-scenarios.md`, ask:

"For the [Quality Attribute] scenario, what architectural tactics are you considering or have already decided on? Name 2–3 approaches and for each say: what it addresses, what it costs."

*(If the architect is unsure, offer examples from the relevant quality attribute:*
- *Availability: circuit breaker, bulkhead, idempotent state machine, dead-letter queue, health probe*
- *Performance: latency budget per hop, caching, async non-critical path, risk-based fast path*
- *Modifiability: provider-neutral interface, adapter pattern, feature flag for cutover*
- *Security: zero-trust network, mTLS, input validation at boundaries, least-privilege API keys*
- *Auditability: event sourcing, correlation ID propagation, append-only audit store*
- *Scalability: horizontal scaling, sharding, read replicas, queue-based load levelling*
- *Recoverability: point-in-time backup, blue-green deployment, data replication across zones)*

Write `approaches.md` immediately after all scenario tactics are captured. A tactic is not automatically a technology choice: “queue-based load levelling” belongs here; “Azure Service Bus Premium” belongs in the technology profile and may require an ADR.

### approaches.md template

```markdown
---
orace_phase: A
generated_by: orace-workshop
generated_at: YYYY-MM-DD
system: [System Name]
---

# Architectural Approaches — [System Name]

| Scenario | Tactic | What it addresses | Cost / Trade-off | Status |
|----------|--------|-------------------|------------------|--------|
| QA-[ATTR]-[NN] | [tactic] | [response or measure supported] | [complexity, cost, coupling, or operational burden] | Considering / Selected / Rejected |
```

### Step A-2: Technology baseline

Read the `Project State` and Technology Constraints from `outcomes.md`. If an older `outcomes.md` lacks either section, ask for that information before continuing and record it in `technology-profile.md`; do not modify `outcomes.md` unless the architect separately approves `--rerun O`. The technology interview has two modes:

- **New**: capture planned implementation units and proposed or accepted choices. A planned source-of-truth path is valid even before the file exists.
- **Existing or Hybrid**: first inspect repository evidence using targeted file discovery (`rg --files`) for manifests, lockfiles, runtime/version files, container definitions, infrastructure code, CI workflows, and observability configuration. Do not scan dependency/vendor folders. Evidence is a candidate, not a decision: present what was observed and ask whether each choice is `Retain`, `Migrate`, `Retire`, or `TBD`. A lockfile alone does not prove a technology is intentionally used.

If this is a first workshop and the module view does not exist yet, ask: "What are the independently buildable or deployable implementation units that need a technology choice?" Use provisional names and reconcile them during Phase C. If a module view already exists, use its component names and do not create synonyms.

For each implementation unit, cover only applicable categories from this list:

- language and runtime;
- application framework or SDK;
- persistence and data processing;
- messaging and integration protocols;
- hosting, orchestration, and infrastructure provisioning;
- identity and security provider;
- build and package management;
- test, lint, type, schema, and architecture validation;
- observability and operations.

Ask the following fields **one at a time** for each choice:

1. **Choice**: "What technology or service is used or proposed for [unit/category]?"
2. **Version policy**: "Which major/runtime version or compatibility policy applies? Exact transitive versions stay in the manifest or lockfile."
3. **Lifecycle status**: for a new choice, `Mandated`, `Proposed`, `Accepted`, or `TBD`; for an observed choice, `Retain`, `Migrate`, `Retire`, or `TBD`. A migration names both the current and target choice.
4. **Rationale**: "Which constraint, tactic, quality scenario, team capability, or operational need supports this choice?"
5. **Source of truth**: "Which repository path, platform configuration, or named owner proves or will own this choice?" For observed choices, verify the path exists. For planned choices, prefix it with `planned:`.
6. **Guidance**: "Which existing SDDF playbook governs this choice?" If none exists, record `Missing — scaffold <id>`; do not stretch a different playbook.

Then capture the important cross-unit technology contracts: protocol or format, schema/versioning policy, and compatibility expectation. Do not duplicate runtime flow steps that belong in `views/runtime.md`.

Write `technology-profile.md`. It declares project-specific truth; reusable instructions for how to use a technology remain in `.spec/10_playbooks/`. Exact dependency versions remain in manifests and lockfiles, which the profile references instead of duplicating.

### technology-profile.md template

```markdown
---
orace_phase: A
generated_by: orace-workshop
generated_at: YYYY-MM-DD
system: [System Name]
project_state: [New | Existing | Hybrid]
---

# Technology Profile — [System Name]

> Project-specific technology choices and their evidence. Exact dependency versions live in the referenced manifests and lockfiles; reusable implementation rules live in the active SDDF playbooks.

## Technology Constraints

| ID | Constraint | Classification | Source | Consequence |
|----|------------|----------------|--------|-------------|
| TC-001 | [constraint] | Existing / Mandated / Preferred / Prohibited | [evidence or owner] | [what it enables or excludes] |

## Component Technology Baseline

| Unit | Category | Current choice | Target choice | Version policy | Lifecycle status | Rationale / Traceability | Source of truth | Playbook |
|------|----------|----------------|---------------|----------------|------------------|--------------------------|-----------------|----------|
| [component] | [category] | [observed choice or N/A] | [selected or proposed choice] | [major/runtime/compatibility policy] | Mandated / Proposed / Accepted / Retain / Migrate / Retire / TBD | [TC/QA/tactic/team need; ADR if present] | [path, platform config, owner, or planned:path] | [playbook id or Missing — scaffold id] |

## Integration Technology

| From | To | Protocol / Format | Compatibility policy | Source / Decision |
|------|----|-------------------|----------------------|-------------------|
| [unit] | [unit or external dependency] | [HTTP/JSON, event/schema, file, etc.] | [versioning and compatibility rule] | [contract path, QA id, or ADR] |

## Delivery Toolchain

| Scope | Build / Package | Required checks | Configuration source |
|-------|-----------------|-----------------|----------------------|
| [unit] | [tool and version policy] | [exact repository commands when evidenced; otherwise TBD] | [manifest or planned:path] |

## Unresolved Technology Decisions

| Item | Owner | Resolution path |
|------|-------|-----------------|
| [TBD or missing playbook] | [stakeholder] | [ADR, spike, playbook scaffold, or evidence collection] |
```

### Step A-3: Identify decisions that need ADRs

After tactics and the technology profile are drafted, ask:

"Which 2–3 choices are highest-stakes—the ones where choosing wrong would be hardest to reverse, would cross a trust or provider boundary, or would put a quality scenario at risk?"

Include technology choices in this assessment. A routine library with a clear source of truth does not need an ADR; a language/runtime commitment, primary datastore, broker, identity provider, cloud dependency, architectural framework, or cross-boundary AI provider usually does when alternatives have materially different consequences.

For each identified high-stakes decision, run the ADR interview:

1. "What is the title of this decision? Use an imperative phrase—for example: 'Use synchronous screening calls' or 'Adopt PostgreSQL for the order ledger'."
2. "What is the context—what situation made this decision necessary? What forces are in tension?"
3. "What alternatives did you consider? For each: what does it give you and what does it cost?"
4. "What did you decide, and what did you explicitly decide NOT to do?"
5. "What are the consequences—what becomes easier, what becomes harder, what risk is now accepted?"
6. "Status: Proposed or Accepted?"

Write each ADR immediately after the interview. Determine the next sequence number by inspecting existing numbered ADR filenames, not by simply counting files. After the ADR is written, backfill its id into the related `approaches.md` or `technology-profile.md` traceability cell.

### decisions/NNN-<slug>.md template

```markdown
---
orace_phase: A
generated_by: orace-workshop
generated_at: YYYY-MM-DD
status: [Proposed | Accepted | Deprecated | Superseded]
scenarios_addressed:
  - [Quality Attribute 1]
  - [Quality Attribute 2]
technology_profile_entries:
  - [unit/category, when applicable]
---

# ADR-[NNN]: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[The situation that made this decision necessary. What forces are in tension? What would happen if no decision were made?]

## Alternatives Considered

| Option | Benefit | Cost |
|--------|---------|------|
| [Option A] | [benefit] | [cost] |
| [Option B] | [benefit] | [cost] |

## Decision
[What was decided, stated directly. What was explicitly NOT chosen.]

## Consequences

**Easier**: [what becomes easier as a result]
**Harder**: [what becomes harder or more complex]
**Risk accepted**: [what residual risk is now carried, and by whom]
```

Also append each identified risk to `risks/risk-register.md` (create it if absent):

### risks/risk-register.md template

```markdown
---
orace_phase: A
generated_by: orace-workshop
generated_at: YYYY-MM-DD
---

# Risk Register — [System Name]

| ID | Risk | Source | Likelihood | Impact | Mitigation | Owner | Status |
|----|------|--------|-----------|--------|-----------|-------|--------|
| R-001 | [risk from ADR consequence] | ADR-NNN | Low/Med/High | Low/Med/High | [mitigation] | [owner] | Open |
```

If no decision needs an ADR, record that conclusion at the end of `approaches.md`; do not create a ceremonial ADR. After Phase A, tell the architect: "Phase A complete—`approaches.md` and `technology-profile.md` written; [N] ADRs present in `decisions/`. Moving to Phase C."

---

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

---

## Phase E — Evidence & Evolution

**Goal**: define how the architecture will be proven to work in production, and how evidence failures drive evolution. Output: `evidence/evidence-plan.md`, `evolution/backlog.md`.

Ask:

"We're building the evidence plan — the production metrics that prove the architecture is actually working.

For each quality-attribute scenario we defined, I need:
1. The metric name
2. What it proves (one sentence)
3. The target value (the architecture is healthy when this holds)
4. The alert threshold (investigate when this is crossed)
5. How it is collected (APM tool, log aggregation, custom counter, chaos test, etc.)

Let's go through each scenario."

For each scenario in `quality-scenarios.md`, ask the five questions above.

Then ask:

"Beyond the per-scenario metrics, are there any one-time validation tests or drills needed before the first production release? Examples: load test at 2× peak volume, chaos test killing a dependency, regulatory retrieval drill, provider-switch drill."

Review `technology-profile.md` and ask one at a time about any architectural technology assumption that still needs proof: capacity, driver or protocol compatibility, migration safety, provider portability, operability, licensing, or support lifetime. Add a validation test only when it has a measurable pass criterion. Routine dependency-update checks do not belong in the architecture evidence plan.

Finally ask:

"When evidence fails and the architecture needs to evolve, what are the known improvement candidates — things you expect to revisit? These go into the evolution backlog."

Write `evidence/evidence-plan.md` and `evolution/backlog.md` using these templates:

```markdown
---
orace_phase: E
generated_by: orace-workshop
generated_at: YYYY-MM-DD
---

# Evidence Plan — [System Name]

> Evidence converts the architecture from a hypothesis into a proven design.
> These metrics run continuously in production. A metric in the red means the architecture assumption it validates is failing.

## Production Metrics

| Metric | Proves | Target | Alert at | How collected |
|--------|--------|--------|----------|---------------|
| [metric name] | [what it proves — one sentence] | [target value] | [alert threshold] | [collection method] |

## Pre-Release Validation Tests

| Test | Scenario Validated | Pass Criterion | Owner |
|------|--------------------|---------------|-------|
| [test name] | [scenario] | [measurable pass/fail] | [team] |

## Technology Assumption Tests

| Assumption | Profile entry / ADR | Validation | Pass criterion | Owner |
|------------|---------------------|------------|----------------|-------|
| [architecturally significant technology assumption] | [unit/category or ADR] | [spike, compatibility test, migration rehearsal, capacity test] | [measurable result] | [team] |

## Governance Signals (for AI components, if present)

| Signal | Healthy range | Action if outside range |
|--------|--------------|------------------------|
| Human override rate on AI proposals | 5%–25% (stable) | < 2%: audit for rubber-stamping; > 40%: retrain or remove |
| AI grounded-claim rate | ≥ 95% with evidence references | < 90%: review model outputs before next deployment |
| Unauthorized capability attempts | 0 | Any non-zero: security incident |
```

```markdown
---
orace_phase: E
generated_by: orace-workshop
generated_at: YYYY-MM-DD
---

# Evolution Backlog — [System Name]

> Items to revisit when evidence signals the architecture needs to change.
> Each item links back to the evidence signal that would trigger it.

| ID | Item | Trigger signal | Revisit level | Owner | Status |
|----|------|---------------|---------------|-------|--------|
| E-001 | [improvement] | [metric or signal] | Outcomes / Requirements / Approaches / Communication | [team] | Pending |
```

---

## Final Output Summary

After Phase E is complete, print the following summary:

```
ORACE Workshop — complete
────────────────────────────────────────
Artifacts written to: <path>

  outcomes.md                          [O — Outcomes]
  quality-scenarios.md                 [R — Requirements, N scenarios]
  approaches.md                        [A — Tactics mapped to scenarios]
  technology-profile.md                [A — Technology baseline and evidence]
  decisions/                           [A — Zero or more costly-to-reverse decisions]
    001-<name>.md                      [A — Approaches]
    002-<name>.md
    ...
  views/
    context.md                         [C — Communication]
    module.md
    runtime.md
    deployment.md
  risks/risk-register.md               [from A phase]
  evidence/evidence-plan.md            [E — Evidence]
  evolution/backlog.md                 [E — Evolution]
────────────────────────────────────────
These files are ready to use as context for an AI coding agent.
```

Then check whether this repository is governed by SDDF (a `.spec/project.json` file exists):

- **Governed repository.** Say: "Architecture complete. The next step is `/spec-bootstrap`, which registers these artifacts in `.spec/INDEX.md`, derives active playbooks and checks from the technology profile, derives or refreshes the backlog from your scenarios and ADRs, and validates the result. Run it now?" Do not register rows or write backlog tasks yourself — that is the bootstrap skill's job and it validates as it goes.
- **Ungoverned folder.** Say: "These files are ready to use as architecture context. To have coding agents actually enforce them, adopt SDDF in this repository (`docs/ADOPTION.md`) and then run `/spec-bootstrap`."

In both cases add: "Use `/orace-adr` to record further decisions as they emerge; each new ADR needs its routing row before it is finished."

Finally, make the token-usage block the **last content** in the completion response. Do not add prose after it.

When measured usage is available:

```text
Token usage — this ORACE workshop invocation
────────────────────────────────────────────
Accuracy: Measured (host-reported, best-effort)
Source: <host session usage | summed turn usage | named source>
Scope: <start boundary> through the last completed turn before this summary
Input tokens: <N>
  Cached input tokens: <N | not reported> (included in input)
Output tokens: <N>
  Reasoning tokens: <N | not reported> (included in output)
Total tokens: <input + output>
Includes workshop subagents: <yes, N turns | none used | attribution unavailable>
Final-summary tokens included: <yes via post-response accounting | no — not knowable while generating this response>
Billing note: best-effort usage; not a final bill
```

For a trace-counted estimate, use the same block with `Accuracy: Estimated (trace-counted)`, name the counter, and add `Exclusions: <anything not present in the exported trace>`. Use `not reported` for cached input and reasoning unless the trace source supplies them.

When usage is unavailable:

```text
Token usage — this ORACE workshop invocation
────────────────────────────────────────────
Accuracy: Unavailable
Source: host exposed no cumulative or per-turn usage, and no model-aware trace count was run
Scope: this workshop invocation through the last completed turn before this summary
Total tokens: not reported
Final-summary tokens included: no — not knowable while generating this response
```


---

## Behaviour Rules

- Ask one question at a time. Never batch multiple questions in one message.
- When a Measure field contains no numbers, probe once before accepting it: "Can you put a specific number on this?"
- When a stakeholder or component is described vaguely ("the backend team"), reflect it back: "Should I record this as 'Backend Engineering team' or do you have a more specific name?"
- Do not invent details. If an answer is missing, record the field as `[TBD — owner: <stakeholder>]`.
- Write each phase's output file immediately after the interview for that phase. Do not wait until all phases are done.
- Never overwrite an existing file without first telling the architect: "This file already exists. I will overwrite it. Proceed?"
- A rerun updates only its named phase or subphase. Preserve existing prose, ids, accepted ADRs, risk ids, and evidence unless the architect explicitly changes them; prefer a focused patch over regenerating the file.
- For existing systems, distinguish observed evidence from architectural intent. Never convert a detected dependency into `Retain` or `Accepted` without the architect's answer.
- Never invent a technology, version, command, manifest path, playbook, or lifecycle status. Record `[TBD — owner: <stakeholder>]` or a missing-playbook action instead.
- Never invent token usage or label a character heuristic as consumed tokens. If the host does not expose usage, print the `Unavailable` block.
- If the architect skips a question with "I'll fill this in later", record `[TBD]` and continue.
- If this folder is registered in `.spec/INDEX.md`, it is canonical. Re-running a phase over it is a promotion, not an edit: tell the architect which rows and which backlog tasks the change may invalidate, and record the change in `.spec/30_delivery/PROMOTION_LOG.md` afterwards.
- If the architect uses the `--reset` flag, confirm before deleting any existing files: "This will overwrite all existing ORACE artifacts in `<path>`. Confirm?"
