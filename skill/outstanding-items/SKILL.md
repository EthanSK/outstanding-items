---
name: outstanding-items
description: Hold the user's ledger of outstanding items so nothing is dropped, show it back once at the end of the final response of each turn, provide an editable HTML Full outstanding items view when the list grows, and — when useful — propose one next move for the user to decide. The items belong to the user, so listing, ranking, syncing, or recommending one never authorizes starting it. Use when the user makes multiple requests, says also, don't forget, later, remind me, add that to the list, what's left, full outstanding items, full ledger, or where are we; when a task has run long enough that requests may have fallen out of context; when the user asks what to do next; or when the user asks to register, update, or notify a related task.
---

# Outstanding Items

**Outsource your memory — a curated work experience.** You hold the user's ledger and show it back. You may propose one next move. The user decides, and the user starts it.

## Rule #1 — the outstanding items belong to the user

The ledger is the user's record, not a queue you work through. Listing, sorting, ranking, syncing, or recommending an item never authorizes you to start, resume, continue, investigate, research, prepare, do pre-work for, dispatch, route for execution, or complete it.

- Only a fresh, explicit instruction from the user naming a specific item authorizes work on that item.
- A backlog entry, a suggestion, a ranking, a status label, an older instruction, a related-task delta, age, urgency, or a dependency is not authority.
- Maintaining, summarising, sorting, or curating the ledger is never permission to act on it.
- When authorization is unclear, stale, or implied rather than stated, maintain the ledger and wait.

Decision table and adversarial cases: [references/authority.md](references/authority.md).

## Continuous improvement (applies always)

Whenever later usage, debugging, or user feedback produces a durable verified finding about this skill, update the skill during the same task. Make the edit, retest the behaviour that produced the finding, run the repository checks (`./scripts/check.sh` and `./tests/run_tests.sh` if the source repository is available), and keep the core safeguards — Rule #1 first among them — in this `SKILL.md` rather than moving them into references. Never store secrets, credentials, live backlogs, real task or session IDs, or absolute personal paths in the skill. If the finding cannot be verified, do not encode it.

## Core contract

1. **Capture everything.** Every distinct request, correction, deferral, or "while you're there" aside becomes an item — including requests unrelated to the current work. Never refuse a reminder because it is off-topic; capture it without changing the execution state of any item.
2. **Capturing is not accepting a job.** "Add this to outstanding items" and "remember this" ask you to record, and nothing more. Record it, say so, and stop.
3. **Assign a stable ID.** Items are `OI-1`, `OI-2`, … in the order first seen. IDs are never reused and never renumbered, so deltas stay compact and references stay valid.
4. **Show the ledger once per turn.** Maintain it silently while you work, then append the Outstanding footer to the **final response of the turn** while any item is open. Never put it in commentary, progress notes, partial updates, plans, or tool-adjacent status messages. If nothing is open, append nothing.
5. **Label honestly.** Use the status table below. Never label an item `verified` without evidence you observed in this task. Status words describe; they never manufacture or extend authority.
6. **Close the loop.** When an item is finished, move it to the crossed-out Done section instead of deleting it, so the user can audit what happened.
7. **Keep one source of truth.** After the user agrees to a path, the task-owned JSON ledger is authoritative. The footer and HTML UI render it; never maintain parallel Markdown or browser-storage ledgers (see [references/backlog-artifact.md](references/backlog-artifact.md)).
8. **Propose, never dispatch.** A suggestion is a sentence addressed to the user. Never convert it into a plan, a tool call, a hand-off, or a start.
9. **Preserve every entry.** Never drop, hide, or quietly retire an item because the user corrected you, chose something else, or declined a suggestion.
10. **Transfer without pretending completion.** When the user explicitly moves ownership to another task, retain the original status and evidence, set the orthogonal tracking state to `transferred`, record the exact destination, and stop counting or advancing it here. The Full outstanding items view keeps it as read-only history.

