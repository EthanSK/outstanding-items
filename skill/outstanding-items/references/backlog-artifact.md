# Backlog artifact

Schema and lifecycle for the task-owned canonical ledger. Load when the footer overflows, the user asks for the full list, or a related task needs registering.

The ledger records the user's items. It never authorizes work — see [authority.md](authority.md).

## One source of truth

The agreed task-owned `outstanding-items.json` file is authoritative. The conversation footer is a compact rendering of it, and the Full outstanding items HTML UI is a live editor for it. Neither is a second ledger.

- Update the JSON for agent-side ledger changes, using `scripts/ledger_ui.py upsert` where practical.
- The HTML UI reads the JSON on load, polls it every two seconds, and writes edits back atomically through the loopback server.
- Never embed a copy of the item data in HTML, maintain parallel Markdown tables, or treat browser storage as authoritative.
- A migrated Markdown ledger becomes a frozen legacy snapshot. Preserve it, label it archived, and stop updating it after the JSON migration succeeds.
- If a UI edit races an external JSON update, the server rejects the stale revision with HTTP 409 and returns the newest ledger instead of overwriting it.

The UI process and operational commands are in [ledger-ui.md](ledger-ui.md).

## When to create it

Create the JSON ledger after asking once when any of these becomes true:

- More than 7 items under **Outstanding for you**.
- More than 20 items in total.
- The user asks for the full list, a plan, a handover, or the Full outstanding items UI.
- A related task is registered.

Prefer, in order: a path the user names; a task/session scratch directory; `outstanding-items.json` in the working directory. In a Git repository, offer to add the exact ledger and its `.ledger-ui-*` runtime files to `.git/info/exclude`.

Do not silently create a ledger before those triggers. When the user has already explicitly asked for the Full outstanding items UI or durable ledger file, that request supplies the path-creation authority; choose the task-owned output directory when one exists and report it.

## Schema version 3

```json
{
  "schema_version": 3,
  "owner": "user",
  "authorizes_work": false,
  "title": "Outstanding items",
  "task_id": "task_EXAMPLE_4b7c",
  "revision": 12,
  "created_at": "2026-05-04T10:00:00Z",
  "updated_at": "2026-05-04T11:20:00Z",
  "latest_unanswered_suggestion": null,
  "items": [
    {
      "id": "OI-4",
      "title": "Fix the flaky login test",
      "status": "implemented",
      "completed": false,
      "tracking_state": "active",
      "position": 0,
      "group": "Outstanding for you",
      "state_text": "implemented; CI proof pending",
      "details_markdown": "Retried 20x locally, not on CI.",
      "explanation": "This is the login test that passes locally and fails at random on CI. The fix is in, and a green CI run is what would settle it.",
      "completed_at": null,
      "completed_session_id": null
    },
    {
      "id": "OI-1",
      "title": "Rename the deploy script",
      "status": "verified",
      "completed": true,
      "position": 0,
      "group": "Done",
      "state_text": "verified",
      "details_markdown": "`./deploy.sh --help` ran clean.",
      "completed_at": "2026-05-04T11:10:00Z",
      "completed_session_id": "sess_EXAMPLE_9d21"
    }
  ],
  "sections": [
    {"title": "Related tasks", "markdown": "Registry context the item rows do not hold."}
  ],
  "source": {"kind": "native-json", "status": "canonical"}
}
```

## Field rules

| Field | Rule |
| --- | --- |
| `schema_version` | Exactly `3` for this implementation. Reject unknown versions. |
| `owner` / `authorizes_work` | Always `"user"` / `false`. UI edits never change them. |
| `revision` | Non-negative integer incremented after every successful mutation. It prevents stale overwrites. |
| `id` | `OI-n`, permanent, unique, never renumbered. Gaps are normal. |
| `title` | The editable todo text shown in the footer and UI. |
| `status` | One of the nine labels from `SKILL.md`. A label describes; it grants no authority. |
| `completed` | Derived mechanically: true only for `verified` or `dropped`. Completed items render after all open items. |
| `tracking_state` | Optional `active` (the default) or `transferred`. It is orthogonal to status and never implies completion. |
| `transferred_to` | Required only when transferred: exact destination task ID/title, transfer timestamp, and optional handoff path. |
| `position` | Contiguous zero-based ordering inside the open or completed group. Dragging changes open positions only. |
| `group` | A display label preserving the originating queue/category. It does not determine execution or section membership. |
| `state_text` | The exact human state sentence when migrating a rich ledger. Preserve it even when `status` is normalized. |
| `details_markdown` | Full item-specific notes, evidence, constraints, and decisions. The list UI edits the title only. |
| `explanation` | Optional. One short, plain-language paragraph (600 characters or fewer) describing what the item is about, shown as the hover/focus tooltip in the UI. Plain text only — no Markdown, evidence, paths, or next steps. Absent or empty is valid, and the UI then falls back to a sentence based on `status`. |
| `completed_at` | UTC timestamp when checked complete, otherwise null. |
| `completed_session_id` | Stable completing session ID when exposed; otherwise `unavailable` or null. Never invent one. |
| `sections` | Non-item context such as related-task tables, reference maps, and archived decisions. |
| `latest_unanswered_suggestion` | Optional record of the latest unanswered suggestion. It never changes item status or order. Clear it after the user accepts, declines, or replaces the suggestion. |

