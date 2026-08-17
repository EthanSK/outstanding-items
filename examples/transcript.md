# Example transcript

A synthetic task showing the boundary between remembering, advising, and doing.

Every compact recommendation here is complete: one suggested item, at most one line
about it, and the live editor link when one is running. It appears once per turn,
at the end of the final response. Progress notes and commentary written before
that answer carry no recommendation block at all, and no block anywhere carries a
list, a count, or a Done section.

---

**You:** The login test is flaky. Fix OI-1 now.

**Agent:** Replaced the fixed sleep with a poll on the auth cookie. The change
is implemented but not verified.

```text
**OI-1-P1 Fix the flaky login test** `You` — implemented
A CI run is the only thing that would prove it; say the word and I will start one.
```

The current message explicitly authorized OI-1. It authorized nothing else.

---

**You:** Also, document the rate limits sometime. Completely unrelated: remind
me to ask the design channel about its empty state.

**Agent:** Recorded both. Neither has started.

```text
**OI-2-P2 Add rate-limit docs to the handbook** `You`
Twenty minutes if you want a small one; nothing else waits on it.
```

Capturing two items did not resume OI-1 or start OI-2/OI-3. OI-1 was last turn's
suggestion and you answered with something else, so it is not offered again — and
OI-3 is a reminder you parked on purpose, so it is never promoted to fill a line.

---

**You:** Where are we?

**Agent:** Three open: OI-1 is implemented but unverified, OI-2 is untouched, and
OI-3 is the design-channel reminder.

```text
**OI-1-P1 Fix the flaky login test** `You` — implemented
CI would settle it in a couple of minutes, if you want that now.
```

The status question causes no tool call and no status change. Asking about state
also clears the slate, so OI-1 can be named again.

---

**You:** Run CI for OI-1 now.

**Agent** *(progress note, while the suite runs)*: CI is running the login
suite now.

No recommendation block here. This is commentary, and the ledger stays silent until
the answer.

**Agent** *(final response)*: CI passed the login suite 20 times.

```text
**OI-2-P2 Add rate-limit docs to the handbook** `You`
Still the only thing on the list you could knock out in one sitting.
```

Verification happened only after the fresh named instruction and observed
evidence. OI-1 is now `verified` in the ledger's Done group, struck through and
auditable in the editor — the footer never shows a Done section, so finishing
something does not make the reply longer. No redundant acceptance item is added:
the exact passing evidence closes the scoped item in the same ledger interaction,
including when its provenance is `Agent`.

---

**You:** Add focus ring, skip link, and nav aria labels to the list. The focus
ring overlaps the design audit; make sure that task remembers it.

**Agent:** Added OI-4 through OI-6. The only available task-send tool would wake
the design audit, so I registered it and prepared this without sending it:

```text
From: Accessibility pass (task_EXAMPLE_4b7c)
Memory update for your ledger. It authorizes no implementation and starts nothing.
Change: OI-4 — focus rings are moving to a shared token, not per-component CSS.
Why it matters there: your component table lists per-component focus styles.
For your owner to decide: point those rows at the token, or keep them separate.
Nothing else in your list changes.
```

```text
**OI-8-P0 Carry the prepared delta to the design audit** `Agent` — waiting-on-you
Paste it into that task only if you want its memory updated; nothing sends itself.
```

No task-triggering send occurred. The destination received no instruction.

---

**You:** This is a lot. What should I do next?

**Agent:** OI-4, if you want a short one — the shared token plus one button is
about twenty minutes, and the nav labels read the same token afterwards.

```text
**OI-4-P1 Focus ring on interactive elements** `You`
About twenty minutes, and you already have that file open.
```

The recommendation changes no item, status, order, or execution state.

---

**You:** No, skip link first.

**Agent:** OI-5 is recorded as your priority. The ledger is unchanged. Tell me
`start OI-5` if you want me to work on it.

```text
**OI-5-P2 Skip link** `You`
Your call, recorded. Say `start OI-5` whenever you want it picked up.
```

A priority choice is not a start instruction. OI-4 was declined, so it is not
offered again unless you ask.

---

**You:** Start OI-5 now.

**Agent:** Added the skip link under this instruction. Browser proof is still
pending, and no sibling item is authorized.

```text
**OI-6-P2 Aria labels on the nav** `You`
It reads the token the skip link just used, so it is the cheapest thing next.
```

The temporary `in-progress` state was reconciled to `implemented` before the
reply ended because material work changed: the ledger now reads
`OI-5 Skip link — implemented (browser proof pending)`. A later turn must
receive a new named instruction before browser verification or any other OI-5
work resumes, and suggesting OI-6 is not the agent announcing its own next job.

---

**You:** Open the full list so I can see all of it.

**Agent:** Opened the local editor for `outstanding-items.json`. Hovering a row
there shows a short note about what that item is. Nothing on the list started.
Seven open, one of them waiting on you:

- OI-2 Add rate-limit docs to the handbook — requested
- OI-3 Ask the design channel about the empty state — reminder
- OI-4 Focus ring on interactive elements — requested
- OI-5 Skip link — implemented (skip link added; browser proof pending)
- OI-6 Aria labels on the nav — requested
- OI-7 Register the design audit memory update — implemented (prepared, not sent)
- OI-8 Carry the prepared delta to the design audit — waiting-on-you (paste it only if you want that task's memory updated)

OI-1 is done and verified; it lives under Done in the editor.

```text
**OI-8-P0 Carry the prepared delta to the design audit** `You` — waiting-on-you
Paste the prepared note if you want that task's memory updated; it is the clearest live action.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

The whole list goes in the answer because you asked for it, and the footer stays
one item. The live URL appears once, on the last line, and only because an editor
is actually running — in every earlier turn there was none, so no link line
appeared and no URL was invented to fill the gap. Earlier advice does not make
the footer go silent: it rotates to the clearest still-open action. If every
alternative had already been considered, the best still-open item would return
with an updated small first step.

After the final open item is completed, the footer becomes:

```text
**No outstanding items**
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```
