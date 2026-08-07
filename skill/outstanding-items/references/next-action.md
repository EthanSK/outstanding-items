# Choosing the one item

How to choose the single item the Outstanding footer names, how to word it, and when to name nothing at all. Load when the choice is not obvious, or when you suspect the honest answer is "nothing new".

The footer is one suggestion addressed to the person. It proposes and then waits. It is never a plan you carry out, and it never becomes authority to start — see [authority.md](authority.md).

## The footer always ends the turn; the suggestion does not always exist

While any item is open, the final response carries the footer. What varies is whether it can honestly name an item.

| Name an item | Use the no-suggestion line |
| --- | --- |
| Something is genuinely the next sensible thing for the user to pick up. | The last suggestion is still unanswered, and nothing else is eligible. |
| They asked what to do next, where to start, or what matters most. | They declined your last one and nothing has changed since. |
| They returned after a gap, or a burst of items just landed. | Everything left is `blocked`, `transferred`, or deliberately parked. |
| Something finished and the obvious path opened or closed. | They are winding down, and the kind answer is "nothing needs you tonight". |
| Everything left needs them personally — a click, a key, a yes. | You genuinely cannot tell, and inventing a rationale would be dishonest. |

The no-suggestion line is one quiet sentence — `**Outstanding** — nothing new to suggest; your list is unchanged.` — with no item, no count, and no reproach. It is a legitimate outcome, not a failure, and it is what stops the footer from becoming a lecture that nobody reads by turn four.

## What to weigh

There is no score. Hold these together and use judgement.

| Factor | The question |
| --- | --- |
| Dependencies | Does something else become possible once this is done? Is anything already waiting on it? |
| Momentum | Is the user already inside this file, this idea, this mood? Continuing costs far less than restarting. |
| Effort against value | What is the smallest thing with a real payoff? Prefer twenty minutes with an outcome over three hours with a milestone. |
| Availability to them | Can *they* pick it up right now? A `blocked` item is not a candidate. An item that needs them in person is. |
| Urgency | Real deadlines and real consequences only. Volume is not urgency, and neither is age. |
| Load | How much is this person carrying right now? After a long push, the kind suggestion is the small one, or none at all. |
| Kindness | Would a thoughtful colleague say this out loud right now, or leave them alone? |
| Autonomy | Is this their call to make? It always is. Offer the move, not a verdict on their week. |

Availability is judged from the user's side, not yours. Something you cannot touch may still be exactly what they should do next.

## What to say

Two lines maximum, plus the live UI link when one exists:

```text
**Outstanding** — OI-4 Focus ring on interactive elements — requested
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
**Outstanding** — OI-4 Focus ring on interactive elements — requested
A close call, but this is the smaller restart and you were already in that file.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

If the user wants the alternatives, they will ask — and then you answer in the body of the reply, not by widening the footer.

## Do not offer the same thing twice

A suggestion the user did not take up is answered. Repeating it is nagging, and nagging is how a footer becomes something people skim past.

- **Unanswered.** They replied about something else. Do not re-offer that item; pick a different eligible one, or use the no-suggestion line.
- **Unless they ask.** "What should I do next?" clears the slate. An explicit request for advice answers every earlier offer, so name the best item even if you named it before.
- **Declined.** "No", "not that one", "skip link first" — drop it without argument, and never bring it back on your own initiative.
- **Record it.** Keep `latest_unanswered_suggestion` current, and note the offer against the item, so a task resumed tomorrow does not start the same loop again.
- **When they act on it**, the record is answered and cleared. The same item may legitimately be suggested again later if it is genuinely the next thing — for example, after the user asked you to implement it and the honest next move is their own verification.
- **When the pool empties**, that is the no-suggestion line, and the footer goes quiet until something changes. That is the correct behaviour, not a gap to fill.

## Items that need the user in person

A `waiting-on-you` item is a perfectly good suggestion: they are the one who would act, and one click of theirs may be worth more than an hour of anything else.

- Say what the action is, in their words, in the imperative.
- Do not perform it, dispatch it, arrange it, or write to another system to chase it.
- Do not repeat it every turn because it is small. It is still their decision.

A `blocked` item is not a suggestion. Nothing they do moves it. Mention the wall in the body of the reply if it explains why the rest of the list looks the way it does — never in the footer.

## When to refuse to pick

- **The user already stated a priority.** Record and acknowledge it, leave every status and item order unchanged, and wait for a fresh instruction naming what the agent should start. The footer may name that item; it may not name a rival.
- **The information is not there.** If you genuinely cannot tell, say what you would need to know instead of inventing a rationale.
- **They are winding down.** "Nothing here needs you tonight" is a legitimate footer and often the right one.
- **The honest answer is rest, or a decision that is not yours.** Say it plainly and briefly, once.

## What a suggestion must never do

| Never | Why |
| --- | --- |
| Start, resume, continue, investigate, research, prepare, do pre-work for, dispatch, route, or complete the thing it suggested | The suggestion was a question. Answering it yourself takes the decision away. |
| Drop, hide, merge, or reorder items that were not chosen | The ledger is the user's record, not a queue you manage. Suggesting is a comment, not an edit. |
| Deprioritise something out of existence | An item not suggested is still exactly as open as it was. |
| Promote a `reminder` unprompted | It was parked on purpose. Wait for the user, or for real new urgency. |
| Put the assistant forward as the next move | The line is about the user's work, not about who is busy. |
| Turn into a plan, a checklist, or a set of numbered phases | That is a proposal to run the person's week. Offer one move. |
| Repeat the same suggestion every turn | Once is advice, twice is nagging, three times is noise. |
| Name a runner-up so the user can choose | Two items is a list, and the list is what the footer exists to keep out of the chat. |
| Invent a pick because the line looks empty | A suggestion nobody believes costs more than an honest silence. |
| Argue after a "no" | They know things you do not. Drop the suggestion and wait. |
| Claim certainty about value, effort, or urgency | You are estimating from a transcript. Say so when it matters. |
| Moralise about the backlog | No commentary on how long something has been open, or on how much is on the list. |

## Worked shapes

Each of these is the whole footer, at the end of the final response of its turn.

**Asked directly, several things open**

```text
**Outstanding** — OI-4 Focus ring on interactive elements — requested
About twenty minutes, and you are already in that file.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

**Everything left needs them in person**

```text
**Outstanding** — OI-8 Approve the staging deploy — waiting-on-you
Click approve in the deploy UI; it is the smallest thing on the list that only you can do.
```

**Returning after a gap**

```text
**Outstanding** — OI-4 Focus ring on interactive elements — implemented
You left it half-done and the suite still passes, so it is the cheapest restart.
```

**Overloaded**

```text
**Outstanding** — OI-5 Skip link — requested
Just the first section of it, if anything. Nothing here has a date on it.
```

**They declined the last one, and nothing else is eligible**

```text
**Outstanding** — nothing new to suggest; your list is unchanged.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

**Winding down**

```text
**Outstanding** — nothing here needs you tonight.
```

**The user already decided** — the body says it, the footer names their choice and nothing else:

> OI-5 is recorded as your priority. Ledger unchanged; tell me `start OI-5` if you want me to work on it.

**They said yes**

> **User:** go on then, do OI-4.
>
> Only now does the work start — because they named it, in this turn, in plain words.
