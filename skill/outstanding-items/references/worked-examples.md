# Worked examples

Annotated synthetic transcripts. Every name, task ID, and session ID is invented. Load when you want to see the behaviour end to end — especially where the ledger stops and the user's authority begins.

Some teaching excerpts below show only the changed portion of a reply for brevity. In real use the complete applicable Outstanding footer appears once per turn, at the end of the final response — never in the commentary or progress messages that come before it.

---

## 1. Capture, including the unrelated aside

**Turn 1 — User:** The login test is flaky, sort it out.

That is a fresh, explicit instruction naming a specific thing, so the work is authorized. It is the only thing that is.

**Agent** *(does the work, then)*:

```text
**Outstanding** (1 for you)

**Outstanding for you**
- OI-1 Fix the flaky login test — implemented
```

> `implemented`, not `verified`. The retry loop was changed; CI has not run yet.

**Turn 2 — User:** Also we should document the rate limits in the handbook at some point.

**Agent (body):** Noted — I have not started it.

```text
**Outstanding** (2 for you)

**Outstanding for you**
- OI-1 Fix the flaky login test — implemented
- OI-2 Add rate-limit docs to the handbook — requested
```

> "At some point" is a capture, not a commission. The item exists; the work does not.

**Turn 3 — User:** Oh and completely unrelated, remind me to ask the design channel about the empty state.

> Unrelated is fine. Capture it, do not start it, and do not change the execution state of anything else. It is a `reminder` rather than a `requested` item because there is no execution request and no deadline — the user wants it held, not done.

```text
**Outstanding** (2 for you · 1 reminder)

**Outstanding for you**
- OI-1 Fix the flaky login test — implemented
- OI-2 Add rate-limit docs to the handbook — requested

**Intentional reminders**
- OI-3 Ask the design channel about the empty state — reminder
```

**Turn 4 — User:** Where are we?

**Agent (body):** Login fix is in but unproven — CI would settle it. The other two are untouched.

> The answer is the footer. One sentence in the body, then the ledger. Asking where things are is not asking for anything to happen, so nothing happens.

---

## 2. Promotion to `verified`, and the Done section

**Turn 5 — User:** run CI.

**Agent** runs CI, and the login test passes 20 times.

```text
**Outstanding** (1 for you · 1 reminder · 1 done)

**Outstanding for you**
- OI-2 Add rate-limit docs to the handbook — planned

**Intentional reminders**
- OI-3 Ask the design channel about the empty state — reminder

**Done**
- ~~OI-1 Fix the flaky login test~~ — verified
```

> `verified` arrived only after evidence observed in this task. OI-2 moved to `planned` because an approach was agreed in the same turn — an agreement about *how*, not a licence to start.

**Turn 6 — User:** Actually forget the handbook thing, we're deleting that page.

```text
**Outstanding** (1 reminder · 2 done)

**Intentional reminders**
- OI-3 Ask the design channel about the empty state — reminder

**Done**
- ~~OI-2 Add rate-limit docs to the handbook~~ — dropped (user cancelled, page being deleted)
- ~~OI-1 Fix the flaky login test~~ — verified
```

> Dropped items are struck through and kept, not deleted. The note says who decided and why. Most recently completed first.

---

## 3. Overflow, and asking before writing a file

**Turn 11 — User:** …and while you're there: the focus ring, the skip link, the nav aria labels, the muted-text contrast, a reduced-motion pass, the dialog focus trap, heading order on settings, and alt text on the empty-state art.

Eight items now sit under **Outstanding for you**. That is the overflow trigger.

**Agent (body):** That takes it to eight items for you, past what the footer should carry. Shall I create the canonical `outstanding-items.json` in this directory and open its local Full outstanding items editor? It is a Git repository, so I would exclude the JSON and its runtime files from Git too. None of the items are started.

> Ask once, propose a path, name the exclusion. Do not create the file first and mention it afterwards. And say plainly that a longer list is still not a list of things you are doing.

