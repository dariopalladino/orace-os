# Reference — Python persistence and async

Load when writing repositories, migrations, transactions, or async I/O.

## Separate ORM models from domain entities

```python
# adapters/persistence/models.py
class OrderRow(Base):
    __tablename__ = "orders"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    status: Mapped[str]
    total_minor: Mapped[int]
    currency: Mapped[str] = mapped_column(String(3))

# adapters/persistence/mappers.py
def to_domain(row: OrderRow) -> Order:
    return Order(id=OrderId(row.id), status=OrderStatus(row.status),
                 total=Money(row.total_minor, Currency(row.currency)))
```

One class serving as both is the most common way CA-04 is violated. The cost of the mapper is small; the cost of an ORM session leaking into domain logic is a rewrite.

## Unit of work

```python
class SqlAlchemyUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type:
            await self._session.rollback()
        else:
            await self._session.commit()
```

Repositories call `add`/`flush`, never `commit` (PY-08).

## Async discipline

- Use an async driver end to end (`asyncpg`, `aiohttp`/`httpx.AsyncClient`). One blocking driver in an async handler serialises the whole event loop.
- Wrap unavoidable blocking work: `await anyio.to_thread.run_sync(blocking_call, arg)`.
- Bound every outbound call (`NFR-01`): `httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0))`.
- Use `asyncio.TaskGroup` for concurrent fan-out; it cancels siblings on failure. Never `create_task` and forget (PY-12).
- Share one `AsyncClient` per process, created at startup and closed at shutdown. A client per request exhausts sockets.

## Queries

```python
# parameterised, always (SEC-10)
stmt = select(OrderRow).where(OrderRow.customer_id == customer_id).limit(limit + 1)
```

- Fetch `limit + 1` rows to answer "is there a next page" without a second count query (API-07).
- Eager-load the relationships a use case needs (`selectinload`) rather than discovering N+1 in production. Assert the query count in a test for hot paths.
- Never return ORM rows from a repository; map at the boundary.

## Migrations

```sh
alembic revision --autogenerate -m "add orders.settled_at"
alembic upgrade head
alembic downgrade -1     # DATA-12: prove the rollback
```

Autogenerate is a draft, not an answer. Always read the generated file: it misses server defaults, enum changes, index concurrency, and data backfills.

Expand–migrate–contract (DATA-13) across three releases:

```
release n     add nullable settled_at, write it alongside the old field
release n+1   backfill in batches, read from settled_at, keep writing both
release n+2   stop writing the old field, drop it
```

Batched backfill, restartable and bounded:

```python
while True:
    rows = await session.execute(
        select(OrderRow.id).where(OrderRow.settled_at.is_(None)).limit(1000))
    ids = rows.scalars().all()
    if not ids:
        break
    await session.execute(update(OrderRow).where(OrderRow.id.in_(ids)).values(settled_at=...))
    await session.commit()
```

On PostgreSQL, create indexes on hot tables with `CREATE INDEX CONCURRENTLY` in a migration marked non-transactional, and state the expected duration in the proposal (DATA-15).

## Integration tests

Run against a real ephemeral database with the real migrations applied (TEST-03). A mocked repository proves your mock works; it proves nothing about your schema, constraints, or SQL.
