# Reference — Auth0 API token validation and authorisation

Load when implementing token validation, scope mapping, or tenant isolation.

## Validation, done once, at the edge of the adapter layer

```python
jwks = PyJWKClient(f"https://{settings.auth0_domain}/.well-known/jwks.json", cache_keys=True)

def verify(token: str) -> Claims:
    signing_key = jwks.get_signing_key_from_jwt(token).key     # refreshes on unknown kid
    payload = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256"],                                   # AU0-01: allow-list, never token-chosen
        audience=settings.auth0_audience,                       # exact API identifier
        issuer=f"https://{settings.auth0_domain}/",             # trailing slash matters
        leeway=30,
        options={"require": ["exp", "iat", "iss", "aud", "sub"]},
    )
    return Claims.model_validate(payload)
```

Failure modes this closes: `alg: none`, a token minted for a different API (`aud` confusion), a token from another tenant, an expired token accepted because `exp` was optional.

Cache the JWKS and refresh on an unrecognised `kid`. Fetching JWKS per request adds a hard dependency on Auth0 to every call and will be your first outage.

## Scopes are capabilities; policy is yours

```python
def require(*scopes: str):
    async def dependency(claims: Claims = Depends(current_claims)) -> Claims:
        granted = set(claims.scope.split())
        if not set(scopes) <= granted:
            raise Forbidden()                       # 403, no detail (AU0-07)
        return claims
    return dependency

@router.get("/orders/{order_id}", dependencies=[Depends(require("orders:read"))])
async def get_order(order_id: OrderId, claims: Claims = Depends(current_claims)):
    order = await repo.get(order_id)
    if order is None or order.tenant_id != claims.tenant_id:   # AU0-05, SEC-03
        raise NotFound()                                       # 404, not 403 — do not confirm existence
    return OrderResponse.from_domain(order)
```

The scope check says *this client may read orders*. The ownership check says *this caller may read this order*. Both are required; the scope alone is an IDOR waiting to happen.

## Tenant isolation

- The tenant comes from a validated, namespaced claim, then is checked against the row. Never from a header, query parameter, or body field.
- Where the data store supports it, add a defence in depth: PostgreSQL row-level security keyed to a session variable set from the claim, so a forgotten `WHERE` clause still cannot cross tenants.
- Test the negative case explicitly: tenant A's token requesting tenant B's object must return 404 (`TESTING.md` TEST-15).

## Roles and permissions

Enable RBAC on the API in Auth0 and add permissions to the access token, or map roles to permissions in an Action. Either way the API treats the result as an assertion about the *subject*, not authority over an *object* (AU0-03/AU0-04).

```python
ROLE_PERMISSIONS = {"admin": {"orders:read", "orders:write", "orders:refund"},
                    "agent": {"orders:read", "orders:write"}}
```

Keeping this map in the API means a compromised or misconfigured tenant cannot silently grant refund rights.

## Machine-to-machine

One Auth0 application per consuming service, each with the minimum scopes (AU0-06). Cache the token until shortly before expiry; requesting a new token per call will hit the tenant rate limit under load and is indistinguishable from an attack.

## What to log

Log the decision, not the credential: correlation id, `sub`, endpoint, required scopes, granted/denied, and reason code. Never the token, and never the full claim set (AU0-10, `OBSERVABILITY.md` OBS-04).
