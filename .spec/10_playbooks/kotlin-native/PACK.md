---
id: play-kotlin
playbook: kotlin-native
---

# Playbook pack — Kotlin native mobile

> Applies `CLEAN_ARCHITECTURE.md`, `UI_CONVENTIONS.md`, and `SECURITY.md` to a Kotlin/Jetpack Compose application. Load for native work when this playbook is active.

> **Precedence.** Every number, threshold, and preferred choice in this pack is a *default*.
> Where an approved architecture scenario `Measure` or an accepted ADR speaks to the artifact
> being changed, the architecture governs and the default here falls away
> (`PRINCIPLES.md`, Resolving a conflict). Security rules are the exception: an ADR never
> silently overrides one — escalate instead.

## Baseline

- Kotlin with explicit API mode on library modules; Jetpack Compose for UI; coroutines and `Flow` for concurrency.
- Gradle with a version catalog (`libs.versions.toml`) and convention plugins. Versions are declared once.
- `ktlint`/`detekt` and the Android lint baseline are in `.spec/project.json` `checks`.

## Module layout

```
app/                 composition root, navigation graph, DI setup
core/domain/         entities, value objects, use cases     — pure Kotlin, no Android
core/data/           repository implementations, DTOs, mappers, local + remote sources
core/ui/             design system: theme, tokens, shared composables
feature/<x>/         screen, ViewModel, feature-scoped UI state
```

## Rules

- **KT-01** `core/domain` is a pure Kotlin module with **no Android dependency**. Enforce with a module-dependency check in CI (`CLEAN_ARCHITECTURE.md` CA-09).
- **KT-02** A feature module MUST NOT depend on another feature module. Shared behaviour moves to `core/`.
- **KT-03** Each screen has one immutable UI state type exposed as `StateFlow<UiState>` from a `ViewModel`. Composables receive state and emit events; they do not fetch.
- **KT-04** UI state is modelled as a sealed hierarchy or a data class with explicit loading, empty, error, and content representations (`UI_CONVENTIONS.md` UI-05). A nullable field standing in for "loading" is a defect.
- **KT-05** State is collected lifecycle-aware (`collectAsStateWithLifecycle`). Collecting in a way that keeps running in the background is forbidden.
- **KT-06** One-off events (navigation, snackbar) use a `Channel`/event queue, never a `StateFlow` that replays on rotation.
- **KT-07** Composables are side-effect free during composition. All effects go through `LaunchedEffect`, `DisposableEffect`, or `rememberCoroutineScope` with a correct key.
- **KT-08** No blocking call on the main dispatcher. I/O runs on an injected dispatcher; `Dispatchers.IO` is never hard-coded inside a use case (it is injected so tests can replace it).
- **KT-09** Coroutines follow structured concurrency: scoped to the `ViewModel` or a lifecycle; `GlobalScope` is forbidden. Cancellation is cooperative and exceptions surface as UI state, not crashes.
- **KT-10** Nullability is real: no `!!` outside tests, no unchecked casts, no platform types crossing a module boundary without an explicit contract.
- **KT-11** Domain and DTO types are distinct with explicit mappers; a serialization annotation MUST NOT appear on a domain type (`CLEAN_ARCHITECTURE.md` CA-03).
- **KT-12** Secrets, tokens, and credentials are stored in the Android Keystore / `EncryptedSharedPreferences` — never in `SharedPreferences`, a file, or a build config field (`SECURITY.md` SEC-09/SEC-25).
- **KT-13** Network uses TLS with certificate validation intact; a debug-only trust override MUST NOT be reachable in a release build. Release builds enable minification and resource shrinking with a maintained keep-rules file.
- **KT-14** Every permission requested is justified in the proposal, requested at point of use with a rationale, and degrades gracefully on denial.
- **KT-15** Screens handle process death: state that must survive goes through `SavedStateHandle`, and the restore path is tested.
- **KT-16** Offline behaviour is explicit: the local store is the source of truth for the screen, sync is idempotent, and conflict resolution is stated (see the reference).
- **KT-17** Accessibility: every interactive composable has a content description or merged semantics, touch targets ≥ 48 dp, and text scales with the system font setting (`UI_CONVENTIONS.md` UI-10..UI-16).
- **KT-18** Tests: pure JVM unit tests for `core/domain` and ViewModels with a test dispatcher and turbine-style flow assertions; Compose UI tests for critical screens only.

## References — load only when the work needs them

| File | Load when |
|---|---|
| `references/compose-and-state.md` | building a screen, ViewModel, navigation, or state restoration |
| `references/offline-and-security.md` | local persistence, sync, token storage, or release hardening |

## Checks

```sh
./gradlew ktlintCheck detekt
./gradlew testDebugUnitTest
./gradlew assembleRelease
```
