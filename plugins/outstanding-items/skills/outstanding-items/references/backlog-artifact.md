# Backlog artifact

Schema and lifecycle for the task-owned canonical ledger. Load when the footer overflows, the user asks for the full list, or a related task needs registering.

The ledger records the user's items. It never authorizes work — see [authority.md](authority.md).

## One source of truth

The agreed task-owned `outstanding-items.json` file is authoritative. The conversation footer quotes exactly one suggested item from it, and the Full outstanding items HTML UI is a live editor for all of it. Neither is a second ledger, and the footer is not a summary of this file — it is one line drawn from it.

- Update the JSON for agent-side ledger changes, using `scripts/ledger_ui.py upsert` where practical.
- The HTML UI reads the JSON on load, polls it every two seconds, and writes edits back atomically through the loopback server.
- Never embed a copy of the item data in HTML, maintain parallel Markdown tables, or treat browser storage as authoritative.
- A migrated Markdown ledger becomes a frozen legacy snapshot. Preserve it, label it archived, and stop updating it after the JSON migration succeeds.
- If a UI edit races an external JSON update, the server rejects the stale revision with HTTP 409 and returns the newest ledger instead of overwriting it.

The UI process and operational commands are in [ledger-ui.md](ledger-ui.md).

## Default project location

When a chat is scoped to a Git project, create or resolve its canonical ledger before the first captured item:

```sh
python3 ~/.codex/skills/outstanding-items/scripts/ledger_ui.py project-ledger \
  --project-root /absolute/project/root \
  --task-id task_EXAMPLE_4b7c \
  --project-storage
```

Project storage defaults to on, so `--project-storage` is normally optional; it exists to make the setting explicit. Use `--no-project-storage` only for an explicit opt-out. The command then writes nothing and prints `PROJECT_STORAGE_ENABLED=false`.

The canonical project path is `.outstanding-items/<stable-task-id>/outstanding-items.json` under the Git root. Each chat gets a separate directory. The command adds `/.outstanding-items/` to the root `.gitignore` exactly once, refuses a symlinked `.gitignore`, creates the private storage directories with mode `0700`, and creates the ledger with mode `0600`. Re-running it resolves the same ledger without resetting its revision, status, order, or evidence.

Use the stable task/session ID exposed by the harness. Codex can read `CODEX_THREAD_ID`; Claude Code or another harness passes its stable session ID explicitly. If no stable ID is available, stop and ask rather than merging chats or inventing unstable identity. If several repositories are involved, use the primary project for the task and record the others as context; never create competing ledgers.

An already-existing canonical ledger remains authoritative. Do not silently copy or relocate it when a project later enters scope, because that would create two sources of truth. Move it only through an explicit, verified migration.

## Non-project chats

The footer never lists items, so a durable file and its UI are where the user reads the whole thing. For a chat with no Git project, create the JSON ledger after asking once when any of these becomes true:

- More than 7 open items for the user.
- More than 20 items in total.
- The user asks for the full list, a plan, a handover, or the Full outstanding items UI.
- A related task is registered.

Prefer, in order: a path the user names; a task/session scratch directory; `outstanding-items.json` in the working directory.

Do not silently create a ledger before those triggers. When the user has already explicitly asked for the Full outstanding items UI or durable ledger file, that request supplies the path-creation authority; choose the task-owned output directory when one exists and report it.

## Schema version 5

