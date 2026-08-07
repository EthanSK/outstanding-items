# Outstanding items

> **Legacy migration fixture.** This Markdown snapshot is preserved to test and
> explain one-time migration. It is not a writable or canonical ledger. The
> current synthetic source of truth is [`outstanding-items.json`](outstanding-items.json).

Owner: the user. Task: task_EXAMPLE_4b7c · Session: sess_EXAMPLE_9d21 · Updated: 2026-05-04T11:20Z

Nothing in this file authorizes work. An item starts only when the user gives a
fresh instruction naming it.

## Outstanding for you

| ID | Item | Status | Note | First seen |
| --- | --- | --- | --- | --- |
| OI-4 | Focus ring on interactive elements | requested | Shared token is a possible route, not permission. | turn 7 |
| OI-5 | Skip link | requested | | turn 7 |
| OI-6 | Aria labels on the nav | requested | Reads the same token as OI-4. | turn 7 |
| OI-7 | Muted-text contrast | requested | Current ratio 3.1:1; target 4.5:1. | turn 7 |
| OI-8 | Reduced-motion pass | requested | | turn 7 |
| OI-9 | Keyboard trap in the dialog | blocked | Upstream bug 4821; local patch regresses Safari. | turn 7 |

## Waiting on you

| ID | Item | Status | The exact action | First seen |
| --- | --- | --- | --- | --- |
| OI-10 | Carry the focus-token memory update | waiting-on-you | Paste the prepared note only if you want the other task's ledger updated. | turn 8 |
| OI-11 | Approve the staging deploy | waiting-on-you | Click approve if you choose to resume the deploy item. | turn 9 |

## Intentional reminders

| ID | Item | Status | Note | First seen |
| --- | --- | --- | --- | --- |
| OI-3 | Ask the design channel about the empty state | reminder | Parked on purpose; no deadline. | turn 3 |

## Suggested for you

OI-4, about twenty minutes: add the shared token and check one button. This is
advice for the user, offered once. It did not change any row above and did not
start work. Tell the agent `start OI-4` only if the agent should do it.

## Done

| ID | Item | Final status | Evidence |
| --- | --- | --- | --- |
| OI-2 | ~~Add rate-limit docs to the handbook~~ | dropped | User cancelled in turn 5; the page is being deleted. |
| OI-1 | ~~Fix the flaky login test~~ | verified | CI run 481: login suite green 20/20. |

## Related tasks

| Title | ID | Direction | Last delta | Result |
| --- | --- | --- | --- | --- |
| Design system audit | task_EXAMPLE_8f31 | outbound | 2026-05-04T11:18Z | prepared (not sent) |

## Notes

- The prepared delta is memory only and cannot be delivered through a tool
  that wakes the destination.
- OI-9 is a genuine external impasse. OI-10 and OI-11 belong to the user and
  may sit untouched indefinitely.
- OI-3 is an intentional reminder, never an execution request.

```json
{
  "version": 2,
  "owner": "user",
  "authorizes_work": false,
  "task_id": "task_EXAMPLE_4b7c",
  "updated": "2026-05-04T11:20Z",
  "outstanding_for_you": [
    { "id": "OI-4", "title": "Focus ring on interactive elements", "status": "requested", "first_seen": "turn 7" },
    { "id": "OI-5", "title": "Skip link", "status": "requested", "first_seen": "turn 7" },
    { "id": "OI-6", "title": "Aria labels on the nav", "status": "requested", "first_seen": "turn 7" },
    { "id": "OI-7", "title": "Muted-text contrast", "status": "requested", "first_seen": "turn 7" },
    { "id": "OI-8", "title": "Reduced-motion pass", "status": "requested", "first_seen": "turn 7" },
    { "id": "OI-9", "title": "Keyboard trap in the dialog", "status": "blocked", "note": "upstream bug 4821; local patch regresses Safari", "first_seen": "turn 7" }
  ],
  "waiting_on_you": [
    { "id": "OI-10", "title": "Carry the focus-token memory update", "status": "waiting-on-you", "note": "paste the prepared note only if wanted" },
    { "id": "OI-11", "title": "Approve the staging deploy", "status": "waiting-on-you", "note": "click approve only after choosing to resume" }
  ],
  "reminders": [
    { "id": "OI-3", "title": "Ask the design channel about the empty state", "status": "reminder" }
  ],
  "suggested_for_you": {
    "id": "OI-4",
    "step": "add the shared token and check one button",
    "why": "about twenty minutes, and it clarifies OI-6",
    "started": false
  },
  "done": [
    { "id": "OI-2", "title": "Add rate-limit docs to the handbook", "status": "dropped", "evidence": "user cancelled in turn 5" },
    { "id": "OI-1", "title": "Fix the flaky login test", "status": "verified", "evidence": "CI run 481, 20/20 green" }
  ],
  "related": [
    { "title": "Design system audit", "id": "task_EXAMPLE_8f31", "result": "prepared (not sent)" }
  ]
}
```
