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
