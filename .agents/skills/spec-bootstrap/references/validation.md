## Step 7 — Validate and report

```sh
python3 scripts/spec.py validate
python3 scripts/spec.py select --task <first task id>
```

`validate` fails while any architecture artifact is unregistered — that check is the reason this step exists. Fix the registry until it passes.

Then show the user the selection for one real task: which documents it pulled, why each one, and the token estimate. That output is the evidence that the wiring works, and it is worth reading carefully — if a task about a login form is not pulling the deployment view, a surface mapping is wrong.

Finally, record the bootstrap in `.spec/30_delivery/PROMOTION_LOG.md`: what was registered or refreshed, which technology-profile evidence drove each playbook/check change, how many tasks were derived or reopened, and the validation result.
