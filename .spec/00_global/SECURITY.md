---
id: security
---

# Security baseline (OWASP)

> Mapped to the OWASP Top 10 and ASVS. Load for auth, api, data, backend, infra, and native work. Non-negotiable.

## Access control — A01

- **SEC-01** Authorisation is enforced server-side on every request, at the resource instance level. A UI that hides a button is not access control.
- **SEC-02** Deny by default. A new endpoint without an explicit policy MUST fail closed.
- **SEC-03** Every object access checks ownership or an explicit grant (prevent IDOR). Never trust an id in a path, body, or token claim as proof of entitlement.
- **SEC-04** Authorisation decisions happen in one place per context (a policy layer), not scattered across handlers.
- **SEC-05** Privilege escalation paths (role assignment, tenant switch, impersonation) are audited with actor, subject, and reason.

## Cryptography and data — A02

- **SEC-06** TLS 1.2+ everywhere, including internal hops that cross a trust boundary declared in the deployment view.
- **SEC-07** Personal and secret data is encrypted at rest; the key management mechanism is named in the deployment view.
- **SEC-08** No custom cryptography. Use vetted library primitives with current parameters; no ECB, no MD5/SHA-1 for security purposes, no hard-coded IVs.
- **SEC-09** Secrets live in a secret manager or the environment, never in source, config files, logs, error messages, or client bundles. A committed secret is an incident: rotate first, then remove.

## Injection — A03

- **SEC-10** All database access uses parameterised queries or a query builder. String-concatenated SQL is forbidden without exception.
- **SEC-11** Output is encoded for its destination (HTML, attribute, URL, shell, LDAP). Never build a shell command from user input; use argument arrays.
- **SEC-12** Untrusted input is validated against an allow-list of shape, type, length, and range at the boundary. Rejecting known-bad is not validation.
- **SEC-13** File uploads are validated by content type and size, stored outside the web root, and never executed. Generated filenames only.

## Design — A04

- **SEC-14** Rate limiting and abuse controls apply to authentication, password reset, token issuance, search, and any expensive endpoint.
- **SEC-15** Security-relevant flows (payment, permission change, data export) are modelled as explicit state machines with server-side transition validation.
- **SEC-16** Threat assumptions for a sensitive feature are recorded in the proposal: what an attacker controls, what they gain, what stops them.

## Configuration — A05

- **SEC-17** Production disables debug modes, verbose errors, directory listing, and default credentials.
- **SEC-18** Security headers are set: `Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, and a frame-ancestors restriction.
- **SEC-19** CORS allow-lists explicit origins. `*` with credentials is forbidden.
- **SEC-20** Cloud storage, queues, and databases are private by default; public exposure requires an approved justification.

## Components — A06

- **SEC-21** Dependencies are pinned with a lock file. A vulnerability scan (SCA) runs in CI and blocks on known-exploited or critical findings.
- **SEC-22** Adding a dependency requires a stated reason, licence check, and maintenance signal in the proposal.

## Identity and sessions — A07

- **SEC-23** Tokens are verified on every request: signature, issuer, audience, expiry, and algorithm allow-list. Never accept `alg: none` or a client-chosen algorithm.
- **SEC-24** Access tokens are short-lived; refresh tokens rotate and are revocable. Logout invalidates server-side state.
- **SEC-25** Browser sessions use `HttpOnly`, `Secure`, `SameSite` cookies. Tokens MUST NOT be stored in `localStorage`.
- **SEC-26** Authentication responses are uniform: no message reveals whether an account exists.
- **SEC-27** Multi-factor authentication is supported for privileged roles.

## Integrity — A08

- **SEC-28** CI/CD artifacts are built from a pinned toolchain; deployment requires a reviewed change. No unreviewed production pushes.
- **SEC-29** Deserialisation of untrusted data uses safe formats only. No pickle, no arbitrary object graph deserialisation from a client.

## Logging and monitoring — A09

- **SEC-30** Authentication failures, authorisation denials, input validation rejections, and privilege changes are logged with correlation id, actor, and outcome.
- **SEC-31** Logs MUST NOT contain credentials, tokens, full card numbers, or unmasked personal data. Redaction is implemented centrally, not per call site.
- **SEC-32** Security-relevant alerting thresholds are defined in the architecture evidence plan.

## SSRF — A10

- **SEC-33** Server-side fetches of user-supplied URLs are blocked by default. Where required, they use an allow-list of hosts, resolve and re-check the IP, block link-local and private ranges, and disable redirects.

## Review gate

Any change touching authentication, authorisation, cryptography, personal data, payments, file handling, deserialisation, or outbound fetching requires `SECURITY_REVIEW.md` with verdict `approved` before close (`DEFINITION_OF_DONE.md` DOD-06).
