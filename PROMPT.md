# A complete example: improve an existing permit portal

This example follows one change from adopting the framework to closing a reviewed task. The example repository, `../permit-portal`, already contains a React web app and a Python API. Applicants can sign in, but the status page does not yet show their permit status. The feature must never reveal another applicant's permit.

The paths and task id below belong to this example. Use the paths and id confirmed in your own repository; do not copy them into a project with a different layout.

## 1. Install the framework into the application repository

Run this **from the ORACE-OS checkout**. The target repository must already exist.

```sh
python3 scripts/orace.py init --target ../permit-portal
cd ../permit-portal
```

Read `.spec/40_workspace/PROJECT_DISCOVERY.json` and `.spec/project.json`. Discovery reports what the repository appears to use; it does not approve a technology choice, activate playbooks, or invent validation commands. Existing `AGENTS.md`, `CLAUDE.md`, and Copilot instructions are preserved and extended.

Open the **permit portal** in your coding agent. Codex discovers `AGENTS.md` and the skills in `.agents/skills/`; Claude Code has the corresponding commands; for GitHub Copilot, explicitly tell it to read the relevant `SKILL.md`. The prompts below use skill names in ordinary language so they work in all three hosts. To invoke explicitly, use `$orace-workshop` in Codex or `/orace-workshop` in Claude Code.

## 2. Capture the architecture that this change must respect

Send this to the agent:

> Use the `orace-workshop` skill with `.spec/15_architecture`. This is an existing permit portal. Inspect the repository as evidence, then interview me one question at a time. We need to document who may read a permit, the business failure caused by cross-account disclosure, the current identity provider, and a measurable security scenario. Treat observed technology as a candidate until I confirm whether we retain it. Do not invent an access rule, a performance target, or a test command.

Answer the workshop questions with your real system constraints. For this worked example, the confirmed security scenario is `QA-SEC-01`: a signed-in applicant requesting another applicant's permit gets no permit data. Its `Measure` is **“A cross-account status request returns 404 and exposes zero permit fields.”** The accepted architecture also records where authorization is enforced and how that negative case will be tested. Your project's measure may differ; the workshop records what you approve.

When the workshop finishes, inspect the artifacts under `.spec/15_architecture/`. Then send:

> Use the `spec-bootstrap` skill for `.spec/15_architecture`. Register the accepted architecture in `.spec/INDEX.md`; propose only the playbooks, module roots, and exact check commands supported by the technology profile and repository files. Derive a backlog task for the permit status feature, carrying `QA-SEC-01`'s Measure verbatim. Show me the proposed configuration, routing rows, task, and promotion entries before applying canonical changes.

Review that proposal. In this example, the confirmed project uses the `react-frontend`, `python-backend`, and `auth0-identity` packs; the backlog task is `PERMIT-014`. The accepted task owns `api/src/permits/`, `api/tests/permits/`, and `web/src/features/permits/`. Those facts come from this example's repository and your confirmation, not from the installer.

After the approved bootstrap changes are applied, validate the routing:

```sh
python3 scripts/spec.py validate
python3 scripts/spec.py select --task PERMIT-014
```

Check that selection includes the security scenario, authorization policy, relevant views, and active packs. Correct a missing surface or routing row before implementation.

## 3. Propose the implementation

Send:

> Use the `spec-workflow` skill to implement `PERMIT-014` from `.spec/20_backlog/TASKS.md`. Run `python3 scripts/spec.py select --task PERMIT-014` and read every selected document in full. Confirm the task's semantic surfaces and required mode. Record the selected ids, the exact `QA-SEC-01` Measure, authorized paths, acceptance criteria, and checks in `.spec/40_workspace/PERMIT-014/TASK_CONTEXT.md`. In supervisor mode, give the API and UI work packages disjoint file ownership and routing ids; use sequential execution if subagents are unavailable. Write concrete `PROPOSED_CHANGES.md` files in the task workspace and show them to me before editing application code.

Because authorization and personal data are involved, this is a **Governed** change. The proposal should name the API authorization point, the UI's loading/empty/error states, the cross-account negative test, and the exact checks available in `.spec/project.json`. It must not relax the scenario Measure to make the feature easier to ship.

Once the proposals are accurate, an approval message for this example is:

> I approve the `PERMIT-014` proposals now recorded under `.spec/40_workspace/PERMIT-014/`. Implement only within `api/src/permits/`, `api/tests/permits/`, and `web/src/features/permits/`. Keep the `QA-SEC-01` Measure unchanged. If a contract or architectural decision is missing, record a clarification before proceeding.

## 4. Implement, verify, and hand off

The implementer now changes the approved files, adds the negative authorization test, and writes a `HANDOFF.md` for each work package. The handoff names each acceptance criterion, its governing requirement, and the observation that proves it. A sensitive change also gets `agent_security/SECURITY_REVIEW.md` with the wrong-account, missing-credential, and other applicable negative cases.

Ask the agent to run the check groups actually configured for this project. In this example, bootstrap confirmed `backend_when_present` and `frontend_when_present`, so the evidence command is:

```sh
python3 scripts/orace.py verify \
  --check backend_when_present \
  --check frontend_when_present \
  --task PERMIT-014 \
  --output .spec/40_workspace/PERMIT-014/evidence.json
```

Read the result. `verify` records command output and exit codes; it does not by itself prove that the UI works or that no cross-account data is disclosed. The tests and handoffs must connect those claims to the actual observations. A failed or unavailable check remains open.

## 5. Review and close

Use a fresh reviewer context and send:

> Use the `spec-review` skill for `PERMIT-014`. Review the task context, every handoff, the security review, and the evidence file. Check that the cross-account test really asserts the `QA-SEC-01` Measure, that the changed files stayed in the approved paths, and that no check or security control was weakened. Write `REVIEW_REPORT.md` with `accept`, `revise`, or `reopen` and the exact actions still needed. Do not fix the implementation in the reviewer role.

If the verdict is `revise` or `reopen`, address the findings and run affected checks again before another review. On `accept`, the supervisor closes `PERMIT-014` in the backlog and records that canonical status change in `.spec/30_delivery/PROMOTION_LOG.md`. The final report should give the changed files, requirements met, exact checks and results, review verdict, and any remaining production evidence to collect.

## The next request

The architecture interview is not repeated for every small change. For a new request that is not yet in the backlog, start with the CLI's task planner. For example:

```sh
python3 scripts/orace.py task "Fix permit status empty-state wording" \
  --path web/src/features/permits/PermitStatus.tsx \
  --surface frontend \
  --output .spec/40_workspace/permit-empty-state/plan.json
```

Inspect the inferred surfaces, selected documents, draft criteria, and recommended Lite/Standard/Governed mode. Then ask the agent to use `spec-workflow` on that plan. The command prepares a plan; it does not edit code or approve its own draft criteria. If production evidence later contradicts an accepted scenario or ADR, use `orace.py impact` and the `orace-adr` or targeted `orace-workshop` skill to revisit the affected decision.
