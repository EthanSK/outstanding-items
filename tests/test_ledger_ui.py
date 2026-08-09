#!/usr/bin/env python3
"""End-to-end tests for the canonical ledger and local HTML editor server."""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import types
import unittest
import urllib.error
import urllib.parse
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skill" / "outstanding-items" / "scripts" / "ledger_ui.py"
ASSETS = ROOT / "skill" / "outstanding-items" / "assets"
SPEC = importlib.util.spec_from_file_location("ledger_ui", SCRIPT)
assert SPEC and SPEC.loader
ledger_ui = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ledger_ui)


def sample_ledger() -> dict:
    return {
        "schema_version": 4,
        "owner": "user",
        "authorizes_work": False,
        "title": "Synthetic full ledger",
        "task_id": "task_EXAMPLE_1234",
        "revision": 1,
        "created_at": "2026-08-07T10:00:00Z",
        "updated_at": "2026-08-07T10:00:00Z",
        "latest_unanswered_suggestion": None,
        "items": [
            {
                "id": "OI-1",
                "title": "First open item",
                "status": "requested",
                "completed": False,
                "position": 0,
                "group": "Outstanding for you",
                "state_text": "requested",
                "details_markdown": "Synthetic note one.",
                "explanation": "A synthetic item kept here so the tooltip has something plain to say.",
                "provenance": "user-requested",
                "completed_at": None,
                "completed_session_id": None,
            },
            {
                "id": "OI-2",
                "title": "Second open item",
                "status": "planned",
                "completed": False,
                "position": 1,
                "group": "Outstanding for you",
                "state_text": "planned",
                "details_markdown": "Synthetic note two.",
                "provenance": "agent-added",
                "completed_at": None,
                "completed_session_id": None,
            },
            {
                "id": "OI-3",
                "title": "Already complete",
                "status": "verified",
                "completed": True,
                "position": 0,
                "group": "Done",
                "state_text": "verified",
                "details_markdown": "Synthetic proof.",
                "provenance": "unknown-legacy",
                "completed_at": "2026-08-07T10:00:00Z",
                "completed_session_id": "sess_EXAMPLE_1234",
            },
        ],
        "sections": [{"title": "Notes", "markdown": "Synthetic global context."}],
        "source": {"kind": "synthetic-test", "path": "synthetic", "status": "test-only"},
    }


