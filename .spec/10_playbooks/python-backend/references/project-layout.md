# Reference — Python project layout and wiring

Load when scaffolding a service, adding a module, or wiring dependency injection.

## Ports and adapters in practice

```python
# application/ports.py — owned by the application layer
from typing import Protocol
from domain.order import Order, OrderId

class OrderRepository(Protocol):
    async def get(self, order_id: OrderId) -> Order | None: ...
    async def save(self, order: Order) -> None: ...

class PaymentGateway(Protocol):
    async def authorize(self, order: Order) -> AuthorizationResult: ...
```

```python
# application/place_order.py — one use case, one transaction boundary
class PlaceOrder:
    def __init__(self, orders: OrderRepository, payments: PaymentGateway, uow: UnitOfWork) -> None:
        self._orders, self._payments, self._uow = orders, payments, uow

    async def __call__(self, command: PlaceOrderCommand) -> OrderId:
        async with self._uow:                      # CA-05: the boundary lives here
            order = Order.place(command.customer_id, command.lines)   # invariants in the aggregate
            await self._orders.save(order)
            return order.id
```

The adapter implements the Protocol structurally — it does not import it, and the use case never imports the adapter.

## Composition root

Wiring happens in exactly one place. Framework dependency-injection helpers are adapter-layer details; the use case constructor stays plain.

```python
# composition/container.py
def build_place_order(session: AsyncSession) -> PlaceOrder:
    return PlaceOrder(
        orders=SqlAlchemyOrderRepository(session),
        payments=HttpPaymentGateway(settings.payment_base_url),
        uow=SqlAlchemyUnitOfWork(session),
    )
```

The router resolves the use case per request and does nothing else of substance:

```python
@router.post("/orders", status_code=201, response_model=OrderCreated)
async def create_order(body: CreateOrderRequest, use_case: PlaceOrder = Depends(build_place_order)):
    order_id = await use_case(body.to_command())
    return OrderCreated(id=str(order_id))
```

## Settings

One typed settings object, loaded once, injected. Never read the environment at call sites.

```python
class Settings(BaseSettings):
    database_url: SecretStr
    auth0_domain: str
    auth0_audience: str
    model_config = SettingsConfigDict(env_file=".env", extra="forbid")
```

`extra="forbid"` turns a typo in an environment variable into a startup failure instead of a silent default.

## Enforcing the dependency rule

Add a contract that CI runs (PY-01 / CA-09). With `import-linter`:

```ini
[importlinter:contract:layers]
name = Clean architecture layers
type = layers
layers =
    myapp.adapters
    myapp.application
    myapp.domain
```

An architecture test is an acceptable alternative: walk `domain/` modules, assert no import outside the standard library and `domain` itself. Either way, it must fail the build — a rule enforced only by review is not enforced.

## Errors

```python
# domain/errors.py
class DomainError(Exception): ...
class OrderNotFound(DomainError): ...
class InsufficientStock(DomainError): ...
```

```python
# adapters/api/errors.py — one place maps domain failures to the wire (API-06)
ERROR_STATUS = {OrderNotFound: 404, InsufficientStock: 409}

@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    status = ERROR_STATUS.get(type(exc), 400)
    return JSONResponse(status, problem_detail(exc, request.state.correlation_id))
```

The domain never imports a status code; the adapter never re-implements a rule.
