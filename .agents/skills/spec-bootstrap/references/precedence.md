## Step 6 — Check the precedence surface

Compare each scenario `Measure` against the defaults in `.spec/00_global/NONFUNCTIONAL.md` and any active playbook pack. Where a scenario is stricter *or looser* than a default, note it explicitly in the task's `Objective` line:

```
governed by QA-PERF-02 (p99 ≤ 500 ms); NONFUNCTIONAL 300 ms default not applicable
```

The framework already resolves this in favour of the architecture (`PRINCIPLES.md`, Resolving a conflict), so no policy edit is needed — but an agent that has not been told which number governs will read both and guess. Writing it into the task removes the guess.

If a scenario or ADR conflicts with a **security** rule rather than a performance default, do not record a precedence note. Raise it: security rules are not overridden by an ADR without an explicit, logged risk acceptance.
