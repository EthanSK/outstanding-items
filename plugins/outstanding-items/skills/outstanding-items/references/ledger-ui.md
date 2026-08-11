# Full outstanding items UI

Operational guide for the local interactive ledger. Load after a canonical JSON ledger exists, when a **Full outstanding items** link must be shown, or when the editor needs diagnosis.

## Resolve a project chat ledger

For a Git-project chat, resolve its canonical per-chat ledger before the first capture:

```sh
python3 ~/.codex/skills/outstanding-items/scripts/ledger_ui.py project-ledger \
  --project-root /absolute/project/root \
  --task-id task_EXAMPLE_4b7c
```

Project storage is enabled by default. The command prints `LEDGER_PATH`, stores that chat under `.outstanding-items/<task-id>/`, and adds `/.outstanding-items/` to the project's `.gitignore`. Pass `--no-project-storage` for an explicit opt-out; it writes nothing. Use the printed `LEDGER_PATH` for every later `upsert`, validation, and UI command in that chat.

## Start or reuse it

The installed runtime lives inside the skill:

```sh
python3 ~/.codex/skills/outstanding-items/scripts/ledger_ui.py start \
  --ledger /absolute/task/path/outstanding-items.json
```

Use the equivalent `~/.claude/skills/` path under Claude Code. The command prints `LEDGER_URL`, `LEDGER_PID`, and `LEDGER_LOG`. It reuses the exact healthy process for that ledger only after both its API and browser assets respond and their fingerprint matches the currently installed plugin. If a plugin cache was replaced beneath a still-running process, or a healthy process serves an older UI, `start` replaces that exact stale runtime automatically. After a deliberate stop or replacement, it reuses the same private loopback port and token from the user-only connection file, so an existing browser tab and previously supplied link reconnect instead of becoming a dead URL.

Use the printed URL as the last line of the compact footer:

```markdown
**OI-4 Focus ring on interactive elements** `You`
Twenty minutes, and the shared token is the whole first step.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

The label is exactly **Full outstanding items**, on its own line, once, as the final line of the footer. This link is the only place the rest of the ledger appears: the footer names one item, and everything else — the other open items, the intentional reminders, and the whole Done history — lives behind it.

If no verified live UI URL exists for this ledger, write no link line at all: never invent, guess, shorten, or redact a URL, never reuse one from an earlier task, and never link the footer to the raw JSON or an archived Markdown list. Use exactly what `start` printed. The token is local runtime state, not ledger data; do not copy it into a repository file, cross-task delta, or public message.

The footer itself, with or without that link, belongs only to the final response of a turn — never to commentary or progress messages.

## Interaction model

Keep the resting interface visually quiet: each actionable row shows only its real checkbox and task text. The task text is the edit control. Clicking or pressing it creates one inline textarea at the same location; `Enter` saves, `Shift+Enter` inserts a line break, `Escape` cancels, and leaving the editor saves. An unchanged edit sends no mutation. Never pre-render a text input or separate Edit button beneath every item.

The whole row and editable task text never trigger item details. A small caret sits above the existing drag grip in the same action column, so it uses no additional horizontal content width. Hovering or keyboard-focusing that disclosure shows one tooltip above the row: the item's `OI-n` and a friendly state phrase on the first line, then its short explanation paragraph. Click or tap toggles it where hover is unavailable, `Escape` dismisses it without moving focus, and it flips below only when there is not enough space above. The tooltip is text only, rendered with `textContent`, and it is never used to show Markdown, evidence, logs, or a next step.

Outstanding-item reorder controls are latent rather than absent: hover or keyboard focus reveals the drag grip and move buttons. `Alt+Up` and `Alt+Down` on focused task text provide the same keyboard movement without requiring the buttons. Completed items stay at the bottom and may be reopened with their checkbox.

After a successful completion mutation, show a temporary snackbar with **Undo**. Undo sends a real reopen mutation using the current `base_revision`; it never rewinds client state independently of the canonical JSON. Keep the snackbar available for eight seconds, pause its timeout during hover or keyboard focus, do not steal focus, and allow `Command+Z` or `Control+Z` while it is live. A failed or stale mutation must report the error and render the server's current ledger instead of claiming success.

Transferred entries remain read-only under **Owned elsewhere**, which is a closed disclosure by default. Opening it shows the task text plus the destination Codex task title, stable task/session ID, and transfer date. Do not render completion, edit, drag, or move controls for them. Preserve their item ID, status, provenance, destination ID, cached title, transfer time, and optional handoff path in canonical JSON.

On Codex, the loopback server checks exact stored destination IDs through `codex app-server`'s read-only `thread/list` protocol at most once per minute and after a successful browser mutation. It disables remote plugin sync for that short-lived lookup, reads titles only, and updates `transferred_to.title` plus its source/time metadata when a name changed. It never searches for replacement identities, reads turns, wakes a task, sends a message, or changes destination work. When Codex is unavailable (including Claude Code), cached titles remain valid and the editor continues normally.

## Canonical mutations

Validate before and after a batch:

```sh
python3 ~/.codex/skills/outstanding-items/scripts/ledger_ui.py validate \
  --ledger /absolute/task/path/outstanding-items.json