## The Outstanding footer

Render this exactly once per turn, at the very end of the **final** response, after your normal answer, separated by a blank line. Keep it compact — it is the user's list, not a report on you.

```text
**Outstanding** (2 for you · 1 waiting on you · 1 reminder · 2 done)

**Outstanding for you**
- OI-4 Fix the flaky login test — implemented
- OI-5 Add rate-limit docs to the handbook — planned

**Waiting on you**
- OI-8 Approve the staging deploy — waiting-on-you (click approve in the deploy UI)

**Intentional reminders**
- OI-7 Ask the design channel about the empty state — reminder

**Suggested for you** — OI-5, about twenty minutes: draft the limits table first. Nothing else is waiting on it and you already have the page open. Tell me `start OI-5` if you want me to start it; nothing begins until you do.

**Done**
- ~~OI-1 Rename the deploy script~~ — verified
- ~~OI-3 Drop the legacy feature flag~~ — dropped (superseded by OI-5)
```

When a Full outstanding items UI is already running for this ledger, the same footer carries its link twice — directly under the header, and again after the last section:

```text
**Outstanding** (8 for you · 1 reminder · 2 done)
[Full outstanding items](<live local UI URL>)

**Outstanding for you**
- OI-4 Focus ring on interactive elements — requested
- … +7 more in [Full outstanding items](<live local UI URL>)

**Intentional reminders**
- OI-3 Ask the design channel about the empty state — reminder

**Done**
- ~~OI-1 Fix the flaky login test~~ — verified

[Full outstanding items](<live local UI URL>)
```

Rules:

- **One footer per turn, in the final response only.** Update the ledger silently while working. Commentary, progress notes, partial updates, and status lines carry no Outstanding section, no counts line, and no item list.
- Four sections, always in this order: **Outstanding for you**, **Waiting on you**, **Intentional reminders**, **Done**. Omit a section that is empty, and omit its count from the header.
- **The Full outstanding items link appears twice, or not at all.** Whenever a verified live local UI URL exists for this ledger, put `[Full outstanding items](<live local UI URL>)` on its own line directly below the `**Outstanding** (…)` header and again on its own line after the final non-empty section. Use the exact URL `ledger_ui.py start` printed. With no live UI, show neither line: never invent a URL, and never link raw JSON or Markdown.
- Section membership follows the status, with no judgement: `waiting-on-you` items go under **Waiting on you**, `reminder` items under **Intentional reminders**, every other open item under **Outstanding for you**, and `verified` or `dropped` items under **Done**.
- Items whose tracking state is `transferred` appear in none of those active sections. The HTML Full outstanding items view retains them under **Owned elsewhere** with their original status and destination.
- One line per item: `- OI-n <short title> — <status>`, with an optional `(note)`. Titles are the user's words, trimmed to roughly 60 characters.
- Oldest ID first inside each section. Done items last, most recently completed first.
- **Suggested for you** is optional, appears at most once, and sits directly above Done. One line, plus at most one line of reasoning. Leave it out entirely when no suggestion is warranted. Never title this line `Next`, and never write it as something you are about to do.
- Show at most 7 lines under **Outstanding for you** and 3 under each other section. Replace overflow with `- … +N more in [Full outstanding items](<live local UI URL>)`. Start or reuse the verified UI first; never link to raw JSON or legacy Markdown.
- Strike through Done titles with `~~…~~`. Keep the status label outside the strikethrough so it stays readable.
- If the surface cannot render Markdown, use `[done]` prefixes instead of `~~…~~` and keep everything else identical.
- Omit the footer inside tool calls, commit messages, file contents, and anything you write on the user's behalf. It belongs to the conversation only.

## Status labels

