# Workshop token accounting

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
