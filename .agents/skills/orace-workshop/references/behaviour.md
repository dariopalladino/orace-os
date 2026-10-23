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
