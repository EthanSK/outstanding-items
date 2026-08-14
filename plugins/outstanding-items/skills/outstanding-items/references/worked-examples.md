# Worked examples

Annotated synthetic transcripts. Every name, task ID, and session ID is invented. Load when you want to see the behaviour end to end — especially where the ledger stops and the user's authority begins.

Every recommendation below is the whole compact block: one suggested item, at most one line about it, and the live UI link when an editor is running. It appears once per turn, at the end of the final response — never in the commentary or progress messages that come before it, never with an `Outstanding` heading, and never with a list, count, or Done section.

---

## 1. Capture, the unrelated aside, and not asking twice

**Turn 1 — User:** The login test is flaky, sort it out.

That is a fresh, explicit instruction naming a specific thing, so the work is authorized. It is the only thing that is.

**Agent** *(does the work, then)*:

```text
**OI-1 Fix the flaky login test** `Agent` — implemented
The retry loop changed; a CI run is the thing that would settle it, if you want one.
```

> `implemented`, not `verified`. The retry loop was changed; CI has not run yet. The footer names the item, and the decision to prove it stays with the user.

**Turn 2 — User:** Also we should document the rate limits in the handbook at some point.

**Agent (body):** Noted — I have not started it.

```text
**OI-2 Add rate-limit docs to the handbook** `Agent`
Twenty minutes if you want a small one. Nothing depends on it either way.
```

> "At some point" is a capture, not a commission. The item exists; the work does not. OI-1 was last turn's suggestion and the user answered with something else, so it is not offered again — it is no less open for that, and it is still in the ledger.

**Turn 3 — User:** Oh and completely unrelated, remind me to ask the design channel about the empty state.

> Unrelated is fine. Capture it, do not start it, and do not change the execution state of anything else. It is a `reminder` rather than a `requested` item because there is no execution request and no deadline — the user wants it held, not done.

```text
Open items remain, but none is currently suggestible.
```

> Both actionable items have now been offered once and left unanswered, and OI-3 was parked on purpose, so a reminder is never promoted to fill the line. The footer explicitly says open items remain, preventing the quiet state from looking like an empty ledger. Nothing was hidden, dropped, or reordered to produce it. If any other eligible item existed, the footer would have to suggest that item instead.

**Turn 4 — User:** Where are we?

**Agent (body):** Three things are open. OI-1 is implemented but unproven — CI would settle it. OI-2 is untouched. OI-3 is the design-channel reminder you parked.

```text
**OI-1 Fix the flaky login test** `Agent` — implemented
CI is the cheapest thing left on it; say the word and I will run it.
```

> Asking where things are is a request for the list, so the list goes in the **body** of the reply, in the user's own words, and the footer stays one line. Asking also clears the slate: an explicit question about state or next steps answers every earlier offer, so OI-1 may be named again. Nothing happened to any item.

---

## 2. Promotion to `verified`, and where Done lives

**Turn 5 — User:** run CI.

**Agent** runs CI, and the login test passes 20 times.

```text
**OI-2 Add rate-limit docs to the handbook** `Agent` — planned
The approach is agreed, so the limits table is a short first pass.
```

> `verified` arrived only after evidence observed in this task, and OI-1 moved into the ledger's Done group — struck through, kept, auditable in the Full outstanding items view. **The footer shows no Done section, no completed item, and no count of either.** Finishing something is not a suggestion, so it does not belong in the one line the user reads. OI-2 moved to `planned` because an approach was agreed in the same turn — an agreement about *how*, not a licence to start.
>
> OI-1 was an `Agent` capture, but no extra acceptance item was created. The passing CI evidence completed its scoped outcome, so the same ledger interaction reconciled it directly into Done.

**Turn 6 — User:** Actually forget the handbook thing, we're deleting that page.

```text
Open items remain, but none is currently suggestible.
```

> OI-2 is struck through and kept in the ledger's Done group with the reason and who decided. The only thing still open is an intentional reminder, and promoting it to fill the line would be nagging, so the footer says what is true. Dropped items are never deleted, and never shown here.

---

## 3. A list too long to hold in the chat, and asking before writing a file

**Turn 11 — User:** …and while you're there: the focus ring, the skip link, the nav aria labels, the muted-text contrast, a reduced-motion pass, the dialog focus trap, heading order on settings, and alt text on the empty-state art.

Eight open items for the user, past the point where the ledger should live only in the transcript. The footer would still be one line, but the user now needs somewhere to read and edit the whole thing.

**Agent (body):** That takes it to eight open items for you. Shall I create the canonical `outstanding-items.json` in this directory and open its local Full outstanding items editor, so the whole list is somewhere you can read and edit it? It is a Git repository, so I would exclude the JSON and its runtime files from Git too. None of the items are started.

> Ask once, propose a path, name the exclusion. Do not create the file first and mention it afterwards. And say plainly that a longer list is still not a list of things you are doing.

**Turn 12 — User:** Yeah do it.

