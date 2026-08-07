# Outstanding Items

**Outsource your memory — a curated work experience.**

A skill for [Codex](https://developers.openai.com/codex/) and [Claude Code](https://www.anthropic.com/claude-code) that does two things across a long, branching task — and, deliberately, nothing more.

**It holds the list.** You talk freely — including asides that have nothing to do with what the agent is currently doing — and each turn finishes with a compact **Outstanding** footer split into what is outstanding for you, what is waiting on you, what you parked on purpose, and a crossed-out Done section. It appears once, in the final response, so progress chatter never turns into three copies of the same list. The backlog lives in the transcript instead of in your head.

**It curates, and curation proposes.** When it would genuinely help, one line suggests a next move *for you*, says why, and stops. **You decide, and you start it.**

> ### Rule #1 — the outstanding items belong to you
>
> The ledger is your record, not the agent's work queue. Listing, sorting, ranking, syncing, or recommending an item never authorizes the agent to start, resume, continue, investigate, research, prepare, do pre-work for, dispatch, route, or complete it. Only a fresh, explicit instruction from you naming a specific item does that. "Add this to outstanding items" means add it, and nothing else.

Website: <https://ethansk.github.io/outstanding-items/>

## Status

Working, and simple on purpose. This is a **prompt-level skill** with one small optional local editor: one `SKILL.md` operating contract, seven focused references, and a standard-library HTML ledger UI. Installing it starts nothing and opens no port. When you explicitly open the Full outstanding items view, one loopback-only process edits that task's canonical JSON file; it is not a cross-task service or database. The skill still grants the agent no authority over your work. Cross-task propagation happens only when the harness exposes task tools, and only as a memory update that starts nothing; otherwise the skill registers the relationship and hands you the exact text to carry across yourself.

## What it actually does

| Behaviour | What you see |
| --- | --- |
| Multi-request tracking | Every request in the task gets a permanent `OI-n` ID, in the order you said it. |
| Unrelated asides accepted | "Remind me to ask the design channel" is captured mid-task and never refused for being off-topic. |
| Capture without commission | Something added to the list is recorded, confirmed, and left alone until you say otherwise. |
| One footer per turn | Four sections — Outstanding for you, Waiting on you, Intentional reminders, Done — rendered once, at the end of the final response. Commentary and progress messages stay clean. |
| Crossed-out Done section | Finished and cancelled items move to the bottom, struck through, so you can audit what happened. |
| Honest status labels | `requested` / `in-progress` / `implemented` / `verified` are four different amounts of proof, and the skill may not round them up. |
| Labels that are not licences | `in-progress` records the instruction that started it. When the turn ends, so does the permission. |
| Intentional reminders | Something parked on purpose is labelled `reminder` — visible, never started, never quietly retired, never nagged about. |
| A real difference between stuck and yours | Something needing your click, key, or approval is `waiting-on-you`, with the exact action. `blocked` is reserved for a genuine external wall. |
| One suggestion, for you | One item, one small possible first step, one sentence of reasoning — then it waits. |
| Canonical task ledger | Past the overflow threshold the full list lives in one task-owned `outstanding-items.json` — after asking you for a path. |
| Editable Full outstanding items | A quiet local list: click task text to edit it, drag or use keyboard controls to reorder, and check it complete with a temporary Undo action. Completed items remain at the bottom. |
| A plain-words tooltip per item | Hover an item, or move keyboard focus to it, and a small note above the row says in ordinary language what that item is about. |
| Auditable ownership transfer | Moving work to another task preserves its status and notes as read-only history here instead of pretending it was completed. |
| Registered related tasks | Another conversation is resolved once, stored by title plus stable ID, and receives memory-only deltas that authorize nothing. |

A real footer looks like this — once per turn, at the end of the final response:

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

IDs are permanent. Nothing is ever renumbered, so a reference you made ten turns ago still points at the same thing.

Once a local editor is running for that task, the same footer carries its link twice — directly under the header and again after the last section, so it is there whichever end you are reading from:

```text
**Outstanding** (8 for you · 1 reminder · 2 done)
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)

… your sections …

[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

Both links are the exact URL the editor printed. If no editor is running, neither line appears — the skill does not invent a URL to fill the space.

## Full outstanding items is an editor, not a raw file

When the compact footer overflows, **Full outstanding items** opens a private local HTML view instead of a huge Markdown or JSON file. At rest, a row is just its checkbox and task text. Click the text to create an inline editor; no blank input exists before that interaction. Drag with the reorder grip or reveal the keyboard move controls with focus. Checking a task complete moves it to the bottom and shows a temporary snackbar with **Undo**.

Hovering a row — or giving its task text keyboard focus — shows one small tooltip above it: the item's ID, a friendly state phrase, and a short paragraph in ordinary words about what the item is. It comes from the item's own optional `explanation` field, written by the agent for a moment when the title alone is not enough. Items saved before that field existed still get a plain sentence based on their status, so nothing looks blank. `Escape` dismisses a tooltip, the pointer can move onto it without it vanishing, and every row's text is rendered as text, never as markup.

There is still only one ledger: the task-owned `outstanding-items.json`. The UI reads and atomically writes that file through a token-protected server bound to `127.0.0.1`; it stores no copy in the HTML or browser storage. Agent-side changes update the same JSON, and an open page notices a new revision within two seconds. If two edits race, the stale one is rejected and reloaded instead of overwriting newer work.

When you explicitly transfer ownership to another task, the original records stay in that JSON with their status and evidence unchanged. They move into a read-only **Owned elsewhere** section, leave the active counts, and retain the exact destination and handoff time.

The generic HTML, CSS, and JavaScript ship with the skill, so no page regeneration is needed when the data changes. A migrated Markdown ledger is retained as a frozen source snapshot, then never updated again. See the [data model](skill/outstanding-items/references/backlog-artifact.md) and [editor operations](skill/outstanding-items/references/ledger-ui.md).

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

The full decision table, with the reasoning and the hard cases, lives in [`references/authority.md`](skill/outstanding-items/references/authority.md).

## Status labels

The other thing that makes the ledger worth trusting: the skill may not claim a rung it did not climb.

| Label | Means | Required evidence |
| --- | --- | --- |
| `requested` | You want it at some point. Nothing decided or started. | None. It is not an instruction to begin. |
| `planned` | An approach exists and was stated. Nothing has changed. | The approach, in one sentence. |
| `in-progress` | You explicitly said to start this item and it is being worked on now. | Your own start instruction, written into the note. |
| `implemented` | The change was made but not proven to work. | The edit or action the agent performed in this task. |
| `verified` | The change was proven to work. | Command output, a passing check, or your confirmation, observed in this task. |
| `waiting-on-you` | It needs you in person: a press, an approval, a choice, a credential, an acceptance. | The exact action, written in the imperative. |
| `blocked` | A genuine external impasse, after every safe in-scope route was tried. | The blocker **and** what was already attempted. |
| `reminder` | An **Intentional reminder**: parked on purpose, no execution request, no deadline. | None. It waits until you give it one. |
| `dropped` | Deliberately not doing it. | Who decided, and why. |

`implemented` never becomes `verified` because something "should" work. Three distinctions do most of the work here:

- **A label is not a licence.** `in-progress` is a description of a turn you authorized. When that turn ends, the permission ends with it — resuming needs you to say so again.
- **`waiting-on-you` is not `blocked`.** "Blocked" reads as *nothing to be done* and gets ignored for a week. If the only missing thing is your click, your key, or your yes, the ledger says so and tells you exactly what to press.
- **`reminder` is not a neglected request.** It was parked deliberately, so it stays visible, never retires itself, and never becomes a suggestion unless you ask or something genuinely becomes urgent.

Full definitions, transitions, and anti-patterns: [`references/status-labels.md`](skill/outstanding-items/references/status-labels.md).

## Outsource your memory — a curated work experience

The second half of the skill. The ledger knows what is outstanding; curation is a suggestion about what to do with it — offered to you, decided by you.

When you ask what to do next, come back after time away, sound overloaded, or hit a natural decision point, the footer gains a single line:

```text
**Suggested for you** — OI-4, about twenty minutes, and it settles OI-6 at the same time. Tell me `start OI-4` if you want me to pick it up.
```

What goes into it — weighed as judgement, never as a score:

| Weighed | Meaning |
| --- | --- |
| Dependencies | Does finishing this make other things possible? Is anything already waiting on it? |
| Momentum | Are you already inside this file, this idea, this mood? Restarting is the expensive part. |
| Effort against value | The smallest thing with a real payoff. Twenty minutes with an outcome beats three hours toward a milestone. |
| Availability to you | Can *you* pick it up now? A `blocked` item is never suggested; something needing your approval may well be. |
| Urgency | Real consequences only. Age is not urgency and neither is list length. |
| Load | What you are carrying right now. After a long push, the honest suggestion is a small one — or none. |
| Autonomy | It is your call. The line offers a move, not a verdict on your week. |

And the rules that keep it from becoming a productivity lecture:

- **It proposes, then waits.** The suggestion is never a plan the agent carries out, and never permission to begin.
- **One item, one small step, one sentence.** No frameworks, no scores, no numbered plans.
- **It is addressed to you.** A line about what the assistant would carry on with is not your next move, and is not allowed there.
- **Not every turn.** Most replies carry no suggestion at all. A footer that advises constantly stops being read.
- **It never edits the ledger.** Nothing is dropped, reordered, merged, hidden, or deprioritised out of existence because it was not the thing chosen.
- **Your priorities win.** Say what you want and it stops, immediately and without a counter-proposal.
- **Calibrated, not confident.** If it is a close call it says so and names the alternative.
- **Advice, once.** Ignore it and it drops the subject — it does not repeat it, and it certainly does not start it.

Weighing, wording, and the cases where it should refuse to pick: [`references/next-action.md`](skill/outstanding-items/references/next-action.md).

## Related tasks, without waking anything

If another conversation should know about one of your items, the skill registers it once — visible title plus stable ID — and prepares a **memory-only delta**: one change, additively phrased, with a line stating in plain words that it authorizes no implementation and starts nothing.

It will only deliver that note through a mechanism that does not start a turn in the destination. If the only available tool would wake, resume, or dispatch that conversation, the delta is marked `prepared (not sent)` and handed to you instead — because a note that arrives as an instruction turns somebody else's backlog into work nobody authorized.

Registry schema, delivery gate, loop prevention, and failure wording: [`references/related-tasks.md`](skill/outstanding-items/references/related-tasks.md).

## Install

Everything installs from the checked-out repository. No network access, no package manager, no build step.

```sh
git clone https://github.com/EthanSK/outstanding-items.git
cd outstanding-items
sh scripts/install.sh --dry-run   # print the exact file plan, change nothing
sh scripts/install.sh             # install for every harness found on this machine
```

By default the installer targets each harness whose home directory already exists and skips the others with a note. To be explicit:

```sh
sh scripts/install.sh --target codex    # ~/.codex/skills/outstanding-items/
sh scripts/install.sh --target claude   # ~/.claude/skills/outstanding-items/
sh scripts/install.sh --target both     # create both, even if one is missing
sh scripts/install.sh --dest /tmp/preview   # install under an arbitrary root
```

The installer:

- copies file by file from a manifest built out of the repository, validating every path — it never runs a recursive delete;
- creates only `<root>/skills/outstanding-items/` and its subdirectories;
- refuses to touch an existing `outstanding-items` skill that something else owns, and refuses to overwrite locally modified files without `--force`;
- is idempotent — running it twice with unchanged sources reports `unchanged` and writes nothing;
- prints a per-file plan of `create`, `update`, `unchanged`, or `skip` before it acts;
- copies the skill's text, HTML, CSS, JavaScript, and Python runtime only. Installing it starts nothing and does not authorize any agent to work on anything in your ledger.

### Manual install

If you would rather see every step:

```sh
mkdir -p ~/.codex/skills/outstanding-items
cp -R skill/outstanding-items/. ~/.codex/skills/outstanding-items/

mkdir -p ~/.claude/skills/outstanding-items
cp -R skill/outstanding-items/. ~/.claude/skills/outstanding-items/
```

One canonical source, copied twice. The `SKILL.md` frontmatter (`name` + `description`) is valid for both harnesses; `agents/openai.yaml` uses Codex's supported `interface` schema and Claude Code ignores it. A manual copy does not create the install manifest, so remove a manual installation manually; use `scripts/install.sh` when you want conflict-aware updates and manifest-scoped uninstalling.

### Uninstall

```sh
sh scripts/uninstall.sh --dry-run
sh scripts/uninstall.sh
```

It removes only manifest-listed files whose hashes still match what this repository installed, then removes directories **only if they are empty**. Files you added or edited by hand are left alone and reported. If the manifest is missing, it refuses to guess.

## Make it fire without being asked

Harnesses discover skills from the `description` field, which is why the trigger phrases are written into it. To make invocation more reliable, add a rule to your global agent instructions. This is optional; the skill works without it.

Codex — append to `~/.codex/AGENTS.md`:

```markdown
## Outstanding items
Use the `outstanding-items` skill in any task with more than one request.
The outstanding items belong to me. Capture asides even when they are unrelated,
keep the ledger silently while you work, and end the final response of each turn
with one Outstanding footer and its crossed-out Done section — never in
commentary or progress messages. When a local ledger UI is running, link it as
**Full outstanding items** below the header and after the last section, using the
exact URL it printed. Anything needing my click, key, or approval is
`waiting-on-you`, not `blocked`. Never start, resume, investigate, research,
prepare, do pre-work for, dispatch, route, hand off, continue, or complete an
item unless my current message names it and tells you to. That authority ends
with the response turn. When I ask what to do next, suggest one thing and a
small first step, then wait for me.
```

Claude Code — append to `~/.claude/CLAUDE.md`:

```markdown
## Outstanding items
Use the `outstanding-items` skill in any session with more than one request.
The list is mine. Maintain it silently while you work and end the final response
of each turn with one Outstanding footer — never in commentary or progress
messages — link a running local UI as **Full outstanding items** below the header
and after the last section, never
label an item `verified` without evidence you observed in this session, and never
label something `blocked` when it is really waiting on me. Being on the list,
being suggested, or being labelled `in-progress` is never permission to work on
something — only my current message naming the item is, and that authority ends
with the response turn.
```

Ready-to-paste copies live in [`examples/global-rules/`](examples/global-rules/). Repository-level integration examples: [`AGENTS.md`](AGENTS.md) and [`CLAUDE.md`](CLAUDE.md).

## Check it

```sh
sh scripts/check.sh              # validate this repository
sh scripts/check.sh --installed  # also validate the copies in your home directory
```

`check.sh` needs only `sh` and `python3`. It validates required files, frontmatter and YAML basics, internal links, site base paths, asset integrity, the synthetic-ID privacy rule, the honesty guards, and the ownership and authority contract — including adversarial cases where a status, a ranking, or a cross-task delta might be mistaken for permission. It also exercises Markdown migration, JSON validation, atomic edit/check/reorder operations, stale-revision rejection, token gating, and external JSON refresh. There are no third-party dependencies and it makes no outbound network requests.

## What this does not do

Stated plainly, because these are the assumptions people arrive with:

- It **does not give the agent authority over your work**. Nothing in the ledger, and nothing the skill writes, is permission to start something.
- Installation **does not run a background daemon**. Nothing is scheduled. The optional Full outstanding items view starts one explicit per-ledger loopback process, and `ledger_ui.py stop` ends it without touching the data.
- It **does not create a cross-task message bus**. There is no broker, no queue, no inbox — and a delta never wakes the conversation it describes.
- It **does not create a persistent database**. The only durable ledger is one plain JSON file at a path you approve; the UI is a live view of that file, not another store.
- It **does not guarantee automatic invocation**. Harnesses decide when to load a skill from its description. Global rules make it likelier, not certain.
- It **does not discover other conversations by itself**. Without task tools in the harness, it says `registered (manual)` and gives you the text to carry.
- The installer and website make **no project-owned outbound application requests** and add no analytics or third-party runtime dependency. Your agent and harness may still use their existing model, task, or filesystem tools; this project does not hide or replace those calls.
- It **does not read your existing tasks** during installation, and it never edits a skill it did not install.
- It **does not know what you have the appetite for**. The suggestion is a judgement made from what you said in this task — offered once, dropped if ignored. It is not a prediction, not a schedule, and not a claim about what matters most in your life.

## Repository layout

| Path | Purpose |
| --- | --- |
| `skill/outstanding-items/SKILL.md` | The canonical operating contract, Rule #1 first. Single source of truth. |
| `skill/outstanding-items/references/` | Seven one-level references: authority, status labels, suggesting a next move, backlog artifact, Full outstanding items operations, related tasks, worked examples. |
| `skill/outstanding-items/assets/` | Generic local ledger HTML, CSS, and JavaScript. It contains no user data. |
| `skill/outstanding-items/scripts/ledger_ui.py` | Standard-library JSON migration, validation, mutation, and loopback editor runtime. |
| `skill/outstanding-items/agents/openai.yaml` | Codex packaging metadata. |
| `scripts/install.sh` | Dry-runnable, non-destructive installer. |
| `scripts/uninstall.sh` | Manifest-scoped removal. |
| `scripts/check.sh` | Repository and installation validation. |
| `scripts/serve.sh` | Local preview of the website. |
| `tests/run_tests.sh`, `tests/run_checks.py`, `tests/test_ledger_ui.py` | Deterministic contract and end-to-end ledger checks. Python standard library only. |
| `docs/` | The GitHub Pages site. No build step, no runtime dependencies. |
| `examples/` | A synthetic canonical JSON ledger, its legacy migration fixture, a worked transcript, delta messages, and global rules. |
| `AGENTS.md` / `CLAUDE.md` | Integration instructions and examples for each harness. |

## Privacy and security

- The skill records **titles and short notes only**. It is instructed never to copy secrets, tokens, credentials, file contents, or personal identifiers into the ledger or the artifact.
- The canonical JSON ledger is working memory. It is created only after you approve a path, it is offered a `.git/info/exclude` entry together with its `.ledger-ui-*` runtime files when the directory is a Git repository, and it is never committed. This repository's `.gitignore` blocks task ledgers and their local runtime files for the same reason.
- Every task ID and session ID anywhere in this repository is synthetic and contains the literal string `EXAMPLE`. A check enforces it, so a real identifier cannot be pasted in unnoticed.
- Cross-task deltas carry one change and no context dumps: never the whole ledger, never file contents, never credentials, never identifiers.
- The installer writes only inside `<root>/skills/outstanding-items/`, validates every manifest path and resolved path boundary, refuses symbolic-link traversal, and never deletes recursively.
- The uninstaller removes only hash-matching manifest entries. Modified files and unrecognised files survive; a missing manifest stops removal rather than guessing.
- The website ships no analytics, no cookies, no CDN fonts, and no third-party requests. The optional ledger editor also makes no outbound requests; it talks only to its token-protected `127.0.0.1` server and uses no browser storage.

## Adapting it

Fork it and change four things:

1. **The `description` in `SKILL.md`** — trigger phrases decide when the skill loads. Put your own vocabulary in it ("chuck that on the list", "next thing").
2. **The status labels** — if your work has a different pipeline, replace the table. Keep the requested / implemented / verified split, keep `waiting-on-you` separate from `blocked`, and keep every label descriptive; those are the parts that prevent optimistic reporting and silent stalling. If you would rather the ledger addressed you by name, rename the label — `waiting-on-ada` reads just as well, it only has to be consistent across `SKILL.md` and the references.
3. **The thresholds** — the 7-line / 20-total overflow rule and the footer line budgets live in `SKILL.md` and [`references/status-labels.md`](skill/outstanding-items/references/status-labels.md).
4. **What a suggestion means to you** — the weighing in [`references/next-action.md`](skill/outstanding-items/references/next-action.md) is deliberately human. If your work needs deadlines to dominate, or wants suggestions only when asked, say so there.

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

## License

MIT. See [LICENSE](LICENSE).
