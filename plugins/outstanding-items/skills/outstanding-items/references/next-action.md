# Choosing the one item

How to choose the single item the compact recommendation names and how to preserve an actionable next step whenever work remains. Load when the choice is not obvious, when every candidate was already offered, or when the remaining work is blocked.

The footer is one suggestion addressed to the person. It proposes and then waits. It is never a plan you carry out, and it never becomes authority to start — see [authority.md](authority.md).

## The footer always ends the turn and names an item while work remains

Before treating the ledger as empty, scan the current request, results, blockers, decisions, and unverified outcomes. Add every concrete unresolved thing the user still needs to review, decide, provide, verify, or return to as `agent-added`. Then inspect the actionable frontier:

- If a normal actionable item exists, recommend the best one.
- If the best result is blocked, recommend another actionable item instead.
- If blocked work has no captured next step, add the nearest useful prerequisite, workaround, decision, or time/condition-bound follow-up as a separate `agent-added` item, note which parent it unblocks, and recommend from those actionable items.
- If every item has been offered before, choose the best still-open item again rather than going silent. Refresh the small first step so the line is useful now.
- If only an intentional reminder remains, it may be the recommendation without changing its status. Do not start it or invent urgency.
- If nothing remains after the loose-end and actionable-frontier scans, use `**No outstanding items**`.

Transferred records are not active in this ledger. A pure external wait is still a real blocker, but silence is not the next action: capture an honest check tied to a meaningful time or condition. Never add immediate busywork merely to satisfy the footer.

## What to weigh

There is no score. Hold these together and use judgement.

| Factor | The question |
| --- | --- |
| Dependencies | Does something else become possible once this is done? Is anything already waiting on it? |
| Momentum | Is the user already inside this file, this idea, this mood? Continuing costs far less than restarting. |
| Effort against value | What is the smallest thing with a real payoff? Prefer twenty minutes with an outcome over three hours with a milestone. |
| Availability to them | Can *they* pick it up right now? A blocked parent is not a candidate; its captured prerequisite or follow-up is. An item that needs them in person is. |
| Urgency | Real deadlines and real consequences only. Volume is not urgency, and neither is age. |
| Load | How much is this person carrying right now? After a long push, choose the smallest honest next move and phrase it gently. |
| Kindness | Would a thoughtful colleague say this out loud right now, or leave them alone? |
| Autonomy | Is this their call to make? It always is. Offer the move, not a verdict on their week. |

Availability is judged from the user's side, not yours. Something you cannot touch may still be exactly what they should do next.

## What to say

Two lines maximum, plus the live UI link when one exists:

```text
**OI-4 Focus ring on interactive elements** `You`
Twenty minutes, and the smallest version is the shared token plus one button.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

- **One item.** A shortlist is a decision handed back to the person who asked you to make it. One `OI-n` in the footer, and no other.
- **A small possible first step.** Name the twenty-minute version, so starting is cheap and stopping is allowed.
- **One plain sentence of reasoning.** Say the real reason: it is quick, they are already there, something depends on it. Drop the sentence entirely when the title says it all.
- **Calibrated confidence.** "Probably", "if you have the energy", "it is a close call" are all better than false certainty.
- **The user is the subject.** Write what *they* might do. A line about what the assistant would carry on with is not a next move for the user, and must never appear here.
- **No structure.** No headings, no bullets, no numbered plan, no framework names, no scores, no counts.
- **End open.** Make it obvious that nothing starts without a word from them, without labouring the point every time.

## When the choice is close

Say it is close, and leave the runner-up unnamed. Naming a second item turns the footer back into the list it exists to replace, and the whole ledger is one click away in the UI:

```text
**OI-4 Focus ring on interactive elements** `You`
A close call, but this is the smaller restart and you were already in that file.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

If the user wants the alternatives, they will ask — and then you answer in the body of the reply, not by widening the footer.

## Rotate before repeating

A suggestion the user did not take up should not be repeated while another useful option exists. Rotation prevents nagging; it does not permit the footer to go empty while work remains.

