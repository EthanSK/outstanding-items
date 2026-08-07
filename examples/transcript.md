# Example transcript

A synthetic task showing the boundary between remembering, advising, and doing.

This teaching transcript sometimes shows only the changed portion of a reply for brevity. In real use, every user-facing reply still ends with the complete applicable Outstanding footer.

---

**You:** The login test is flaky. Fix OI-1 now.

**Agent:** Replaced the fixed sleep with a poll on the auth cookie. The change
is implemented but not verified.

```text
**Outstanding** (1 for you)

**Outstanding for you**
- OI-1 Fix the flaky login test — implemented
```

The current message explicitly authorized OI-1. It authorized nothing else.

---

**You:** Also, document the rate limits sometime. Completely unrelated: remind
me to ask the design channel about its empty state.

**Agent:** Recorded both. Neither has started.

```text
**Outstanding** (2 for you · 1 reminder)

**Outstanding for you**
- OI-1 Fix the flaky login test — implemented
- OI-2 Add rate-limit docs to the handbook — requested

**Intentional reminders**
- OI-3 Ask the design channel about the empty state — reminder
```

Capturing two items did not resume OI-1 or start OI-2/OI-3.

---

**You:** Where are we?

**Agent:** OI-1 is implemented but unverified; OI-2 and OI-3 are untouched.

The status question causes no tool call and no status change.

---

**You:** Run CI for OI-1 now.

**Agent:** CI passed the login suite 20 times.

```text
**Outstanding** (1 for you · 1 reminder · 1 done)

**Outstanding for you**
- OI-2 Add rate-limit docs to the handbook — requested

**Intentional reminders**
- OI-3 Ask the design channel about the empty state — reminder

**Done**
- ~~OI-1 Fix the flaky login test~~ — verified (CI green 20/20)
```

Verification happened only after the fresh named instruction and observed
evidence.

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
**Outstanding** (5 for you · 1 waiting on you · 1 reminder · 1 done)

**Outstanding for you**
- OI-2 Add rate-limit docs to the handbook — requested
- OI-4 Focus ring on interactive elements — requested
- OI-5 Skip link — requested
- OI-6 Aria labels on the nav — requested
- OI-7 Register the design audit memory update — implemented (prepared, not sent)

**Waiting on you**
- OI-8 Carry the prepared delta to the design audit — waiting-on-you (paste it only if you want that task's memory updated)

**Intentional reminders**
- OI-3 Ask the design channel about the empty state — reminder

**Done**
- ~~OI-1 Fix the flaky login test~~ — verified (CI green 20/20)
```

No task-triggering send occurred. The destination received no instruction.

---

**You:** This is a lot. What should I do next?

**Agent:** **Suggested for you** — OI-4, about twenty minutes: add the shared
token and check one button. It also clarifies OI-6. Tell me `start OI-4` if you
want me to do it.

```text
**Outstanding for you**
- OI-4 Focus ring on interactive elements — requested
- OI-5 Skip link — requested
- OI-6 Aria labels on the nav — requested
```

The recommendation changes no item, status, order, or execution state.

---

**You:** No, skip link first.

**Agent:** OI-5 is recorded as your priority. The ledger is unchanged. Tell me
`start OI-5` if you want me to work on it.

A priority choice is not a start instruction.

---

**You:** Start OI-5 now.

**Agent:** Added the skip link under this instruction. Browser proof is still
pending, and no sibling item is authorized.

```text
**Outstanding for you**
- OI-4 Focus ring on interactive elements — requested
- OI-5 Skip link — implemented (skip link added; browser proof pending)
- OI-6 Aria labels on the nav — requested
```

The temporary `in-progress` state was reconciled to `implemented` before the
reply ended because material work changed. A later turn must receive a new
named instruction before browser verification or any other OI-5 work resumes.
