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
