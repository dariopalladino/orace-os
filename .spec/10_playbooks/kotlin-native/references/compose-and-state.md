# Reference — Compose screens, state, and navigation

Load when building a screen, ViewModel, navigation graph, or state restoration.

## One immutable state type per screen

```kotlin
data class OrderListUiState(
    val orders: ImmutableList<OrderUi> = persistentListOf(),
    val isLoading: Boolean = false,
    val error: UiText? = null,
) {
    val isEmpty: Boolean get() = !isLoading && error == null && orders.isEmpty()
}
```

Model loading, empty, error, and content explicitly (KT-04). A nullable list standing in for "not loaded yet" forces every composable to guess.

```kotlin
@HiltViewModel
class OrderListViewModel @Inject constructor(
    private val observeOrders: ObserveOrders,
    private val savedState: SavedStateHandle,
) : ViewModel() {

    private val _state = MutableStateFlow(OrderListUiState())
    val state: StateFlow<OrderListUiState> = _state.asStateFlow()

    private val _events = Channel<OrderListEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()          // KT-06: one-off, never replayed

    init {
        viewModelScope.launch {
            observeOrders()
                .onStart { _state.update { it.copy(isLoading = true) } }
                .catch { t -> _state.update { it.copy(isLoading = false, error = t.toUiText()) } }
                .collect { orders -> _state.update { it.copy(isLoading = false, orders = orders) } }
        }
    }
}
```

The ViewModel never touches Android UI types, and the use case never knows a ViewModel exists.

## Composables receive state, emit events

```kotlin
@Composable
fun OrderListRoute(viewModel: OrderListViewModel = hiltViewModel(), onOpen: (OrderId) -> Unit) {
    val state by viewModel.state.collectAsStateWithLifecycle()   // KT-05
    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) { is OrderListEvent.Open -> onOpen(event.id) }
        }
    }
    OrderListScreen(state = state, onOrderClick = viewModel::onOrderClick)
}

@Composable
fun OrderListScreen(state: OrderListUiState, onOrderClick: (OrderId) -> Unit) { /* stateless */ }
```

Keeping the stateless `OrderListScreen` separate is what makes previews and UI tests cheap.

## Stability and recomposition

- Prefer immutable types in state (`kotlinx.collections.immutable`). A plain `List` is treated as unstable and defeats skipping.
- Pass lambdas as stable references (`viewModel::onOrderClick`) rather than newly allocated lambdas capturing changing values.
- In `LazyColumn`, always supply a stable `key = { it.id }`, or scroll position and animations break on update.
- Defer reads of frequently changing state into the smallest possible scope (lambda-based modifiers) so recomposition does not climb the tree.
- Never mutate state during composition and never launch work outside `LaunchedEffect`/`rememberCoroutineScope` (KT-07).

## Navigation and process death

```kotlin
// survives process death; a plain ViewModel field does not (KT-15)
var query by savedState.saveable { mutableStateOf("") }
```

- Pass identifiers through navigation arguments, not whole objects.
- Test restoration: `StateRestorationTester` in Compose tests, and verify with "Don't keep activities" enabled.
- Deep links declare their arguments and validate them; a malformed deep link must not crash or bypass an auth gate.

## Errors

Domain failures map to a `UiText` (a string resource id plus arguments), never a raw exception message. An exception surfaces as UI state; an unhandled one in a coroutine crashes the process (KT-09).

## Tests

```kotlin
@Test
fun `emits empty state when repository returns nothing`() = runTest {
    val viewModel = OrderListViewModel(observeOrders = { flowOf(emptyList()) }, savedState = SavedStateHandle())
    viewModel.state.test {
        assertTrue(awaitItem().isLoading.not() || awaitItem().isEmpty)
    }
}
```

Inject the dispatcher so tests use `StandardTestDispatcher` (KT-08). Reserve Compose UI tests for the few screens whose interaction genuinely carries risk.
