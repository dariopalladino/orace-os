---
id: hitl
---

# Human in the loop

> Where a person must decide, how they are given enough to decide well, and what is recorded.

## Choosing the control

| Mode | Use when | Requirement |
|---|---|---|
| Human-in-the-loop (approve before effect) | Consequential, hard to reverse, legally or financially significant, or low model confidence | The action cannot execute without an explicit approval event |
| Human-on-the-loop (monitor, intervene) | High volume, reversible, well-measured | Live visibility plus a working stop control |
| Human-in-command (set policy, audit after) | Low risk, high volume, cheap to undo | Sampling review and an audit trail |

- **HITL-01** Every automated decision path MUST declare its mode in the architecture deployment view. An undeclared path defaults to human-in-the-loop.
- **HITL-02** Actions that move money, change permissions, delete or export personal data, communicate externally on a user's behalf, or affect a legal or safety outcome MUST be human-in-the-loop.

## Designing the decision point

- **HITL-03** An approval request MUST show: what will happen, what triggered it, the evidence behind the proposal, the confidence or uncertainty, and what happens if it is rejected or ignored.
- **HITL-04** Approve and reject MUST be equally easy. A one-click approve beside a multi-step reject manufactures consent.
- **HITL-05** Rejecting MUST be possible without a free-text justification, but a reason MUST be capturable — reasons are the training signal for the next iteration.
- **HITL-06** The reviewer MUST be able to inspect the underlying data without leaving the decision, and to escalate rather than being forced into a binary.
- **HITL-07** Bulk approval of individually consequential items is forbidden. Batch controls apply only to items the policy has classified as low risk.
- **HITL-08** Timeouts fail **closed**: an unanswered approval expires without effect and is re-queued or escalated. It never auto-approves.
- **HITL-09** Approval queues have an owner, an SLA, and an alert when the queue ages past it. An unstaffed gate is theatre.

## Evidence and oversight

- **HITL-10** Every approval and rejection is recorded with actor, timestamp, the exact proposal version shown, the decision, and any reason — append-only.
- **HITL-11** Override rate is monitored per decision type (`AI_GOVERNANCE.md` AIG-18). A collapsing override rate triggers a rubber-stamping audit.
- **HITL-12** Where a decision materially affects a person, they are told a human can review it, and how to ask.
- **HITL-13** A stop control (kill switch) exists for every autonomous path, is tested, and its use is documented in the runbook.
- **HITL-14** Reviewers are shown the model's uncertainty honestly. Presenting a low-confidence proposal with a confident UI is a defect.

## Review checks

- Mode declared and matched to consequence class.
- Timeout behaviour fails closed.
- Approval record is append-only and complete.
- Stop control exists and has been exercised.
