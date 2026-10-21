# Execution adapters and evidence boundary

`task` can emit a versioned JSON execution contract for the native coding-agent workflow or an external method. The contract carries selected specification ids, authorised paths, the approval gate, decision authority, required check groups, review level, and handoff fields. It does not grant an external executor permission to override accepted architecture or skip a required approval.

```sh
python3 scripts/orace.py task "Change password reset validation" \
  --path web/src/auth/reset.tsx \
  --executor external --external-name Superpowers \
  --output .spec/40_workspace/AUTH-021/plan.json
```

Pass the plan to the external method. It reads the selected documents, works only inside `authorized_paths`, and stops at `approval_gate` when required. The human or repository approval process owns architectural decisions. The external method returns a handoff JSON file:

```json
{
  "schema_version": 1,
  "selected_spec_ids": ["protocol", "security"],
  "changed_files": ["web/src/auth/reset.tsx"],
  "criteria": [
    {"id": "AC-01", "claim": "covered", "check_commands": []},
    {"id": "AC-02", "claim": "covered", "check_commands": ["npm test -- --run"]}
  ]
}
```

Capture configured checks with `verify`, then run:

```sh
python3 scripts/orace.py review \
  --plan .spec/40_workspace/AUTH-021/plan.json \
  --handoff .spec/40_workspace/AUTH-021/handoff.json \
  --evidence .spec/40_workspace/AUTH-021/evidence.json
```

`review` checks scope, selected ids, check results, and evidence commit and worktree identity. It reports each criterion as `covered`, `unproven`, or `contradicted`. Only a criterion explicitly about a check can be machine-covered by a passing command; behavioral and production claims stay unproven until a reviewer examines suitable observations. For Governed changes the independent reviewer and host approval controls remain required.

The CLI exports and reconciles contracts. It does not install or discover Superpowers or any other external method; `run` invokes only the command explicitly supplied by the operator. An adapter name is a label for the method that consumed the contract, not a claim that the method is present.

## Run a saved plan through an executable

Use `run` when the chosen coding method has a command you can invoke. The command receives `ORACE_PLAN_PATH` and `ORACE_REPO_ROOT` in its environment. It should read the plan before editing, leave Git commits to the operator, and return a nonzero exit code on failure. No shell interprets the command string.

```sh
python3 scripts/orace.py run \
  --plan .spec/40_workspace/AUTH-021/plan.json \
  --command '<your executor command and arguments>' \
  --authorize-path web/src/auth/ \
  --evidence .spec/40_workspace/AUTH-021/evidence.json \
  --output .spec/40_workspace/AUTH-021/run.json
```

You may refine the plan's acceptance text and add criteria before running it; keep its baseline behavior and check criteria. `run` checks that routing and scope still match current configuration, compares changed files before and after execution, rejects changes outside the authorized paths, and rejects an executor that changes the plan, approval record, configured checks, or Git `HEAD`. It then runs the plan's configured check groups and produces a preflight review. The evidence and run report paths must be new, distinct files. The result `ready_for_review` means the executor and mechanical checks completed; behavioral acceptance still belongs to a reviewer.

For a Governed plan, add `--approval-record <path>`. The JSON record must contain `"decision": "approved"`, a nonempty `"approver"`, and `"plan_sha256"` equal to the SHA-256 digest of the exact saved plan bytes. The CLI verifies the binding and records the supplied approver name. Your host approval process must establish that the record came from an authorized person; a repository file alone cannot prove identity.

## Live checks for pull requests

`check --diff <base...HEAD> --run-checks --strict` executes configured commands during the check invocation and can gate deterministic routing gaps and failed checks. `--evidence <file>` remains useful for inspecting prior local results, but supplied JSON cannot satisfy a strict command gate. The installed pull request workflow stays informational until the project configures its application dependencies and enables live checks. A passing command establishes only that command's result, not a production quality measure or behavioral acceptance.