```

Add or update an item without maintaining a second format:

```sh
python3 ~/.codex/skills/outstanding-items/scripts/ledger_ui.py upsert \
  --ledger /absolute/task/path/outstanding-items.json \
  --id OI-12 \
  --title "Confirm the release" \
  --status waiting-on-you \
  --provenance user-requested \
  --group "Release" \
  --explanation "The release is built and ready; it just needs your yes before it goes out. One click in the release page is the whole job."
```

For rich notes, write a task-local temporary note and pass `--notes-file`; do not squeeze paragraphs through shell quoting. The command atomically increments the revision, and an open UI sees it within two seconds.

`--provenance` is required when creating a new item. Use `user-requested` only when the user explicitly asks to add that specific thing to Outstanding Items. If the user merely requests or discusses the underlying work and the agent captures it automatically, use `agent-added`. Use `unknown-legacy` only when migrating an older item whose capture source cannot be proved. Later `upsert` calls preserve provenance. The UI shows a tiny inline `You` or `Agent` pill only for the two known origins; hovering explains that `You` means an explicit request for the ledger entry itself. `unknown-legacy` remains in the JSON for honesty but adds no visible badge.

When evidence proves an earlier classification wrong, use the audited correction route instead of hand-editing JSON:

```sh
python3 scripts/ledger_ui.py correct-provenance \
  --ledger outstanding-items.json \
  --ids OI-7 OI-8 \
  --provenance agent-added \
  --reason "The source messages requested work but never requested ledger capture." \
  --session-id sess_EXAMPLE_7f2a
```

This command validates the whole batch before writing, increments the revision once, and appends each item's `provenance_history`. It changes no status, completion state, position, transfer state, title, or evidence. The browser cannot invoke it.

A newly created outstanding item receives a fresh relevance timestamp. Automatic reconciliation places it according to actionable status and recency; a `waiting-on-you` item can therefore surface above a newer ordinary request. Explicit drag/keyboard positions remain fixed, and creating a completed historical item does not disturb the active order.

## Writing the explanation

`--explanation` fills the tooltip. Write it as if the user is meeting the item for the first time in a while and wants to feel oriented, not tested.

- One or two warm, ordinary sentences. Up to 600 characters, and shorter is better.
- Use imperative Git commit-subject style: lead with the concrete action and a direct verb such as `Write`, `Add`, `Check`, or `Finish`.
- Say what the item does and why it is on the list, in the user's own vocabulary.
- Plain text only: no Markdown, no code, no file paths, no ticket numbers, no command output, no evidence, no credentials.
- Describe the item, never the plan. It states nothing about what will happen next, claims no progress, and is not permission to act.
- Omit throat-clearing such as “This is”, “This would”, “This one”, or “The idea is”. Do not force a genuinely non-action fact into a command.
- No apologies, no reference to forgetting or remembering, and nothing that reads as talking down to the user.

Good: `Write the real rate limits into the handbook so the docs page gives people the numbers they need.`

Avoid: `This would add rate-limit numbers to the handbook.`

Leaving it out is safe. Ledgers written before this field existed stay valid, and the UI starts its fallback with the item title before adding a plain sentence based on the status. Fill the field in when you can: the fallback describes the state, while a written explanation describes the item.

Transfer exact items after an explicitly authorized handoff:

```sh
python3 ~/.codex/skills/outstanding-items/scripts/ledger_ui.py transfer \
  --ledger /absolute/task/path/outstanding-items.json \
  --ids OI-12 OI-14 \
  --task-id task_EXAMPLE_target \
  --task-title "Destination task" \
  --handoff-path /absolute/task/path/handoff.md
```

Transfer preserves each item's status, completion state, details, and ID. It records the destination and makes the source copy read-only historical context. Never use transfer as a substitute for completing or dropping work.

## Migrate one legacy Markdown ledger

```sh
python3 ~/.codex/skills/outstanding-items/scripts/ledger_ui.py migrate-markdown \
  --source /absolute/task/path/outstanding-items.md \
  --ledger /absolute/task/path/outstanding-items.json \
  --title "Outstanding items" \
  --task-id task_EXAMPLE_4b7c
