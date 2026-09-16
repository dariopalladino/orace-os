---
id: data-modelling
---

# Data modelling and persistence

> Rules for schema design, migrations, and data lifecycle. Load for any change under a data module root.

## Schema

- **DATA-01** Every table has a primary key. Prefer an opaque surrogate key (UUIDv7 or a monotonic id) for identity and a separate unique constraint for the natural key.
- **DATA-02** Every foreign key is declared with an explicit `ON DELETE` behaviour. Application-only referential integrity is a defect.
- **DATA-03** Constraints belong in the database: `NOT NULL`, `UNIQUE`, `CHECK`, and enum/lookup constraints. The application validates for good messages; the database guarantees.
- **DATA-04** Normalise to third normal form by default. Denormalise only with a measured read requirement, recorded in the proposal, plus a stated mechanism keeping copies consistent.
- **DATA-05** Money is stored as exact numeric (integer minor units or `NUMERIC`), never floating point. Currency is stored alongside every amount.
- **DATA-06** Timestamps are stored in UTC with time zone (`timestamptz`), named `*_at`. Store the originating time zone separately when local wall-clock meaning matters.
- **DATA-07** Soft delete is opt-in, not default. When used, every query path MUST filter it, enforced by a view or a repository-level default — not by developer discipline.
- **DATA-08** Nullable means "unknown or not applicable". Do not use `NULL` as a sentinel for a business state; model the state.
- **DATA-09** JSON columns are permitted for genuinely open-ended payloads only. Anything queried, sorted, or constrained gets a column. A JSON blob holding the core model requires an ADR.
- **DATA-10** Every table intended to be queried by a non-key column has a stated index plan in the proposal, with the query it serves.

## Migrations

- **DATA-11** Migrations are versioned, ordered, forward-only files in the repository, applied by a tool — never by hand-run SQL against an environment.
- **DATA-12** Every migration has a tested rollback path, or an explicit, approved statement that it is irreversible.
- **DATA-13** Destructive changes are expand–migrate–contract across separate releases: add the new shape, backfill, dual-write or dual-read, switch, then drop in a later release. A column is never dropped in the same release that stops using it.
- **DATA-14** Backfills of large tables run in batches with bounded transactions and are restartable. A single transaction rewriting a production table is a blocking incident.
- **DATA-15** Migrations that take a lock on a hot table declare the expected lock and duration in the proposal.
- **DATA-16** Schema changes are promoted (`GOVERNANCE.md` GOV-06) before the dependent implementation task begins.

## Data lifecycle and privacy

- **DATA-17** Every table carrying personal data is classified in the architecture's deployment view, with a documented retention period and a deletion mechanism.
- **DATA-18** Secrets, tokens, and credentials are never stored in application tables. Password-equivalents are stored only as a modern salted hash (Argon2id or equivalent).
- **DATA-19** Audit tables are append-only, carry actor, action, subject, timestamp, and correlation id, and are not writable by application roles.
- **DATA-20** Test fixtures and seed data MUST NOT contain real production data.

## Review checks

- Migration reviewed with rollback evidence.
- Index plan present for new query paths.
- No float money, no naive timestamps, no unclassified personal data.