class LedgerModelTests(unittest.TestCase):
    def test_acting_on_the_suggested_item_clears_the_unanswered_pointer(self) -> None:
        data = sample_ledger()
        data["latest_unanswered_suggestion"] = {
            "id": "OI-1",
            "text": "Synthetic suggestion",
            "outcome": "unanswered",
        }
        edited = ledger_ui.mutate(
            data,
            {"base_revision": 1, "action": "edit", "id": "OI-1", "title": "Edited item"},
        )
        self.assertIsNone(edited["latest_unanswered_suggestion"])

    def test_v3_ledger_migrates_to_unknown_legacy_without_item_state_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = pathlib.Path(temp) / "ledger.json"
            legacy = sample_ledger()
            legacy["schema_version"] = 3
            legacy["revision"] = 8
            for item in legacy["items"]:
                item.pop("provenance")
            before = copy.deepcopy(legacy["items"])
            ledger.write_text(json.dumps(legacy), encoding="utf-8")

            migrated = ledger_ui.read_json(ledger)

            self.assertEqual(migrated["schema_version"], 4)
            self.assertEqual(migrated["revision"], 9)
            self.assertTrue(all(item["provenance"] == "unknown-legacy" for item in migrated["items"]))
            after = copy.deepcopy(migrated["items"])
            for item in after:
                item.pop("provenance")
            self.assertEqual(after, before)
            self.assertEqual(json.loads(ledger.read_text(encoding="utf-8"))["schema_version"], 4)

    def test_current_schema_requires_supported_provenance(self) -> None:
        data = sample_ledger()
        data["items"][0].pop("provenance")
        with self.assertRaisesRegex(ValueError, "unsupported provenance"):
            ledger_ui.validate_ledger(data)
        data["items"][0]["provenance"] = "probably-user"
        with self.assertRaisesRegex(ValueError, "unsupported provenance"):
            ledger_ui.validate_ledger(data)

    def test_markdown_migration_preserves_items_notes_and_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = pathlib.Path(temp) / "legacy.md"
            source.write_text(
                "# Legacy ledger\n\nIntro text.\n\n"
                "## Product work\n\nGroup note.\n\n"
                "### OI-1 Build the thing\n\n- **State:** requested; untouched.\n- **Wanted:** Keep this detail.\n\n"
                "### OI-2 Verify the thing\n\n- **State:** verified complete.\n- **Evidence:** Synthetic pass.\n\n"
                "## Related tasks\n\n| Title | ID |\n|---|---|\n| Example | task_EXAMPLE_1234 |\n",
                encoding="utf-8",
            )
            data = ledger_ui.migrate_markdown(source, "Migrated ledger", "task_EXAMPLE_9999")
            self.assertEqual([item["id"] for item in data["items"]], ["OI-1", "OI-2"])
            self.assertIn("Keep this detail", data["items"][0]["details_markdown"])
            self.assertFalse(data["items"][0]["completed"])
            self.assertTrue(data["items"][1]["completed"])
            self.assertTrue(
                all(item["provenance"] == "unknown-legacy" for item in data["items"])
            )
            self.assertTrue(any(section["title"] == "Related tasks" for section in data["sections"]))
            ledger_ui.validate_ledger(data)

    def test_markdown_migration_promotes_struck_id_items_to_completed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = pathlib.Path(temp) / "legacy.md"
            source.write_text(
                "# Legacy ledger\n\n"
                "## Done — verified milestones only\n\n"
                "- ~~OI-9 Ship the editor.~~ Verified by synthetic browser proof.\n"
                "  The retained detail belongs to OI-9.\n"
                "- ~~An unnumbered milestone.~~ Preserved as section context.\n"
                "- ~~OI-7 Drop the old route.~~\n"
                "  Dropped by the user on the following line.\n",
                encoding="utf-8",
            )
            data = ledger_ui.migrate_markdown(source, "Migrated ledger", None)
            self.assertEqual([item["id"] for item in data["items"]], ["OI-9", "OI-7"])
            self.assertEqual([item["status"] for item in data["items"]], ["verified", "dropped"])
            self.assertTrue(all(item["completed"] for item in data["items"]))
            self.assertIn("retained detail", data["items"][0]["details_markdown"])
            section_text = "\n".join(section["markdown"] for section in data["sections"])
            self.assertIn("An unnumbered milestone", section_text)
            ledger_ui.validate_ledger(data)

    def test_validation_rejects_duplicate_ids(self) -> None:
        data = sample_ledger()
        duplicate = dict(data["items"][0])
        duplicate["position"] = 2
        data["items"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "duplicate item id"):
            ledger_ui.validate_ledger(data)

    def test_explanation_is_optional_typed_and_bounded(self) -> None:
        data = sample_ledger()
        # OI-2 and OI-3 predate the field, which must stay valid on its own.
        self.assertNotIn("explanation", data["items"][1])
        self.assertNotIn("explanation", data["items"][2])
        ledger_ui.validate_ledger(data)

        data["items"][1]["explanation"] = "A short, plain sentence about this item."
        ledger_ui.validate_ledger(data)

        data["items"][1]["explanation"] = 42
        with self.assertRaisesRegex(ValueError, "explanation must be a string"):
            ledger_ui.validate_ledger(data)

        data["items"][1]["explanation"] = "x" * (ledger_ui.MAX_EXPLANATION_CHARS + 1)
        with self.assertRaisesRegex(ValueError, "at most"):
            ledger_ui.validate_ledger(data)

    def test_upsert_writes_and_preserves_an_explanation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = pathlib.Path(temp) / "ledger.json"
            ledger_ui.atomic_write_json(ledger, sample_ledger())
            args = types.SimpleNamespace(
                ledger=str(ledger),
                id="OI-9",
                title="A newly captured item",
                status="requested",
                provenance="user-requested",
                group=None,
                explanation="  A gentle sentence\n  spread over two lines.  ",
                notes_file=None,
                session_id=None,
            )
            self.assertEqual(ledger_ui.command_upsert(args), 0)
            created = next(
                item for item in ledger_ui.read_json(ledger)["items"] if item["id"] == "OI-9"
            )
            self.assertEqual(created["explanation"], "A gentle sentence spread over two lines.")
            self.assertEqual(created["provenance"], "user-requested")
            open_items = sorted(
                (item for item in ledger_ui.read_json(ledger)["items"] if not item["completed"]),
                key=lambda item: item["position"],
            )
            self.assertEqual([item["id"] for item in open_items], ["OI-9", "OI-1", "OI-2"])

            args.explanation = None
            args.title = "A renamed item"
            args.provenance = None
            self.assertEqual(ledger_ui.command_upsert(args), 0)
            kept = next(
                item for item in ledger_ui.read_json(ledger)["items"] if item["id"] == "OI-9"
            )
            self.assertEqual(kept["title"], "A renamed item")
            self.assertEqual(kept["explanation"], "A gentle sentence spread over two lines.")
            self.assertEqual(kept["provenance"], "user-requested")

            args.explanation = "y" * (ledger_ui.MAX_EXPLANATION_CHARS + 1)
            with self.assertRaisesRegex(ValueError, "at most"):
                ledger_ui.command_upsert(args)

    def test_new_completed_history_does_not_reorder_open_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = pathlib.Path(temp) / "ledger.json"
            ledger_ui.atomic_write_json(ledger, sample_ledger())
            args = types.SimpleNamespace(
                ledger=str(ledger),
                id="OI-9",
                title="A completed historical item",
                status="verified",
                provenance="user-requested",
                group="Done",
                explanation=None,
                notes_file=None,
                session_id="sess_EXAMPLE_9012",
            )

            self.assertEqual(ledger_ui.command_upsert(args), 0)
            data = ledger_ui.read_json(ledger)
            open_items = sorted(
                (item for item in data["items"] if not item["completed"]),
                key=lambda item: item["position"],
            )
            done_items = sorted(
                (item for item in data["items"] if item["completed"]),
                key=lambda item: item["position"],
            )
            self.assertEqual([item["id"] for item in open_items], ["OI-1", "OI-2"])
            self.assertEqual([item["id"] for item in done_items], ["OI-3", "OI-9"])

    def test_status_update_clears_the_matching_unanswered_suggestion(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = pathlib.Path(temp) / "ledger.json"
            data = sample_ledger()
            data["latest_unanswered_suggestion"] = {
                "id": "OI-1",
                "text": "Synthetic suggestion",
                "outcome": "unanswered",
            }
            ledger_ui.atomic_write_json(ledger, data)
            args = types.SimpleNamespace(
                ledger=str(ledger),
                id="OI-1",
                title=None,
                status="verified",
                provenance=None,
                group=None,
                explanation=None,
                notes_file=None,
                session_id="sess_EXAMPLE_5678",
            )
            self.assertEqual(ledger_ui.command_upsert(args), 0)
            self.assertIsNone(ledger_ui.read_json(ledger)["latest_unanswered_suggestion"])

    def test_new_item_requires_provenance_and_existing_origin_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = pathlib.Path(temp) / "ledger.json"
            ledger_ui.atomic_write_json(ledger, sample_ledger())
            args = types.SimpleNamespace(
                ledger=str(ledger),
                id="OI-9",
                title="A newly captured item",
                status="requested",
                provenance=None,
                group=None,
                explanation=None,
                notes_file=None,
                session_id=None,
            )
            with self.assertRaisesRegex(ValueError, "--provenance is required"):
                ledger_ui.command_upsert(args)

            for provenance in sorted(ledger_ui.PROVENANCES):
                args.id = f"OI-{10 + len(ledger_ui.read_json(ledger)['items'])}"
                args.provenance = provenance
                ledger_ui.command_upsert(args)
                created = next(
                    item for item in ledger_ui.read_json(ledger)["items"] if item["id"] == args.id
                )
                self.assertEqual(created["provenance"], provenance)

            args.id = "OI-1"
            args.title = None
            args.provenance = "agent-added"
            with self.assertRaisesRegex(ValueError, "provenance is immutable"):
                ledger_ui.command_upsert(args)

    def test_migration_leaves_the_explanation_empty_for_the_ui_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = pathlib.Path(temp) / "legacy.md"
            source.write_text(
                "# Legacy ledger\n\n## Product work\n\n"
                "### OI-1 Build the thing\n\n- **State:** requested; untouched.\n",
                encoding="utf-8",
            )
            data = ledger_ui.migrate_markdown(source, "Migrated ledger", None)
            self.assertEqual(data["items"][0]["explanation"], "")
            ledger_ui.validate_ledger(data)

    def test_transfer_preserves_status_and_records_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = pathlib.Path(temp) / "ledger.json"
            ledger_ui.atomic_write_json(ledger, sample_ledger())
            args = types.SimpleNamespace(
                ledger=str(ledger),
                ids=["OI-1", "OI-3"],
                task_id="task_EXAMPLE_target",
                destination_title="Destination task",
                handoff_path=str(pathlib.Path(temp) / "handoff.md"),
            )
            self.assertEqual(ledger_ui.command_transfer(args), 0)
            data = ledger_ui.read_json(ledger)
            by_id = {item["id"]: item for item in data["items"]}
            self.assertEqual(by_id["OI-1"]["status"], "requested")
            self.assertEqual(by_id["OI-3"]["status"], "verified")
            self.assertEqual(by_id["OI-1"]["provenance"], "user-requested")
            self.assertEqual(by_id["OI-3"]["provenance"], "unknown-legacy")
            self.assertEqual(by_id["OI-1"]["tracking_state"], "transferred")
            self.assertEqual(by_id["OI-3"]["transferred_to"]["task_id"], "task_EXAMPLE_target")
            self.assertNotEqual(by_id["OI-2"].get("tracking_state"), "transferred")
            ledger_ui.validate_ledger(data)


class LedgerServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.temp.name)
        self.ledger = root / "ledger.json"
        ledger_ui.atomic_write_json(self.ledger, sample_ledger())
        self.state_file = root / "state.json"
        self.token = "token_EXAMPLE_1234"
        self.process = subprocess.Popen(
            [
                sys.executable,
                str(SCRIPT),
                "serve",
                "--ledger",
                str(self.ledger),
                "--port",
                "0",
                "--token",
                self.token,
                "--instance-id",
                "instance_EXAMPLE_1234",
                "--state-file",
                str(self.state_file),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 5
        self.state = None
        while time.monotonic() < deadline:
            if self.state_file.exists():
                self.state = json.loads(self.state_file.read_text(encoding="utf-8"))
                if ledger_ui.health(self.state["url"], self.token):
                    break
            if self.process.poll() is not None:
                stderr = self.process.stderr.read() if self.process.stderr else ""
                self.fail(f"server exited early: {stderr}")
            time.sleep(0.05)
        if not self.state:
            self.fail("server did not become ready")
        parsed = urllib.parse.urlsplit(self.state["url"])
        self.base = f"{parsed.scheme}://{parsed.netloc}"

    def tearDown(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        if self.process.stdout:
            self.process.stdout.close()
        if self.process.stderr:
            self.process.stderr.close()
        self.temp.cleanup()

    def request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict | str]:
        url = f"{self.base}{path}"
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}token={urllib.parse.quote(self.token)}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers={"Content-Type": "application/json", "X-Ledger-Token": self.token},
        )
        try:
            with urllib.request.urlopen(request, timeout=2) as response:
                content = response.read().decode("utf-8")
                return response.status, json.loads(content) if "application/json" in response.headers.get("Content-Type", "") else content
        except urllib.error.HTTPError as exc:
            try:
                content = exc.read().decode("utf-8")
                return exc.code, json.loads(content)
            finally:
                exc.close()

    def test_edit_reorder_complete_and_external_refresh(self) -> None:
        status, current = self.request("GET", "/api/ledger")
        self.assertEqual(status, 200)
        self.assertEqual(current["revision"], 1)
        self.assertEqual(current["_runtime"]["ledger_path"], str(self.ledger.resolve()))

        status, edited = self.request(
            "POST",
            "/api/mutate",
            {"base_revision": 1, "action": "edit", "id": "OI-1", "title": "Edited first item"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(edited["revision"], 2)
        self.assertEqual(edited["items"][0]["title"], "Edited first item")

        status, reordered = self.request(
            "POST",
            "/api/mutate",
            {"base_revision": 2, "action": "reorder", "order": ["OI-2", "OI-1"]},
        )
        self.assertEqual(status, 200)
        open_order = [item["id"] for item in sorted(
            (item for item in reordered["items"] if not item["completed"]), key=lambda item: item["position"]
        )]
        self.assertEqual(open_order, ["OI-2", "OI-1"])

        status, completed = self.request(
            "POST",
            "/api/mutate",
            {"base_revision": 3, "action": "toggle", "id": "OI-2", "completed": True},
        )
        self.assertEqual(status, 200)
        item = next(item for item in completed["items"] if item["id"] == "OI-2")
        self.assertTrue(item["completed"])
        self.assertEqual(item["status"], "verified")
        self.assertEqual(item["provenance"], "agent-added")

        status, reopened = self.request(
            "POST",
            "/api/mutate",
            {"base_revision": 4, "action": "toggle", "id": "OI-2", "completed": False},
        )
        self.assertEqual(status, 200)
        item = next(item for item in reopened["items"] if item["id"] == "OI-2")
        self.assertFalse(item["completed"])
        self.assertEqual(item["status"], "planned")
        self.assertEqual(item["provenance"], "agent-added")

        external = ledger_ui.read_json(self.ledger)
        external["title"] = "Externally updated title"
        external["revision"] += 1
        external["updated_at"] = ledger_ui.utc_now()
        ledger_ui.atomic_write_json(self.ledger, external)
        status, refreshed = self.request("GET", "/api/ledger")
        self.assertEqual(status, 200)
        self.assertEqual(refreshed["title"], "Externally updated title")

    def test_stale_revision_conflicts_without_overwrite(self) -> None:
        status, _ = self.request(
            "POST",
            "/api/mutate",
            {"base_revision": 1, "action": "edit", "id": "OI-1", "title": "Fresh edit"},
        )
        self.assertEqual(status, 200)
        status, conflict = self.request(
            "POST",
            "/api/mutate",
            {"base_revision": 1, "action": "edit", "id": "OI-1", "title": "Stale overwrite"},
        )
        self.assertEqual(status, 409)
        self.assertIn("changed elsewhere", conflict["error"])
        saved = ledger_ui.read_json(self.ledger)
        self.assertEqual(next(item for item in saved["items"] if item["id"] == "OI-1")["title"], "Fresh edit")

    def test_transferred_items_are_read_only_and_excluded_from_reorder(self) -> None:
        data = ledger_ui.read_json(self.ledger)
        item = next(item for item in data["items"] if item["id"] == "OI-1")
        item["tracking_state"] = "transferred"
        item["transferred_to"] = {
            "task_id": "task_EXAMPLE_target",
            "title": "Destination task",
            "transferred_at": ledger_ui.utc_now(),
        }
        data["revision"] = 2
        ledger_ui.normalize_positions(data)
        ledger_ui.atomic_write_json(self.ledger, data)

        status, error = self.request(
            "POST",
            "/api/mutate",
            {"base_revision": 2, "action": "edit", "id": "OI-1", "title": "Must not change"},
        )
        self.assertEqual(status, 400)
        self.assertIn("read-only", error["error"])

        status, reordered = self.request(
            "POST",
            "/api/mutate",
            {"base_revision": 2, "action": "reorder", "order": ["OI-2"]},
        )
        self.assertEqual(status, 200)
        self.assertEqual(reordered["revision"], 3)

    def test_browser_mutation_cannot_rewrite_an_explanation(self) -> None:
        original = next(
            item for item in ledger_ui.read_json(self.ledger)["items"] if item["id"] == "OI-1"
        )["explanation"]
        status, payload = self.request(
            "POST",
            "/api/mutate",
            {
                "base_revision": 1,
                "action": "edit",
                "id": "OI-1",
                "title": "Edited title only",
                "explanation": "Injected by the browser",
            },
        )
        self.assertEqual(status, 200)
        item = next(entry for entry in payload["items"] if entry["id"] == "OI-1")
        self.assertEqual(item["title"], "Edited title only")
        self.assertEqual(item["explanation"], original)

    def test_browser_mutation_cannot_rewrite_provenance(self) -> None:
        original = next(
            item for item in ledger_ui.read_json(self.ledger)["items"] if item["id"] == "OI-1"
        )["provenance"]
        status, payload = self.request(
            "POST",
            "/api/mutate",
            {
                "base_revision": 1,
                "action": "edit",
                "id": "OI-1",
                "title": "Edited title only",
                "provenance": "agent-added",
            },
        )
        self.assertEqual(status, 200)
        item = next(entry for entry in payload["items"] if entry["id"] == "OI-1")
        self.assertEqual(item["provenance"], original)

    def test_html_assets_and_token_gate(self) -> None:
        status, html = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("Full outstanding items", html)
        self.assertIn("item-template", html)
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(f"{self.base}/api/ledger", timeout=2)
        self.assertEqual(raised.exception.code, 401)
        raised.exception.close()


class LedgerAssetTests(unittest.TestCase):
    def test_ui_contains_required_interactions(self) -> None:
        html = (ASSETS / "ledger.html").read_text(encoding="utf-8")
        script = (ASSETS / "ledger.js").read_text(encoding="utf-8")
        self.assertIn("type=\"checkbox\"", html)
        self.assertIn("draggable=\"true\"", html)
        self.assertNotIn("edit-form", html)
        self.assertNotIn("class=\"edit-input\"", html)
        self.assertNotIn("type=\"text\"", html)
        self.assertIn('document.createElement("textarea")', script)
        self.assertIn("beginEdit", script)
        self.assertIn("snackbar-action", html)
        self.assertIn("undoCompletion", script)
        self.assertIn("transferred-list", html)
        for action in ("toggle", "reorder", "edit"):
            self.assertIn(f'action: "{action}"', script)
        self.assertIn("window.setInterval", script)
        self.assertIn("tracking_state === \"transferred\"", script)

    def test_known_provenance_has_a_compact_badge_and_legacy_unknown_stays_hidden(self) -> None:
        html = (ASSETS / "ledger.html").read_text(encoding="utf-8")
        script = (ASSETS / "ledger.js").read_text(encoding="utf-8")
        style = (ASSETS / "ledger.css").read_text(encoding="utf-8")

        self.assertEqual(html.count('class="provenance-badge"'), 1)
        for value in ("user-requested", "agent-added"):
            self.assertIn(f'"{value}"', script)
        for label in ("You asked", "Agent added"):
            self.assertIn(label, script)
        self.assertNotIn("Source unknown", script)
        self.assertIn('class="provenance-badge" hidden', html)
        self.assertIn("badge.hidden = true", script)
        self.assertIn("badge.hidden = false", script)
        self.assertIn(".provenance-badge[hidden]", style)
        self.assertIn('badge.setAttribute("aria-label"', script)
        self.assertIn("attachProvenance(node, item)", script)
        self.assertIn("grid-template-columns: minmax(0, 1fr) auto", style)
        self.assertIn("white-space: nowrap", style)

    def test_every_row_carries_an_accessible_explanation_tooltip(self) -> None:
        html = (ASSETS / "ledger.html").read_text(encoding="utf-8")
        script = (ASSETS / "ledger.js").read_text(encoding="utf-8")
        style = (ASSETS / "ledger.css").read_text(encoding="utf-8")

        # One tooltip per row, in the shared template rather than per ledger.
        self.assertEqual(html.count('class="item-tooltip"'), 1)
        self.assertIn('role="tooltip"', html)
        self.assertIn("item-tooltip-label", html)
        self.assertIn("item-tooltip-text", html)

        # Safe text rendering only, wired to the item's own explanation.
        self.assertNotIn("innerHTML", script)
        self.assertNotIn("insertAdjacentHTML", script)
        self.assertIn('querySelector(".item-tooltip-label").textContent', script)
        self.assertIn('querySelector(".item-tooltip-text").textContent', script)
        self.assertIn("item.explanation", script)
        self.assertIn('setAttribute("aria-describedby", tooltip.id)', script)

        # A ledger written before the field existed still says something useful.
        for status in (
            "requested",
            "planned",
            "in-progress",
            "implemented",
            "verified",
            "waiting-on-you",
            "blocked",
            "reminder",
            "dropped",
        ):
            self.assertRegex(script, rf'(?m)^\s*"?{re.escape(status)}"?:')
        self.assertIn("TOOLTIP_FALLBACK", script)
        self.assertIn("transferred_to?.title", script)

        # Pointer hover, keyboard focus, dismissal, and flipped placement.
        self.assertIn(":hover .item-tooltip", style)
        self.assertIn("focus-visible ~ .item-tooltip", style)
        self.assertIn("tooltip-dismissed", style)
        self.assertIn('data-tooltip="below"', style)
        self.assertIn('node.addEventListener("pointerenter", place)', script)
        self.assertIn('node.addEventListener("focusin", place)', script)
        self.assertIn("tooltip-dismissed", script)
        self.assertIn('event.key !== "Escape"', script)


if __name__ == "__main__":
    unittest.main(verbosity=2)
