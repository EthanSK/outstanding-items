---
name: outstanding-items
description: Hold the user's ledger of outstanding items so nothing is dropped, reconcile proven completions into Done, keep the whole list out of the chat, maintain an actionable next step whenever work remains, and end the final response of each turn with one compact recommendation plus a link to the editable HTML Full outstanding items view. The items belong to the user, so listing, ranking, syncing, or recommending one never authorizes starting it. Use when the user makes multiple requests, says also, don't forget, later, remind me, add that to the list, what's left, full outstanding items, full ledger, or where are we; when work leaves a concrete review, decision, input, verification, blocker, or follow-up for the user; when a task has run long enough that requests may have fallen out of context; when the user asks what to do next; or when the user asks to register, update, or notify a related task.
---

# Outstanding Items

**Outsource your memory — a curated work experience.** You hold the user's ledger, keep it out of the conversation, and end the turn with one suggested next move. The user decides, and the user starts it.

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
3. **Assign a stable ID and explicit priority.** Keep the permanent ledger key as `OI-1`, `OI-2`, … in first-seen order, and give every item one priority: `P0` critical, `P1` high, `P2` normal/default, or `P3` low. Show the composite current reference everywhere user-facing — for example `OI-12-P1` — while retaining `OI-12` internally so changing priority never breaks history, links, or commands. Existing items with no provable priority migrate to `P2`; never invent urgency. Priority describes relative importance and never grants authority.
4. **Record ledger provenance, not task authorship.** Set `provenance` to `user-requested` only when the user explicitly says to add or record that specific thing in Outstanding Items, the outstanding-items ledger, or the outstanding-items list. A normal work request — including “we need to do X”, “can you do X”, “remember X”, or an instruction to start X — does **not** qualify. If you capture that request automatically, use `agent-added`. Use `unknown-legacy` only for an older record whose capture source cannot be proved. Never infer `user-requested` from who wanted the underlying work, from a title, status, note, or later start instruction. Decision table, corrections, and examples: [references/provenance.md](references/provenance.md).
5. **Never leave a real loose end out.** Automatically create an `agent-added` item whenever the current work reveals a concrete unresolved thing the user still needs to review, decide, provide, verify, or return to, even when they did not explicitly ask to add it to Outstanding Items. Before declaring the ledger empty, scan the current request, results, blockers, decisions, and unverified outcomes for such a user-facing loose end. Do not invent filler or speculative improvements when genuinely nothing remains; the ledger is memory, not idea exhaust.
6. **Keep an actionable frontier.** Whenever any active item remains open, ensure the ledger also contains at least one concrete thing the user can choose to do next. A blocked parent does not justify silence: capture the nearest useful prerequisite, workaround, decision, or time/condition-bound follow-up as a separate `agent-added` item and record which item it unblocks. Prefer another already-open actionable item when one exists. Never invent busywork or pretend an external wait can be accelerated; for a pure external wait, create the next honest check at a sensible time or condition.
7. **Phrase actions for scanning.** Write actionable titles, explanations, recommendations, and user-facing next steps in imperative Git commit-subject style: lead with a direct verb such as `Write`, `Add`, or `Check`, name the outcome, and omit throat-clearing such as “This is” or “This would”. Preserve clear user wording and do not force non-action facts into commands.
8. **Show one recommendation, once per turn.** Maintain the ledger silently while you work, then append the compact recommendation to the **final response of the turn**. Start directly with the suggested item, never an `Outstanding` heading or the list. Never put it in commentary, progress notes, partial updates, plans, or tool-adjacent status messages. If anything active is open, name one item; if nothing is open, use the bold empty-ledger line below.
9. **Label honestly.** Use the status table below. Never label an item `verified` without evidence you observed in this task or exact completion evidence already preserved in the canonical item and checked now. Status words describe; they never manufacture or extend authority.
10. **Reconcile completion every time.** Whenever you read, add, update, suggest from, render, or otherwise interact with a ledger, inspect the evidence already recorded and any evidence observed in this task. If an item's scoped outcome is actually complete and verified — or the user explicitly dropped it — set the corresponding `verified` or `dropped` status, mark it completed, and move it to Done while preserving its evidence. Apply this to every provenance, and especially never leave completed `agent-added` work open merely to demand redundant user acceptance. This is ledger maintenance, not authority to perform unfinished work. Do not close speculative, merely implemented, unverified, `waiting-on-you`, `blocked`, `reminder`, transferred, or genuinely unfinished items.
11. **Reconcile order without erasing intent.** Whenever you open, reconcile, or update a canonical ledger, run `ledger_ui.py reconcile-order` (or use the equivalent server path). Automatic items sort first by actionable status, then by priority from P0 through P3 as the fallback within that status band, then by newest relevance and newest stable ID. A drag or keyboard move in the Full outstanding items UI records `manual` order metadata; keep that item in its chosen slot until the user moves it again. Never infer manual placement for a legacy item, silently clear manual metadata, or reorder the ledger merely to match the footer recommendation.
12. **Persist project chats by default.** When this chat is scoped to a Git project, resolve its per-chat ledger before the first capture with `ledger_ui.py project-ledger --project-root <root> --task-id <stable-task-id>`. Project storage is on by default: the canonical path is `<root>/.outstanding-items/<task-id>/outstanding-items.json`, and the command adds `/.outstanding-items/` to that project's `.gitignore` exactly once. Use `--no-project-storage` only when the user or project instructions explicitly opt this chat out. Never combine different chats into one ledger, never commit the private directory, and never create a second ledger when an existing canonical ledger already owns the chat.
13. **Keep one source of truth.** The per-chat JSON ledger is authoritative. The footer quotes one item from it and the HTML UI renders all of it; never maintain parallel Markdown or browser-storage ledgers (see [references/backlog-artifact.md](references/backlog-artifact.md)).
14. **Propose, never dispatch.** A suggestion is a sentence addressed to the user. Never convert it into a plan, a tool call, a hand-off, or a start.
15. **Preserve every entry.** Never drop, hide, or quietly retire an item because the user corrected you, chose something else, or declined a suggestion.
16. **Transfer without pretending completion.** When the user explicitly moves ownership to another task, retain the original status and evidence, set the orthogonal tracking state to `transferred`, record the exact stable destination task/session ID plus its cached visible title, and stop counting or advancing it here. The Full outstanding items view keeps it as read-only history. When Codex is locally available, the editor may refresh that cached title through the read-only app-server protocol by exact ID; this never authorizes discovering, waking, messaging, or changing the destination task.

