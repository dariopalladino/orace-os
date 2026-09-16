---
id: play-auth0
playbook: auth0-identity
---

# Playbook pack — Auth0 identity

> Authentication and authorisation with Auth0/OIDC. Load for auth work when this playbook is active. Extends `SECURITY.md`; where they overlap, the stricter rule wins.

> **Precedence.** Every number, threshold, and preferred choice in this pack is a *default*.
> Where an approved architecture scenario `Measure` or an accepted ADR speaks to the artifact
> being changed, the architecture governs and the default here falls away
> (`PRINCIPLES.md`, Resolving a conflict). Security rules are the exception: an ADR never
> silently overrides one — escalate instead.

## Model

Auth0 is the **identity provider**: it proves who the caller is and issues tokens. It is not the authorisation engine for domain objects — instance-level permission ("may *this* user edit *this* order") is always decided by the API against its own data (`SECURITY.md` SEC-03).

```
client ──login (Authorization Code + PKCE)──▶ Auth0 ──access token (audience = your API)──▶ your API
                                                                                              │
                                                                          verify signature, iss, aud, exp, alg
                                                                          map scopes/permissions → policy
                                                                          check instance ownership in your DB
```

## Rules — API side

- **AU0-01** The API MUST validate the JWT on every request: signature against the tenant JWKS (cached, refreshed on unknown `kid`), `iss` exactly the tenant issuer, `aud` exactly this API's identifier, `exp`/`nbf` with ≤ 60 s leeway, and an algorithm allow-list of `RS256` only. Never trust a token's `alg` header (`SECURITY.md` SEC-23).
- **AU0-02** The API MUST NOT call `/userinfo` per request. Identity comes from the validated access token.
- **AU0-03** Scopes are coarse capability grants (`orders:read`). Roles and permissions are mapped to a policy in the API. A role claim alone MUST NOT authorise an object operation.
- **AU0-04** Custom claims are namespaced (`https://<your-domain>/roles`) and treated as **assertions from the IdP**, never as ownership proof.
- **AU0-05** Tenant isolation is enforced server-side from a validated claim plus a database check. A tenant id taken from a request body, query string, or header is forbidden.
- **AU0-06** Machine-to-machine access uses the client credentials grant with a dedicated application per consumer and least-privilege scopes. A shared M2M client across services is forbidden.
- **AU0-07** Token verification failures return `401` with no detail about why; authorisation failures return `403`. Neither reveals object existence (`API_DESIGN.md` API-05/06).
- **AU0-08** Every endpoint declares its required scopes/permissions in the OpenAPI contract, and the default is deny (`SECURITY.md` SEC-02).
- **AU0-09** Auth0 domain, audience, and client ids are configuration, not code. Client **secrets** exist only in server-side secret storage and never in a client bundle or mobile binary.
- **AU0-10** Authentication and authorisation outcomes are logged with correlation id, subject, and decision — never with the token itself (`OBSERVABILITY.md` OBS-04).

## Rules — client side

- **AU0-11** All interactive logins use Authorization Code + PKCE. The implicit flow, the resource owner password grant, and any flow that puts a secret in a client are forbidden.
- **AU0-12** `state` and `nonce` are generated per request and verified on return. Redirect URIs are exact-match allow-listed; wildcards are forbidden.
- **AU0-13** In a browser, tokens MUST NOT be persisted in `localStorage`/`sessionStorage`. Use in-memory tokens with refresh-token rotation in a secure cookie, or a backend-for-frontend holding the tokens in an `HttpOnly` cookie session (`SECURITY.md` SEC-25).
- **AU0-14** On mobile, the login runs in the system browser tab (Custom Tabs / `ASWebAuthenticationSession`), never an embedded WebView. Tokens go to the platform secure store (`stack-kotlin` KT-12).
- **AU0-15** Refresh tokens rotate and the client handles reuse detection by forcing re-authentication. Silent renewal never blocks the UI on a hard failure.
- **AU0-16** Logout clears local state *and* ends the Auth0 session where the product requires it; the post-logout redirect is allow-listed.
- **AU0-17** The client MUST NOT make authorisation decisions that matter. It may hide UI for a missing scope; the server still refuses (`UI_CONVENTIONS.md` UI-04).

## Tenant configuration

- **AU0-18** Tenant configuration (applications, APIs, rules/actions, connections) is managed as code (Deploy CLI or Terraform) and reviewed. Console-only changes are drift and are forbidden in production.
- **AU0-19** Auth0 Actions are versioned in the repository, tested, and MUST NOT embed secrets or perform unbounded external calls in the login path.
- **AU0-20** Separate tenants exist for development and production. A production tenant is never used from a developer machine.
- **AU0-21** MFA is enabled for privileged roles; brute-force protection and suspicious-IP throttling stay on (`SECURITY.md` SEC-14/SEC-27).

## References — load only when the work needs them

| File | Load when |
|---|---|
| `references/api-authorization.md` | implementing token validation, scope mapping, or tenant isolation |
| `references/client-login-flows.md` | wiring login, refresh, logout, or session handling in a client |

## Review gate

Every change under this pack is a sensitive change and requires `SECURITY_REVIEW.md` before close (`DEFINITION_OF_DONE.md` DOD-06).
