# Benchmarking ORACE-OS

`python3 scripts/benchmark.py run --suite benchmarks/routing-suite.json` measures deterministic routing on the shipped synthetic cases. It reports policy recall, irrelevant selection, mode accuracy, selected context size, and routing time. These cases are regression probes, not evidence of developer productivity.

For a real comparison, run the same small fix, ordinary feature, sensitive change, and multi-module refactor with an unmodified coding agent, an external execution method such as Superpowers, and ORACE-OS. Use equivalent models, resource budgets, repository state, and acceptance criteria. Record observed runs in JSON:

```json
{
  "runs": [
    {
      "system": "ORACE-OS",
      "task": "observed task id",
      "onboarding_seconds": 0,
      "routine_overhead_seconds": 0,
      "tokens": 0,
      "required_policy_recall": 0.0,
      "irrelevant_selection_count": 0,
      "violations_found": 0,
      "supported_claim_rate": 0.0
    }
  ]
}
```

The numbers above illustrate the input shape only; replace them with observations. Omit a field when it was not measured. `python3 scripts/benchmark.py report --input runs.json` reports medians and observation counts, leaving missing measurements as `null`. Preserve raw task traces and reviewer decisions alongside the results so the comparison can be audited.
