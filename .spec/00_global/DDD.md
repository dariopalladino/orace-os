---
id: ddd
---

# Domain-driven design

> How the domain is modelled and split. Load for domain, data, and architecture work.

## Rules

- **DDD-01** Names in code MUST match the names in the architecture's module view and glossary. If the business says "settlement", the class is not `PaymentProcessor2`.
- **DDD-02** Every bounded context has one owner, one persistence boundary, and an explicit relationship to its neighbours (customer-supplier, conformist, anti-corruption layer, shared kernel). Record it in the architecture's module view.
- **DDD-03** A context MUST NOT read or write another context's tables. Cross-context communication goes through a published contract — an API call or a domain event.
- **DDD-04** Translation at a context boundary happens in an **anti-corruption layer**. An upstream model's vocabulary never leaks into a downstream domain.
- **DDD-05** An aggregate is the consistency boundary. One transaction MUST modify one aggregate instance. Cross-aggregate consistency is eventual, via domain events.
- **DDD-06** Aggregates are referenced by identity, never by object reference across aggregate boundaries.
- **DDD-07** Keep aggregates small. If an aggregate loads a collection that grows unboundedly, it is a query concern, not an aggregate member.
- **DDD-08** Invariants live inside the aggregate root. A value that can be invalid MUST NOT be constructible — validate in the constructor or factory, not in the caller.
- **DDD-09** Use value objects for anything with a unit, a format, or a constraint: money, email, identifier, date range, percentage. Raw `str`/`float`/`String` for these is a defect.
- **DDD-10** Money MUST be a value object carrying currency, stored as a minor-unit integer or exact decimal. Never a float.
- **DDD-11** Domain events are named in past tense (`OrderPlaced`), carry the aggregate id and a version, are immutable, and are part of the published contract once other contexts consume them.
- **DDD-12** Repositories expose aggregate-level operations (`get`, `save`, named queries). They MUST NOT expose a query-builder or leak persistence types to callers.
- **DDD-13** Domain services exist only for logic that genuinely belongs to no single entity. A service holding all the logic while entities hold only data is an anemic model — flag it in review.
- **DDD-14** Read models for complex queries are separate from aggregates. Do not distort the write model to serve a screen.

## Escalation

Introducing a new bounded context, changing a context boundary, or splitting an aggregate is a **structural** change: it requires an ADR before code (see `GOVERNANCE.md`).

## Review checks

- Ubiquitous language: class and endpoint names match the architecture glossary.
- One aggregate mutated per transaction.
- No cross-context table access.
- No primitive obsession on money, identity, or contact fields.
