---
id: play-python
playbook: python-backend
---

# Playbook pack — Python backend

> Applies `CLEAN_ARCHITECTURE.md`, `DDD.md`, `API_DESIGN.md`, and `SECURITY.md` to a Python service. Load for backend, api, and data work when this playbook is active.

> **Precedence.** Every number, threshold, and preferred choice in this pack is a *default*.
> Where an approved architecture scenario `Measure` or an accepted ADR speaks to the artifact
> being changed, the architecture governs and the default here falls away
> (`PRINCIPLES.md`, Resolving a conflict). Security rules are the exception: an ADR never
> silently overrides one — escalate instead.

## Baseline

- Python 3.12+; one dependency manager with a committed lock file (`uv`, Poetry, or pip-tools — chosen once, recorded in an ADR).
- Web framework: an ASGI framework with first-class schema generation (FastAPI/Starlette or equivalent). The framework lives in the inbound adapter layer only.
- Formatting and linting: `ruff format` + `ruff check`; typing: `mypy --strict` (or `pyright` strict) on `domain/` and `application/` at minimum.
- Every check in this pack has a command in `.spec/project.json` `checks`.

## Layout

```
src/<package>/
  domain/          entities, value objects, domain events, invariants  — stdlib only
  application/     use cases, port protocols, unit of work             — imports domain
  adapters/
    api/           routers, request/response DTOs, error mapping
    persistence/   ORM models, repository implementations, migrations
    clients/       outbound HTTP, queue, model clients
  composition/     settings, DI wiring, app factory, entrypoints
tests/
```

## Rules

- **PY-01** `domain/` MUST NOT import the web framework, the ORM, or any I/O library. Enforce with an import-linter contract or an architecture test in CI (`CLEAN_ARCHITECTURE.md` CA-09).
- **PY-02** Ports are `typing.Protocol` classes owned by `application/`. Adapters implement them; the composition root binds them. No adapter is imported by a use case.
- **PY-03** Request and response models are Pydantic (or dataclass) DTOs in `adapters/api/`, with `extra="forbid"`. They are distinct types from domain objects and from ORM models (`CLEAN_ARCHITECTURE.md` CA-04).
- **PY-04** Domain types are immutable where possible: frozen dataclasses or Pydantic models with validation in `__post_init__`/validators. Invalid states MUST be unconstructable (`DDD.md` DDD-08).
- **PY-05** Money uses `decimal.Decimal` or an integer minor-unit value object with currency. `float` for money is a defect.
- **PY-06** No mutable default arguments, no module-level mutable state, no import-time I/O. Settings load through one typed settings object, injected.
- **PY-07** Async and sync are not mixed carelessly: in an async handler, blocking calls run in a worker thread. A blocking DB driver inside the event loop is a production incident.
- **PY-08** Database sessions are request-scoped and injected; the unit of work commits once per use case (`CLEAN_ARCHITECTURE.md` CA-05). Repositories never commit.
- **PY-09** All SQL is parameterised through the ORM/driver. `text()` with an f-string is forbidden (`SECURITY.md` SEC-10).
- **PY-10** Exceptions: domain failures are typed exception classes in `domain/`; one exception handler in `adapters/api/` maps them to the error envelope (`API_DESIGN.md` API-06). `except Exception: pass` is forbidden; a bare re-raise must preserve the traceback.
- **PY-11** Logging uses the structured logger with correlation id from middleware (`OBSERVABILITY.md` OBS-01/02). `print` is forbidden outside scripts.
- **PY-12** Background work uses a real task runner with idempotent, restartable handlers. Fire-and-forget `asyncio.create_task` for business-critical work is forbidden.
- **PY-13** Dependencies are pinned in a lock file and scanned in CI (`SECURITY.md` SEC-21). `pickle`/`yaml.load` on untrusted input is forbidden (SEC-29).
- **PY-14** Tests use `pytest`; integration tests run against a real ephemeral database (containerised), never a mocked DB layer (`TESTING.md`).
- **PY-15** Type ignores and lint suppressions require an inline reason comment. An unexplained `# type: ignore` fails review.

## References — load only when the work needs them

| File | Load when |
|---|---|
| `references/project-layout.md` | scaffolding a new service, adding a module, or wiring DI |
| `references/persistence-and-async.md` | writing repositories, migrations, transactions, or async I/O |

## Checks

```sh
ruff format --check . && ruff check .
mypy src
pytest -q
```