```json
{
  "schema_version": 5,
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
      "provenance": "user-requested",
      "order_intent": {
        "kind": "automatic",
        "relevance_updated_at": "2026-05-04T11:20:00Z"
      },
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
      "provenance": "unknown-legacy",
      "order_intent": {
        "kind": "automatic",
        "relevance_updated_at": null
      },
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
| `schema_version` | Exactly `5` after loading. Versions 3 and 4 are upgraded atomically; other unknown versions are rejected. |
| `owner` / `authorizes_work` | Always `"user"` / `false`. UI edits never change them. |
| `revision` | Non-negative integer incremented after every successful mutation. It prevents stale overwrites. |
| `id` | `OI-n`, permanent, unique, never renumbered. Gaps are normal. |
| `title` | The editable todo text shown in the UI, and in the footer on the turn this item is the one suggested. |
| `status` | One of the nine labels from `SKILL.md`. A label describes; it grants no authority. |
| `completed` | Derived mechanically: true only for `verified` or `dropped`. Completed items render after all open items. |
| `tracking_state` | Optional `active` (the default) or `transferred`. It is orthogonal to status and never implies completion. |
| `transferred_to` | Required only when transferred: exact stable destination task/session ID, cached visible title, transfer timestamp, optional handoff path, and optional title source/update time. The ID is identity; the title is refreshable display metadata. |
| `position` | Contiguous zero-based ordering inside the open or completed group. Automatic reconciliation changes active automatic positions only; completed and transferred groups remain separate. |
| `order_intent` | Required ordering metadata. `automatic` stores nullable `relevance_updated_at`. `manual` additionally stores `manually_positioned_at`, `manual_order_updated_at`, `manual_order_revision`, and stable neighbouring `placed_after_id` / `placed_before_id` anchors. A drag or keyboard move changes only the moved item to `manual`; ordinary edits and reconciliation preserve it. |
| `group` | A display label preserving the originating queue/category. It does not determine execution or section membership. |
| `state_text` | The exact human state sentence when migrating a rich ledger. Preserve it even when `status` is normalized. |
| `details_markdown` | Full item-specific notes, evidence, constraints, and decisions. The list UI edits the title only. |
| `explanation` | Optional. One short, plain-language paragraph (600 characters or fewer) describing what the item is about, shown as the hover/focus tooltip in the UI. Plain text only — no Markdown, evidence, paths, or next steps. Absent or empty is valid, and the UI then falls back to a sentence based on `status`. |
| `provenance` | Required. `user-requested` only when the user explicitly asked to add that specific thing to Outstanding Items; a normal task request captured automatically is `agent-added`. Use `unknown-legacy` only when an older item's capture source cannot be proved. Ordinary mutations preserve this field. |
| `provenance_history` | Optional append-only correction audit. Each record stores `from`, `to`, `corrected_at`, `reason`, and an optional correcting `session_id`. Only `correct-provenance` writes it. |
| `completed_at` | UTC timestamp when checked complete, otherwise null. |
| `completed_session_id` | Stable completing session ID when exposed; otherwise `unavailable` or null. Never invent one. |
| `sections` | Non-item context such as related-task tables, reference maps, and archived decisions. |
| `latest_unanswered_suggestion` | Optional record of the last item the footer suggested that the user has not taken up: `{"id": "OI-4", "text": "…", "outcome": "unanswered"}`. `outcome` is optional and is either `unanswered` or `declined`. It never changes item status or order. Clear it to `null` once the user acts on that item, asks for a fresh suggestion, or the suggestion is replaced. |

The server validates IDs, statuses, completion consistency, unique positions, provenance and its optional correction history, the `explanation` type and length, and the owner/authority invariant before every atomic write. Suggestion metadata is agent-maintained ledger context rather than a browser mutation field.

### Version 3 migration and version 4 migration

Loading a valid version 3 or 4 ledger upgrades it atomically to version 5 and increments its revision once. Version 3 also receives conservative `provenance: "unknown-legacy"`; both versions receive `order_intent: {"kind": "automatic", "relevance_updated_at": null}`. Migration never fabricates a manual placement from old positions, titles, status labels, notes, or conversational wording, and it preserves the existing item order during the schema write. The next explicit `reconcile-order`, server start, or UI load may then intelligently order those automatic items. Status, completion, tracking/transfer state, evidence, and all other item content stay unchanged.

### Ordering policy

The active list has two kinds of ordering intent:

- **Automatic:** surface `waiting-on-you` first, then `in-progress`, then `implemented`, then `planned`/`requested`, then `reminder`, then `blocked`. Within a status band, newest `relevance_updated_at` comes first; when no timestamp is available, the newest permanent `OI-n` ID breaks the tie. Creating or substantively editing an item refreshes its relevance time.
- **Manual:** a Full outstanding items drag or keyboard move fixes the moved item in its selected active-list slot. Automatic items may reorder around those fixed slots, but later reconciliation does not move or clear a manual item. Only another explicit user move changes it again.

This policy avoids whole-list churn: reconciliation writes only when the visible active order actually changes, leaves completed/transferred order alone, and never rearranges the ledger to match the footer's one recommendation.

### Not offering the same thing twice

The footer names one item per turn, so repeating a rejected one is the fastest way to make it unreadable. This field is how that survives a resumed task.

- Write it when the footer suggests something, with `outcome` left out or set to `unanswered`.
- Set `outcome` to `declined` when the user says no, picks something else, or states a different priority. Keep the record; do not delete the item, change its status, or move it.
- While a record is present, exclude that ID while another actionable open item exists. When every alternative has been considered, the best still-open item returns to the candidate pool; refresh its small first step instead of leaving the footer empty or repeating stale copy.
- Clear it to `null` when the user acts on the item, or when they explicitly ask what to do next — an explicit request for advice answers every earlier offer.
- The record is advice history, never authority. Nothing in it permits work, and a resumed task reads it only to stay quiet about the right things.

### Compatibility of `explanation`

`explanation` was added inside schema version 3 rather than by bumping it, because it is additive and optional in both directions:

- A ledger written before the field existed loads, validates, and renders unchanged. Every item without it gets the UI's status fallback, so nothing looks empty or broken.
- A ledger written with it is still an ordinary v3 file. Older tooling ignores the unknown key, and no reader has to understand it.
- `migrate-markdown` writes `explanation: ""` for migrated items rather than inventing a description from the archived Markdown. Fill it in deliberately with `upsert --explanation`, never by guessing.
- The browser never writes this field. It is agent- and CLI-owned, so it cannot drift away from the canonical JSON.

## Ownership transfer

When the user explicitly consolidates work into another task, keep every item in the canonical JSON and preserve its status, evidence, completion state, and ID. Set `tracking_state=transferred` plus `transferred_to`; never relabel it `verified` or `dropped` merely to make it stop appearing, and never suggest a transferred item in the footer. The HTML renders transferred entries read-only inside a collapsed **Owned elsewhere** disclosure and names the destination task, while active counts, completion controls, and suggestions ignore them.

The destination task/session ID is permanent identity. Its title is cached display metadata. When the local Codex binary is available, the editor may refresh only those exact stored IDs through the read-only app-server `thread/list` method and persist a changed title with `title_source=codex-app-server` and `title_updated_at`. Failure is non-fatal, and other harnesses keep the cached title. A refresh never discovers a new destination, reads task turns, sends a message, wakes a task, or changes ownership.

The handoff must identify collisions where the destination already uses the same ID for a different item. Preserve both histories and let the destination's newer state win; never overwrite one item just to make IDs globally unique across independent tasks.

## UI completion semantics

Checking an open item is the user's direct confirmation that it is complete. The server stores its previous status, sets `status=verified`, moves it to the completed group, and records the completion time. When the harness does not provide a session ID, it records `unavailable` rather than inventing one.

Unchecking restores the prior non-retiring status when available, otherwise `requested`, and returns the item to the bottom of the open list. `dropped` remains a deliberate agent/CLI status; the checkbox represents completion, not cancellation.

Agent-side ledger maintenance uses the same canonical mutation path. On every ledger interaction, compare each active item's recorded scope with exact completion evidence observed now or already preserved in that item. When that evidence proves the scoped outcome complete, `upsert --status verified` moves it to Done and preserves its provenance and proof. Do this for `agent-added` items without creating a redundant acceptance chore. Leave implemented-but-unverified, waiting-on-user, blocked, reminder, transferred, speculative, and otherwise unfinished items open.

## Lifecycle

1. **Create or migrate.** Create native JSON, or run `migrate-markdown` once against the existing ledger. Validate the result before retiring the Markdown file from active use.
2. **Start the UI.** Run the loopback-only server and capture its tokenized URL. The footer's single **Full outstanding items** link points to this HTML URL, never to the raw JSON or legacy Markdown. Normal stop/start cycles reuse the same user-only connection record so already-open tabs reconnect.
3. **Update.** Agent-side changes mutate the JSON. UI changes use revision-checked atomic writes. The open browser refreshes itself whenever the JSON revision changes.
4. **Transfer when explicitly instructed.** Send the authorized handoff once, run `transfer` for the exact IDs, and verify they are read-only history with unchanged statuses.
5. **Reconcile.** On task resume, validate and read the JSON, choose at most one active item for the footer of that turn's final response, honour any `latest_unanswered_suggestion` by not repeating it, then wait. Restoring a ledger starts nothing. A stale `in-progress` label must be reconciled to `implemented` when material work changed, `planned` when only an agreed route exists, or `requested` when neither is true; none of those labels authorizes resumption.
6. **Close.** Leave the canonical JSON, transferred history, and completed history in place. Stop the UI server when the user no longer wants the link available; never delete the ledger as cleanup.

## Safety

- Bind the editor to `127.0.0.1` only. API calls require the random token in the Full outstanding items URL, reject foreign Host headers, set no CORS permission, and write no browser storage.
- The browser makes no outbound requests and loads no third-party assets. Optional Codex title refresh uses a short-lived local app-server process with remote plugin sync disabled.
- Write ledger JSON with a same-directory temporary file, `fsync`, and `os.replace`; never partially rewrite it in place.
- Keep runtime token/state/log files next to the task ledger with user-only state-file permissions. Never commit or share them.
- Never put credentials or secret file contents into titles, notes, explanations, sections, URLs, examples, or logs.
- A public repository contains only the generic UI and synthetic fixtures. Real ledgers remain task-owned and private.
