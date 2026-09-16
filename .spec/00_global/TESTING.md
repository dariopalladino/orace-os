---
id: testing
---

# Testing

> What must be tested, at which level, and what a test result has to prove.

## Shape

| Level | Covers | Speed | Isolation |
|---|---|---|---|
| Domain/unit | Invariants, value objects, state machines, pure rules | milliseconds | no I/O at all |
| Use case | Orchestration with test doubles for ports | fast | in-process |
| Contract | HTTP/event boundary against the published schema | fast | fake or containerised dependency |
| Integration | Real database, real migrations, real adapter | seconds | ephemeral instance |
| End-to-end | One critical user journey per release-blocking flow | slow | full stack |

- **TEST-01** Every domain invariant has a unit test asserting the rejection path, not only the happy path.
- **TEST-02** Every published endpoint and event has a contract test that fails when the schema drifts.
- **TEST-03** Every migration is exercised against a database created from the previous revision, forward and back.
- **TEST-04** End-to-end tests are reserved for critical journeys. A large, slow, flaky end-to-end suite is worse than none.

## Traceability

- **TEST-05** Each quality-attribute scenario from the architecture MUST have at least one test named after its id — scenario `QA-AVAIL-01` maps to `test_qa_avail_01_*`. This makes the requirement greppable from the test suite and the test greppable from the architecture.
- **TEST-06** Each acceptance criterion in a backlog task names the test or observation that proves it. A criterion with no proof cannot close (`DEFINITION_OF_DONE.md` DOD-01).
- **TEST-07** A bug fix starts with a failing test that reproduces the bug. The commit shows red before green.

## Quality of tests

- **TEST-08** Tests are deterministic. No reliance on wall-clock time, timezone, network, randomness, or execution order; clocks and ids are injected.
- **TEST-09** No `sleep` for synchronisation. Wait on a condition with a bounded timeout.
- **TEST-10** A test asserts observable behaviour, not internal call sequences. Heavy mock-interaction assertions make refactoring impossible and prove nothing about correctness.
- **TEST-11** Test data is built with factories and explicit intent. Shared mutable fixtures across tests are forbidden.
- **TEST-12** A flaky test is quarantined **with an issue and an owner** within the same change, or fixed. Retry-until-green is forbidden.
- **TEST-13** Skipped, expected-failure, and quarantined tests are reported in the handoff. A green suite hiding twelve skips is a false signal.
- **TEST-14** Coverage is a diagnostic, not a target. Untested error paths, authorisation branches, and money calculations are defects regardless of the percentage.

## Security and performance tests

- **TEST-15** Authorisation is tested negatively: a request from the wrong tenant, wrong role, and no credentials MUST be asserted to fail.
- **TEST-16** Input validation is tested with boundary and malformed input on every public boundary.
- **TEST-17** Where a scenario states a latency, throughput, or recovery `Measure`, a load or chaos test asserts it before release, per the architecture evidence plan.

## Review checks

- New tests fail without the change (verified, not assumed).
- Negative authorisation cases present for touched endpoints.
- No new skips or retries introduced silently.
