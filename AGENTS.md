# AGENTS.md — Outstanding Items

Instructions for agents working **in this repository**, plus the integration snippets to copy **out** of it. Codex reads `AGENTS.md`; the equivalent file for Claude Code is [`CLAUDE.md`](CLAUDE.md).

## What this repository is

A skills-only OpenAI plugin, a Claude Code plugin, a static public website, and an optional Python-standard-library local ledger editor. There is no build step or third-party runtime dependency. Both plugin formats package the same canonical skill under `plugins/outstanding-items/skills/outstanding-items/`; direct standalone installation is deliberately unsupported so each harness has one discovery path.

The product it describes has one non-negotiable rule, and every file here has to agree with it:

> **Rule #1 — the outstanding items belong to the user.** Listing, sorting, ranking, syncing, or recommending an item never authorizes an agent to start, resume, continue, investigate, research, prepare, do pre-work for, dispatch, route, or complete it. Only a fresh, explicit instruction from the user naming a specific item does.

## Ground rules for changes here

1. **`plugins/outstanding-items/skills/outstanding-items/SKILL.md` is the source of truth.** Do not edit an installed copy in `~/.codex/skills/`, `~/.claude/skills/`, or a plugin cache and expect it to survive. Edit here, then reinstall.
2. **Rule #1 stays at the top of `SKILL.md`,** above everything except the title, and ahead of the continuous-improvement contract. Nothing you add may weaken it, and nothing may imply that a ledger entry, a status, a ranking, or a delta is permission.
3. **Keep safeguards in `SKILL.md`.** References are for schemas, examples, and edge cases. If a rule prevents harm, prevents a false claim, or protects the user's authority, it belongs in the core file.
4. **References stay one level deep.** `references/*.md`, linked directly from `SKILL.md`. No reference-of-a-reference chains.
5. **Every identifier is synthetic.** Task and session IDs must match `task_EXAMPLE_xxxx` / `sess_EXAMPLE_xxxx`. A check fails the build otherwise.
6. **No personal state.** No live backlogs, no real task IDs, no absolute paths from anyone's machine, no credentials, no private URLs. Examples are invented, and stay invented.
7. **Truthful capability claims only.** Installation starts no process. The optional Full outstanding items editor is a per-ledger loopback process backed by one JSON file, not a daemon, cross-task bus, or database. Do not claim guaranteed invocation. The public site has no analytics, third-party runtime dependencies, or outbound application requests. `tests/run_checks.py` enforces these boundaries.
8. **The site has no runtime dependencies.** No CDN, no analytics, no fonts fetched over the network, no framework. All internal links are relative so the site works under `/outstanding-items/`.
9. **Keep the public surfaces synchronized.** Whenever user-visible behaviour, setup, status, or limitations change, review `README.md` and `docs/` in the same change and update both wherever the public story changed. If either surface needs no edit, record what was checked rather than assuming. When publication is authorized, do not stop at a successful push: wait for the GitHub Pages build, verify the live HTTPS page comes from the expected commit, and compare deterministic live/local bytes where practical.
10. **Keep plugin versions synchronized.** Whenever anything inside `plugins/outstanding-items/` changes for a public update, bump the semantic version in both plugin manifests to the same value. OpenAI and Claude Code cache installed plugin versions; leaving the version unchanged can strand users on stale files.
11. **Run the checks before you claim anything works.**

```sh
./scripts/check.sh
```

12. **Refresh after every local repository change, whoever made it.** At the start of a task, inspect `git status --short` so changes Ethan made locally are not mistaken for already-installed plugin state. Before finishing any task that leaves a coherent local change anywhere in this repository—whether made by Ethan, this agent, or another agent—run `python3 scripts/sync_plugin_dev.py`. Do not finish until it reports the cache-busted installed plugin is verified and no manifest-owned standalone duplicate remains. It validates the whole repository, reinstalls the plugin, restores the authored versions, verifies the installed copy, and safely removes any manifest-owned legacy standalone copy. Never install conflicted or obviously half-written work; preserve it and report the blocker instead. Do not hand-edit plugin caches or marketplace configuration.

## Working on the outstanding items of this repository

If a task here produces a list of remaining work, that list is the user's. Write it down, show it, and stop. Do not pick the next one up because it is obvious, small, ranked first, or already labelled `in-progress`. Ask, then wait to be told which one — by name.

## Where things live

| Path | Notes |
| --- | --- |
| `plugins/outstanding-items/.codex-plugin/plugin.json` | OpenAI plugin identity and presentation metadata. |
| `plugins/outstanding-items/.claude-plugin/plugin.json` | Claude Code plugin identity; no duplicate workflow content. |
| `plugins/outstanding-items/skills/outstanding-items/SKILL.md` | Always-loaded operating contract. Keep it imperative and short. |
| `plugins/outstanding-items/skills/outstanding-items/references/` | Conditional detail: authority, status labels, choosing the one item the footer names, backlog artifact, related tasks, worked examples. |
| `plugins/outstanding-items/skills/outstanding-items/scripts/ledger_ui.py` | Canonical JSON validation/migration, atomic persistence API, and loopback-only editor lifecycle. |
| `plugins/outstanding-items/skills/outstanding-items/assets/` | Generic Full outstanding items HTML, CSS, and JavaScript. Never put a real ledger here. |
| `plugins/outstanding-items/skills/outstanding-items/agents/openai.yaml` | OpenAI skill interface metadata. Claude Code ignores it. |
| `.agents/plugins/marketplace.json` | OpenAI repo marketplace pointing at the plugin package. |
| `.claude-plugin/marketplace.json` | Claude Code repo marketplace pointing at that same package. |
| `docs/` | GitHub Pages site. `docs/assets/app.js` renders the ledger demo from the JSON in `docs/index.html`. |
| `scripts/` | POSIX `sh` plus one Python-standard-library plugin sync command. Dry-runnable and non-destructive by default. |
| `tests/run_checks.py` | Python standard library only. Add a check when you add an invariant — especially an authority invariant. |

