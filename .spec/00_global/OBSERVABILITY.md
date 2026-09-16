---
id: observability
---

# Observability

> A change that cannot be observed in production is not finished.

## Rules

- **OBS-01** Every inbound request, job, and message carries a correlation id, generated at the edge if absent, propagated to every downstream call, and present in every log line and span for that unit of work.
- **OBS-02** Logs are structured (one JSON object per event) with a stable event name, level, correlation id, actor or tenant identifier, and outcome. Free-text-only logging is forbidden on service paths.
- **OBS-03** Log levels mean what they say: `ERROR` requires human attention; `WARN` is a degraded but handled condition; `INFO` marks a business-meaningful event; `DEBUG` is off in production. An `ERROR` nobody acts on is noise that hides real errors.
- **OBS-04** Logs never contain credentials, tokens, full card numbers, or unmasked personal data. Redaction is centralised (`SECURITY.md` SEC-31).
- **OBS-05** Every service exposes the RED signals — request rate, error rate, duration distribution — per endpoint, and queue depth and consumer lag for asynchronous paths.
- **OBS-06** Latency is reported as percentiles (p50/p95/p99), never as an average.
- **OBS-07** Distributed traces cover every cross-service and cross-boundary call, with the external dependency, the database, and the model call as spans.
- **OBS-08** Metric names, targets, and alert thresholds come from the architecture evidence plan. A metric invented at implementation time without a plan entry is unowned.
- **OBS-09** Every alert has an owner, a runbook link, and a stated user-visible symptom. Alerts that cannot be acted on are deleted, not muted.
- **OBS-10** Health checks distinguish liveness (process is alive) from readiness (dependencies are usable). A readiness check that always returns 200 is a lie the orchestrator believes.
- **OBS-11** Feature flags and model or prompt versions are emitted as attributes on the requests they affect, so behaviour can be attributed after the fact.
- **OBS-12** Business-critical outcomes (payment confirmed, order placed, approval granted) are counted as first-class metrics, not inferred from log greps.
- **OBS-13** Dashboards for a new critical path are created in the same change as the path, not afterwards.

## Review checks

- Metric and alert names match the evidence plan exactly.
- Correlation id present end to end in a real traced request.
- No sensitive data in emitted log samples.
