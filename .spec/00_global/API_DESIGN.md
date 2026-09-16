---
id: api-design
---

# API design

> Contract rules for HTTP and event interfaces. Load for any change to a published boundary.

## Rules

- **API-01** The contract is the source of truth and is written **before** the implementation: OpenAPI for HTTP, a registered schema for events. Generated-from-code contracts are acceptable only when the generated artifact is committed and diffed in review.
- **API-02** Resources are plural nouns; behaviour lives in the method, not the path. `POST /orders/{id}/cancel` is acceptable for a state transition that is not a resource; `POST /doOrderCancel` is not.
- **API-03** Methods carry their standard semantics. `GET` and `HEAD` are safe and side-effect free; `PUT` and `DELETE` are idempotent; `POST` is not, unless made so by an idempotency key.
- **API-04** Every state-changing endpoint that a client may retry MUST accept an `Idempotency-Key` header and return the original result on replay.
- **API-05** Status codes are used honestly: `200/201/202/204` for success, `400` malformed, `401` unauthenticated, `403` unauthorised, `404` absent or invisible, `409` conflict, `422` semantically invalid, `429` throttled, `5xx` server fault only.
- **API-06** Errors use one machine-readable shape across the whole API (RFC 9457 `application/problem+json` or an equivalent documented envelope) with a stable `type`/`code`, a human `detail`, and a correlation id. Error bodies MUST NOT leak stack traces, SQL, internal hostnames, or whether an account exists.
- **API-07** All list endpoints are paginated by default with a documented maximum page size. Cursor pagination for data that changes under the reader; offset only for stable, small sets.
- **API-08** Breaking changes require a new version. Additive, optional fields are non-breaking; changing a type, removing a field, tightening validation, or changing a default is breaking.
- **API-09** Versioning strategy is chosen once per API and recorded in an ADR (URI path or media type). Mixed strategies are forbidden.
- **API-10** Deprecation is announced in the contract with `Deprecation`/`Sunset` headers and a documented window before removal.
- **API-11** Every endpoint declares its authentication and required scopes/permissions in the contract. "Public" is an explicit annotation, never an omission.
- **API-12** Input validation happens at the boundary against the contract schema, rejecting unknown fields by default. Validation is never delegated to the database or the ORM.
- **API-13** Every response documents its cache semantics. Responses containing personal or authorisation-dependent data are `Cache-Control: no-store`.
- **API-14** Timestamps are RFC 3339 UTC with an explicit offset. Money is an object with an amount in minor units and an ISO 4217 currency. Ids are opaque strings to the client.
- **API-15** Rate limits are documented and communicated with `RateLimit-*` headers and `429` with `Retry-After`.
- **API-16** Long-running work returns `202` with a status resource. Do not hold a request open past the documented latency budget.
- **API-17** Every request and response carries a correlation id, propagated to downstream calls and present in logs (see `OBSERVABILITY.md`).
- **API-18** Event contracts are versioned and backward compatible within a major version; consumers MUST tolerate unknown fields.

## Review checks

- Contract diff attached to the proposal for any boundary change.
- Error envelope consistent with the rest of the API.
- Auth and scopes declared per endpoint.
- Pagination, idempotency, and rate-limit behaviour present where applicable.