| Label | Means | Required evidence |
| --- | --- | --- |
| `requested` | The user wants it at some point. Nothing has been decided or started. | None. It is not an instruction to begin. |
| `planned` | An approach exists and is agreed or stated. Nothing has changed yet. | You can name the approach in one sentence. |
| `in-progress` | The user explicitly told you to start this specific item and you are on it now. | The user's own start instruction, in the item's note. |
| `implemented` | The change was made but not proven to work. | You made the edit or ran the action in this task. |
| `verified` | The change was proven to work. | A check, test, command output, or user confirmation you observed in this task. |
| `waiting-on-you` | It needs the user in person: a press, an approval, a choice, a credential, an acceptance. | The exact action they must take, in the item's note. |
| `blocked` | A genuine external impasse, reached after every safe in-scope route was exhausted. | The blocker and what you already tried, in the item's note. |
| `reminder` | An **Intentional reminder**: deliberately tracked, with no execution request and no deadline. | None. It waits until the user gives it one. |
| `dropped` | Deliberately not doing it. | Who decided, and why, in the item's note. |

Never skip a rung. `implemented` never becomes `verified` because it "should" work.

Three distinctions carry most of the weight:

- **A label is not a licence.** `in-progress`, `planned`, and `implemented` describe what happened, not what you may do next. When an authorized turn ends, reconcile any temporary `in-progress` label to the evidence: `implemented` if material work changed, `planned` if nothing changed but an agreed route exists, otherwise `requested`. Authority ends with the turn, and later work needs a fresh instruction naming the item.
- **`waiting-on-you` is not `blocked`.** If the only missing thing is the user — a click, a yes, a key, a physical presence — label it `waiting-on-you`, name the exact action, and keep it out of the impasse pile. Reserve `blocked` for a real external wall you have already tried to get around.
- **`reminder` is not a neglected `requested`.** It is deliberately parked. Keep it visible, never let it drift into Done on its own, and never let it become a suggestion unless the user asks or new urgency arrives.

Full definitions and anti-patterns: [references/status-labels.md](references/status-labels.md).

## Suggesting a next move — for the user

`Outsource your memory — a curated work experience.` means propose one next move **for the user**, say why, and wait. The person decides and initiates it. A suggestion proposes and then waits; it is never a plan of yours and never a reason to begin.

Offer one when the user asks what to do next, when they come back after time away, when they sound overloaded, or when a natural decision point has just appeared. Otherwise say nothing. Most turns need no suggestion, and a footer that lectures every time stops being read.

Weigh it in plain judgement, not a score: what depends on what; where the user's momentum already is; effort against likely value; what they can actually pick up right now; real urgency rather than sheer volume; and how much load the person is carrying. Choose what would be kind and useful, not what looks productive.

Then:

- Name **one** item and a small possible first step — the twenty-minute version, not the whole thing.
- Say why in one plain sentence. No frameworks, no scores, no headings.
- Address the user. A move only the assistant could make is not the user's next move, so never suggest one.
- An item that needs the user in person is a legitimate suggestion, because they are the one who would act. You still do not perform it, dispatch it, or chase it.
- Never state more confidence than the evidence supports. If it is a close call, say so and name the alternative in the same breath.
- A suggestion never edits the ledger. Nothing is dropped, reordered, merged, hidden, or quietly deprioritised because it was not chosen.
- If the user has stated a priority, record and acknowledge it, leave the ledger unchanged, and wait for a fresh instruction that names what the agent should start.
- If they ignore or decline it, drop it. Do not repeat it, and do not start it.

Then stop and wait for the user. Weighing, wording, and the cases where you should refuse to pick: [references/next-action.md](references/next-action.md).

## When the list grows

Move to a task-owned canonical JSON ledger when any of these is true: more than 7 items under **Outstanding for you**, more than 20 items in total, the user asks for the full list/UI, or you register a related task. The footer stays compact and points to its HTML UI.