## The compact recommendation

One small block at the very end of the **final** response of the turn, after your normal answer, separated by a blank line. At most three lines: the one item you suggest next, an optional line saying how to start it and why, and the live UI link when one exists. Everything else stays in the ledger, out of the chat.

```text
**OI-5-P1 Add rate-limit docs to the handbook** `You` — planned
Draft the limits table first, about twenty minutes; nothing else is waiting on it.
[Full outstanding items](<live local UI URL>)
```

With no live UI, the link line is simply absent and nothing replaces it:

```text
**OI-8-P0 Approve the staging deploy** `You` — waiting-on-you
Click approve in the deploy UI; it is the one thing left that only you can do.
```

An active open ledger always names one item. Prefer a different item after unanswered or declined advice; once every alternative has been considered, choose the best still-open item again rather than going silent. A blocked parent is never the recommendation: first ensure a concrete prerequisite, workaround, decision, or sensible follow-up check exists as its own open item, then recommend from that actionable frontier.

When the ledger has no open items at all, first perform the loose-end scan required by Core contract 5. If a concrete unresolved thing still needs the user's attention, add it as `Agent` instead. Only an honestly empty ledger says this, plainly and in bold:

```text
**No outstanding items**
[Full outstanding items](<live local UI URL>)
```

Rules:

