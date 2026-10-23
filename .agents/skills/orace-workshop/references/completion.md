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
