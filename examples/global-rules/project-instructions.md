# Per-project rule

Use this when you want the ledger in one repository rather than everywhere. Paste it into that project's `AGENTS.md` (Codex), `CLAUDE.md` (Claude Code), or both.

The skill must still be installed. A project instruction can ask for a skill; it cannot supply one.

```markdown
## Task hygiene

Work in this repository arrives in bursts of half-related requests. Use the
`outstanding-items` skill for every session here.

- The outstanding items are mine. Keeping the list, sorting it, or suggesting
  something from it is never permission to start, resume, investigate, research,
  prepare, do pre-work for, dispatch, route, or complete it. Wait until I name an
  item and tell you to go in the current message.
- Keep the ledger silently while you work and put one compact recommendation
  at the end of the final response of each turn, starting directly with the single item you think I
  should do next, at most one line about it, and nothing else. No list, no
  counts, no section headings, no Done section. Commentary and progress messages
  carry none of it.
- Capture asides that have nothing to do with the current change. Recording
  something is the whole job when I only asked you to record it.
- Record `user-requested` only when I explicitly ask to add that specific thing
  to Outstanding Items. A normal work request captured automatically is
  `agent-added`; use `unknown-legacy` only when an old capture source cannot be
  proved.
- Automatically add every concrete unresolved thing I still need to review,
  decide, provide, verify, or return to as `agent-added`. Before saying there
  are no outstanding items, check current results, blockers, decisions, and
  unverified outcomes for anything omitted. Never invent filler or speculative work.
- Past seven open items for me, ask before writing `outstanding-items.json` and
  start its local HTML editor. Link it as **Full outstanding items** on the
  footer's last line, using the exact URL it printed, and add the private
  ledger/runtime files to `.git/info/exclude` rather than to `.gitignore`. That
  editor is where the rest of the list lives.
- Never label an item `verified` without a passing check from this repository's
  test suite, and never treat `in-progress` from an earlier turn as a reason to
  carry on in this one.
- Whenever you interact with the ledger, reconcile completion evidence and move
  genuinely verified or explicitly dropped items to Done while preserving the
  proof. Never leave completed `Agent` work open merely to demand redundant
  acceptance; leave implemented-but-unverified and unfinished work open.
- Whenever you open or update the ledger, reconcile its order. Sort automatic
  items by actionable status and newest relevance, but preserve every explicit
  drag or keyboard placement recorded as manual order intent.
- Anything needing a review approval, a merge button, or a secret from me is
  `waiting-on-you` with the exact action. `blocked` means an upstream wall you
  already tried to route around.
- The footer's one item is a suggestion, not a plan: one item, one small step,
  then stop. Do not repeat one I ignored or declined, and say there is nothing
  new to suggest rather than inventing a pick.
```

## Variant: repositories with a strict review culture

```markdown
## Task hygiene

Use the `outstanding-items` skill. Each turn ends with one compact recommendation
in the final response only, starting directly with one suggested item and nothing else.

`verified` in this repository means one specific thing: `make check` passed on
the current working tree, and you saw the output. Anything else is
`implemented`. Reviewers read that one line, so an inflated status is a review
problem, not a formatting one.

`blocked` is equally strict: it means an external wall, with the attempted
route recorded next to it. Waiting on a human reviewer is `waiting-on-you`.

Nothing in the footer is a work order. Changes start when I ask for them by
name, in the message where I ask.
```

## Variant: research and writing repositories

```markdown
## Task hygiene

Use the `outstanding-items` skill. Requests here are usually vague, plural, and
arrive out of order — capture them verbatim and do not tidy the phrasing.

Half of what I say is thinking out loud rather than a request. Put it on the
list, show me one thing at the end of each answer, and let me choose what gets
picked up. Give me the whole list in the answer itself when I ask for it.

`verified` means I confirmed it, not that the draft reads well. Keep dropped
items struck through in the ledger so the reasoning stays legible later.
```

## What not to put in a project instruction

- Real task or session IDs from your own history.
- Absolute paths from your machine.
- Anything that turns the ledger into a queue — "work through the open items", "start the top one when you have capacity", "keep going until the list is empty". That is the one thing this skill exists to prevent.
- Anything that puts the list back throughout the conversation — "show me everything each turn", "include the done items", "add a progress count". The footer is one item on purpose; ask for the full list when you want it.
- Anything about notifying other tasks. That depends on the harness at runtime, not on the repository.