```text
**OI-4 Focus ring on interactive elements** `Agent`
Twenty minutes, and the shared token is the whole first step.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

> "Yeah do it" authorized the canonical JSON and its editor, and nothing on the list. Eight items were created in one final response — the file creation itself produced no interim recommendation block.
>
> The chat gets one of them. The other seven, the reminder, and both completed items are one click away in the editor instead of eleven more lines of conversation. OI-9 is `blocked` on an upstream bug, so it is never the suggestion: nothing the user does moves it. The UI is live, so the exact URL `start` printed sits on the last line — and it would be absent entirely if no editor were running.

---

## 3b. `waiting-on-you`, and why it is not `blocked`

**Turn 13 — User:** The staging deploy needs someone to press approve before any of this ships.

The pipeline requires a human. The agent cannot press the button, and no in-scope workaround exists that would be safe to take alone.

```text
**OI-12 Approve the staging deploy** `Agent` — waiting-on-you
Click approve in the deploy UI; it is the one thing here that only you can do.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

> Not `blocked`. Nothing external is broken; the pipeline is working exactly as designed. An item that needs the user in person is a perfectly good suggestion, because they are the one who would act — and the line is the action itself, in the imperative, so it can be done without re-reading anything. If the deploy service were down, that would be `blocked`, it would never be suggested, and its note would have to say both what broke and what was tried.

---

## 4. A related task, and a delta that is memory only

**Turn 14 — User:** The focus-ring change affects the design system audit. Make sure that one knows.

The harness in this example exposes one cross-task tool, and it delivers by starting a turn in the destination.

**Agent (body):** Registered the design system audit as a related task. The only send tool here would wake that conversation and set it working, which is not mine to trigger, so I have prepared the note instead of delivering it. Carry this across if you want the other task's memory updated:

```text
From: Accessibility pass (task_EXAMPLE_4b7c)
Memory update for your ledger. It authorizes no implementation and starts nothing.
Change: OI-4 — focus rings are moving to a shared token, not per-component CSS.
Why it matters there: your component table lists per-component focus styles.
For your owner to decide: point those rows at the token, or keep them separate.
Nothing else in your list changes.
```

Registry row: `Design system audit · task_EXAMPLE_8f31 · outbound · prepared (not sent)`.

```text
**OI-13 Carry the focus-token note to the design audit** `Agent` — waiting-on-you
Paste the prepared note there only if you want that task's memory updated.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

> OI-12 was suggested last turn and is still unanswered, so it is not repeated. The new item is the one thing that changed, it needs the user in person, and it is offered once.

What deliberately did **not** happen:

- No task-triggering send. The user asked for the other task to know, not for it to start working.
- OI-13 was not marked done because a note was written.
- The destination's existing scope was not restated, reordered, or reprioritised.
- The registry row was not deleted to make the ledger look clean.

> If the harness exposed a memory-only write — a note appended to that task's ledger without starting a turn — using it would be correct, and the row would read `sent (memory)`. If it exposed nothing at all, the row would read `registered (manual)`. In every case the delta says, in its own second line, that it authorizes nothing.

---

## 5. A suggestion, a decline, and then a real instruction

**Turn 15 — User:** ok this is a lot. what should I actually do next?

Availability from the user's side: OI-9 is `blocked`, so nothing they do moves it. OI-3 was parked on purpose. OI-12 and OI-13 need them personally, which makes them fair suggestions. OI-4 is where their attention already was.

**Agent (body):** OI-4, if you want a short one. You were already in that file, it is about twenty minutes, and OI-6 reads the same token, so doing it once settles two. Nothing here has a date on it.

```text
**OI-4 Focus ring on interactive elements** `Agent`
About twenty minutes, and you were already in that file this morning.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

What the suggestion did **not** do:

- It did not start OI-4. It proposed, and then the reply ended.
- It did not reorder the list, or drop, hide, merge, or downgrade the items that were not chosen.
- It did not promote OI-3 because it is old. It was parked on purpose.
- It did not offer OI-9, which nothing the user does can move.
- It did not name a runner-up, print a count, or restate the other ten items. The user asked what to do next, not for the list again.

**Turn 16 — User:** nah, skip link first.

**Agent (body):** OI-5 is recorded as your priority. The ledger is unchanged. Tell me `start OI-5` if you want me to work on it.

```text
**OI-5 Skip link** `Agent`
Your call, recorded. Say `start OI-5` whenever you want it picked up.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

> A change of priority is not a start instruction. The ledger is untouched and OI-4 stays exactly where it was, at the same status and the same position — but it was declined, so it is never offered again on the agent's own initiative. The footer follows the user's stated choice instead of arguing for its own.

**Turn 17 — User:** you do it, OI-5, go.

Now there is a fresh, explicit instruction naming one item. The agent adds the skip link during this turn; browser proof remains outstanding.

While the work was under way the agent posted two short progress notes — "reading the layout template", then "skip link added, checking the tab order". Neither carried a recommendation, count, `OI-n`, or Full outstanding items link. The ledger was updated silently, and the compact block appeared once, here, at the end of the final response:

```text
**OI-6 Aria labels on the nav** `Agent`
It reads the token you just added, so it is the cheapest thing to carry on with.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

