---
id: nonfunctional
---

# Non-functional defaults

> Defaults for behaviour no architecture scenario covers. Where an approved quality-attribute scenario defines a `Measure` for an artifact, **that Measure governs for that artifact** and these defaults fall away (`PRINCIPLES.md`, Precedence).

## Defaults

| Concern | Default | Supersede with |
|---|---|---|
| API latency | p95 < 300 ms, p99 < 800 ms for standard read operations | a performance scenario |
| Availability | 99.5% monthly for user-facing paths | an availability scenario |
| Recovery | RTO 1 hour, RPO 15 minutes | a recoverability scenario |
| Client startup | interactive within 2.5 s on a mid-tier device and network | a performance scenario |
| Payload size | list responses ≤ 1 MB; pagination mandatory beyond | an explicit contract note |
| Dependency timeout | 3 s connect, 10 s total, with a stated retry and backoff policy | a dependency-specific scenario |
| Data retention | personal data minimised, retention stated per table | a regulatory constraint |

## Rules

- **NFR-01** Every external call has an explicit timeout. An unbounded call is a latent outage.
- **NFR-02** Retries are bounded, exponential, jittered, and applied only to idempotent operations.
- **NFR-03** Every dependency whose failure would cascade has a circuit breaker or bulkhead, and a defined degraded behaviour.
- **NFR-04** Degraded behaviour is a designed product state, not an exception trace. State what the user sees when a dependency is down.
- **NFR-05** Graceful shutdown drains in-flight work within a bounded window; in-flight requests are not dropped on deploy.
- **NFR-06** Background work is idempotent and restartable; a redelivered message must not double-charge, double-send, or double-apply.
- **NFR-07** Scaling assumptions (expected volume, peak multiple, growth horizon) are stated in the proposal for any new critical path.
- **NFR-08** Cost-significant resources (model calls, egress, storage growth, always-on compute) are named in the proposal with an order-of-magnitude estimate.
- **NFR-09** Localisation-affecting values — dates, numbers, currency, names, addresses, sort order — are formatted by locale-aware libraries, never by hand.
- **NFR-10** Time is handled as UTC internally with explicit conversion at the edges; scheduling near DST boundaries is tested.

## Review checks

- Timeouts and retry policy stated for new outbound calls.
- Degraded behaviour described for new critical dependencies.
- Latency and availability claims matched against the governing scenario, not against this table, when a scenario exists.
