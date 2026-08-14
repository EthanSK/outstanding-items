# Examples

Copy-paste material. Everything here is synthetic: the task titles are invented and every identifier contains the literal string `EXAMPLE`.

| File | What it is |
| --- | --- |
| [`transcript.md`](transcript.md) | A full task read end to end: one compact footer per turn in the final response, naming a single suggested item — plus `waiting-on-you` against `blocked`, an intentional reminder, rotation after declined advice, the whole list answered in the body when asked, and the distinct genuinely-empty footer. |
| [`outstanding-items.json`](outstanding-items.json) | The synthetic schema-v5 canonical ledger used by the Full outstanding items UI, including immutable provenance, durable ordering intent, and optional tooltip explanations. |
| [`outstanding-items.md`](outstanding-items.md) | A frozen legacy fixture showing the Markdown format accepted by one-time migration. |
| [`delta-messages.md`](delta-messages.md) | Well-formed cross-task deltas, and the malformed versions to avoid. |
| [`global-rules/codex-agents-md.md`](global-rules/codex-agents-md.md) | Paste into `~/.codex/AGENTS.md`. |
| [`global-rules/claude-code-claude-md.md`](global-rules/claude-code-claude-md.md) | Paste into `~/.claude/CLAUDE.md`. |
| [`global-rules/project-instructions.md`](global-rules/project-instructions.md) | Paste into one project's `AGENTS.md` or `CLAUDE.md`. |

In `outstanding-items.json`, three items carry an `explanation` and the completed one deliberately does not — that is the older-ledger case, where the UI shows a plain sentence based on the item's status instead.

None of these files is read at runtime. The canonical skill is `plugins/outstanding-items/skills/outstanding-items/`.