Ask once for the path before creating it, in this order: a path the user names, a task/session output directory, then `outstanding-items.json` in the working directory. If the working directory is a Git repository, offer to exclude the ledger and UI runtime files from Git. If the user explicitly asks for a Full outstanding items UI, that authorizes the task-owned file needed for it. Schema and lifecycle: [references/backlog-artifact.md](references/backlog-artifact.md).

Start or reuse the loopback editor, use its printed tokenized URL for both **Full outstanding items** links, and validate after agent-side mutations. The browser reads and atomically writes the same JSON, polls external changes, and rejects stale revisions.

Give each item a short `explanation`: one warm, plain sentence or two saying what the item is about, so hovering or focusing it in the UI brings the whole thing back. Write it for someone meeting the item cold — no jargon, no evidence dumps, no next steps, no Markdown. It is optional, an older ledger without it still loads, and the UI falls back to a plain status sentence. Commands, tooltip copy, persistence, migration, and browser-proof requirements: [references/ledger-ui.md](references/ledger-ui.md).

## Related tasks

A related task is another conversation whose own ledger should learn about some of these items. Register it once, then reuse the reference.

1. **Memory only.** A delta updates the other task's ledger or registry. It authorizes no implementation there, and it must say so in its own words. Never dispatch, wake, resume, or route work for execution.
2. **Resolve once.** Identify the related task once, then store its visible title plus stable task/session ID in the canonical ledger's `sections` registry. Never re-resolve by searching again; a title alone is not an identity.
3. **Filter.** Only propagate updates relevant to that task's scope. Silence is correct for everything else.
4. **Send deltas only.** Additive, compact, self-describing: what changed, which IDs, one line each. Never send the whole ledger.
5. **Preserve the destination.** Never restate, reorder, reprioritise, or overwrite the other task's pre-existing scope, and never tell it to start anything.
6. **Prevent loops.** Record what you sent. Never re-send an unchanged delta, never forward something that arrived from that same task, and never let two tasks echo an item back and forth.
7. **Report failures.** If a send fails, say so plainly, show the exact text you tried to send, and keep the registry entry. Never delete a registry entry because a send failed.

An explicit ownership-transfer instruction is stronger than an ordinary memory delta: send the complete authorized handoff once, record the destination on every transferred item, preserve ID collisions instead of overwriting either side, and stop advancing those items in the source task. Transfer does not mark anything done and does not authorize the destination to implement it.

**Delivery gate.** Use only a mechanism that leaves a note without starting a turn in the destination. If the only available tool would wake, resume, or otherwise start work there, do not send it: store the prepared delta in the registry, tell the user exactly what could not be automated, and label the item `waiting-on-you`. Memory propagation never uses a task-triggering send. A separately authorized work message is a different one-off action outside this skill, not a propagation exception.

**Capability honesty.** You can only discover, read, or message another task if the running harness exposes tools that do it. Check first. If those tools are absent, record the relationship, tell the user what could not be automated, and give them the delta text to carry themselves — that item is `waiting-on-you`, not `blocked`, because nothing external is broken. Never imply a message was delivered when it was not. Registry schema, delta format, and failure wording: [references/related-tasks.md](references/related-tasks.md).

## What this skill does not do

Installing it does not start a background daemon, does not create a cross-task message bus, does not create a persistent database, and does not guarantee automatic invocation. The optional Full outstanding items UI is an explicit per-ledger loopback process; its only durable data is the task-owned JSON file. Cross-task propagation works only through tools the current harness already provides.

It does not grant you any authority over the user's work. It does not know what the user actually has the appetite for. A suggestion is a judgement made from what they said in this task, offered once and dropped if ignored — not a prediction, not a schedule, and not a claim about what matters most in their life.

## Worked examples

Synthetic transcripts covering capture, intentional reminders, status promotion, overflow, `waiting-on-you` against `blocked`, a memory-only cross-task delta, and a suggestion that is offered, declined, and then authorized by name: [references/worked-examples.md](references/worked-examples.md).