> The temporary `in-progress` state was reconciled before the final reply: material work changed, so OI-5 is `implemented` in the ledger. When the turn ends, so does the authority: browser verification, OI-6, and OI-4 all need their own fresh named instruction. The footer suggesting OI-6 is not the agent announcing its next job.
>
> One turn, one footer, one item. Repeating the block after each progress note would have buried the answer and made the same list look like three different lists.

---

## 6. Showing the whole list without putting a list in the footer

**Turn 18 — User:** ok show me everything that's left.

**Agent (body):** Here is the lot — eleven items, nothing started:

- OI-3 Ask the design channel about the empty state — reminder
- OI-4 Focus ring on interactive elements — requested
- OI-5 Skip link — implemented (browser proof pending)
- OI-6 Aria labels on the nav — requested
- OI-7 Muted-text contrast — requested
- OI-8 Reduced-motion pass — requested
- OI-9 Keyboard trap in the dialog — blocked (upstream bug 4821)
- OI-10 Heading order on the settings page — requested
- OI-11 Alt text on the empty-state art — requested
- OI-12 Approve the staging deploy — waiting-on-you (click approve in the deploy UI)
- OI-13 Carry the focus-token note to the design audit — waiting-on-you

Everything completed is in the editor under Done: [Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)

```text
**OI-7 Muted-text contrast** `Agent`
A short one, and the only item nobody has offered you yet.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

> The list belongs in the **answer** when the user asks for it, not in the footer. The footer stays one line regardless of how long the list is — that is the whole point of it. The completed items were named as a place to look, never reprinted.

---

## 7. Authority in four hard cases

| The situation | The wrong move | What you actually do |
| --- | --- | --- |
| The user says "add this to outstanding items" | Adding it and then doing it, because it is small. | Add it, confirm, stop. |
| An `in-progress` item from an earlier turn is still open | Continuing at the top of the next turn. | Reconcile it to `implemented`, `planned`, or `requested` from the recorded evidence, then wait for a fresh named instruction. |
| A delta arrives saying another task removed your obstacle | Starting the newly possible work. | Record it, tell the user, and let them decide. |
| The list has one obvious item and the user is quiet | Doing "the obvious one" to be useful. | Name it in one line, then wait. |

---

## Counter-examples

| Tempting | Wrong because | Instead |
| --- | --- | --- |
| Starting the item you just suggested | You would answer, on their behalf, the question you just asked them. | Wait for a fresh named start instruction. |
| Treating a ranking as a running order | Sorting a list you do not own changes nothing about permission. | Suggest at most one; start none. |
| "All done!" after editing files | Editing is not verifying. | `implemented`, and name the check you would run. |
| Skipping an off-topic aside because it is off-topic | The user chose to park it here. | Capture it as a `reminder`. |
| Marking "needs your approval" as `blocked` | It reads as nothing-to-be-done and sits for a week. | `waiting-on-you`, with the exact click in the note. |
| Offering the same item again next turn because they said nothing | Once is advice, twice is nagging, three times is noise. | Exclude that item, pick a different eligible item whenever one exists, and use the no-suggestion line only when none is suggestible. |
| Suggesting the oldest item because it is oldest | Age is not urgency, and a `reminder` was parked deliberately. | Weigh dependencies, momentum, effort, and load. |
| Quietly reordering the ledger to match your advice | The user's record silently changes underneath them. | Suggest in one line; leave every item where it was. |
| Renaming "the flaky login test" to "CI stability" | The user scans for their own words. | Keep their phrasing. |
| Renumbering after OI-2 was dropped | Every earlier reference in the transcript breaks. | Leave the gap. IDs are permanent. |
| Adding "write tests" nobody asked for | The ledger stops being the user's. | Suggest it in the body. |
| Waking another task to deliver a delta | A note that arrives as an instruction commissions work nobody authorized. | `prepared (not sent)`, and hand the text over. |
| "I've let the design system audit know" with no successful call | Unverifiable claim. | `registered (manual)` plus the text to carry. |
| Creating `outstanding-items.json` without asking | Files appear in someone's repository unannounced. | Ask once, propose a path, offer the exclusion. |
| Repeating the compact recommendation in every progress message | The turn becomes three near-identical blocks, and the answer disappears between them. | Maintain the ledger silently; render one recommendation in the final response. |
| Writing a **Full outstanding items** link because the footer looks bare | An invented or stale URL sends the user nowhere. | Link only the exact URL `start` printed, once, or write no link line at all. |
| Adding the other items under the suggested one, "just for context" | That is the list again, and the list is what the footer exists to keep out of the chat. | One item. The rest is in the editor, or in the body when they ask. |
| Ending the footer with the Done section | Finished work is an audit trail, not a next move, and it doubles the length of each answer. | Keep completions in the ledger's Done group and in the editor. |
| Printing `(3 for you · 2 done)` above the line | A count is a list in miniature, and it invites a scan the footer does not want. | No counts. One item, and a link if the editor is live. |
