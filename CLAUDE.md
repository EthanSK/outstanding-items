# CLAUDE.md — Outstanding Items

Instructions for Claude Code working **in this repository**, plus the integration snippets to copy **out** of it. The Codex equivalent is [`AGENTS.md`](AGENTS.md); both files describe the same project and are kept in sync deliberately.

## What this repository is

A prompt-level skill, a static website, and an optional Python-standard-library local ledger editor. There is no build step or third-party runtime dependency. The canonical skill, generic editor assets, and loopback server live in `skill/outstanding-items/` and are copied verbatim into `~/.claude/skills/outstanding-items/` by `scripts/install.sh --target claude`.

Everything here is built around one rule:

> **Rule #1 — the outstanding items belong to the user.** Listing, sorting, ranking, syncing, or recommending an item never authorizes an agent to start, resume, continue, investigate, research, prepare, do pre-work for, dispatch, route, or complete it. Only a fresh, explicit instruction from the user naming a specific item does.

## Ground rules for changes here

1. **`skill/outstanding-items/SKILL.md` is the source of truth.** Never edit the installed copy under `~/.claude/skills/`; edit here and reinstall.
2. **Rule #1 stays at the top of `SKILL.md`,** ahead of the continuous-improvement contract. Nothing may imply that a backlog entry, a status, a ranking, or a cross-task delta is permission to act.
3. **Keep safeguards in `SKILL.md`.** References carry schemas, worked examples, and edge cases. Anything that prevents harm, prevents a false claim, or protects the user's authority stays in the core file.
4. **References stay one level deep** and are linked directly from `SKILL.md`.
5. **All identifiers are synthetic** — `task_EXAMPLE_xxxx`, `sess_EXAMPLE_xxxx`. A check enforces it.
6. **No personal state**: no live backlogs, real IDs, absolute machine paths, credentials, or private URLs.
7. **Truthful capability claims only.** Installation starts no process. The optional Full outstanding items editor is a per-ledger loopback process backed by one JSON file, not a daemon, message bus, or database. There is no guaranteed invocation. The public website has no analytics, third-party runtime dependencies, or outbound application requests.
8. **No runtime dependencies on the site**, and all internal links relative so it works under `/outstanding-items/`.
9. **Keep the public surfaces synchronized.** Whenever user-visible behaviour, setup, status, or limitations change, review `README.md` and `docs/` in the same change and update both wherever the public story changed. If either surface needs no edit, record what was checked rather than assuming. When publication is authorized, do not stop at a successful push: wait for the GitHub Pages build, verify the live HTTPS page comes from the expected commit, and compare deterministic live/local bytes where practical.
10. **Run the checks before claiming success:**

```sh
./scripts/check.sh
```

## Working on the outstanding items of this repository

Any list of remaining work produced here belongs to the person you are talking to. Record it, show it, and stop. Do not start the next one because it is obvious, small, first in the list, or already labelled `in-progress`. Ask which one, and wait for it to be named.

## Skill authoring notes specific to Claude Code

- Claude Code discovers skills from the YAML frontmatter `name` and `description`. The description is the only thing read before the skill loads, so trigger conditions must live inside it — and so must the ownership claim, because a description that reads like a task queue invites exactly the failure this skill prevents.
- The body of `SKILL.md` should read as an operating contract — imperative, short, scannable. It is loaded into context whole.
- Progressive disclosure is the point of `references/`: the model reads them only when a decision needs them. Do not inline their content back into `SKILL.md`.
- `agents/openai.yaml` sits in the same directory. Claude Code ignores it; leave it in place so a single source tree serves both harnesses.

## Where things live

| Path | Notes |
| --- | --- |
| `skill/outstanding-items/SKILL.md` | Always-loaded operating contract, Rule #1 first. |
| `skill/outstanding-items/references/` | `authority.md`, `status-labels.md`, `next-action.md` (choosing the one item), `backlog-artifact.md`, `ledger-ui.md`, `related-tasks.md`, `worked-examples.md`. |
| `docs/` | GitHub Pages site. `docs/assets/app.js` renders the ledger demo from JSON embedded in `docs/index.html`. |
| `scripts/` | POSIX `sh`, dry-runnable, non-destructive. |
| `tests/run_checks.py` | Standard library only. Add a check when you add an invariant, including the authority ones. |

## Copy this into your global Claude Code instructions

Append to `~/.claude/CLAUDE.md` to make the skill fire without being asked. Optional; the skill's `description` already carries its triggers.

```markdown
## Outstanding items

Use the `outstanding-items` skill in any session where I make more than one request.

- The outstanding items are mine. Being on the list, being suggested, being
  ranked first, or being labelled `in-progress` is never permission to work on
  something. Only my current message naming the item is, and that authority
  ends with the response turn.
- Capture every request, correction, and aside as an item, including asides that
  are unrelated to the current work. Never refuse a reminder for being
  off-topic, and never start something because I asked you to remember it.
- Add an agent-created item only for a concrete loose end, dependency, risk, or
  follow-up that is genuinely useful and would otherwise be lost. Never clutter
  my ledger with speculative improvements or possible work.
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
  JSON or a Markdown list.
- Use only these labels: requested, planned, in-progress, implemented, verified,
  waiting-on-you, blocked, reminder, dropped. Never label something `verified`
  without evidence you observed in this session.
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
- Tell another session about something only as a memory update that starts
  nothing there. Ask me before using anything that would wake or dispatch it.
- Ask before writing a backlog file anywhere.
```

Ready-to-paste copy: [`examples/global-rules/claude-code-claude-md.md`](examples/global-rules/claude-code-claude-md.md).

## Using the skill in one project only

Put this in that project's own `CLAUDE.md` instead of the global file:

```markdown
## Task hygiene

Work here arrives in bursts of half-related requests. Use the `outstanding-items`
skill for every session in this repository and end the final response of each
turn with one compact recommendation naming a single suggested item, with its
compact `You` or `Agent` source marker immediately after the item — never in
commentary or progress messages, and never as a list, a count, or a Done
section. The list is mine: capture it, keep it out of the chat, suggest at most
one next move, and wait for my current message to name the item you should
start. Authority ends with that response turn. Past seven open items for me, ask
before writing `outstanding-items.json` and start its local HTML editor. Link it
as **Full outstanding items** on the footer's last line, and add its private
ledger/runtime files to `.git/info/exclude`.
```

The skill still has to be installed. A project instruction can ask for it; it cannot supply it.

## Honesty contract

When describing this project anywhere:

- "Copies files into your skills directory" rather than a description of a service.
- "Registered (manual)" when no task tools exist, rather than "notified".
- "Prepared (not sent)" when the only delivery mechanism would wake the other session.
- "Makes invocation likelier" rather than a promise that it happens every time.
- "Implemented" for work done, "verified" only for work checked.
- "Waiting on you" when the obstacle is a person; "blocked" only for a real wall.
- "Suggests" for the curation feature — a judgement offered once to the user, not a plan or a prediction.
- "One suggested item" for the footer, never "a summary of your list". It shows one thing; the ledger and its editor hold everything.
- Never call the ledger a work queue, and never imply that maintaining it is permission to work through it.

This project exists to stop overstatement, and to stop assumed permission. The repository holds itself to the same standard.
