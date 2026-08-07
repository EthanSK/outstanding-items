# Delta messages

Cross-task updates are memory only. They never wake a destination, never carry
an execution request, and never change an item's status. All identifiers below
are synthetic.

## Well formed

### Scope change

```text
From: Accessibility pass (task_EXAMPLE_4b7c)
Memory update for your ledger. It authorizes no implementation and starts nothing.
Change: OI-4 — focus rings are moving to a shared token, not per-component CSS.
Why it matters there: your component table lists per-component focus styles.
For your owner to decide: point those rows at the token, or keep them separate.
Nothing else in your list changes.
```

### Obstacle removed

```text
From: API migration (task_EXAMPLE_2a70)
Memory update for your ledger. It authorizes no implementation and starts nothing.
Change: OI-12 — the v2 rate-limit endpoint is live in staging.
Why it matters there: your OI-5 was waiting on it.
For your owner to decide: whether and when to resume OI-5.
Nothing else in your list changes.
```

### Invalidated assumption

```text
From: Checkout rebuild (task_EXAMPLE_8f31)
Memory update for your ledger. It authorizes no implementation and starts nothing.
Change: OI-6 — guest checkout is staying, not being removed.
Why it matters there: your test plan assumes a single authenticated path.
For your owner to decide: whether the guest path needs separate cases.
Nothing else in your list changes.
```

## Malformed

| Message | What breaks |
| --- | --- |
| "Here's my current list: OI-1 … OI-14." | Dumps the whole ledger. |
| "Update your list: drop item 3, move item 5 to the top." | Manages the destination's scope. |
| "You can start OI-5 now." | Converts a memory update into execution authority. |
| "Requested: point those rows at the token." | Aims an imperative at the destination agent. |
| "The design audit says the token approach is wrong." | Relays third-task hearsay. |
| "Re: your note — agreed." | Echoes a delta back toward its origin. |
| "See `~/work/notes/scratch.md`." | Leaks a private path and unavailable context. |

## Checklist before delivery

1. Is it exactly one relevant scope change, removed obstacle, invalidated
   assumption, or user-requested memory update?
2. Is the mandatory second line present verbatim?
3. Does it cite one stable `OI-n`?
4. Does it contain no work order, imperative to the agent, status promotion,
   removal, reordering, or claim that the destination may start?
5. Does it say the rest of the destination's scope is untouched?
6. Is the de-duplication hash absent from the destination registry's `Sent`
   column, and is this not an inbound echo?
7. Can the harness deliver it without starting a turn? If not, mark it
   `prepared (not sent)` and hand the text to the user.

## Honest delivery wording

No memory-only tool:

> Registered **Design system audit** (`task_EXAMPLE_8f31`). This harness cannot
> leave a note without starting that task, so the delta is prepared but not
> sent. You may paste the block above if you want its memory updated.

Failed memory-only write:

> The memory write to **Design system audit** failed: `task is archived`. I
> kept the registry row, did not retry, and preserved the exact prepared text.

Never claim `sent (memory)` unless a non-triggering memory write returned
success.