**Turn 12 — User:** Yeah do it.

```text
**Outstanding** (8 for you · 1 reminder · 2 done)
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)

**Outstanding for you**
- OI-4 Focus ring on interactive elements — requested
- OI-5 Skip link — requested
- OI-6 Aria labels on the nav — requested
- OI-7 Muted-text contrast — requested
- OI-8 Reduced-motion pass — requested
- OI-9 Keyboard trap in the dialog — blocked (upstream bug 4821; local patch regresses Safari)
- OI-10 Heading order on the settings page — requested
- … +1 more in [Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)

**Intentional reminders**
- OI-3 Ask the design channel about the empty state — reminder

**Done**
- ~~OI-2 Add rate-limit docs to the handbook~~ — dropped (user cancelled, page being deleted)
- ~~OI-1 Fix the flaky login test~~ — verified

[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

> "Yeah do it" authorized the canonical JSON and its editor, and nothing on the list. Seven lines are shown, the overflow points at the live HTML UI, and the JSON is the only writable ledger. `blocked` carries both facts: the wall, and the route already tried.
>
> The UI is now running, so the exact URL `start` printed appears twice: once directly under the header and once after the last section. It is the same link in both places, and it would appear in neither if no UI were live. The eight items were created and shown in one final response — the file creation itself produced no interim Outstanding block.

---

## 3b. `waiting-on-you`, and why it is not `blocked`

**Turn 13 — User:** The staging deploy needs someone to press approve before any of this ships.

The pipeline requires a human. The agent cannot press the button, and no in-scope workaround exists that would be safe to take alone.

```text
**Outstanding** (8 for you · 1 waiting on you · 1 reminder · 2 done)
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)

**Outstanding for you**
- OI-4 Focus ring on interactive elements — requested
- … +7 more in [Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)

**Waiting on you**
- OI-12 Approve the staging deploy — waiting-on-you (click approve in the deploy UI)

**Intentional reminders**
- OI-3 Ask the design channel about the empty state — reminder

**Done**
- ~~OI-2 Add rate-limit docs to the handbook~~ — dropped (user cancelled, page being deleted)
- ~~OI-1 Fix the flaky login test~~ — verified

[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

> Not `blocked`. Nothing external is broken; the pipeline is working exactly as designed. The note is the action itself, in the imperative, so it can be done without re-reading anything. If the deploy service were down, that would be `blocked` — and the note would then have to say both what broke and what was tried.

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
**Outstanding** (8 for you · 2 waiting on you · 1 reminder · 2 done)
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)

**Outstanding for you**
- OI-4 Focus ring on interactive elements — requested
- … +7 more in [Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)

**Waiting on you**
- OI-12 Approve the staging deploy — waiting-on-you (click approve in the deploy UI)
- OI-13 Carry the focus-token note to the design audit — waiting-on-you (paste the prepared note there)

**Intentional reminders**
- OI-3 Ask the design channel about the empty state — reminder

**Done**
- ~~OI-2 Add rate-limit docs to the handbook~~ — dropped (user cancelled, page being deleted)
- ~~OI-1 Fix the flaky login test~~ — verified

[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

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
**Outstanding** (8 for you · 2 waiting on you · 1 reminder · 2 done)
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)

**Outstanding for you**
- OI-4 Focus ring on interactive elements — requested
- … +7 more in [Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)

**Waiting on you**
- OI-12 Approve the staging deploy — waiting-on-you (click approve in the deploy UI)
- OI-13 Carry the focus-token note to the design audit — waiting-on-you (paste the prepared note there)

**Intentional reminders**
- OI-3 Ask the design channel about the empty state — reminder

**Suggested for you** — OI-4, about twenty minutes, and it settles OI-6 at the same time. Tell me `start OI-4` if you want me to pick it up.

**Done**
- ~~OI-2 Add rate-limit docs to the handbook~~ — dropped (user cancelled, page being deleted)
- ~~OI-1 Fix the flaky login test~~ — verified