```

The migration preserves every `### OI-n` item title and body, its queue heading, normalized status, non-item sections, source path, and SHA-256. It refuses to overwrite an existing JSON ledger without `--force`. Use `--force` only after inspecting the exact target and deliberately replacing a failed migration; never use it for ordinary updates.

After validation, add an archive notice to the old Markdown or otherwise mark it frozen. Do not regenerate or manually update both formats.

## Persistence and live updates

- `outstanding-items.json` is the single editable record. Version 3 and 4 ledgers upgrade atomically to version 5. Version 3 receives conservative `unknown-legacy` provenance; both receive automatic ordering metadata without pretending their legacy positions were manual intent.
- Every browser mutation carries the revision it read. A stale mutation gets HTTP 409 and the new ledger, so it cannot erase an agent-side update.
- A drag or keyboard move sends the exact moved ID and stores manual placement time, revision, and neighbouring anchors. Automatic reconciliation keeps manual items fixed while ordering only automatic items by actionable status and relevance recency.
- Writes are validated and atomic.
- The browser polls the canonical JSON revision every two seconds while visible. External CLI/agent changes appear without regenerating HTML or restarting the server.
- The per-ledger private connection file preserves the exact loopback URL across normal stop/start cycles. A disconnected page explains that it will retry instead of surfacing the browser's raw `Failed to fetch` text.
- The server snapshots its generic HTML, CSS, and JavaScript at startup and exposes one SHA-256 fingerprint for that complete browser shell. Removing or replacing the plugin cache cannot strand a running API with a 404 or outdated browser shell; `start` refuses to reuse a runtime whose UI is unavailable or whose fingerprint differs from the installed plugin.
- The HTML, CSS, and JavaScript are a generic shell installed with the skill. They contain no task items and never need regeneration when ledger data changes.
- Transferred items render read-only inside a collapsed **Owned elsewhere** disclosure, show their destination metadata, and are excluded from active outstanding/completed counts without being deleted.
- `explanation` is an optional per-item string of at most 600 characters. It travels with the rest of the ledger, needs no schema bump, and an item or ledger without it stays valid; the browser supplies the status fallback at render time and stores nothing of its own. Only the dedicated caret discloses it; row hover and task-text focus do not.
- Double-click a non-control part of a row to pin that same detail popover open, or focus the task text and press `Alt+Enter`. Repeat either action, use the existing disclosure control, or press `Escape` to dismiss it. A single task-text click still enters editing, checkbox clicks still control completion, and drag/reorder controls never trigger row disclosure.
- Treat every even stationary click count as a double-click toggle. Browsers can continue a fixed-pointer sequence as clicks three and four without emitting another native `dblclick`; the even-click handler keeps the second toggle reliable and suppresses any redundant native event.
- `provenance` is required per item, displayed as a compact accessible badge, and preserved by edit, completion, undo, reorder, transfer, and ordinary `upsert` mutations. The browser cannot change it. Only the agent-side, reason-required `correct-provenance` command may repair a proven mistake, and it appends an audit record.

## Stop or inspect

```sh
python3 ~/.codex/skills/outstanding-items/scripts/ledger_ui.py status \
  --ledger /absolute/task/path/outstanding-items.json

python3 ~/.codex/skills/outstanding-items/scripts/ledger_ui.py stop \
  --ledger /absolute/task/path/outstanding-items.json
```

`stop` first queries the tokenized health endpoint and matches the instance ID and exact ledger path before sending SIGTERM. It refuses a stale or ambiguous PID. Stopping the UI never deletes or rewrites the JSON ledger.

## Verification boundary

Automated API tests prove validation, migration, atomic edit/toggle/reopen/reorder behavior, stale-revision rejection, token gating, external-file refresh, and the optional `explanation` field. Asset checks prove that no text input or textarea exists in the resting HTML, that editing creates its textarea on demand, and that every row carries a `role="tooltip"` element wired through `aria-describedby` to its dedicated disclosure control and filled with `textContent`. A real-browser pass must still verify the uncluttered resting state; no detail on row or task-text hover; detail disclosure on caret hover, keyboard focus, and click/tap; `Escape` dismissal; an item with no `explanation`; click-to-edit behavior; completion snackbar and Undo; pointer drag without accidental detail activation; keyboard movement; transferred read-only presentation; responsive layout; and saved-state feedback before calling a new UI design verified.

During that pass, capture the rendered ledger and load the screenshot into vision; DOM, Accessibility, file-existence, and automated-test evidence do not prove visual quality. Fix visible defects caused by the current UI change before finishing. Report a pre-existing browser/display/control problem as the exact acceptance blocker instead of changing unrelated windows or substituting an isolated browser.