The server validates IDs, statuses, completion consistency, unique positions, the `explanation` type and length, and the owner/authority invariant before every atomic write.

### Compatibility of `explanation`

`explanation` was added inside schema version 3 rather than by bumping it, because it is additive and optional in both directions:

- A ledger written before the field existed loads, validates, and renders unchanged. Every item without it gets the UI's status fallback, so nothing looks empty or broken.
- A ledger written with it is still an ordinary v3 file. Older tooling ignores the unknown key, and no reader has to understand it.
- `migrate-markdown` writes `explanation: ""` for migrated items rather than inventing a description from the archived Markdown. Fill it in deliberately with `upsert --explanation`, never by guessing.
- The browser never writes this field. It is agent- and CLI-owned, so it cannot drift away from the canonical JSON.

## Ownership transfer

When the user explicitly consolidates work into another task, keep every item in the canonical JSON and preserve its status, evidence, completion state, and ID. Set `tracking_state=transferred` plus `transferred_to`; never relabel it `verified` or `dropped` merely to remove it from the active footer. The HTML renders transferred entries read-only under **Owned elsewhere**, while active counts, completion controls, and suggestions ignore them.

The handoff must identify collisions where the destination already uses the same ID for a different item. Preserve both histories and let the destination's newer state win; never overwrite one item just to make IDs globally unique across independent tasks.

## UI completion semantics

Checking an open item is the user's direct confirmation that it is complete. The server stores its previous status, sets `status=verified`, moves it to the completed group, and records the completion time. When the harness does not provide a session ID, it records `unavailable` rather than inventing one.

Unchecking restores the prior non-retiring status when available, otherwise `requested`, and returns the item to the bottom of the open list. `dropped` remains a deliberate agent/CLI status; the checkbox represents completion, not cancellation.

## Lifecycle

1. **Create or migrate.** Create native JSON, or run `migrate-markdown` once against the existing ledger. Validate the result before retiring the Markdown file from active use.
2. **Start the UI.** Run the loopback-only server and capture its tokenized URL. Both of the footer's **Full outstanding items** links point to this HTML URL, never to the raw JSON or legacy Markdown.
3. **Update.** Agent-side changes mutate the JSON. UI changes use revision-checked atomic writes. The open browser refreshes itself whenever the JSON revision changes.
4. **Transfer when explicitly instructed.** Send the authorized handoff once, run `transfer` for the exact IDs, and verify they are read-only history with unchanged statuses.
5. **Reconcile.** On task resume, validate and read the JSON, render the footer from active items in the final response of that turn, then wait. Restoring a ledger starts nothing. A stale `in-progress` label must be reconciled to `implemented` when material work changed, `planned` when only an agreed route exists, or `requested` when neither is true; none of those labels authorizes resumption.
6. **Close.** Leave the canonical JSON, transferred history, and completed history in place. Stop the UI server when the user no longer wants the link available; never delete the ledger as cleanup.

## Safety

- Bind the editor to `127.0.0.1` only. API calls require the random token in the Full outstanding items URL, reject foreign Host headers, set no CORS permission, and write no browser storage.
- The UI makes no outbound requests and loads no third-party assets.
- Write ledger JSON with a same-directory temporary file, `fsync`, and `os.replace`; never partially rewrite it in place.
- Keep runtime token/state/log files next to the task ledger with user-only state-file permissions. Never commit or share them.
- Never put credentials or secret file contents into titles, notes, explanations, sections, URLs, examples, or logs.
- A public repository contains only the generic UI and synthetic fixtures. Real ledgers remain task-owned and private.