- **Unanswered.** They replied about something else. Exclude that item and pick a different actionable one whenever one exists.
- **Unless they ask.** "What should I do next?" clears the slate. An explicit request for advice answers every earlier offer, so name the best item even if you named it before.
- **Declined.** "No", "not that one", "skip link first" — exclude it without argument while another actionable item exists, and consider the alternatives normally.
- **Record it.** Keep `latest_unanswered_suggestion` current, and note the offer against the item, so a task resumed tomorrow does not start the same loop again.
- **When they act on it**, the record is answered and cleared. The same item may legitimately be suggested again later if it is genuinely the next thing — for example, after the user asked you to implement it and the honest next move is their own verification.
- **When every alternative has been considered but work remains open**, return the best still-open item to the pool. Use a current first step instead of copying the previous line mechanically.
- **When the ledger itself has zero open items after both scans**, use `**No outstanding items**`. Never let a concrete user-facing follow-up disappear just to make the ledger look empty.

## Items that need the user in person

A `waiting-on-you` item is a perfectly good suggestion: they are the one who would act, and one click of theirs may be worth more than an hour of anything else.

- Say what the action is, in their words, in the imperative.
- Do not perform it, dispatch it, arrange it, or write to another system to chase it.
- Do not repeat it every turn because it is small. It is still their decision.

A `blocked` parent is not a suggestion. Nothing they do moves the parent directly. Ensure its nearest useful unblock or follow-up exists as a separate open item, then suggest that item or another actionable one. Mention the wall in the body only when it helps explain the choice.

## When the choice is awkward

- **The user already stated a priority.** Record and acknowledge it, leave every status and item order unchanged, and wait for a fresh instruction naming what the agent should start. The footer may name that item; it may not name a rival.
- **The information is not there.** Choose the smallest reversible open action and say the choice is close; do not invent a strong rationale.
- **They are winding down.** Still name the smallest honest item, but phrase it as something to return to, not pressure to act tonight.
- **The honest answer is rest.** The footer may name the next item for later while the body says to stop now. Recommendation timing never becomes urgency.

## What a suggestion must never do

| Never | Why |
| --- | --- |
| Start, resume, continue, investigate, research, prepare, do pre-work for, dispatch, route, or complete the thing it suggested | The suggestion was a question. Answering it yourself takes the decision away. |
| Drop, hide, merge, or reorder items that were not chosen | The ledger is the user's record, not a queue you manage. Suggesting is a comment, not an edit. |
| Deprioritise something out of existence | An item not suggested is still exactly as open as it was. |
| Promote a `reminder` merely to fill the line | It was parked on purpose. Keep its status; suggest it only when no better actionable item remains. |
| Put the assistant forward as the next move | The line is about the user's work, not about who is busy. |
| Turn into a plan, a checklist, or a set of numbered phases | That is a proposal to run the person's week. Offer one move. |
| Repeat the same suggestion while alternatives exist | Rotation is more useful and less noisy. Consider every actionable alternative first. |
| Name a runner-up so the user can choose | Two items is a list, and the list is what the footer exists to keep out of the chat. |
| Invent busywork because a parent is blocked | Capture the nearest honest prerequisite or scheduled/conditional check, not motion for its own sake. |
| Argue after a "no" | They know things you do not. Drop the suggestion and wait. |
| Claim certainty about value, effort, or urgency | You are estimating from a transcript. Say so when it matters. |
| Moralise about the backlog | No commentary on how long something has been open, or on how much is on the list. |

## Worked shapes

Each of these is the whole footer, at the end of the final response of its turn.

**Asked directly, several things open**

```text
**OI-4 Focus ring on interactive elements** `You`
About twenty minutes, and you are already in that file.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

**Everything left needs them in person**

```text
**OI-8 Approve the staging deploy** `You` — waiting-on-you
Click approve in the deploy UI; it is the smallest thing on the list that only you can do.
```

**Returning after a gap**

```text
**OI-4 Focus ring on interactive elements** `You` — implemented
You left it half-done and the suite still passes, so it is the cheapest restart.
```

**Overloaded**

```text
**OI-5 Skip link** `You`
Just the first section of it, if anything. Nothing here has a date on it.
```

**They declined the last one, and every alternative was considered**

```text
**OI-5 Skip link** `You`
The other options were considered; this remains the smallest useful restart.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

**Winding down**

```text
**OI-5 Skip link** `You`
Leave this as the clean restart for tomorrow; nothing needs to begin tonight.
```

**Everything is complete**

```text
**No outstanding items**
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

**Everything is complete, with no editor running**

```text
**No outstanding items**
```

**The user already decided** — the body says it, the footer names their choice and nothing else:

> OI-5 is recorded as your priority. Ledger unchanged; tell me `start OI-5` if you want me to work on it.

**They said yes**

> **User:** go on then, do OI-4.
>
> Only now does the work start — because they named it, in this turn, in plain words.
