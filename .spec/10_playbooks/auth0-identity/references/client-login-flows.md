# Reference — Auth0 client login, refresh, and logout

Load when wiring login, token refresh, logout, or session handling in a client.

## Browser: choose the storage model first

| Model | Tokens live in | Use when |
|---|---|---|
| Backend-for-frontend | `HttpOnly`, `Secure`, `SameSite=Lax` server session cookie | Default for anything handling personal or financial data |
| SPA with in-memory tokens | JavaScript memory, refresh via rotating refresh token in a secure cookie | Pure static SPA with no server component |

`localStorage` and `sessionStorage` are not options (AU0-13, SEC-25). Any XSS on the page reads them, and the token leaves with the attacker.

```ts
// SPA model — the SDK keeps the access token in memory and handles rotation
createAuth0Client({
  domain, clientId,
  authorizationParams: { audience, redirect_uri: window.location.origin },
  useRefreshTokens: true,
  cacheLocation: 'memory',
})
```

Accept the consequence honestly: with in-memory tokens, a full page reload requires a silent re-authentication round trip. Design the loading state for it rather than reaching for `localStorage` to avoid the flash.

## The flow, and what each part defends

1. Client generates `code_verifier`, derives `code_challenge`, and a random `state` and `nonce`.
2. Redirect to `/authorize` with `response_type=code`, `code_challenge_method=S256`, the API `audience`, and the exact registered `redirect_uri`.
3. On return, verify `state` matches before doing anything else (AU0-12) — this is the CSRF defence.
4. Exchange the code with the `code_verifier` — this is what stops an intercepted code being redeemed.
5. Verify `nonce` inside the ID token; use the *access* token for API calls and the ID token only for displaying identity.

Never send an ID token as an API credential. It is addressed to the client, not the API, and a correctly configured API will reject it on `aud`.

## Refresh and expiry

- Enable refresh token rotation with reuse detection. On a reuse error, clear local state and force a fresh login — that error means a token was replayed.
- Refresh proactively, shortly before expiry, and queue in-flight requests behind a single refresh; a naive implementation fires one refresh per concurrent 401 and trips rate limits.
- A failed refresh is a logout, not a retry loop.

## Logout

```ts
await auth0.logout({ logoutParams: { returnTo: window.location.origin } })
```

Clear the local cache *and* end the Auth0 session when the product requires it (shared devices, step-up flows). The `returnTo` URL must be in the allowed logout URLs; a wildcard here is an open redirect (AU0-16).

## Mobile

- Use the Auth0 SDK's system-browser flow — Custom Tabs on Android, `ASWebAuthenticationSession` on iOS. An embedded WebView breaks single sign-on, blocks passkeys and MFA providers, and lets the app observe credentials; several identity providers refuse it outright (AU0-14).
- Store tokens in the platform secure store (`kotlin-native` KT-12). Clear them, the local database, and cached media on logout.
- Register the app's callback scheme exactly; on Android prefer App Links over a custom scheme so another app cannot claim the callback.
- Handle the "user cancelled" branch as a normal outcome, not an error dialog.

## What the client may decide

Hiding a button for a missing scope is good UX. It is not access control — the server refuses regardless (AU0-17, UI-04). Never gate a security decision on a claim decoded in the browser or the app.