If you change the demo, change the JSON in `docs/index.html` — the static fallback and the interactive version are both generated from it, and a check compares them.

## Copy this into your global Codex instructions

Append to `~/.codex/AGENTS.md` to make the skill fire without being asked. Optional; the skill's own `description` already carries its trigger conditions.

```markdown
## Outstanding items

Use the `outstanding-items` skill in any task where I make more than one request.

- The outstanding items are mine. Being on the list, being suggested, being
  ranked first, or being labelled `in-progress` is never permission to work on
  something. Only my current message naming the item is, and that authority
  ends with the response turn.
- Capture every request, correction, and aside as an item, including asides that
  are unrelated to what you are currently doing. Never refuse a reminder for
  being off-topic, and never start something just because I asked you to
  remember it.
- Automatically add every concrete unresolved thing I still need to review,
  decide, provide, verify, or return to as `Agent`, even when I did not ask to
  add it to Outstanding Items. Before saying there are no outstanding items,
  check the current results, blockers, decisions, and unverified outcomes for
  such a loose end. Never invent filler or speculative work when nothing remains.
- Use `You` / `user-requested` only when I explicitly tell you to add that
  specific thing to Outstanding Items. If I merely request or discuss the work
  and you capture it automatically, use `Agent` / `agent-added`.
- Give each item a permanent `OI-n` ID. Never renumber.
- Keep the ledger silently while you work, then end the **final response of the
  turn** with one compact recommendation: the single item you think I should
  do next, immediately followed by its compact `You` or `Agent` source marker,
  at most one line about it, and nothing else. No list, no counts, no
  section headings, no reminders, no Done section. Never put it in commentary,
  progress notes, partial updates, or status messages.
- Whenever a local ledger UI is running, put the exact tokenized URL it printed
  on its own line as **Full outstanding items**, once, as the footer's last
  line. With no live UI, write no link line at all, and never point it at raw
  JSON or a Markdown list. One task-owned JSON file is authoritative; the footer
  quotes one item from it and the UI renders and mutates the rest.
- Use only these labels: requested, planned, in-progress, implemented, verified,
  waiting-on-you, blocked, reminder, dropped. Never label something `verified`
  without evidence you observed now or exact completion evidence already stored
  in the canonical item and checked now.
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
  is `waiting-on-you` with the exact action, not `blocked`. It is a perfectly
  good thing to suggest.
- Something I parked on purpose is a `reminder`. Keep it in the ledger, do not
  start it, do not suggest it, and do not nag me about it.
- Choose that one item with judgement — dependencies, where my attention already
  is, effort against value, what I can actually pick up now, real urgency, and
  how much I am carrying. Never rearrange the ledger to match the advice.
- Never offer the same item twice. If I ignored or declined it, pick another
  eligible one or say there is nothing new to suggest — unless I ask what to do
  next, which clears the slate.
- If I ask for the whole list, put it in the answer itself and keep the footer
  to one line.
- Tell another task about something only as a memory update that starts nothing
  there. Ask me before using anything that would wake or dispatch it.
- Ask before writing a backlog file anywhere.
```

Ready-to-paste copy: [`examples/global-rules/codex-agents-md.md`](examples/global-rules/codex-agents-md.md).

## Using the skill in a project repository

To turn the ledger on for one project rather than globally, put this in that project's own `AGENTS.md`:

```markdown
## Task hygiene

This project's work tends to arrive in bursts of half-related requests. Use the
`outstanding-items` skill for every session here, and end the final response of
each turn with one compact recommendation naming a single suggested item —
with its compact `You` or `Agent` source marker immediately after the item —
never in commentary or progress messages, and never as a list, a count, or a
Done section. The list is mine: record it, keep it out of the chat, suggest at
most one next move, and wait for my current message to name the item to start.
`You` means I explicitly asked for that Outstanding Items entry; a normal work
request captured automatically is `Agent`. Authority ends with that response
turn. If the list passes seven open items for
me, ask before writing `outstanding-items.json` and start its local HTML editor.
Link it as **Full outstanding items** on the footer's last line, and add its
private ledger/runtime files to `.git/info/exclude`.
```

The skill still has to be installed — a project instruction can ask for it, but it cannot supply it.

## Honesty contract

When describing this project, in commits, issues, docs, or replies:

- Say "copies files into your skills directory" rather than describing a service.
- Say "registered (manual)" when no task tools exist, rather than "notified".
- Say "prepared (not sent)" when the only delivery mechanism would wake the other task.
- Say "makes invocation likelier" rather than promising it happens every time.
- Say "implemented" for work you did and "verified" only for work you checked.
- Say "waiting on you" when the obstacle is a person, and keep "blocked" for a real wall.
- Say "suggests" for the curation feature. It is a judgement offered once to the user, not a plan, a priority system, or a prediction.
- Say "one suggested item" for the footer, never "a summary of your list". It shows one thing; the ledger and its editor hold everything.
- Never describe the footer as a work queue, and never describe an item as something you are about to get on with unless the user has just asked for it by name.

The project is about not overstating what happened, and about not assuming permission that was never given. The repository holds itself to the same standard.