- **One recommendation per turn, in the final response only.** Update the ledger silently while working. Commentary, progress notes, partial updates, and status lines carry no recommendation, item, count, or link.
- **No heading or label.** Start immediately with the item itself. Never prefix the block with `Outstanding`, `Suggested for you`, `Next`, or another heading.
- **Exactly one item.** One composite `OI-n-Px` reference appears in the footer, and it is the one you suggest. Never add a second item, an alternative, a shortlist, counts, section headings, reminders, or a `+N more` row. A footer that lists things has stopped being this footer.
- **No Done section, ever.** A `verified`, `dropped`, or `transferred` item never appears in the footer — not as a line, not struck through, not as a count, not as a heading. Completions live in the ledger's Done group and in the Full outstanding items view, which is where the user audits them.
- Line one starts with `**OI-n-Px <short title>**`, immediately followed by the inline-code source marker `You` or `Agent`; append ` — <status>` only for a non-default state. Use `You` for `user-requested`, `Agent` for `agent-added`, and omit the marker for `unknown-legacy` rather than inventing an origin. Use the current priority suffix and the user's own words trimmed to roughly 60 characters. Before using `**No outstanding items**`, perform the Core contract 5 loose-end scan and the actionable-frontier scan in Core contract 6; use it only when zero active items remain open and no concrete user-facing loose end was omitted. The ledger retains `requested`; the compact footer omits it because it adds no useful signal there.
- Line two is optional and never more than one line: a small first step, one plain reason, or the exact action a `waiting-on-you` item needs. Leave it out when it adds nothing.
- **The Full outstanding items link appears once, or not at all.** Whenever a verified live local UI URL exists for this ledger, put `[Full outstanding items](<live local UI URL>)` on its own line as the last line of the footer, using the exact URL `ledger_ui.py start` printed. With no live UI, write no link line at all: never invent a URL, and never link raw JSON or Markdown.
- **Rotate before repeating.** Exclude an unanswered or declined suggestion while another actionable open item exists. When every alternative has been considered, choose the best still-open item again with a useful, current first step rather than producing an empty recommendation. When the user asks what to do next, the slate is immediately clear. Do not mechanically repeat the same item on consecutive turns.
- The item you name is a suggestion, never a claim. Nothing about appearing in the footer changes an item's status, position, or execution state, and every item you did not name is exactly as open as it was.
- If the surface cannot render Markdown, drop the link syntax and print `Full outstanding items: <live local UI URL>` on its own last line.
- Omit the footer inside tool calls, commit messages, file contents, and anything you write on the user's behalf. It belongs to the conversation only.
- **When the user asks to see everything**, answer them in the body of that reply — or open the Full outstanding items UI — and still close with the one-line footer. Never widen the footer itself back into a list.

## Status labels

| Label | Means | Required evidence |
| --- | --- | --- |
| `requested` | The user wants it at some point. Nothing has been decided or started. | None. It is not an instruction to begin. |
| `planned` | An approach exists and is agreed or stated. Nothing has changed yet. | You can name the approach in one sentence. |
| `in-progress` | The user explicitly told you to start this specific item and you are on it now. | The user's own start instruction, in the item's note. |
| `implemented` | The change was made but not proven to work. | You made the edit or ran the action in this task. |
| `verified` | The change was proven to work. | A check, test, command output, or user confirmation you observed now, or exact completion evidence already preserved in the canonical item and checked now. |
| `waiting-on-you` | It needs the user in person: a press, an approval, a choice, a credential, an acceptance. | The exact action they must take, in the item's note. |
| `blocked` | A genuine external impasse, reached after every safe in-scope route was exhausted. | The blocker and what you already tried, in the item's note. |
| `reminder` | An **Intentional reminder**: deliberately tracked, with no execution request and no deadline. | None. It waits until the user gives it one. |
| `dropped` | Deliberately not doing it. | Who decided, and why, in the item's note. |

Never skip a rung. `implemented` never becomes `verified` because it "should" work. Once trustworthy evidence proves the scoped result complete, reconcile it into Done immediately instead of inventing another acceptance gate.

Three distinctions carry most of the weight:

- **A label is not a licence.** `in-progress`, `planned`, and `implemented` describe what happened, not what you may do next. When an authorized turn ends, reconcile any temporary `in-progress` label to the evidence: `implemented` if material work changed, `planned` if nothing changed but an agreed route exists, otherwise `requested`. Authority ends with the turn, and later work needs a fresh instruction naming the item.
- **`waiting-on-you` is not `blocked`.** If the only missing thing is the user — a click, a yes, a key, a physical presence — label it `waiting-on-you`, name the exact action, and keep it out of the impasse pile. Reserve `blocked` for a real external wall you have already tried to get around.
- **`reminder` is not a neglected `requested`.** It is deliberately parked. Keep it in the ledger, never let it drift into Done on its own, and never let it become the footer's suggestion unless the user asks or new urgency arrives.

