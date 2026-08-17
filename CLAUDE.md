# CLAUDE.md — Outstanding Items

Instructions for Claude Code working **in this repository**, plus the integration snippets to copy **out** of it. The Codex equivalent is [`AGENTS.md`](AGENTS.md); both files describe the same project and are kept in sync deliberately.

## What this repository is

A skills-only OpenAI plugin, a Claude Code plugin, a static website, and an optional Python-standard-library local ledger editor. There is no build step or third-party runtime dependency. Both plugin formats package the same canonical skill under `plugins/outstanding-items/skills/outstanding-items/`; direct standalone installation is deliberately unsupported so each harness has one discovery path.

Everything here is built around one rule:

> **Rule #1 — the outstanding items belong to the user.** Listing, sorting, ranking, syncing, or recommending an item never authorizes an agent to start, resume, continue, investigate, research, prepare, do pre-work for, dispatch, route, or complete it. Only a fresh, explicit instruction from the user naming a specific item does.

## Ground rules for changes here

1. **`plugins/outstanding-items/skills/outstanding-items/SKILL.md` is the source of truth.** Never edit the installed copy under `~/.claude/skills/` or a plugin cache; edit here and reinstall.
2. **Rule #1 stays at the top of `SKILL.md`,** ahead of the continuous-improvement contract. Nothing may imply that a backlog entry, a status, a ranking, or a cross-task delta is permission to act.
3. **Keep safeguards in `SKILL.md`.** References carry schemas, worked examples, and edge cases. Anything that prevents harm, prevents a false claim, or protects the user's authority stays in the core file.
4. **References stay one level deep** and are linked directly from `SKILL.md`.
5. **All identifiers are synthetic** — `task_EXAMPLE_xxxx`, `sess_EXAMPLE_xxxx`. A check enforces it.
6. **No personal state**: no live backlogs, real IDs, absolute machine paths, credentials, or private URLs.
7. **Truthful capability claims only.** Installation starts no process. The optional Full outstanding items editor is a per-ledger loopback process backed by one JSON file, not a daemon, message bus, or database. There is no guaranteed invocation. The public website has no analytics, third-party runtime dependencies, or outbound application requests.
8. **No runtime dependencies on the site**, and all internal links relative so it works under `/outstanding-items/`.
9. **Keep the public surfaces synchronized.** Whenever user-visible behaviour, setup, status, or limitations change, review `README.md` and `docs/` in the same change and update both wherever the public story changed. If either surface needs no edit, record what was checked rather than assuming. When publication is authorized, do not stop at a successful push: wait for the GitHub Pages build, verify the live HTTPS page comes from the expected commit, and compare deterministic live/local bytes where practical.
10. **Keep plugin versions synchronized.** Whenever anything inside `plugins/outstanding-items/` changes for a public update, bump the semantic version in both plugin manifests to the same value. OpenAI and Claude Code cache installed plugin versions; leaving the version unchanged can strand users on stale files.
11. **Run the checks before claiming success:**

```sh
./scripts/check.sh
```

12. **Refresh after every local repository change, whoever made it.** At the start of a task, inspect `git status --short` so changes Ethan made locally are not mistaken for already-installed plugin state. Before finishing any task that leaves a coherent local change anywhere in this repository—whether made by Ethan, this agent, or another agent—run `python3 scripts/sync_plugin_dev.py`. Do not finish until it reports the cache-busted installed plugin is verified and no manifest-owned standalone duplicate remains. It validates the whole repository, reinstalls the Codex plugin, restores the authored versions, verifies the installed copy, and safely removes any manifest-owned legacy standalone copy. Never install conflicted or obviously half-written work; preserve it and report the blocker instead. Do not hand-edit plugin caches or marketplace configuration.

## Working on the outstanding items of this repository

Any list of remaining work produced here belongs to the person you are talking to. Record it, show it, and stop. Do not start the next one because it is obvious, small, first in the list, or already labelled `in-progress`. Ask which one, and wait for it to be named.

## Skill authoring notes specific to Claude Code

- Claude Code discovers skills from the YAML frontmatter `name` and `description`. The description is the only thing read before the skill loads, so trigger conditions must live inside it — and so must the ownership claim, because a description that reads like a task queue invites exactly the failure this skill prevents.
- The body of `SKILL.md` should read as an operating contract — imperative, short, scannable. It is loaded into context whole.
- Progressive disclosure is the point of `references/`: the model reads them only when a decision needs them. Do not inline their content back into `SKILL.md`.
- `agents/openai.yaml` sits in the canonical skill directory. Claude Code ignores it; leave it in place so a single source tree serves both harnesses.
- `.claude-plugin/plugin.json` packages the skill for native Claude Code plugin installation. `.codex-plugin/plugin.json` packages the same directory for OpenAI; neither contains a second copy of the workflow.

