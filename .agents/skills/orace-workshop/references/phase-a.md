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
7. "Who owns this decision, and which repository paths or module roots does it govern? Use directory prefixes ending in `/`, or exact files."

Write each ADR immediately after the interview. Determine the next sequence number by inspecting existing numbered ADR filenames, not by simply counting files. After the ADR is written, backfill its id into the related `approaches.md` or `technology-profile.md` traceability cell.

### decisions/NNN-<slug>.md template

```markdown
---
orace_phase: A
generated_by: orace-workshop
generated_at: YYYY-MM-DD
status: [Proposed | Accepted | Deprecated | Superseded]
owner: [person or accountable role]
affected_paths:
  - [repository-relative directory prefix or exact file]
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
