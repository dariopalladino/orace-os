# Reference — Kotlin offline data, sync, and release hardening

Load for local persistence, sync, token storage, or release configuration.

## Local store as the screen's source of truth

```kotlin
class OrderRepositoryImpl(
    private val local: OrderDao,
    private val remote: OrderApi,
    private val io: CoroutineDispatcher,
) : OrderRepository {

    override fun observe(): Flow<List<Order>> = local.observeAll().map { it.map(OrderEntity::toDomain) }

    override suspend fun refresh(): Result<Unit> = withContext(io) {
        runCatching { remote.listOrders() }
            .onSuccess { local.upsertAll(it.map(OrderDto::toEntity)) }
            .map { }
    }
}
```

The screen observes the database; refresh is a separate, failable action (KT-16). This is what makes the app usable on a bad connection instead of showing a spinner over an empty list.

## Sync rules

- Outgoing changes are queued locally with a client-generated id and replayed with that id as the idempotency key (`API_DESIGN.md` API-04). A retried request must never create a second order.
- Every synced record carries a server version or `updatedAt`. Conflict policy is chosen explicitly — last-write-wins, server-wins, or merge — and stated in the proposal; an unstated policy means silent data loss.
- Sync runs in `WorkManager` with constraints and backoff, not in a `ViewModel` coroutine that dies with the screen.
- A failed sync is visible to the user, with a way to retry.

## Secure storage

```kotlin
val prefs = EncryptedSharedPreferences.create(
    context, "auth",
    MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
)
```

- Tokens, refresh tokens, and any credential go here or in the Keystore (KT-12). Plain `SharedPreferences`, a file, `BuildConfig`, or a log line are all disqualifying.
- Keys for high-value operations are generated in the Keystore with `setUserAuthenticationRequired(true)` where the product warrants biometric gating.
- Clear all local personal data on logout, including the database and any cached images.

## Network hardening

- TLS validation is never relaxed. A debug `TrustManager` must live in a `debug` source set so it cannot be compiled into a release (KT-13).
- Consider certificate pinning for high-value APIs, with at least one backup pin and a documented rotation plan — an expired pin bricks every installed client.
- Set OkHttp call, connect, read, and write timeouts explicitly (`NONFUNCTIONAL.md` NFR-01), and add a retry interceptor only for idempotent requests.
- Do not log request or response bodies in release builds.

## Release configuration

```kotlin
buildTypes {
    release {
        isMinifyEnabled = true
        isShrinkResources = true
        proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
    }
}
```

- Keep rules are maintained alongside reflection-using libraries; verify the release build runs the critical flows before shipping, because minification failures appear only there.
- `android:debuggable`, cleartext traffic, and exported components default to off. Every `exported="true"` component needs a permission and a stated reason.
- Backup rules exclude the encrypted auth store and any local personal data.
- Strip or gate any developer menu behind a build-type check, not a runtime flag.

## Permissions

Request at point of use with an in-context rationale, handle denial as a designed state, and never block the app on an optional permission (KT-14). Each permission in the manifest is justified in the proposal; a reviewer removing one should break nothing.
