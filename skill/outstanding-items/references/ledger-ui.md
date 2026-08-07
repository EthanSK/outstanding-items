# Full outstanding items UI

Operational guide for the local interactive ledger. Load after a canonical JSON ledger exists, when a **Full outstanding items** link must be shown, or when the editor needs diagnosis.

## Start or reuse it

The installed runtime lives inside the skill:

```sh
python3 ~/.codex/skills/outstanding-items/scripts/ledger_ui.py start \
  --ledger /absolute/task/path/outstanding-items.json
```

Use the equivalent `~/.claude/skills/` path under Claude Code. The command prints `LEDGER_URL`, `LEDGER_PID`, and `LEDGER_LOG`. It reuses the exact healthy process for that ledger; otherwise it starts a loopback-only process on an available port.

Use the printed URL as the last line of the compact footer:

```markdown
**OI-4 Focus ring on interactive elements** — requested
Twenty minutes, and the shared token is the whole first step.
[Full outstanding items](http://127.0.0.1:PORT/?token=LOCAL_TOKEN)
```

The label is exactly **Full outstanding items**, on its own line, once, as the final line of the footer. This link is the only place the rest of the ledger appears: the footer names one item, and everything else — the other open items, the intentional reminders, and the whole Done history — lives behind it.

If no verified live UI URL exists for this ledger, write no link line at all: never invent, guess, shorten, or redact a URL, never reuse one from an earlier task, and never link the footer to the raw JSON or an archived Markdown list. Use exactly what `start` printed. The token is local runtime state, not ledger data; do not copy it into a repository file, cross-task delta, or public message.

The footer itself, with or without that link, belongs only to the final response of a turn — never to commentary or progress messages.

## Interaction model

Keep the resting interface visually quiet: each actionable row shows only its real checkbox and task text. The task text is the edit control. Clicking or pressing it creates one inline textarea at the same location; `Enter` saves, `Shift+Enter` inserts a line break, `Escape` cancels, and leaving the editor saves. An unchanged edit sends no mutation. Never pre-render a text input or separate Edit button beneath every item.

Hovering a row with a pointer, or moving keyboard focus onto its task text, shows one small tooltip above that row: the item's `OI-n` and a friendly state phrase on the first line, then its short explanation paragraph. It flips below the row only when there is not enough space above. `Escape` dismisses it without moving the pointer or the focus, the pointer can travel onto the tooltip without it closing, and it stays up as long as the row is hovered or focused. The tooltip is text only, rendered with `textContent`, and it is never used to show Markdown, evidence, logs, or a next step.

Open-item reorder controls are latent rather than absent: hover or keyboard focus reveals the drag grip and move buttons. `Alt+Up` and `Alt+Down` on focused task text provide the same keyboard movement without requiring the buttons. Completed items stay at the bottom and may be reopened with their checkbox.

After a successful completion mutation, show a temporary snackbar with **Undo**. Undo sends a real reopen mutation using the current `base_revision`; it never rewinds client state independently of the canonical JSON. Keep the snackbar available for eight seconds, pause its timeout during hover or keyboard focus, do not steal focus, and allow `Command+Z` or `Control+Z` while it is live. A failed or stale mutation must report the error and render the server's current ledger instead of claiming success.

Transferred entries remain plain read-only task text under **Owned elsewhere**. Do not render completion, edit, drag, or move controls for them, and preserve their ID, status, and destination in the accessible label and canonical JSON.

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
  --group "Release" \
  --explanation "The release is built and ready; it just needs your yes before it goes out. One click in the release page is the whole job."
```

For rich notes, write a task-local temporary note and pass `--notes-file`; do not squeeze paragraphs through shell quoting. The command atomically increments the revision, and an open UI sees it within two seconds.

## Writing the explanation

`--explanation` fills the tooltip. Write it as if the user is meeting the item for the first time in a while and wants to feel oriented, not tested.

- One or two warm, ordinary sentences. Up to 600 characters, and shorter is better.
- Say what the item is and why it is on the list, in the user's own vocabulary.
- Plain text only: no Markdown, no code, no file paths, no ticket numbers, no command output, no evidence, no credentials.
- Describe the item, never the plan. It states nothing about what will happen next, claims no progress, and is not permission to act.
- No apologies, no reference to forgetting or remembering, and nothing that reads as talking down to the user.

Good: `The docs page for rate limits has no numbers in it yet, so this is the one where the real limits get written down.`

Avoid: `Per OI-12 above, blocked on the CI matrix; see details_markdown for the full evidence trail.`

Leaving it out is safe. Ledgers written before this field existed stay valid, and the UI falls back to a plain sentence based on the item's status — for example, a `waiting-on-you` item reads as ready and simply needing a moment from the user. Fill the field in when you can: the fallback describes the state, while a written explanation describes the item.

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

- `outstanding-items.json` is the single editable record.
- Every browser mutation carries the revision it read. A stale mutation gets HTTP 409 and the new ledger, so it cannot erase an agent-side update.
- Writes are validated and atomic.
- The browser polls the canonical JSON revision every two seconds while visible. External CLI/agent changes appear without regenerating HTML or restarting the server.
- The HTML, CSS, and JavaScript are a generic shell installed with the skill. They contain no task items and never need regeneration when ledger data changes.
- Transferred items render read-only under **Owned elsewhere** and are excluded from active open/done counts without being deleted.
- `explanation` is an optional per-item string of at most 600 characters. It travels with the rest of the ledger, needs no schema bump, and an item or ledger without it stays valid; the browser supplies the status fallback at render time and stores nothing of its own.

## Stop or inspect

```sh
python3 ~/.codex/skills/outstanding-items/scripts/ledger_ui.py status \
  --ledger /absolute/task/path/outstanding-items.json

python3 ~/.codex/skills/outstanding-items/scripts/ledger_ui.py stop \
  --ledger /absolute/task/path/outstanding-items.json
```

`stop` first queries the tokenized health endpoint and matches the instance ID and exact ledger path before sending SIGTERM. It refuses a stale or ambiguous PID. Stopping the UI never deletes or rewrites the JSON ledger.

## Verification boundary

Automated API tests prove validation, migration, atomic edit/toggle/reopen/reorder behavior, stale-revision rejection, token gating, external-file refresh, and the optional `explanation` field. Asset checks prove that no text input or textarea exists in the resting HTML, that editing creates its textarea on demand, and that every row carries a `role="tooltip"` element wired to its task text through `aria-describedby` and filled with `textContent`. A real-browser pass must still verify the uncluttered resting state, the tooltip on pointer hover and on keyboard focus (including its `Escape` dismissal and an item with no `explanation`), click-to-edit behavior, completion snackbar and Undo, pointer drag, keyboard movement, transferred read-only presentation, responsive layout, and saved-state feedback before calling a new UI design verified.

During that pass, capture the rendered ledger and load the screenshot into vision; DOM, Accessibility, file-existence, and automated-test evidence do not prove visual quality. Fix visible defects caused by the current UI change before finishing. Report a pre-existing browser/display/control problem as the exact acceptance blocker instead of changing unrelated windows or substituting an isolated browser.
