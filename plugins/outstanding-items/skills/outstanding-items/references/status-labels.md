# Status labels

Full definitions, transitions, and anti-patterns for the nine labels in `SKILL.md`. Load when a status decision is not obvious, or when you are tempted to round one upwards.

**A label is a description, never a permission.** Nothing in this file authorizes work. What does: [authority.md](authority.md).

## Definitions and evidence

| Label | The item is… | Evidence you must be able to point at | Never use it when |
| --- | --- | --- | --- |
| `requested` | Wanted at some point, untouched. | The user's own words in this task. | You have already agreed an approach — that is `planned`. |
| `planned` | Decided, not started. | One sentence naming the approach. | The approach is still a question you are asking. |
| `in-progress` | Being worked on right now, under a live instruction. | The user's own start instruction, quoted in the note. | You inferred permission from the list, a ranking, or your own suggestion. |
| `implemented` | Changed, unproven. | The edit or action you performed in this task. | Someone else claims it is done and you did not see it. |
| `verified` | Proven to work. | Command output, a passing check, or user confirmation you observed now, or exact completion evidence already preserved in the canonical item and checked now. | It "should" work, compiles, or looks right. |
| `waiting-on-you` | Held up by the user in person. | The exact action they must take, in the note. | You could still do it yourself, under an instruction you already have. |
| `blocked` | Stopped by a real external wall. | The blocker **and** what you already tried, in the note. | You simply have not been asked to start, or the only obstacle is the user. |
| `reminder` | Deliberately parked, on purpose, indefinitely. | Nothing. | There is a live request or a deadline attached. |
| `dropped` | Deliberately abandoned. | Who decided, and why, in the note. | You quietly gave up. That is still open. |

The requested / planned / implemented / verified split exists to stop optimistic reporting. Four labels, four different amounts of proof. Collapsing them is one of the two failure modes this skill was written to prevent. The opposite error matters too: once exact recorded evidence proves the item's scoped outcome complete, leave no verified item open merely to obtain redundant acceptance.

## `in-progress` — the label most likely to be misread

`in-progress` means: the user named this item, told you to start it, and you are on it in this turn. Write their instruction into the note (`started on your "do the skip link now"`), so a later reader can see where the authority came from.

- It is not a claim on the future. When the turn ends, the authority ends with it.
- Resuming needs a fresh instruction naming the item. "It was already in progress" is not one.
- At the end of the authorized turn, reconcile the temporary label to evidence: use `implemented` if material work changed; `planned` if nothing changed but an agreed route exists; otherwise `requested`. Later resumption still needs a fresh named instruction.
- Never apply it to something you decided to start. If there is no instruction to quote, there is no `in-progress`.

## `waiting-on-you` versus `blocked`

These get confused constantly, and the confusion is expensive: `blocked` reads as "someone else's problem, nothing to do", while `waiting-on-you` reads as "thirty seconds of your time would move this".

Use `waiting-on-you` when the missing ingredient is the person you are talking to:

- a physical press, a plug, a device in their hand, a machine only they can reach
- an approval, a sign-off, a merge button, a deploy confirmation
- a choice only they can make — which option, which name, which trade-off
- a credential, a key, a token, a login, a permission grant
- acceptance of a change you already made and cannot verify yourself
- something you can only hand over, such as text they must carry into another conversation

Write the exact action in the note, in the imperative, so it can be done without re-reading the transcript: `waiting-on-you (click approve in the deploy UI)`, not `waiting-on-you (needs approval)`.

Use `blocked` only after you have exhausted the safe routes inside your scope, under an instruction you actually have:

- an upstream bug, an outage, a dependency that does not exist yet
- another team's work that has not landed
- something outside the boundaries you were given, where no in-scope workaround exists

`blocked` therefore carries two facts, not one: what stopped you, and what you already tried. A `blocked` item with no attempt behind it is usually a `requested` item nobody has asked you to start, or a `waiting-on-you` item you mislabelled.

**Neither label is an instruction to fix it.** An item can sit at `waiting-on-you` for a month. That is the user's business.

## `reminder` — the intentional reminder

A `reminder` is an item the user deliberately wants tracked, with no execution request and no deadline. "Remind me to ask the design channel about the empty state" is a reminder. "Ask the design channel today" is a request — and still not a licence to start it without a fresh instruction.

- Keep it visible in the ledger's **Intentional reminders** group. It is not a second-class item and it is never hidden to tidy the list.
- Do not start it. Do not ask clarifying questions about it unless invited.
- It never moves to Done on its own. Only the user retires it, by acting on it or dropping it.
- Keep it behind ordinary actionable work. If it is the only active unfinished item, it may be the footer's recommendation without changing its `reminder` status; recommending it still grants no permission and invents no urgency.
- Do not editorialise about how long it has been sitting there. That is the point of it.

An item that is merely unrelated to the current work is not automatically a `reminder`. If the user wants it done eventually and just mentioned it out of order, it is `requested` with a note such as `(unrelated to current work)`. The difference is whether they want it done, not whether it fits the current topic.

## Legal transitions