Full definitions and anti-patterns: [references/status-labels.md](references/status-labels.md).

## Priority labels

| Priority | Means |
| --- | --- |
| `P0` | Critical now: a serious immediate consequence or urgent hard deadline. |
| `P1` | High: important or meaningfully blocking near-term work. |
| `P2` | Normal: the honest default when no stronger priority is established. |
| `P3` | Low: useful later, with little current consequence. |

Priority is deliberately coarser than curation. Use it as a fallback among similarly actionable items, not as a replacement for dependencies, user momentum, real urgency, or what the user can do now. Changing priority changes the composite display reference, not the permanent `OI-n` identity, and never starts the item.

## Choosing the one item — for the user

`Outsource your memory — a curated work experience.` means the footer offers one next move **for the user** and then waits. The person decides and initiates it. It is never a plan of yours and never a reason to begin.

Weigh it in plain judgement, not a score: what depends on what; where the user's momentum already is; effort against likely value; what they can actually pick up right now; real urgency rather than sheer volume; how much load the person is carrying; and whether a thoughtful colleague would say this out loud at all. Choose what would be kind and useful, not what looks productive.

Then:

- Name **one** item and a small possible first step — the twenty-minute version, not the whole thing.
- Say why in one plain sentence, and only when it helps. No frameworks, no scores, no headings, no named alternatives.
- Address the user. A move only the assistant could make is not the user's next move, so never suggest one.
- An item that needs the user in person is a legitimate suggestion, because they are the one who would act. You still do not perform it, dispatch it, or chase it. Never suggest a `blocked` parent directly; suggest its separately captured actionable prerequisite or follow-up. A transferred item is owned elsewhere and is not active here.
- Never state more confidence than the evidence supports. If it is a close call, say so in the reason; do not name the runner-up, because the whole list is one click away.
- A suggestion never edits the ledger. Nothing is dropped, reordered, merged, hidden, or quietly deprioritised because it was not chosen.
- If the user states a priority, record and acknowledge it by updating only that item's priority field, then wait for a fresh instruction that names what the agent should start. The priority edit may affect automatic presentation order; it does not change status, manual placement, provenance, or authority.
- If they ignore or decline it, rotate to another actionable open item and never start it. Record the offer so a resumed task does not immediately restart the same loop. If every alternative has already been considered and the item is still open, it returns to the candidate pool; refresh the first step instead of repeating stale wording.
- If only blocked parents remain, the ledger is missing its actionable frontier. Add the nearest honest unblock or time/condition-bound follow-up as `agent-added` before writing the footer. Do not fabricate a check that is not yet useful.

Then stop and wait for the user. Weighing, wording, and the cases where you should refuse to pick: [references/next-action.md](references/next-action.md).

## Where the ledger lives

For a Git-project chat, create or resolve the canonical ledger before the first captured item. Run `project-ledger` against the task's primary project root; it separates chats by stable task ID, creates the private directory with restrictive permissions, and adds the project-level ignore entry. This storage is enabled by default. An explicit `--no-project-storage` disables it without writing to the project. If several repositories are involved, use the task's primary project rather than duplicating the ledger.

For a chat with no project, keep the small in-context ledger until a durable file is needed: more than 7 active items, more than 20 total items, a Full outstanding items request, or a related-task registry. Ask once for a path, preferring a user-named path and then the task/session output directory. An existing canonical ledger keeps ownership until the user explicitly authorizes a move; never silently duplicate it merely because a project later enters scope. Schema and lifecycle: [references/backlog-artifact.md](references/backlog-artifact.md).

Start or reuse the loopback editor, use its printed tokenized URL for the footer's single **Full outstanding items** link, and validate after agent-side mutations. The browser reads and atomically writes the same JSON, polls external changes, and rejects stale revisions.

Keep each row width-efficient: render the composite `OI-n-Px` reference as a slim metadata line above the task text inside the content column, never as a dedicated side column that squeezes the task.

Reconcile the canonical order whenever you open or change the ledger. Automatic items sort by actionable status, then P0→P3 priority, then newest relevance and stable ID; explicit drag/keyboard placement stays fixed through its recorded manual-order metadata. This is presentation maintenance only; it never starts work and does not replace the footer's contextual judgement.

