---
id: clean-architecture
---

# Clean architecture

> How code is arranged so that business rules survive a change of framework, database, or UI.

## Layers

```
        inbound adapters            outbound adapters
  HTTP / CLI / jobs / UI  ──▶  application  ──▶  ports  ◀──  persistence / HTTP clients / queues
                                    │
                                  domain
```

| Layer | Contains | May import |
|---|---|---|
| `domain` | Entities, value objects, domain services, domain events, invariants | nothing outside `domain` |
| `application` | Use cases, orchestration, transaction boundaries, port interfaces | `domain` |
| `adapters/inbound` | Controllers, routers, screens, view models, serializers | `application`, DTOs |
| `adapters/outbound` | Repositories, clients, publishers, ORM models | `application` port interfaces, `domain` types |
| `composition` | Wiring, DI container, settings, entrypoints | everything |

## Rules

- **CA-01** Dependencies point inward only. `domain` MUST NOT import from `application`, any adapter, or any framework package (no ORM base classes, no HTTP decorators, no UI types).
- **CA-02** A use case MUST depend on a **port** (an interface it owns), never on a concrete adapter. The adapter implements the port; the composition root binds them.
- **CA-03** Data crossing a boundary MUST be converted. Domain objects do not leave as HTTP responses, and request bodies do not enter as domain objects. Explicit DTO ↔ domain mappers only.
- **CA-04** ORM models and domain entities are separate types. Sharing one class for both is the most common way clean architecture is claimed but not practiced.
- **CA-05** The transaction boundary lives in the application layer, one per use case. Repositories do not commit.
- **CA-06** Framework and infrastructure concerns (retries, connection pools, serialization formats, auth middleware) live in adapters. A domain rule never knows it is behind HTTP.
- **CA-07** Errors cross boundaries as typed domain failures. Adapters translate them into transport codes; the domain never raises an HTTP status.
- **CA-08** A new third-party dependency in the `domain` layer requires an ADR. In other layers it requires a note in the proposal.
- **CA-09** The dependency rule MUST be enforced by a check (import linter, module graph test, or architecture unit test), not by reviewer memory. Its command belongs in `project.json` `checks`.
- **CA-10** Do not create a layer with one pass-through function per call. Collapse it and record why in the proposal; ceremony is not architecture.

## When to relax

A thin CRUD surface with no invariants may collapse `application` into the inbound adapter, provided: no domain rule exists, the route is not security-sensitive, and the proposal says so explicitly. Anything with an invariant, a money amount, a state machine, or an authorisation decision keeps the full separation.

## Review checks

- Import graph has no inward-pointing violations.
- No framework import appears under `domain/`.
- Each use case has one entry point and one transaction boundary.
- DTOs and domain types are distinct in both directions.
