# Codex global rule

Append the block below to `~/.codex/AGENTS.md`. Optional — the skill's own `description` already carries its trigger conditions — but a global rule makes invocation more reliable in long tasks where the description alone may not fire.

It does not make invocation guaranteed. Nothing does.

The first bullet is the important one. Everything else is formatting.

```markdown
## Outstanding items

Use the `outstanding-items` skill in any task where I make more than one request.

- The outstanding items are mine. Being on the list, being suggested, being
  ranked first, being old, being urgent, or being labelled `in-progress` is
  never permission to work on something. Only my current message naming the
  item is — it covers that item only and ends with the response turn.
- Capture every request, correction, and aside as an item, including asides that
  are unrelated to what you are currently doing. Never refuse a reminder for
  being off-topic. If I say "add this to outstanding items" or "remember this",
  record it, tell me it is recorded, and stop there.
- Give each item a permanent `OI-n` ID. Never renumber.
- In a Git-project task, create or resolve this chat's ledger under
  `.outstanding-items/<task-id>/`, add `/.outstanding-items/` to the root
  `.gitignore`, and keep project storage on unless I explicitly opt out.
- Record each item's source when it is created: `user-requested` only when I
  explicitly tell you to add that specific thing to Outstanding Items. If I
  merely request or discuss the work and you capture it automatically, use
  `agent-added`. Use `unknown-legacy` only when an older capture source cannot
  be proved.
- Automatically add every concrete unresolved thing I still need to review,
  decide, provide, verify, or return to as `agent-added`, even when I did not
  ask to add it to Outstanding Items. Before saying there are no outstanding
  items, check the current results, blockers, decisions, and unverified outcomes
  for such a loose end. Never invent filler or speculative work when nothing remains.
- Keep the ledger silently while you work, then end the **final response of the
  turn** with one compact recommendation that starts directly with the single item you think I should
  do next, immediately followed by a compact `You` or `Agent` source marker,
  at most one line about it, and nothing else. No list, no counts, no
  section headings, no reminders, no Done section. Never put it in commentary,
  progress notes, partial updates, or status messages.
- When a local HTML editor is running for this ledger, link it as
  **Full outstanding items** on its own line, once, as the footer's last line,
  using the exact URL it printed. With no live editor, write no link line, and
  never link raw JSON or Markdown. Keep one task-owned JSON ledger as the source
  of truth, and let it hold everything the footer does not show.
- Never offer the same item twice. If I ignored or declined it, choose another
  eligible one, or say plainly that there is nothing new to suggest — unless I
  ask what to do next, which clears the slate.
- If I ask for the whole list, put it in the answer itself and keep the footer to
  one line.
- Use only these labels: requested, planned, in-progress, implemented, verified,
  waiting-on-you, blocked, reminder, dropped. Never label something `verified`
  without evidence you observed now or exact completion evidence already stored
  in the canonical item and checked now; never treat a label as a licence to carry on.
- Whenever you interact with the ledger, reconcile completion evidence and move
  genuinely verified or explicitly dropped items to Done while preserving the
  proof. Apply this to every provenance; never leave completed `Agent` work open
  merely to demand redundant acceptance. Leave implemented-but-unverified,
  waiting-on-you, blocked, reminders, transferred, and unfinished work open.
- Whenever you open or update the ledger, reconcile its order. Sort automatic
  items by actionable status and newest relevance, but preserve every explicit
  drag or keyboard placement recorded as manual order intent. Never rearrange
  the ledger merely to match the footer recommendation.
- If the only thing missing is me — a click, an approval, a key, a choice — that
  is `waiting-on-you` with the exact action, not `blocked`. Keep `blocked` for a
  real external wall you already tried to get around.
- Something I parked on purpose is a `reminder`. Keep it in the ledger, do not
  start it, do not suggest it, and do not nag me about it.
- Choose the one item you show me with judgement — dependencies, where my
  attention already is, effort against value, what I can actually pick up now,
  real urgency, and how much I am carrying. Name a small first step, address it
  to me, then wait. Never rearrange the ledger to match it, and never start it
  yourself.
- You may record a genuinely useful relationship to another task locally. That
  link alone never authorizes messaging, waking, starting, reprioritising, or
  altering the other task; ask me separately before sending any memory update.
- For a non-project task, ask before writing a durable backlog file.
```

## Shorter version

If your global instructions are already crowded:

```markdown
## Outstanding items
Use the `outstanding-items` skill whenever I make more than one request in a task.
Capture unrelated asides too, and end the final response of each turn with one
compact recommendation naming a single suggested item — never in commentary
or progress messages, and never as a list, a count, or a Done section. Link a
running local editor as **Full outstanding items** on the last line, or write no
link at all. The list is mine: never start, resume, continue, investigate,
research, prepare, do pre-work for, dispatch, route, hand off, or complete an item
unless I have just told you to, naming it. Never mark something `verified` without
evidence you saw. On every ledger interaction, move exact proven completions to
Done instead of asking me to accept finished Agent work. Never say `blocked` when
it is really waiting on me, and never repeat a suggestion I ignored. In a Git
project, keep this chat's ledger under the Git-ignored `.outstanding-items/`
directory by default unless I opt out.
```

## Turning it off for one task

Say so in the task. The skill stops appending the footer when asked and keeps the ledger for the rest of the session.

## Checking it worked

Start a task, make two unrelated requests, and look at the end of the final response. If it does not start directly with one `**OI-n …** — status` recommendation:

1. Confirm the file exists: `ls ~/.codex/skills/outstanding-items/SKILL.md`
2. Confirm the frontmatter is intact — `name:` and `description:` between `---` fences.
3. Ask directly: "use the outstanding-items skill". If that works, discovery is the issue, not installation, and the global rule above is what to strengthen.

Then look at its shape. One footer per turn, two or three lines, one `OI-n` in it. If the same block also appears in a progress or commentary message before the answer, the final-response rule has not landed; if it comes back as sections, counts, or a Done pile, the compact-footer rule has not landed.

Then check the other half, which matters more: say "add something to outstanding items" and see whether the reply records it and stops. If the agent starts the work instead, the ownership rule has not landed — put the first bullet at the very top of your global instructions.