Give each item a short `explanation`: one warm, action-first sentence or two saying what the item is about, so hovering or focusing it in the UI brings the whole thing back. Lead with the concrete action in imperative Git commit-subject style — `Write a LinkedIn post…`, not `This is the idea to…` — then add only the context that helps someone meeting the item cold. Use no jargon, evidence dumps, next steps, or Markdown. It is optional, an older ledger without it still loads, and the UI falls back to a title-led status sentence. Commands, tooltip copy, persistence, migration, and browser-proof requirements: [references/ledger-ui.md](references/ledger-ui.md).

## Related tasks

A related task is another conversation whose own ledger should learn about some of these items. Register it once, then reuse the reference.

1. **Record useful links locally.** When a relationship is genuinely useful, you may add its stable title and task/session ID to this ledger's `sections` registry without asking first. That link is record-only metadata: by itself it never authorizes waking, starting, messaging, reprioritising, or altering the other task.
2. **Message only when separately authorized.** A fresh explicit user instruction is required before sending even a memory-only delta. The delta authorizes no implementation there, and it must say so in its own words. Never dispatch, wake, resume, or route work for execution.
3. **Resolve once; refresh display by exact ID.** Identify the related task once, then store its visible title plus stable task/session ID in the canonical ledger's `sections` registry. Never re-resolve identity by searching from a title. A local read-only title refresh may query the already-stored exact ID so a later rename stays legible; it must not enumerate for a replacement, wake the task, or change any work.
4. **Filter.** Only propagate separately authorized updates relevant to that task's scope. Silence is correct for everything else.
5. **Send deltas only.** Additive, compact, self-describing: what changed, which IDs, one line each. Never send the whole ledger.
6. **Preserve the destination.** Never restate, reorder, reprioritise, or overwrite the other task's pre-existing scope, and never tell it to start anything.
7. **Prevent loops.** Record what you sent. Never re-send an unchanged delta, never forward something that arrived from that same task, and never let two tasks echo an item back and forth.
8. **Report failures.** If a send fails, say so plainly, show the exact text you tried to send, and keep the registry entry. Never delete a registry entry because a send failed.

An explicit ownership-transfer instruction is stronger than an ordinary memory delta: send the complete authorized handoff once, record the destination on every transferred item, preserve ID collisions instead of overwriting either side, and stop advancing those items in the source task. Transfer does not mark anything done and does not authorize the destination to implement it.

**Delivery gate.** Use only a mechanism that leaves a note without starting a turn in the destination. If the only available tool would wake, resume, or otherwise start work there, do not send it: store the prepared delta in the registry, tell the user exactly what could not be automated, and label the item `waiting-on-you`. Memory propagation never uses a task-triggering send. A separately authorized work message is a different one-off action outside this skill, not a propagation exception.

**Capability honesty.** You can only discover, read, or message another task if the running harness exposes tools that do it. Check first. If those tools are absent, record the relationship, tell the user what could not be automated, and give them the delta text to carry themselves — that item is `waiting-on-you`, not `blocked`, because nothing external is broken. Never imply a message was delivered when it was not. Registry schema, delta format, and failure wording: [references/related-tasks.md](references/related-tasks.md).

## What this skill does not do

Installing it does not start a background daemon, does not create a cross-task message bus, does not create a persistent database, and does not guarantee automatic invocation. The optional Full outstanding items UI is an explicit per-ledger loopback process; its only durable item data is the task-owned JSON file, while its private connection file preserves the same local URL across deliberate restarts. The process snapshots and fingerprints its generic browser assets and fingerprints its local server runtime at launch; `start` replaces an API-healthy process when either fingerprint differs from the installed plugin instead of reusing stale code. On Codex, that process may read current titles for exact transferred task IDs through the local app-server protocol; it never reads task content or sends a task message. Cross-task propagation works only through tools the current harness already provides.

It does not grant you any authority over the user's work. It does not know what the user actually has the appetite for. A suggestion is a judgement made from what they said in this task, offered once and dropped if ignored — not a prediction, not a schedule, and not a claim about what matters most in their life.

## Worked examples

Synthetic transcripts covering capture, intentional reminders, status promotion, overflow, `waiting-on-you` against `blocked`, a memory-only cross-task delta, and a suggestion that is offered, declined, and then authorized by name: [references/worked-examples.md](references/worked-examples.md).
