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
- Keep the ledger silently while you work, then end the **final response of the
  turn** with one Outstanding footer: Outstanding for you, Waiting on you,
  Intentional reminders, then the crossed-out Done section. Never put it in
  commentary, progress notes, partial updates, or status messages.
- When a local HTML editor is running for this ledger, link it as
  **Full outstanding items** on its own line directly below the Outstanding
  header and again after the last section, using the exact URL it printed.
  With no live editor, write neither line, and never link raw JSON or Markdown.
  Keep one task-owned JSON ledger as the source of truth.
- Use only these labels: requested, planned, in-progress, implemented, verified,
  waiting-on-you, blocked, reminder, dropped. Never label something `verified`
  without evidence you observed in this task, and never treat a label as a
  licence to carry on.
- If the only thing missing is me — a click, an approval, a key, a choice — that
  is `waiting-on-you` with the exact action, not `blocked`. Keep `blocked` for a
  real external wall you already tried to get around.
- Something I parked on purpose is a `reminder`. Keep it visible, do not start
  it, and do not nag me about it.
- When I ask what to do next, come back after a gap, or sound overloaded,
  suggest one item and a small first step in a single `**Suggested for you**`
  line addressed to me, then wait. Never rearrange the ledger to match it, and
  never start it yourself.
- Anything another task should know is a memory update that starts nothing
  there. Ask me first before using a tool that would wake or dispatch it.
- Ask before writing a backlog file anywhere.
```

## Shorter version

If your global instructions are already crowded:

```markdown
## Outstanding items
Use the `outstanding-items` skill whenever I make more than one request in a task.
Capture unrelated asides too, and end the final response of each turn with one
Outstanding footer — never in commentary or progress messages.
The list is mine: never start, resume, continue, investigate, research, prepare,
do pre-work for, dispatch, route, hand off, or complete an item unless I have just
told you to, naming it. Never mark something `verified` without evidence you saw,
and never say `blocked` when it is really waiting on me. If I ask what is next,
suggest one thing and wait.
```

## Turning it off for one task

Say so in the task. The skill stops appending the footer when asked and keeps the ledger for the rest of the session.

## Checking it worked

Start a task, make two unrelated requests, and look at the end of the final response. If there is no `**Outstanding**` block:

1. Confirm the file exists: `ls ~/.codex/skills/outstanding-items/SKILL.md`
2. Confirm the frontmatter is intact — `name:` and `description:` between `---` fences.
3. Ask directly: "use the outstanding-items skill". If that works, discovery is the issue, not installation, and the global rule above is what to strengthen.

One block per turn is the other thing to look for. If the same list also appears in a progress or commentary message before the answer, the final-response rule has not landed.

Then check the other half, which matters more: say "add something to outstanding items" and see whether the reply records it and stops. If the agent starts the work instead, the ownership rule has not landed — put the first bullet at the very top of your global instructions.
