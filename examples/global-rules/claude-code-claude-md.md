# Claude Code global rule

Append the block below to `~/.claude/CLAUDE.md`. Optional — the skill's `description` already carries its trigger conditions — but a global rule makes invocation more reliable in long sessions.

It does not make invocation guaranteed. Nothing does.

The first bullet is the one that matters. The rest is formatting.

```markdown
## Outstanding items

Use the `outstanding-items` skill in any session where I make more than one request.

- The outstanding items are mine. Being on the list, being suggested, being
  ranked first, being old, being urgent, or being labelled `in-progress` is
  never permission to work on something. Only my current message naming the
  item is — it covers that item only and ends with the response turn.
- Capture every request, correction, and aside as an item, including asides that
  are unrelated to the current work. Never refuse a reminder for being
  off-topic. If I say "add this to outstanding items" or "remember this", record
  it, tell me it is recorded, and stop there.
- Give each item a permanent `OI-n` ID. Never renumber.
- Record each item's source when it is created: `user-requested` only when I
  explicitly tell you to add that specific thing to Outstanding Items. If I
  merely request or discuss the work and you capture it automatically, use
  `agent-added`. Use `unknown-legacy` only when an older capture source cannot
  be proved.
- Add an `agent-added` item only for a concrete loose end, dependency, risk, or
  follow-up that is genuinely useful to me and would otherwise be lost. Do not
  fill my ledger with speculative improvements or possible work.
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
  without evidence you observed in this session, and never treat a label as a
  licence to carry on.
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
- You may record a genuinely useful relationship to another session locally.
  That link alone never authorizes messaging, waking, starting, reprioritising,
  or altering the other session; ask me separately before any memory update.
- Ask before writing a backlog file anywhere.
```

## Shorter version

```markdown
## Outstanding items
Use the `outstanding-items` skill whenever I make more than one request in a session.
Capture unrelated asides too, and end the final response of each turn with one
compact recommendation naming a single suggested item — never in commentary
or progress messages, and never as a list, a count, or a Done section. Link a
running local editor as **Full outstanding items** on the last line, or write no
link at all. The list is mine: never start, resume, continue, investigate,
research, prepare, do pre-work for, dispatch, route, hand off, or complete an item
unless I have just told you to, naming it. Never mark something `verified` without
evidence you saw, and never say `blocked` when it is really waiting on me. Never
repeat a suggestion I ignored.
```

## Turning it off for one session

Say so. The skill stops appending the footer when asked and keeps the ledger for the rest of the session.

## Checking it worked

Make two unrelated requests in one session and look at the end of the final response. If it does not start directly with one `**OI-n …** — status` recommendation — or if it comes back as a labelled heading, multi-section list, count, or Done pile — or if the same block also shows up in the progress messages before it:

1. Confirm the file exists: `ls ~/.claude/skills/outstanding-items/SKILL.md`
2. Run `/skills` and look for `outstanding-items` in the list.
3. Confirm the frontmatter is intact — `name:` and `description:` between `---` fences.
4. Ask directly: "use the outstanding-items skill". If that works, the issue is discovery rather than installation, and the global rule above is what to strengthen.

Then test the ownership half: say "remember that I need to rotate the staging credentials" and watch what happens. The correct reply records it and stops. If anything starts rotating, move the first bullet to the top of your global file.
