# Outstanding Items

**Outsource your memory — a curated work experience.**

An installable plugin for [Codex](https://developers.openai.com/codex/) and [Claude Code](https://www.anthropic.com/claude-code) that keeps the list of everything you asked for out of your way, and hands you one thing at a time — and, deliberately, nothing more.

**It holds the list.** You talk freely — including asides that have nothing to do with what the agent is currently doing — and every item is captured with a permanent ID. The list itself stays out of the conversation: it lives in the ledger, and in a local editor you can open in one click.

**It shows you one thing.** Each turn ends with a two- or three-line recommendation that starts directly with the single item it thinks you should do next, plus a link to everything else. There is no heading to read past. It appears once, in the final response, so progress chatter never turns into three copies of the same list — and there is no Done section, no counts, and no wall of items to skim past.

**It curates, and curation proposes.** That one line is a suggestion *for you*, with a small first step and, when it helps, a reason. **You decide, and you start it.**

> ### Rule #1 — the outstanding items belong to you
>
> The ledger is your record, not the agent's work queue. Listing, sorting, ranking, syncing, or recommending an item never authorizes the agent to start, resume, continue, investigate, research, prepare, do pre-work for, dispatch, route, or complete it. Only a fresh, explicit instruction from you naming a specific item does that. "Add this to outstanding items" means add it, and nothing else.

Website: <https://ethansk.github.io/outstanding-items/>

## Status

Working, and simple on purpose. This is a **skills-only plugin** built on the open Agent Skills format, with one small optional local editor: one canonical `SKILL.md` operating contract, eight focused references, and a standard-library HTML ledger UI. The same folder is packaged for OpenAI's plugin format and Claude Code's plugin format. Direct standalone installation is deliberately unsupported, so each harness has one discovery path and cannot surface duplicate copies. Installing the plugin starts nothing and opens no port. In a Git-project chat, its canonical per-chat JSON ledger lives under the project's ignored `.outstanding-items/` directory by default; project storage can be explicitly disabled. When you open the Full outstanding items view, one loopback-only process edits that task's canonical JSON file; it is not a cross-task service or database. The skill still grants the agent no authority over your work. It may record a genuinely useful cross-task relationship locally, but that link never authorizes contacting or changing the other task; sending even a memory-only delta needs a separate explicit instruction and a non-waking delivery mechanism.

## What it actually does

| Behaviour | What you see |
| --- | --- |
| Multi-request tracking | Every request in the task gets a permanent `OI-n` ID, in the order you said it. |
| Unrelated asides accepted | "Remind me to ask the design channel" is captured mid-task and never refused for being off-topic. |
| Capture without commission | Something added to the list is recorded, confirmed, and left alone until you say otherwise. |
| No lost loose ends | Any concrete unresolved review, decision, input, verification, or follow-up for you is captured automatically as **Agent**. The agent still never invents filler or speculative projects. |
| Strict source badges | **You** means you explicitly asked for that ledger entry. A normal work request captured automatically is **Agent**. |
| One footer per turn | Two or three lines at the end of the final response: one suggested item, an optional line about it, and a link to the rest. Commentary and progress messages stay clean. |
| Nothing else in the chat | No counts, no sections, no reminders, no Done list, no "+7 more". The full ledger is one click away instead of one scroll away. |
| Crossed-out Done group | Finished and cancelled items move to the bottom of the editor, struck through, so you can audit what happened without reading it every turn. |
| Automatic completion reconciliation | Every ledger interaction checks recorded proof and moves genuinely finished work to Done. Completed **Agent** items never stay open just to demand redundant acceptance. |
| Honest status labels | `requested` / `in-progress` / `implemented` / `verified` are four different amounts of proof, and the skill may not round them up. |
| Labels that are not licences | `in-progress` records the instruction that started it. When the turn ends, so does the permission. |
| Intentional reminders | Something parked on purpose is labelled `reminder` — visible, never started, never quietly retired, never nagged about. |
| A real difference between stuck and yours | Something needing your click, key, or approval is `waiting-on-you`, with the exact action. `blocked` is reserved for a genuine external wall. |
| One suggestion, for you | One item, one small possible first step, one sentence of reasoning — then it waits. Ignore it and it picks something else next time, or says nothing. |
| Canonical project-chat ledger | In a Git project, each chat gets one private `.outstanding-items/<task-id>/outstanding-items.json` by default, and the directory is added to `.gitignore`. An explicit flag turns project storage off. |
| Editable Full outstanding items | A quiet local list: click task text to edit it, drag or use keyboard controls to set a lasting manual position, and check it complete with a temporary Undo action. Completed items remain at the bottom. |
| A plain-words detail disclosure | Hover or focus the small caret above the drag grip—or tap it—and a short note explains the item without making the whole row noisy. |
| Auditable ownership transfer | Moving work to another task preserves its status and notes as read-only history here instead of pretending it was completed. |
| Registered related tasks | A useful relationship may be stored locally by title plus stable ID. It contacts nothing; a separately authorized memory-only delta still starts nothing. |

A real footer looks like this — once per turn, at the end of the final response:

```text
**OI-5 Add rate-limit docs to the handbook** `You` — planned
Draft the limits table first, about twenty minutes; nothing else is waiting on it.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

That is the whole thing. One item — the one it thinks you should do next — an optional line saying how to start and why, and a link to everything else. The other nine items, the reminders you parked, and everything you finished are all still there; they are in the editor, not in your chat.

The link is the exact URL the local editor printed. If no editor is running, that line simply is not there — the skill does not invent a URL to fill the space:

```text
**OI-8 Approve the staging deploy** `You` — waiting-on-you
Click approve in the deploy UI; it is the one thing left that only you can do.
```

When active work remains, the footer always names one item. Ignoring one suggestion rotates to another actionable item; after every alternative has been considered, the best still-open item returns with a useful current first step. A blocked parent never creates silence: the ledger captures its nearest useful prerequisite, workaround, decision, or sensible time/condition-bound check as a separate **Agent** item, then recommends from that actionable frontier. It does not invent busywork or pretend an external wait can be accelerated.

If the ledger has no open items at all, the agent first checks the current request, results, blockers, decisions, and unverified outcomes for anything concrete you still need to look at. A real loose end is added as **Agent**. Only a genuinely empty list says `**No outstanding items**`; the agent does not invent filler merely to avoid that honest result.

IDs are permanent. Nothing is ever renumbered, so a reference you made ten turns ago still points at the same thing. And if you want the whole list in the chat, ask for it — you get it in the answer, once, and the footer stays one line.

## Full outstanding items is an editor, not a raw file

Because the footer names one item, **Full outstanding items** is where the rest of it lives — a private local HTML view instead of a huge Markdown or JSON file. Active work sits under **Outstanding**. At rest, a row is its checkbox and task text. A tiny **You** or **Agent** pill flows immediately after the text when the origin is known, so it does not reserve a separate column or force early wrapping. **You** is deliberately strict: it appears only when you explicitly asked to add that specific thing to Outstanding Items. If you merely requested or discussed the underlying work and the agent captured it automatically, the pill is **Agent**. Hover the pill to read that full meaning. Older items keep their honest legacy provenance in the data without adding a noisy or invented badge to the page. Click the text to create an inline editor; no blank input exists before that interaction. Automatic items stay sensibly ordered by actionable status and newest relevance, so a fresh `waiting-on-you` item does not remain buried. Drag with the reorder grip or use the keyboard move controls to set a lasting manual position; automatic reconciliation leaves that chosen slot alone. Checking a task complete moves it to the bottom and shows a temporary snackbar with **Undo**.

The whole row no longer triggers item details on hover. A small caret sits above the existing drag grip, using that same action column instead of taking width from the task text. Hover or keyboard-focus the caret to preview the item's ID, friendly state phrase, and short action-first explanation; click or tap it where hover is unavailable. Double-click the row to keep the same note open, or focus the task text and press `Alt+Enter`; repeat the action without moving the pointer, use the caret, or press `Escape` to dismiss it. A single task-text click still edits. Explanations use imperative Git commit-subject style — `Write a LinkedIn post…`, not `This is the idea to…` — so they scan quickly when the title alone is not enough. Items saved before that field existed start their fallback with the item title, and every row's text is rendered as text, never as markup.

There is still only one ledger: the task-owned `outstanding-items.json`. The UI reads and atomically writes that file through a token-protected server bound to `127.0.0.1`; it stores no copy in the HTML or browser storage. Its private connection record keeps the same local URL through normal restarts, so an old tab reconnects instead of dying with `Failed to fetch`. The server snapshots and fingerprints its generic HTML, CSS, and JavaScript at launch; a later `start` replaces a missing or older UI instead of silently reusing it after a plugin refresh. Agent-side changes update the same JSON, and an open page notices a new revision within two seconds. If two edits race, the stale one is rejected and reloaded instead of overwriting newer work. Whenever an agent touches that ledger, it also checks the recorded evidence and moves genuinely verified or deliberately dropped items to Done. It does not leave completed **Agent** items open merely to ask you to accept proof it already has.

When you explicitly transfer ownership to another task, the original records stay in that JSON with their status and evidence unchanged. They move into a collapsed, read-only **Owned elsewhere** section, leave the active counts, and show the destination task title, stable task/session ID, and handoff date. On Codex, the local editor refreshes cached destination titles by exact ID when a task is renamed; it never reads the task's turns, wakes it, or sends it a message.

The generic HTML, CSS, and JavaScript ship with the skill, so no page regeneration is needed when the data changes. A migrated Markdown ledger is retained as a frozen source snapshot, then never updated again. See the [data model](plugins/outstanding-items/skills/outstanding-items/references/backlog-artifact.md) and [editor operations](plugins/outstanding-items/skills/outstanding-items/references/ledger-ui.md).

For a project-backed chat, the agent resolves the ledger before the first capture:

```sh
python3 ledger_ui.py project-ledger --project-root /path/to/project --task-id <stable-task-id>
```

Project storage is on by default. The command keeps chats separate, creates private `0700` directories and a `0600` ledger, and appends `/.outstanding-items/` to the root `.gitignore` exactly once. `--no-project-storage` is the explicit opt-out and writes nothing. Existing canonical ledgers are not silently copied when a project later enters scope, because two ledgers would be worse than one older location.

## Who owns what

This is the part the whole project is built around, so it is worth being blunt about it.

| Signal | Does it authorize the agent to start? |
| --- | --- |
| The item is on the list | No. |
| The item was suggested last turn as the next move | No. |
| The item is the highest priority, or sorted to the top | No. |
| The item is labelled `in-progress`, `planned`, or `implemented` | No. |
| A related task sent a delta about it | No. It is a memory update and says so. |
| It is obviously next, old, urgent, or blocking everything else | No. |
| You said "add this to outstanding items" or "remember this" | No. |
| The agent tidied, sorted, or summarised the list | No. |
| You said "start OI-4 now" | **Yes** — that one item, in that turn. |

The full decision table, with the reasoning and the hard cases, lives in [`references/authority.md`](plugins/outstanding-items/skills/outstanding-items/references/authority.md).

## Status labels

The other thing that makes the ledger worth trusting: the skill may not claim a rung it did not climb.

| Label | Means | Required evidence |
| --- | --- | --- |
| `requested` | You want it at some point. Nothing decided or started. | None. It is not an instruction to begin. |
| `planned` | An approach exists and was stated. Nothing has changed. | The approach, in one sentence. |
| `in-progress` | You explicitly said to start this item and it is being worked on now. | Your own start instruction, written into the note. |
| `implemented` | The change was made but not proven to work. | The edit or action the agent performed in this task. |
| `verified` | The change was proven to work. | Command output, a passing check, or your confirmation observed now—or exact completion evidence already preserved in the canonical item and checked now. |
| `waiting-on-you` | It needs you in person: a press, an approval, a choice, a credential, an acceptance. | The exact action, written in the imperative. |
| `blocked` | A genuine external impasse, after every safe in-scope route was tried. | The blocker **and** what was already attempted. |
| `reminder` | An **Intentional reminder**: parked on purpose, no execution request, no deadline. | None. It waits until you give it one. |
| `dropped` | Deliberately not doing it. | Who decided, and why. |

`implemented` never becomes `verified` because something "should" work. Three distinctions do most of the work here:

- **A label is not a licence.** `in-progress` is a description of a turn you authorized. When that turn ends, the permission ends with it — resuming needs you to say so again.
- **`waiting-on-you` is not `blocked`.** "Blocked" reads as *nothing to be done* and gets ignored for a week. If the only missing thing is your click, your key, or your yes, the ledger says so and tells you exactly what to press.
- **`reminder` is not a neglected request.** It was parked deliberately, so it stays visible and never retires itself. Ordinary actionable work comes first; if the reminder is the only active unfinished item, it can be the recommendation without changing status or starting anything.

Full definitions, transitions, and anti-patterns: [`references/status-labels.md`](plugins/outstanding-items/skills/outstanding-items/references/status-labels.md).

## Outsource your memory — a curated work experience

The second half of the skill, and the reason the footer is one line. The ledger knows what is outstanding; curation decides which single item is worth putting in front of you — offered to you, decided by you.

```text
**OI-4 Focus ring on interactive elements** `You`
About twenty minutes, and you already have that file open.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

What goes into that choice — weighed as judgement, never as a score:

| Weighed | Meaning |
| --- | --- |
| Dependencies | Does finishing this make other things possible? Is anything already waiting on it? |
| Momentum | Are you already inside this file, this idea, this mood? Restarting is the expensive part. |
| Effort against value | The smallest thing with a real payoff. Twenty minutes with an outcome beats three hours toward a milestone. |
| Availability to you | Can *you* pick it up now? A blocked parent is never suggested; its captured actionable prerequisite or follow-up may be. Something needing your approval may well be. |
| Urgency | Real consequences only. Age is not urgency and neither is list length. |
| Load | What you are carrying right now. After a long push, the honest suggestion is the smallest useful restart, phrased without pressure. |
| Autonomy | It is your call. The line offers a move, not a verdict on your week. |

And the rules that keep it from becoming a productivity lecture:

- **It proposes, then waits.** The suggestion is never a plan the agent carries out, and never permission to begin.
- **One item, one small step, one sentence.** No frameworks, no scores, no numbered plans, no runner-up, no counts.
- **It is addressed to you.** A line about what the assistant would carry on with is not your next move, and is not allowed there.
- **It never edits the ledger.** Nothing is dropped, reordered, merged, hidden, or deprioritised out of existence because it was not the thing chosen. An item that was not suggested is exactly as open as it was.
- **Your priorities win.** Say what you want and it stops, immediately and without a counter-proposal.
- **Calibrated, not confident.** If it is a close call it says so — and leaves the alternative in the editor rather than turning the line into a menu.
- **Rotate before repeating.** Ignore it and the next turn considers another actionable item. Once every alternative has been considered, the best still-open item can return with an updated first step. It never starts itself.
- **Keep an actionable frontier.** If a parent is blocked, capture the nearest honest unblock or future check as its own item. `**No outstanding items**` is reserved for a genuinely empty active ledger.

Weighing, wording, and the cases where it should refuse to pick: [`references/next-action.md`](plugins/outstanding-items/skills/outstanding-items/references/next-action.md).

## Related tasks, without waking anything

If another conversation should know about one of your items, the skill registers it once — visible title plus stable ID — and prepares a **memory-only delta**: one change, additively phrased, with a line stating in plain words that it authorizes no implementation and starts nothing.

It will only deliver that note through a mechanism that does not start a turn in the destination. If the only available tool would wake, resume, or dispatch that conversation, the delta is marked `prepared (not sent)` and handed to you instead — because a note that arrives as an instruction turns somebody else's backlog into work nobody authorized.

Registry schema, delivery gate, loop prevention, and failure wording: [`references/related-tasks.md`](plugins/outstanding-items/skills/outstanding-items/references/related-tasks.md).

## Install

The repository is a marketplace for both plugin systems. Install the same packaged skill in either harness:

### Codex plugin

```sh
codex plugin marketplace add EthanSK/outstanding-items
codex plugin add outstanding-items@outstanding-items
```

Start a new Codex task after installation so it picks up the bundled skill.

#### Refresh a local development copy

After any coherent local change to this repository—including a change you made outside an agent task—one command validates the repository, registers this checkout as a local marketplace when needed, installs a cache-busted copy, restores both authored manifests byte-for-byte, and verifies the installed version:

```sh
python3 scripts/sync_plugin_dev.py
```

Repository agents are instructed to inspect the working tree when they start and run this command before finishing whenever you, they, or another agent changed anything locally. Use `--dry-run` to inspect the exact flow. The command also removes any manifest-owned legacy standalone Codex copy after the plugin is verified. Modified or unowned files are never deleted; if an old manual copy cannot be proved safe to remove, the command stops and explains why. Codex loads refreshed plugin skills in a new task, not retroactively into the task performing the reinstall.

For a Git-backed marketplace release, refresh its snapshot before reinstalling:

```sh
codex plugin marketplace upgrade outstanding-items
codex plugin add outstanding-items@outstanding-items
```

The plugin manifest has no self-update URL. Marketplace refresh and plugin installation are separate operations, which is why the local development command performs both required checks explicitly.

### Claude Code plugin

```sh
claude plugin marketplace add EthanSK/outstanding-items
claude plugin install outstanding-items@outstanding-items --scope user
```

Run `/reload-plugins` or start a new Claude Code session. Claude exposes the bundled skill under its plugin namespace.

### Remove an older standalone installation

Releases before the plugin-only package included a direct installer. If that legacy copy still exists, remove it after installing the plugin:

```sh
sh scripts/uninstall.sh --dry-run --target codex
sh scripts/uninstall.sh --target codex
```

It removes only manifest-listed legacy files whose hashes still match what an older release installed, then removes directories **only if they are empty**. Files you added or edited by hand are left alone and reported. If the manifest is missing, it refuses to guess. New installations use the plugin commands above; there is no standalone install route.

## Make it fire without being asked

Harnesses discover skills from the `description` field, which is why the trigger phrases are written into it. To make invocation more reliable, add a rule to your global agent instructions. This is optional; the skill works without it.

Codex — append to `~/.codex/AGENTS.md`:

```markdown
## Outstanding items
Use the `outstanding-items` skill in any task with more than one request.
The outstanding items belong to me. Capture asides even when they are unrelated,
automatically add every concrete unresolved thing I still need to review, decide, provide, verify, or return to as `Agent`,
check for such loose ends before saying there are no outstanding items, and never invent filler when nothing remains,
use `You` only when I explicitly asked to add that entry to Outstanding Items
(a normal work request captured automatically is `Agent`),
keep the ledger silently while you work, and end the final response of each turn
with one compact recommendation: the single item you think I should do next,
immediately followed by its compact `You` or `Agent` source marker,
at most one line about it, and nothing else — no list, no counts, no reminders,
no Done section. Never put it in commentary or progress messages. When a local
ledger UI is running, put **Full outstanding items** on the footer's last line
using the exact URL it printed; with no live UI, write no link at all. Do not
rotate away from a suggestion I ignored or declined while another actionable
item exists; after every alternative has been considered, return the best
still-open item with a current first step. Anything needing my click, key, or approval is
`waiting-on-you`, not `blocked`. Never start, resume, investigate, research,
prepare, do pre-work for, dispatch, route, hand off, continue, or complete an
item unless my current message names it and tells you to. That authority ends
with the response turn. If I ask for the whole list, give it to me in the answer
and keep the footer to one line. In a Git-project task, create or resolve the
per-chat ledger under `.outstanding-items/<task-id>/`, add `/.outstanding-items/`
to the project's `.gitignore`, and keep project storage on unless I explicitly
opt out.
```

Claude Code — append to `~/.claude/CLAUDE.md`:

```markdown
## Outstanding items
Use the `outstanding-items` skill in any session with more than one request.
The list is mine. Maintain it silently while you work and end the final response
of each turn with one compact recommendation naming a single suggested item
with its compact `You` or `Agent` source marker immediately after it
— never in commentary or progress messages, and never as a list, a count, or a
Done section. Use `You` only when I explicitly asked to add that entry to
Outstanding Items; a normal work request captured automatically is `Agent`.
Link a running local UI as **Full outstanding items** on the
footer's last line, never label an item `verified` without evidence you observed
in this session, and never label something `blocked` when it is really waiting on
me. Being on the list, being suggested, or being labelled `in-progress` is never
permission to work on something — only my current message naming the item is, and
that authority ends with the response turn. For a Git-project session, create or
resolve the per-chat ledger under `.outstanding-items/<task-id>/`, add
`/.outstanding-items/` to `.gitignore`, and keep project storage on unless I
explicitly opt out.
```

Ready-to-paste copies live in [`examples/global-rules/`](examples/global-rules/). Repository-level integration examples: [`AGENTS.md`](AGENTS.md) and [`CLAUDE.md`](CLAUDE.md).

## Check it

```sh
sh scripts/check.sh              # validate this repository
sh scripts/check.sh --installed  # also validate the copies in your home directory
```

`check.sh` needs only `sh` and `python3`. It validates required files, frontmatter and YAML basics, internal links, site base paths, asset integrity, the synthetic-ID privacy rule, the honesty guards, the compact-footer contract — every documented footer must be one suggested item, at most one link, and no counts, sections, or Done entries — and the ownership and authority contract, including adversarial cases where a status, a ranking, or a cross-task delta might be mistaken for permission. It also exercises Markdown migration, JSON validation, atomic edit/check/reorder operations, stale-revision rejection, token gating, and external JSON refresh. There are no third-party dependencies and it makes no outbound network requests.

## What this does not do

Stated plainly, because these are the assumptions people arrive with:

- It **does not give the agent authority over your work**. Nothing in the ledger, and nothing the skill writes, is permission to start something.
- Installation **does not run a background daemon**. Nothing is scheduled. The optional Full outstanding items view starts one explicit per-ledger loopback process, and `ledger_ui.py stop` ends it without touching the data.
- It **does not create a cross-task message bus**. There is no broker, no queue, no inbox — and a delta never wakes the conversation it describes.
- It **does not create a persistent database**. The only durable ledger is one plain JSON file at a path you approve; the UI is a live view of that file, not another store.
- It **does not guarantee automatic invocation**. Harnesses decide when to load a skill from its description. Global rules make it likelier, not certain.
- It **does not discover other conversations by itself**. Without task tools in the harness, it says `registered (manual)` and gives you the text to carry.
- The plugin tooling and website make **no project-owned outbound application requests** and add no analytics or third-party runtime dependency. Your agent and harness may still use their existing model, task, or filesystem tools; this project does not hide or replace those calls.
- It **does not read your existing tasks** during installation, and it never edits a skill it did not install.
- It **does not know what you have the appetite for**. The suggestion is a judgement made from what you said in this task. It rotates through alternatives before repeating and is not a prediction, schedule, or claim about what matters most in your life.

## Repository layout

| Path | Purpose |
| --- | --- |
| `.agents/plugins/marketplace.json` | OpenAI marketplace catalog for the repository. |
| `.claude-plugin/marketplace.json` | Claude Code marketplace catalog for the repository. |
| `plugins/outstanding-items/.codex-plugin/plugin.json` | OpenAI plugin manifest. |
| `plugins/outstanding-items/.claude-plugin/plugin.json` | Claude Code plugin manifest. |
| `plugins/outstanding-items/skills/outstanding-items/SKILL.md` | The canonical operating contract, Rule #1 first. Single source of truth. |
| `plugins/outstanding-items/skills/outstanding-items/references/` | Seven one-level references: authority, status labels, choosing the one item, backlog artifact, Full outstanding items operations, related tasks, worked examples. |
| `plugins/outstanding-items/skills/outstanding-items/assets/` | Generic local ledger HTML, CSS, and JavaScript. It contains no user data. |
| `plugins/outstanding-items/skills/outstanding-items/scripts/ledger_ui.py` | Standard-library JSON migration, validation, mutation, and loopback editor runtime. |
| `plugins/outstanding-items/skills/outstanding-items/agents/openai.yaml` | OpenAI skill interface metadata; Claude Code ignores it. |
| `scripts/sync_plugin_dev.py` | One-command checked, cache-busted local plugin reinstall that restores source versions. |
| `scripts/uninstall.sh` | Manifest-scoped cleanup for legacy standalone installations. |
| `scripts/check.sh` | Repository and installation validation. |
| `scripts/serve.sh` | Local preview of the website. |
| `tests/run_tests.sh`, `tests/run_checks.py`, `tests/test_ledger_ui.py` | Deterministic contract and end-to-end ledger checks. Python standard library only. |
| `docs/` | The GitHub Pages site. No build step, no runtime dependencies. |
| `examples/` | A synthetic canonical JSON ledger, its legacy migration fixture, a worked transcript, delta messages, and global rules. |
| `AGENTS.md` / `CLAUDE.md` | Integration instructions and examples for each harness. |

## Privacy and security

- The skill records **titles and short notes only**. It is instructed never to copy secrets, tokens, credentials, file contents, or personal identifiers into the ledger or the artifact.
- The canonical JSON ledger is working memory. In a Git project it defaults to a separate `.outstanding-items/<task-id>/` directory for each chat, and `/.outstanding-items/` is added to the root `.gitignore`; `--no-project-storage` opts out before any project write. Non-project chats still ask before creating a durable file. Real ledgers and their `.ledger-ui-*` runtime files are never committed.
- Every task ID and session ID anywhere in this repository is synthetic and contains the literal string `EXAMPLE`. A check enforces it, so a real identifier cannot be pasted in unnoticed.
- Cross-task deltas carry one change and no context dumps: never the whole ledger, never file contents, never credentials, never identifiers.
- The legacy cleanup script removes only hash-matching manifest entries. Modified files and unrecognised files survive; a missing manifest stops removal rather than guessing. It validates path boundaries, refuses symbolic-link traversal, and never deletes recursively.
- The website ships no analytics, no cookies, no CDN fonts, and no third-party requests. The optional ledger browser talks only to its token-protected `127.0.0.1` server and uses no browser storage. On Codex, that server may run a short-lived local `codex app-server` title lookup with remote plugin sync disabled; it requests only current names for exact transferred task IDs.

## Adapting it

Fork it and change four things:

1. **The `description` in `SKILL.md`** — trigger phrases decide when the skill loads. Put your own vocabulary in it ("chuck that on the list", "next thing").
2. **The status labels** — if your work has a different pipeline, replace the table. Keep the requested / implemented / verified split, keep `waiting-on-you` separate from `blocked`, and keep every label descriptive; those are the parts that prevent optimistic reporting and silent stalling. If you would rather the ledger addressed you by name, rename the label — `waiting-on-ada` reads just as well, it only has to be consistent across `SKILL.md` and the references.
3. **The thresholds** — when the ledger moves into its own JSON file and editor (7 open items / 20 total) lives in `SKILL.md` and [`references/backlog-artifact.md`](plugins/outstanding-items/skills/outstanding-items/references/backlog-artifact.md). The footer stays one item whatever you set.
4. **What a suggestion means to you** — the weighing in [`references/next-action.md`](plugins/outstanding-items/skills/outstanding-items/references/next-action.md) is deliberately human. If your work needs deadlines to dominate, or you would rather see nothing unless you ask, say so there.

What not to change: Rule #1. If you rewrite the ownership model so that a list entry, a status, or a ranking implies permission, this stops being the same tool, and the checks in `tests/run_checks.py` will say so.

Then run `sh scripts/check.sh`. The checks are structural, so they keep working after you rewrite the prose.

## Development

```sh
sh scripts/check.sh                   # everything: shell, JS, and the checks below
sh tests/run_tests.sh                 # the deterministic checks on their own
python3 tests/run_checks.py --list    # list individual checks
python3 tests/run_checks.py -v        # verbose
sh scripts/serve.sh                   # preview docs/ at http://127.0.0.1:8099/
```

Everything is POSIX `sh` plus `python3` from the standard library — no build step, no
package manager, no network. If you would rather type `./scripts/check.sh`, run
`chmod +x scripts/*.sh tests/*.sh` once.

The website has no build step either: `docs/` is served exactly as committed. The
ledger animation is progressive enhancement, and the page is complete and readable
with JavaScript switched off — a check compares the interactive data against the
static fallback so the two cannot drift apart.

Treat the public documentation as part of every user-visible change. Review both
`README.md` and `docs/` in the same change, update whichever public explanation has
changed, and record the audit when one surface needs no edit. After publishing,
wait for the GitHub Pages build and verify the live HTTPS page against the committed
`docs/` files; a successful push by itself is not publication proof.

## License

MIT. See [LICENSE](LICENSE).