```text
requested ──▶ planned ──▶ in-progress ──▶ implemented ──▶ verified ──▶ Done
     │            │             │               │
     ├────────────┴─────────────┴───────────────┴──▶ waiting-on-you ──▶ (returns to its previous label)
     ├────────────┴─────────────┴───────────────┴──▶ blocked ─────────▶ (returns to its previous label)
     │
     ├──▶ reminder ──▶ requested (when the user asks for it, or urgency arrives)
     │
     └──▶ dropped ──▶ Done (struck through, labelled dropped)
```

- Move forward one rung at a time while work is unfolding. Never claim `planned` became `verified` without the evidence for the missing stages. When the recorded label itself is stale but exact preserved evidence proves the scoped outcome complete, reconcile the record directly to `verified` and Done; do not manufacture intermediate history.
- Only a fresh explicit instruction moves anything into `in-progress`. Evidence reconciliation may retire work that was already completed, but it never changes execution state or performs unfinished work.
- Backwards is honest and expected: a failing check can move `implemented` → `blocked`; an ended turn reconciles `in-progress` to `implemented`, `planned`, or `requested` according to the evidence above.
- `waiting-on-you` and `blocked` both remember where they came from. When the obstacle clears, the item returns to the label it had — not to `in-progress`.
- Only `verified` and `dropped` reach Done. Nothing else leaves the open list, and `reminder` never gets there without the user.
- Reconcile completion on every ledger interaction. Trust exact test output, receipts, or user confirmation already recorded in the item as evidence; do not trust a title, an optimistic state word, or an unsupported claim. Moving proven work to Done is record maintenance, not permission to perform unfinished work.
- Apply the same evidence rule to every provenance. In particular, close proven `agent-added` work automatically instead of converting it into `waiting-on-you` merely to ask whether the user agrees it is finished.

## Notes

Notes are optional for most labels and mandatory for `in-progress`, `blocked`, `dropped`, and `waiting-on-you`.

- Keep them to roughly ten words.
- Facts only: what blocks it, who dropped it, what the check was, which instruction started it.
- Do not use notes to smuggle in status. `— implemented (basically done)` is not a thing.
- Never put secrets, tokens, credentials, file contents, or personal identifiers into a note.

## Where a status shows up

The compact recommendation names one item, so a status no longer decides which chat section an item lands in. It decides how the item reads in the Full outstanding items view, and whether the item can be the one the recommendation suggests.

- Grouping in the ledger and its UI is mechanical: `waiting-on-you` → **Waiting on you**, `reminder` → **Intentional reminders**, every other open item → **Outstanding for you**, `verified` and `dropped` → **Done**, and anything with `tracking_state=transferred` → the read-only **Owned elsewhere** group.
- Eligible to be suggested: any open item the user could pick up now, including `waiting-on-you`; an intentional reminder becomes a fallback only when no ordinary actionable item remains.
- Never suggest a `blocked` parent directly. Capture its nearest useful prerequisite, workaround, decision, or time/condition-bound follow-up as a separate open item and recommend that, or choose another actionable item. A `transferred` record is owned elsewhere and is not active here.
- The footer carries no counts, no section headings, and no overflow row. Nothing is ever trimmed by dropping items, because nothing is listed there in the first place.
- When the user wants the whole list, give it to them in the body of that reply or open the UI — see [backlog-artifact.md](backlog-artifact.md).

## Anti-patterns

| Tempting | Why it is wrong | Do this instead |
| --- | --- | --- |
| Marking everything `verified` at the end | Nothing was checked; the ledger becomes decorative. | Verify what you can, leave the rest `implemented`. |
| Leaving proven agent-added work open for acceptance | It manufactures work for the user after the result is already checked. | Preserve the evidence and move it to Done automatically. |
| Using `in-progress` to justify carrying on | The label was a description of a turn that has ended. | Reconcile it to evidence, then wait for a fresh named instruction. |
| Labelling something `in-progress` because it is next | Nobody said start. | Leave it `planned` and suggest it. |
| Deleting a finished item | The user loses the audit trail. | Move it to Done, struck through. |
| Renumbering after deletions | Breaks every earlier reference in the transcript. | IDs are permanent, gaps are fine. |
| Rewording a title to sound better | The user searches for their own phrasing. | Keep their words. |
| Merging two items silently | One request disappears. | Keep both, or merge and say so once. |
| Inventing items you think are needed | The ledger stops being the user's. | Suggest it in prose; add it only if they agree. |
| Leaving `blocked` without a blocker | Unactionable. | Name the blocker or pick a different label. |
| Marking `dropped` because the user went quiet | Silence is not cancellation. | Leave it open and ask. |
| Calling it `blocked` when you need a click from the user | It reads as nothing-to-be-done, so it gets ignored for days. | `waiting-on-you`, with the exact action in the note. |
| Turning a `reminder` into `requested` to make the list look active | Rewrites what the user asked for. | Keep the status; it may be a fallback recommendation without being promoted. |
| Promoting an item's status to justify starting it | Status is a description; this would make it a permission slip. | Leave the status alone and ask. |
