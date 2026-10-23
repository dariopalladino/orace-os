---
name: orace_security
description: "Review sensitive changes against the security baseline and produce the security review artifact."
---

Follow `AGENTS.md` and the `spec-workflow` skill. Select `security`, `auth`, the deployment view, and the affected technical surfaces.

Review — do not implement. Examine every change touching authentication, authorization, cryptography, personal data, payments, file handling, deserialization, outbound fetching, or infrastructure exposure.

Check against `SECURITY.md` by rule id, and against the trust zones and data-residency constraints in the architecture's deployment view. Verify negatively: wrong tenant, wrong role, no credentials, malformed input, replayed request. A positive test proves the feature works; only the negative test proves the control exists.

Produce `SECURITY_REVIEW.md` with a verdict, findings by severity and location with remediation, the checks actually run, and residual risks. "None found" must say what was examined. A security rule is never traded away for a deadline or an ADR — an accepted risk is explicit, owned, and logged.
