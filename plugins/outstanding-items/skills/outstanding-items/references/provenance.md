# Provenance

Load this reference when creating an item, auditing source badges, or correcting an earlier provenance mistake.

Provenance answers one narrow question: **who explicitly caused this ledger entry to be created?** It does not answer who first mentioned the work, who wants it done, who authorized execution, or who later completed it.

## Classification

| User wording or event | Provenance | Why |
| --- | --- | --- |
| “Add the release note to Outstanding Items.” | `user-requested` | The user explicitly requested this ledger entry. |
| “Record the release note in the outstanding-items ledger.” | `user-requested` | The user explicitly requested this ledger entry. |
| “We need to write the release note.” | `agent-added` if captured | It is a work request, not a request to create a ledger entry. |
| “Can you write the release note?” | `agent-added` if captured | It authorizes work; it does not explicitly request ledger capture. |
| “Remember the release note.” | `agent-added` if captured | It asks the agent to remember, but does not explicitly name Outstanding Items. |
| “Start OI-7 now.” | Preserve the existing provenance | Starting an item never rewrites how it entered the ledger. |
| The current work leaves a concrete review, decision, input, verification, or follow-up for the user. | `agent-added` | The agent must preserve the real loose end even without an explicit request to add it. |
| The agent imagines an optional enhancement with no concrete unresolved need. | Do not add it. | Preventing omission does not authorize filler or speculative projects. |
| An old record has no provable capture wording. | `unknown-legacy` | Do not invent an origin. |

The phrases do not need to be letter-for-letter identical. “Put that on my Outstanding Items list” and “add a new outstanding item for this” are equally explicit. The required fact is that the user deliberately asked for the **ledger entry itself**, not merely for the underlying work.

Before reporting `No outstanding items`, inspect the current request, results, blockers, decisions, and unverified outcomes. Every concrete thing the user still needs to look at becomes `agent-added`. An honestly empty ledger is allowed; an empty ledger caused by forgetting a real loose end is not.

Provenance never changes the completion threshold. Reconcile `user-requested`, `agent-added`, and honest legacy items from the same evidence. When an `agent-added` item's scoped outcome is already verified, move it to Done automatically rather than creating a redundant user-acceptance chore; preserve its provenance and proof.

## Corrections

Ordinary edits, browser mutations, completion, reordering, transfer, and `upsert` preserve provenance. When a recorded origin is demonstrably wrong, use the dedicated agent-side correction command with a short evidence-based reason:

```sh
python3 scripts/ledger_ui.py correct-provenance \
  --ledger outstanding-items.json \
  --ids OI-7 OI-8 \
  --provenance agent-added \
  --reason "The source messages requested work but never requested ledger capture." \
  --session-id sess_EXAMPLE_7f2a
```

The correction changes no title, status, completion state, position, transfer state, or evidence. It increments the ledger revision and appends an immutable `provenance_history` entry containing the old value, new value, timestamp, reason, and the correcting session ID when one is available. Never use the command to replace uncertainty with a guess.
