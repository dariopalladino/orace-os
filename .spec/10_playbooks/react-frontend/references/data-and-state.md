# Reference — React data, state, and forms

Load when adding queries or mutations, caching, optimistic updates, or forms.

## Where each kind of state belongs

| Kind | Home | Example |
|---|---|---|
| Server state | server-state library cache | orders list, current user profile |
| URL state | the router | filters, pagination, selected tab |
| Form state | form library, local to the form | draft values, validation errors |
| Ephemeral UI state | `useState` in the owning component | dropdown open, hover |
| Global client state | a store, rarely | theme, feature flags, unsaved multi-step wizard |

Copying server data into a global store (RX-03/RX-04) creates a second cache you must invalidate by hand. It is the single most common source of stale-UI bugs.

## Query keys and invalidation

```ts
export const orderKeys = {
  all: ['orders'] as const,
  list: (filters: OrderFilters) => [...orderKeys.all, 'list', filters] as const,
  detail: (id: string) => [...orderKeys.all, 'detail', id] as const,
}

export function useOrders(filters: OrderFilters) {
  return useQuery({
    queryKey: orderKeys.list(filters),
    queryFn: ({ signal }) => api.listOrders(filters, { signal }),
    staleTime: 30_000,
  })
}
```

A key factory keeps invalidation honest: `invalidateQueries({ queryKey: orderKeys.all })` after a mutation that can affect any order. Passing the `AbortSignal` through means a superseded request is actually cancelled.

## Mutations and optimistic updates

```ts
useMutation({
  mutationFn: api.cancelOrder,
  onMutate: async (id) => {
    await queryClient.cancelQueries({ queryKey: orderKeys.detail(id) })
    const previous = queryClient.getQueryData(orderKeys.detail(id))
    queryClient.setQueryData(orderKeys.detail(id), (o) => ({ ...o, status: 'cancelling' }))
    return { previous }                                   // RX-08 rollback context
  },
  onError: (_err, id, ctx) => queryClient.setQueryData(orderKeys.detail(id), ctx?.previous),
  onSettled: (_d, _e, id) => queryClient.invalidateQueries({ queryKey: orderKeys.detail(id) }),
})
```

Every optimistic update needs all three handlers. Two out of three leaves the UI lying after a failure (UI-08).

## Generated API types

```sh
npx openapi-typescript ../contracts/openapi.yaml -o src/shared/api/schema.d.ts
```

Run this in CI and fail on a diff. A hand-written `interface Order` will drift from the server within a sprint (RX-02, PRIN-02).

## Forms

```ts
const schema = z.object({
  email: z.string().email(),
  amountMinor: z.number().int().positive(),
})

const form = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) })
```

- Validate on blur and on submit, not on every keystroke — per-keystroke errors punish people mid-word.
- Map server-side field errors back onto the matching fields; a generic banner for a field-level failure forces the user to hunt.
- Never clear the form on a failed submit (UI-09).
- Disable submit only while the request is in flight, and say why in the button label.

## Effects

```ts
// wrong — derived state through an effect (RX-06)
useEffect(() => { setTotal(items.reduce(sum, 0)) }, [items])

// right — derive during render
const total = useMemo(() => items.reduce(sum, 0), [items])
```

Reach for `useEffect` only to synchronise with something outside React: a subscription, a DOM measurement, an analytics event, a timer. Every other use is usually a render-time computation in disguise.

## Error boundaries

Wrap each route with an error boundary and give the fallback a retry that resets the boundary and refetches. An uncaught render error that blanks the whole app is a defect, not an edge case (RX-05).