[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

What the suggestion did **not** do:

- It did not start OI-4. It proposed, and then the reply ended.
- It did not reorder the list, or drop, hide, merge, or downgrade the items that were not chosen.
- It did not promote OI-3 because it is old. It was parked on purpose.
- It did not offer OI-9, which nothing the user does can move.
- It did not run to three paragraphs, and it did not appear on the previous fourteen turns.

**Turn 16 — User:** nah, skip link first.

**Agent (body):** OI-5 is recorded as your priority. The ledger is unchanged. Tell me `start OI-5` if you want me to work on it.

> A change of priority is not a start instruction. The ledger is untouched, OI-4 stays exactly where it was at the same status, and the suggestion is dropped without argument.

**Turn 17 — User:** you do it, OI-5, go.

Now there is a fresh, explicit instruction naming one item. The agent adds the skip link during this turn; browser proof remains outstanding.

While the work was under way the agent posted two short progress notes — "reading the layout template", then "skip link added, checking the tab order". Neither carried an Outstanding block, a counts line, or a single `OI-n` line. The ledger was updated silently, and the footer appeared once, here, at the end of the final response:

```text
**Outstanding** (8 for you · 2 waiting on you · 1 reminder · 2 done)
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)

**Outstanding for you**
- OI-4 Focus ring on interactive elements — requested
- OI-5 Skip link — implemented (skip link added; browser proof pending)
- … +6 more in [Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)

**Waiting on you**
- OI-12 Approve the staging deploy — waiting-on-you (click approve in the deploy UI)
- OI-13 Carry the focus-token note to the design audit — waiting-on-you (paste the prepared note there)

**Intentional reminders**
- OI-3 Ask the design channel about the empty state — reminder

**Done**
- ~~OI-2 Add rate-limit docs to the handbook~~ — dropped (user cancelled, page being deleted)
- ~~OI-1 Fix the flaky login test~~ — verified

[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

> The temporary `in-progress` state was reconciled before the final reply: material work changed, so OI-5 is `implemented`. When the turn ends, so does the authority: browser verification, OI-6, and OI-4 all need their own fresh named instruction.
>
> One turn, one footer. Repeating the block after each progress note would have buried the answer and made the same list look like three different lists.

---

## 6. Authority in four hard cases

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
| Opening every reply with a suggestion | It becomes a lecture and stops being read. | Offer one when asked, or at a real decision point. |
| Suggesting the oldest item because it is oldest | Age is not urgency, and a `reminder` was parked deliberately. | Weigh dependencies, momentum, effort, and load. |
| Quietly reordering the ledger to match your advice | The user's record silently changes underneath them. | Suggest in one line; leave every item where it was. |
| Renaming "the flaky login test" to "CI stability" | The user scans for their own words. | Keep their phrasing. |
| Renumbering after OI-2 was dropped | Every earlier reference in the transcript breaks. | Leave the gap. IDs are permanent. |
| Adding "write tests" nobody asked for | The ledger stops being the user's. | Suggest it in the body. |
| Waking another task to deliver a delta | A note that arrives as an instruction commissions work nobody authorized. | `prepared (not sent)`, and hand the text over. |
| "I've let the design system audit know" with no successful call | Unverifiable claim. | `registered (manual)` plus the text to carry. |
| Creating `outstanding-items.json` without asking | Files appear in someone's repository unannounced. | Ask once, propose a path, offer the exclusion. |
| Repeating the Outstanding block in every progress message | The turn becomes three near-identical lists, and the answer disappears between them. | Maintain the ledger silently; render one footer in the final response. |
| Writing a **Full outstanding items** link because the footer looks bare | An invented or stale URL sends the user nowhere. | Link only the exact URL `start` printed, in both places, or write neither line. |
| Putting the link at the bottom only, to save a line | It is the entry point people reach for first, and the top of the block is where they look. | Same link directly under the header and after the last section. |