## Where things live

| Path | Notes |
| --- | --- |
| `plugins/outstanding-items/.claude-plugin/plugin.json` | Claude Code plugin identity. |
| `plugins/outstanding-items/.codex-plugin/plugin.json` | OpenAI plugin identity. |
| `plugins/outstanding-items/skills/outstanding-items/SKILL.md` | Always-loaded operating contract, Rule #1 first. |
| `plugins/outstanding-items/skills/outstanding-items/references/` | `authority.md`, `status-labels.md`, `next-action.md` (choosing the one item), `backlog-artifact.md`, `ledger-ui.md`, `related-tasks.md`, `worked-examples.md`. |
| `.claude-plugin/marketplace.json` | Claude Code repo marketplace. |
| `.agents/plugins/marketplace.json` | OpenAI repo marketplace. |
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
- Automatically add every concrete unresolved thing I still need to review,
  decide, provide, verify, or return to as `Agent`, even when I did not ask to
  add it to Outstanding Items. Before saying there are no outstanding items,
  check the current results, blockers, decisions, and unverified outcomes for
  such a loose end. Never invent filler or speculative work when nothing remains.
- Keep an actionable frontier whenever active work remains. If a parent item is
  blocked, capture its nearest useful prerequisite, workaround, decision, or
  sensible time/condition-bound check as a separate `Agent` item and record what
  it unblocks. Prefer another existing actionable item; never invent busywork.
- Use `You` / `user-requested` only when I explicitly tell you to add that
  specific thing to Outstanding Items. If I merely request or discuss the work
  and you capture it automatically, use `Agent` / `agent-added`.
- Give each item a permanent internal `OI-n` key and P0–P3 priority. Show the
  composite `OI-n-Px` reference to the user; changing priority never renumbers
  the permanent key. Default unclassified legacy items to P2, never guessed urgency.
- In a Git-project session, create or resolve this chat's canonical ledger under
  `.outstanding-items/<task-id>/` before the first capture, add
  `/.outstanding-items/` to the root `.gitignore`, and keep project storage on
  unless I explicitly opt this chat out.
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
  without evidence you observed now or exact completion evidence already stored
  in the canonical item and checked now.
- Whenever you interact with the ledger, reconcile completion evidence and move
  genuinely verified or explicitly dropped items to Done while preserving the
  proof. Apply this to every provenance; never leave completed `Agent` work open
  merely to demand redundant acceptance. Leave implemented-but-unverified,
  waiting-on-you, blocked, reminders, transferred, and unfinished work open.
- Whenever you open or update the ledger, reconcile its order. Sort automatic
  items by actionable status, then P0–P3 priority, then newest relevance, but preserve every explicit
  drag or keyboard placement recorded as manual order intent. Never rearrange
  the ledger merely to match the footer recommendation.
- If the only thing missing is me — a click, an approval, a key, a choice — that
  is `waiting-on-you` with the exact action, not `blocked`. It is a perfectly
  good thing to suggest.
- Something I parked on purpose is a `reminder`. Keep it in the ledger and do
  not start it. Prefer ordinary actionable work, but if it is the only active
  unfinished item it may be the recommendation without changing its status.
- Choose that one item with judgement — dependencies, where my attention already
  is, effort against value, what I can actually pick up now, real urgency, and
  how much I am carrying. Never rearrange the ledger to match the advice.
- Rotate before repeating. If I ignored or declined an item, exclude it while
  another actionable open item exists. Once every alternative has been
  considered, recommend the best still-open item again with a current first
  step rather than going silent. Asking what to do next clears the slate.
- If I ask for the whole list, put it in the answer itself and keep the footer
  to one line.
- Tell another session about something only as a memory update that starts
  nothing there. Ask me before using anything that would wake or dispatch it.
- For a non-project session, ask before writing a durable backlog file.
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
start. `You` means I explicitly asked for that Outstanding Items entry; a normal
work request captured automatically is `Agent`. Authority ends with that
response turn. Create or resolve this chat's ledger under
`.outstanding-items/<task-id>/outstanding-items.json` before the first capture,
add `/.outstanding-items/` to the repository's `.gitignore`, and keep project
storage on unless I explicitly opt out. Link a running editor as **Full
outstanding items** on the footer's last line.
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
