#!/usr/bin/env python3
"""Local Outstanding Items ledger UI and canonical JSON tooling.

The JSON ledger is the only editable source of truth. The HTML UI never embeds
or owns a second copy: it reads and mutates the JSON through this loopback-only
server. Everything uses the Python standard library.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import queue
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


SCHEMA_VERSION = 6
LEGACY_SCHEMA_VERSIONS = {3, 4, 5}
STATUSES = {
    "requested",
    "planned",
    "in-progress",
    "implemented",
    "verified",
    "waiting-on-you",
    "blocked",
    "reminder",
    "dropped",
}
DONE_STATUSES = {"verified", "dropped"}
TRACKING_STATES = {"active", "transferred"}
PROVENANCES = {"user-requested", "agent-added", "unknown-legacy"}
ORDER_INTENTS = {"automatic", "manual"}
PRIORITIES = {"P0", "P1", "P2", "P3"}
DEFAULT_PRIORITY = "P2"
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
ACTIONABLE_PRIORITY = {
    "waiting-on-you": 0,
    "in-progress": 1,
    "implemented": 2,
    "planned": 3,
    "requested": 3,
    "reminder": 5,
    "blocked": 6,
}
ID_RE = re.compile(r"^OI-\d+$")
ITEM_REFERENCE_RE = re.compile(r"^(OI-\d+)(?:-(P[0-3]))?$")
ITEM_HEADING_RE = re.compile(
    r"^###\s+(?P<id>OI-\d+)(?:-(?P<priority>P[0-3]))?\s+(?P<title>.+?)\s*$"
)
DONE_ITEM_RE = re.compile(
    r"^-\s+~~(?P<id>OI-\d+)(?:-(?P<priority>P[0-3]))?\s+"
    r"(?P<title>.+?)~~\s*(?P<state>.*?)\s*$"
)
SECTION_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
STATE_RE = re.compile(r"^-\s+\*\*State:\*\*\s*(.+?)\s*$", re.I)
MAX_BODY_BYTES = 1_000_000
# One short, plain-language paragraph shown as the item's hover/focus tooltip.
MAX_EXPLANATION_CHARS = 600
MAX_PROVENANCE_REASON_CHARS = 1_000
CODEX_THREAD_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.I,
)
TASK_STORAGE_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PROJECT_LEDGER_DIRECTORY = ".outstanding-items"
PROJECT_GITIGNORE_ENTRY = f"/{PROJECT_LEDGER_DIRECTORY}/"
TITLE_REFRESH_INTERVAL_SECONDS = 60.0
UI_ASSET_NAMES = ("ledger.html", "ledger.css", "ledger.js")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"ledger does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"ledger is not valid JSON: {exc}") from exc
    migrated = migrate_schema(data)
    if migrated:
        atomic_write_json(path, data)
    else:
        validate_ledger(data)
    return data


def automatic_order_intent(relevance_updated_at: str | None = None) -> dict[str, Any]:
    return {
        "kind": "automatic",
        "relevance_updated_at": relevance_updated_at,
    }


def split_item_reference(reference: str) -> tuple[str, str | None]:
    """Return the permanent ID and optional priority suffix from a display reference."""
    if not isinstance(reference, str):
        raise ValueError("item reference must be a string")
    match = ITEM_REFERENCE_RE.fullmatch(reference)
    if not match:
        raise ValueError("item reference must look like OI-35 or OI-35-P1")
    return match.group(1), match.group(2)


def display_id(item: dict[str, Any]) -> str:
    """Build the user-facing reference without changing the permanent ledger key."""
    return f"{item['id']}-{item['priority']}"


def item_for_reference(items: list[dict[str, Any]], reference: str) -> dict[str, Any]:
    """Resolve a stable or display reference and reject a stale priority suffix."""
    item_id, supplied_priority = split_item_reference(reference)
    item = next((entry for entry in items if entry["id"] == item_id), None)
    if item is None:
        raise ValueError(f"unknown item id: {reference!r}")
    if supplied_priority is not None and supplied_priority != item["priority"]:
        raise ValueError(
            f"{reference} has stale priority; current reference is {display_id(item)}"
        )
    return item


def migrate_schema(data: Any) -> bool:
    """Upgrade supported prior schemas without inventing provenance or manual intent."""
    if not isinstance(data, dict):
        raise ValueError("ledger root must be an object")
    version = data.get("schema_version")
    if version == SCHEMA_VERSION:
        validate_ledger(data)
        return False
    if version not in LEGACY_SCHEMA_VERSIONS:
        raise ValueError(
            f"schema_version must be {SCHEMA_VERSION} or a supported legacy version "
            f"in {sorted(LEGACY_SCHEMA_VERSIONS)}"
        )
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("items must be an array")
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("every legacy item must be an object")
        legacy_explanation = item.get("explanation")
        if isinstance(legacy_explanation, str) and len(legacy_explanation) > MAX_EXPLANATION_CHARS:
            # Older ledgers could contain a longer tooltip paragraph. Keep the
            # complete original in the item's durable notes while making the
            # compact UI explanation satisfy the current bounded schema.
            details = item.get("details_markdown", "")
            if not isinstance(details, str):
                raise ValueError(f"{item.get('id', 'legacy item')} details_markdown must be a string")
            if legacy_explanation not in details:
                preserved = f"## Full legacy explanation\n\n{legacy_explanation}"
                item["details_markdown"] = f"{details.rstrip()}\n\n{preserved}".lstrip()
            shortened = legacy_explanation[: MAX_EXPLANATION_CHARS - 1].rstrip()
            item["explanation"] = f"{shortened}…"
        if version == 3:
            item["provenance"] = "unknown-legacy"
        if version in {3, 4}:
            item["order_intent"] = automatic_order_intent()
        item["priority"] = DEFAULT_PRIORITY
    revision = data.get("revision")
    if not isinstance(revision, int) or revision < 0:
        raise ValueError("revision must be a non-negative integer")
    data["schema_version"] = SCHEMA_VERSION
    data["revision"] = revision + 1
    data["updated_at"] = utc_now()
    validate_ledger(data)
    return True


def atomic_write_json(path: pathlib.Path, data: dict[str, Any]) -> None:
    validate_ledger(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_mode = None
    if path.exists():
        previous_mode = path.stat().st_mode & 0o777
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary = pathlib.Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    if previous_mode is not None:
        temporary.chmod(previous_mode)
    else:
        temporary.chmod(0o600)
    os.replace(temporary, path)


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    """Atomically replace a small text file while preserving its existing mode."""
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary = pathlib.Path(handle.name)
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.chmod(previous_mode)
    os.replace(temporary, path)


def git_project_root(start: pathlib.Path) -> pathlib.Path:
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise ValueError(f"project storage needs a Git project: {start}")
    root = pathlib.Path(result.stdout.strip()).resolve()
    if not root.is_dir():
        raise ValueError(f"Git reported a missing project root: {root}")
    return root


def ensure_project_gitignore(project_root: pathlib.Path) -> pathlib.Path:
    gitignore = project_root / ".gitignore"
    if gitignore.is_symlink():
        raise ValueError(f"refusing to edit a symlinked .gitignore: {gitignore}")
    current = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    lines = current.splitlines()
    if PROJECT_GITIGNORE_ENTRY in lines:
        return gitignore
    updated = current
    if updated and not updated.endswith("\n"):
        updated += "\n"
    updated += PROJECT_GITIGNORE_ENTRY + "\n"
    atomic_write_text(gitignore, updated)
    return gitignore


def empty_ledger(title: str, task_id: str, project_root: pathlib.Path) -> dict[str, Any]:
    now = utc_now()
    ledger = {
        "schema_version": SCHEMA_VERSION,
        "owner": "user",
        "authorizes_work": False,
        "title": title,
        "task_id": task_id,
        "revision": 0,
        "created_at": now,
        "updated_at": now,
        "latest_unanswered_suggestion": None,
        "items": [],
        "sections": [],
        "source": {
            "kind": "project-task-json",
            "status": "canonical",
            "project_storage_enabled": True,
            "project_root": str(project_root),
        },
    }
    validate_ledger(ledger)
    return ledger


def validate_ledger(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("ledger root must be an object")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    if data.get("owner") != "user" or data.get("authorizes_work") is not False:
        raise ValueError("ledger must declare owner=user and authorizes_work=false")
    if not isinstance(data.get("title"), str) or not data["title"].strip():
        raise ValueError("ledger title must be a non-empty string")
    if not isinstance(data.get("revision"), int) or data["revision"] < 0:
        raise ValueError("revision must be a non-negative integer")
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("items must be an array")
    seen: set[str] = set()
    positions: dict[bool, set[int]] = {False: set(), True: set()}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"item {index} must be an object")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not ID_RE.fullmatch(item_id):
            raise ValueError(f"item {index} has invalid id {item_id!r}")
        if item_id in seen:
            raise ValueError(f"duplicate item id: {item_id}")
        seen.add(item_id)
        title = item.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"{item_id} title must be non-empty")
        status = item.get("status")
        if status not in STATUSES:
            raise ValueError(f"{item_id} has unsupported status {status!r}")
        priority = item.get("priority")
        if priority not in PRIORITIES:
            raise ValueError(f"{item_id} has unsupported priority {priority!r}")
        completed = item.get("completed")
        if not isinstance(completed, bool):
            raise ValueError(f"{item_id} completed must be boolean")
        if completed != (status in DONE_STATUSES):
            raise ValueError(f"{item_id} completed and status disagree")
        provenance = item.get("provenance")
        if provenance not in PROVENANCES:
            raise ValueError(f"{item_id} has unsupported provenance {provenance!r}")
        order_intent = item.get("order_intent")
        if not isinstance(order_intent, dict):
            raise ValueError(f"{item_id} order_intent must be an object")
        order_kind = order_intent.get("kind")
        if order_kind not in ORDER_INTENTS:
            raise ValueError(f"{item_id} has unsupported order_intent kind {order_kind!r}")
        relevance_updated_at = order_intent.get("relevance_updated_at")
        if relevance_updated_at is not None and (
            not isinstance(relevance_updated_at, str) or not relevance_updated_at.strip()
        ):
            raise ValueError(
                f"{item_id} order_intent relevance_updated_at must be null or a non-empty string"
            )
        if order_kind == "manual":
            for key in ("manually_positioned_at", "manual_order_updated_at"):
                if not isinstance(order_intent.get(key), str) or not order_intent[key].strip():
                    raise ValueError(f"{item_id} manual order_intent needs non-empty {key}")
            manual_revision = order_intent.get("manual_order_revision")
            if not isinstance(manual_revision, int) or manual_revision < 0:
                raise ValueError(
                    f"{item_id} manual order_intent needs non-negative manual_order_revision"
                )
            for key in ("placed_after_id", "placed_before_id"):
                anchor = order_intent.get(key)
                if anchor is not None and (
                    not isinstance(anchor, str) or not ID_RE.fullmatch(anchor) or anchor == item_id
                ):
                    raise ValueError(
                        f"{item_id} manual order_intent {key} must be null or another item ID"
                    )
        history = item.get("provenance_history", [])
        if not isinstance(history, list):
            raise ValueError(f"{item_id} provenance_history must be an array")
        history_value: str | None = None
        for correction_index, correction in enumerate(history):
            if not isinstance(correction, dict):
                raise ValueError(
                    f"{item_id} provenance_history[{correction_index}] must be an object"
                )
            if correction.get("from") not in PROVENANCES or correction.get("to") not in PROVENANCES:
                raise ValueError(
                    f"{item_id} provenance_history[{correction_index}] has unsupported provenance"
                )
            if correction["from"] == correction["to"]:
                raise ValueError(
                    f"{item_id} provenance_history[{correction_index}] does not change provenance"
                )
            if history_value is not None and correction["from"] != history_value:
                raise ValueError(f"{item_id} provenance_history is not a continuous audit chain")
            history_value = correction["to"]
            for key in ("corrected_at", "reason"):
                if not isinstance(correction.get(key), str) or not correction[key].strip():
                    raise ValueError(
                        f"{item_id} provenance_history[{correction_index}] needs non-empty {key}"
                    )
            if len(correction["reason"]) > MAX_PROVENANCE_REASON_CHARS:
                raise ValueError(
                    f"{item_id} provenance_history[{correction_index}] reason is too long"
                )
            if "session_id" in correction and (
                not isinstance(correction["session_id"], str)
                or not correction["session_id"].strip()
            ):
                raise ValueError(
                    f"{item_id} provenance_history[{correction_index}] session_id must be non-empty"
                )
        if history_value is not None and history_value != provenance:
            raise ValueError(f"{item_id} provenance_history does not end at current provenance")
        tracking_state = item.get("tracking_state", "active")
        if tracking_state not in TRACKING_STATES:
            raise ValueError(f"{item_id} has unsupported tracking_state {tracking_state!r}")
        if tracking_state == "transferred":
            transferred_to = item.get("transferred_to")
            if not isinstance(transferred_to, dict):
                raise ValueError(f"{item_id} transferred_to must be an object")
            for key in ("task_id", "title", "transferred_at"):
                if not isinstance(transferred_to.get(key), str) or not transferred_to[key].strip():
                    raise ValueError(f"{item_id} transferred_to needs non-empty {key}")
            for key in ("title_source", "title_updated_at"):
                if key in transferred_to and (
                    not isinstance(transferred_to[key], str) or not transferred_to[key].strip()
                ):
                    raise ValueError(f"{item_id} transferred_to {key} must be a non-empty string")
        position = item.get("position")
        if not isinstance(position, int) or position < 0:
            raise ValueError(f"{item_id} position must be a non-negative integer")
        if position in positions[completed]:
            raise ValueError(f"duplicate {'done' if completed else 'open'} position {position}")
        positions[completed].add(position)
        for key in ("details_markdown", "group", "state_text", "explanation"):
            if key in item and not isinstance(item[key], str):
                raise ValueError(f"{item_id} {key} must be a string")
        # `explanation` is optional: a ledger written before this field existed
        # stays valid, and the UI falls back to a status sentence for it.
        if len(item.get("explanation", "")) > MAX_EXPLANATION_CHARS:
            raise ValueError(
                f"{item_id} explanation must be at most {MAX_EXPLANATION_CHARS} characters"
            )
    for completed, found in positions.items():
        expected = set(range(len(found)))
        if found != expected:
            label = "done" if completed else "open"
            raise ValueError(f"{label} positions must be contiguous from zero")
    sections = data.get("sections", [])
    if not isinstance(sections, list):
        raise ValueError("sections must be an array")
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ValueError(f"section {index} must be an object")
        if not isinstance(section.get("title"), str) or not isinstance(section.get("markdown"), str):
            raise ValueError(f"section {index} needs string title and markdown")
    suggestion = data.get("latest_unanswered_suggestion")
    if suggestion is not None:
        if not isinstance(suggestion, dict):
            raise ValueError("latest_unanswered_suggestion must be an object or null")
        if not isinstance(suggestion.get("id"), str) or not isinstance(suggestion.get("text"), str):
            raise ValueError("latest_unanswered_suggestion needs string id and text")
        if not ID_RE.fullmatch(suggestion["id"]) or suggestion["id"] not in seen:
            raise ValueError(
                "latest_unanswered_suggestion id must be one permanent OI-n item key"
            )


def normalized_status(state_text: str) -> str:
    lowered = state_text.lower()
    if "dropped" in lowered or "cancelled" in lowered:
        return "dropped"
    if "verified complete" in lowered or lowered.startswith("verified"):
        return "verified"
    if "waiting on ethan" in lowered or "waiting-on-you" in lowered:
        return "waiting-on-you"
    if "reminder" in lowered:
        return "reminder"
    if "blocked" in lowered:
        return "blocked"
    if "implemented" in lowered or "implementation exists" in lowered or "app installed" in lowered:
        return "implemented"
    if "planned" in lowered or "architecture designed" in lowered:
        return "planned"
    if "in-progress" in lowered or "in progress" in lowered:
        return "in-progress"
    return "requested"


def migrate_markdown(source: pathlib.Path, title: str, task_id: str | None) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    items: list[dict[str, Any]] = []
    sections: list[dict[str, str]] = []
    current_group = "Preamble"
    section_lines: list[str] = []
    current_item: dict[str, Any] | None = None
    item_lines: list[str] = []

    def flush_section() -> None:
        nonlocal section_lines
        markdown = "\n".join(section_lines).strip()
        if markdown:
            sections.append({"title": current_group, "markdown": markdown})
        section_lines = []

    def flush_item() -> None:
        nonlocal current_item, item_lines
        if current_item is None:
            return
        from_done_bullet = bool(current_item.pop("_from_done_bullet", None))
        details = "\n".join(item_lines).strip()
        state_text = ""
        for line in item_lines:
            match = STATE_RE.match(line)
            if match:
                state_text = match.group(1).strip()
                break
        if from_done_bullet and not state_text:
            state_text = "dropped" if "dropped" in details.lower() else "verified"
        status = normalized_status(state_text)
        current_item.update(
            {
                "status": status,
                "completed": status in DONE_STATUSES,
                "position": 0,
                "group": current_group,
                "state_text": state_text,
                "details_markdown": details,
                "explanation": "",
                "provenance": "unknown-legacy",
                "order_intent": automatic_order_intent(),
                "completed_at": None,
                "completed_session_id": None,
            }
        )
        items.append(current_item)
        current_item = None
        item_lines = []

    for line in text.splitlines():
        done_match = DONE_ITEM_RE.match(line)
        if done_match:
            flush_item()
            title_text = done_match.group("title").strip()
            if title_text.endswith("."):
                title_text = title_text[:-1]
            state = done_match.group("state").strip()
            current_item = {
                "id": done_match.group("id"),
                "priority": done_match.group("priority") or DEFAULT_PRIORITY,
                "title": title_text,
                "_from_done_bullet": True,
            }
            item_lines = [f"- **State:** {state}"] if state else []
            continue
        item_match = ITEM_HEADING_RE.match(line)
        if item_match:
            flush_item()
            current_item = {
                "id": item_match.group("id"),
                "priority": item_match.group("priority") or DEFAULT_PRIORITY,
                "title": item_match.group("title").strip(),
            }
            item_lines = []
            continue
        section_match = SECTION_HEADING_RE.match(line)
        if section_match:
            flush_item()
            flush_section()
            current_group = section_match.group(1).strip()
            continue
        if current_item is not None and current_item.get("_from_done_bullet") and line.startswith("- "):
            flush_item()
            section_lines.append(line)
            continue
        if current_item is not None:
            item_lines.append(line)
        else:
            section_lines.append(line)
    flush_item()
    flush_section()

    open_position = 0
    done_position = 0
    for item in items:
        if item["completed"]:
            item["position"] = done_position
            done_position += 1
        else:
            item["position"] = open_position
            open_position += 1

    now = utc_now()
    ledger: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "owner": "user",
        "authorizes_work": False,
        "title": title,
        "task_id": task_id or "unavailable",
        "revision": 1,
        "created_at": now,
        "updated_at": now,
        "latest_unanswered_suggestion": None,
        "items": items,
        "sections": sections,
        "source": {
            "kind": "markdown-migration",
            "path": str(source.resolve()),
            "sha256": digest,
            "migrated_at": now,
            "status": "archived-read-only",
        },
    }
    validate_ledger(ledger)
    return ledger


def normalize_positions(data: dict[str, Any]) -> None:
    for completed in (False, True):
        subset = sorted(
            (item for item in data["items"] if item["completed"] is completed),
            key=lambda item: (
                item.get("tracking_state") == "transferred",
                item["position"],
                int(item["id"].split("-")[1]),
            ),
        )
        for position, item in enumerate(subset):
            item["position"] = position


def touch_relevance(item: dict[str, Any], when: str) -> None:
    item["order_intent"]["relevance_updated_at"] = when


def automatic_order_key(item: dict[str, Any]) -> tuple[int, int, int, int]:
    """Sort status first, then priority, relevance recency, and stable ID."""
    relevance = item["order_intent"].get("relevance_updated_at") or ""
    try:
        recency = int(dt.datetime.fromisoformat(relevance.replace("Z", "+00:00")).timestamp())
    except (TypeError, ValueError):
        recency = -1
    return (
        ACTIONABLE_PRIORITY[item["status"]],
        PRIORITY_RANK[item["priority"]],
        -recency,
        -int(item["id"].split("-")[1]),
    )


def reconcile_order(data: dict[str, Any]) -> bool:
    """Reorder only automatic active items; keep manual items in their current slots."""
    active = sorted(
        (
            item
            for item in data["items"]
            if not item["completed"] and item.get("tracking_state", "active") == "active"
        ),
        key=lambda item: item["position"],
    )
    if len(active) < 2:
        return False
    manual_slots = {
        index: item
        for index, item in enumerate(active)
        if item["order_intent"]["kind"] == "manual"
    }
    automatic = sorted(
        (item for item in active if item["order_intent"]["kind"] == "automatic"),
        key=automatic_order_key,
    )
    automatic_iter = iter(automatic)
    reconciled = [manual_slots.get(index) or next(automatic_iter) for index in range(len(active))]
    before = [item["id"] for item in active]
    after = [item["id"] for item in reconciled]
    if before == after:
        return False
    for position, item in enumerate(reconciled):
        item["position"] = position
    normalize_positions(data)
    return True


def record_manual_order(data: dict[str, Any], moved_id: str, when: str) -> None:
    """Record the explicit user-authored placement and refresh existing manual anchors."""
    ordered = sorted(
        (
            item
            for item in data["items"]
            if not item["completed"] and item.get("tracking_state", "active") == "active"
        ),
        key=lambda item: item["position"],
    )
    by_id = {item["id"]: item for item in ordered}
    if moved_id not in by_id:
        raise ValueError("moved_id must name one active outstanding item")
    revision = data["revision"] + 1
    for index, item in enumerate(ordered):
        prior = item["order_intent"]
        if item["id"] != moved_id and prior["kind"] != "manual":
            continue
        item["order_intent"] = {
            "kind": "manual",
            "relevance_updated_at": prior.get("relevance_updated_at"),
            "manually_positioned_at": (
                when if item["id"] == moved_id else prior["manually_positioned_at"]
            ),
            "manual_order_updated_at": when,
            "manual_order_revision": revision,
            "placed_after_id": ordered[index - 1]["id"] if index else None,
            "placed_before_id": ordered[index + 1]["id"] if index + 1 < len(ordered) else None,
        }


def clear_suggestion_for(data: dict[str, Any], item_id: str) -> None:
    suggestion = data.get("latest_unanswered_suggestion")
    if isinstance(suggestion, dict) and suggestion.get("id") == item_id:
        data["latest_unanswered_suggestion"] = None


def mutate(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    base_revision = payload.get("base_revision")
    if base_revision != data["revision"]:
        raise ConflictError("The ledger changed elsewhere. Reloaded the newest version; retry your edit.")
    action = payload.get("action")
    item_reference = payload.get("id")
    item = None
    if action in {"edit", "toggle", "priority"}:
        item = item_for_reference(data["items"], item_reference)
    item_id = item["id"] if item is not None else item_reference
    if action in {"edit", "toggle", "priority"} and item.get("tracking_state") == "transferred":
        raise ValueError(f"{item_id} is transferred history and is read-only here")
    if action == "edit":
        title = payload.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be non-empty")
        if len(title.strip()) > 500:
            raise ValueError("title must be at most 500 characters")
        item["title"] = title.strip()
        touch_relevance(item, utc_now())
        clear_suggestion_for(data, item_id)
        reconcile_order(data)
    elif action == "toggle":
        completed = payload.get("completed")
        if not isinstance(completed, bool):
            raise ValueError("completed must be boolean")
        if completed and not item["completed"]:
            item["status_before_completion"] = item["status"]
            item["status"] = "verified"
            item["completed"] = True
            item["completed_at"] = utc_now()
            session_id = payload.get("session_id")
            item["completed_session_id"] = session_id if isinstance(session_id, str) and session_id else "unavailable"
        elif not completed and item["completed"]:
            previous = item.pop("status_before_completion", "requested")
            item["status"] = previous if previous in STATUSES - DONE_STATUSES else "requested"
            item["completed"] = False
            item["completed_at"] = None
            item["completed_session_id"] = None
            touch_relevance(item, utc_now())
        clear_suggestion_for(data, item_id)
        normalize_positions(data)
        reconcile_order(data)
    elif action == "priority":
        priority = payload.get("priority")
        if priority not in PRIORITIES:
            raise ValueError("priority must be P0, P1, P2, or P3")
        item["priority"] = priority
        touch_relevance(item, utc_now())
        clear_suggestion_for(data, item_id)
        reconcile_order(data)
    elif action == "reorder":
        order = payload.get("order")
        if not isinstance(order, list) or not all(isinstance(value, str) for value in order):
            raise ValueError("order must be an array of item ids")
        open_ids = {
            entry["id"]
            for entry in data["items"]
            if not entry["completed"] and entry.get("tracking_state", "active") == "active"
        }
        if len(order) != len(set(order)) or set(order) != open_ids:
            raise ValueError("order must contain every open item exactly once")
        moved_id = payload.get("moved_id")
        if not isinstance(moved_id, str) or moved_id not in open_ids:
            raise ValueError("reorder needs moved_id; reload the ledger and try the move again")
        by_id = {entry["id"]: entry for entry in data["items"]}
        for position, ordered_id in enumerate(order):
            by_id[ordered_id]["position"] = position
        record_manual_order(data, moved_id, utc_now())
    else:
        raise ValueError(f"unsupported action: {action!r}")
    data["revision"] += 1
    data["updated_at"] = utc_now()
    validate_ledger(data)
    return data


def client_ledger(data: dict[str, Any], ledger_path: pathlib.Path) -> dict[str, Any]:
    """Add non-persistent runtime context without creating a second ledger."""
    payload = dict(data)
    payload["_runtime"] = {"ledger_path": str(ledger_path)}
    return payload


def read_codex_thread_titles(
    task_ids: set[str],
    *,
    codex_binary: str | None = None,
    timeout: float = 6.0,
) -> dict[str, str]:
    """Resolve exact saved Codex task IDs through the local app-server protocol.

    This is deliberately read-only and fail-soft. It never messages, wakes, or
    mutates a task, and it disables remote plugin sync for the short-lived local
    protocol process. Non-Codex IDs are ignored so Claude-compatible ledgers
    remain valid without requiring Codex.
    """
    wanted = {task_id for task_id in task_ids if CODEX_THREAD_ID_RE.fullmatch(task_id)}
    if not wanted:
        return {}
    executable = codex_binary or os.environ.get("OUTSTANDING_ITEMS_CODEX_BIN") or shutil.which("codex")
    if not executable:
        return {}
    process: subprocess.Popen[str] | None = None
    deadline = time.monotonic() + timeout
    request_id = 1
    responses: queue.Queue[dict[str, Any]] = queue.Queue()

    def send(payload: dict[str, Any]) -> None:
        assert process and process.stdin
        process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        process.stdin.flush()

    def response_for(expected_id: int) -> dict[str, Any] | None:
        while time.monotonic() < deadline:
            try:
                payload = responses.get(timeout=max(0.0, deadline - time.monotonic()))
            except queue.Empty:
                return None
            if payload.get("id") == expected_id:
                return payload
        return None

    try:
        process = subprocess.Popen(
            [executable, "app-server", "--disable", "remote_plugin", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )

        def read_responses() -> None:
            assert process and process.stdout
            for line in process.stdout:
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    responses.put(payload)

        threading.Thread(target=read_responses, daemon=True).start()
        send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "initialize",
                "params": {
                    "clientInfo": {
                        "name": "outstanding-items",
                        "title": "Outstanding Items",
                        "version": "1.0.0",
                    }
                },
            }
        )
        initialized = response_for(request_id)
        if not initialized or initialized.get("error"):
            return {}
        send({"jsonrpc": "2.0", "method": "initialized", "params": {}})

        found: dict[str, str] = {}
        for archived in (False, True):
            cursor: str | None = None
            for _page in range(50):
                request_id += 1
                params: dict[str, Any] = {
                    "archived": archived,
                    "limit": 100,
                    "sortKey": "updated_at",
                    "sortDirection": "desc",
                    "useStateDbOnly": True,
                }
                if cursor:
                    params["cursor"] = cursor
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "method": "thread/list",
                        "params": params,
                    }
                )
                response = response_for(request_id)
                if not response or response.get("error"):
                    break
                result = response.get("result")
                if not isinstance(result, dict):
                    break
                for thread in result.get("data", []):
                    if not isinstance(thread, dict):
                        continue
                    task_id = thread.get("id") or thread.get("sessionId")
                    title = thread.get("name")
                    if task_id in wanted and isinstance(title, str) and title.strip():
                        found[task_id] = title.strip()
                if wanted <= found.keys():
                    return found
                cursor = result.get("nextCursor")
                if not isinstance(cursor, str) or not cursor:
                    break
        return found
    except (OSError, ValueError, BrokenPipeError, subprocess.SubprocessError):
        return {}
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1.0)
        if process and process.stdin:
            process.stdin.close()
        if process and process.stdout:
            process.stdout.close()


def refresh_transferred_titles(
    data: dict[str, Any],
    *,
    resolver: Any = read_codex_thread_titles,
) -> bool:
    """Refresh cached destination names by stable task ID; return whether data changed."""
    transferred = [
        item["transferred_to"]
        for item in data["items"]
        if item.get("tracking_state") == "transferred"
    ]
    task_ids = {destination["task_id"] for destination in transferred}
    titles = resolver(task_ids)
    if not titles:
        return False
    changed = False
    refreshed_at = utc_now()
    for destination in transferred:
        title = titles.get(destination["task_id"])
        if not title:
            continue
        if (
            destination.get("title") != title
            or destination.get("title_source") != "codex-app-server"
        ):
            destination["title"] = title
            destination["title_source"] = "codex-app-server"
            destination["title_updated_at"] = refreshed_at
            changed = True
    return changed


class ConflictError(ValueError):
    pass


class LedgerHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        handler: type[BaseHTTPRequestHandler],
        ledger_path: pathlib.Path,
        assets: dict[str, bytes],
        token: str,
        instance_id: str,
    ) -> None:
        super().__init__(address, handler)
        self.ledger_path = ledger_path
        self.assets = assets
        self.ui_assets_sha256 = ui_assets_sha256(assets)
        self.runtime_sha256 = current_runtime_sha256()
        self.token = token
        self.instance_id = instance_id
        self.write_lock = threading.Lock()
        self.title_refresh_lock = threading.Lock()
        self.last_title_refresh = 0.0

    def title_refresh_due(self) -> bool:
        return time.monotonic() - self.last_title_refresh >= TITLE_REFRESH_INTERVAL_SECONDS

    def mark_titles_refreshed(self) -> None:
        self.last_title_refresh = time.monotonic()

    def refresh_titles(self, *, force: bool = False) -> None:
        if not force and not self.title_refresh_due():
            return
        if not self.title_refresh_lock.acquire(blocking=False):
            return
        try:
            with self.write_lock:
                snapshot = read_json(self.ledger_path)
                task_ids = {
                    item["transferred_to"]["task_id"]
                    for item in snapshot["items"]
                    if item.get("tracking_state") == "transferred"
                }
            titles = read_codex_thread_titles(task_ids)
            if titles:
                with self.write_lock:
                    current = read_json(self.ledger_path)
                    if refresh_transferred_titles(current, resolver=lambda _ids: titles):
                        current["revision"] += 1
                        current["updated_at"] = utc_now()
                        atomic_write_json(self.ledger_path, current)
            self.mark_titles_refreshed()
        except (OSError, ValueError):
            # Title refresh is optional display maintenance. Ledger reads and
            # user mutations remain available even when Codex metadata is not.
            self.mark_titles_refreshed()
        finally:
            self.title_refresh_lock.release()

    def schedule_title_refresh(self) -> None:
        threading.Thread(
            target=self.refresh_titles,
            kwargs={"force": True},
            daemon=True,
        ).start()


class LedgerHandler(BaseHTTPRequestHandler):
    server: LedgerHTTPServer

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write(f"[{self.log_date_time_string()}] {fmt % args}\n")

    def allowed_host(self) -> bool:
        host = self.headers.get("Host", "")
        hostname = host.rsplit(":", 1)[0].strip("[]").lower()
        return hostname in {"127.0.0.1", "localhost", "::1"}

    def token_ok(self, query: dict[str, list[str]]) -> bool:
        supplied = self.headers.get("X-Ledger-Token") or (query.get("token") or [""])[0]
        return secrets.compare_digest(supplied, self.server.token)

    def common_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")

    def send_json(self, status: int, data: Any) -> None:
        body = (json.dumps(data, ensure_ascii=False) + "\n").encode("utf-8")
        self.send_response(status)
        self.common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_asset(self, name: str, content_type: str) -> None:
        body = self.server.assets.get(name)
        if body is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.OK)
        self.common_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if not self.allowed_host():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        parsed = urllib.parse.urlsplit(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/":
            self.send_asset("ledger.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/assets/ledger.css":
            self.send_asset("ledger.css", "text/css; charset=utf-8")
            return
        if parsed.path == "/assets/ledger.js":
            self.send_asset("ledger.js", "text/javascript; charset=utf-8")
            return
        if parsed.path == "/api/health":
            if not self.token_ok(query):
                self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "invalid token"})
                return
            self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "instance_id": self.server.instance_id,
                    "ledger": str(self.server.ledger_path),
                    "ui_assets_sha256": self.server.ui_assets_sha256,
                    "runtime_sha256": self.server.runtime_sha256,
                },
            )
            return
        if parsed.path == "/api/ledger":
            if not self.token_ok(query):
                self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "invalid token"})
                return
            try:
                self.server.refresh_titles()
                with self.server.write_lock:
                    data = read_json(self.server.ledger_path)
                    if reconcile_order(data):
                        data["revision"] += 1
                        data["updated_at"] = utc_now()
                        atomic_write_json(self.server.ledger_path, data)
            except ValueError as exc:
                self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                return
            self.send_json(HTTPStatus.OK, client_ledger(data, self.server.ledger_path))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if not self.allowed_host():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        parsed = urllib.parse.urlsplit(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        if parsed.path != "/api/mutate":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self.token_ok(query):
            self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "invalid token"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid Content-Length"})
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "request body size is invalid"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("request body must be an object")
            with self.server.write_lock:
                data = read_json(self.server.ledger_path)
                mutated = mutate(data, payload)
                atomic_write_json(self.server.ledger_path, mutated)
        except ConflictError as exc:
            newest = read_json(self.server.ledger_path)
            self.send_json(
                HTTPStatus.CONFLICT,
                {"error": str(exc), "ledger": client_ledger(newest, self.server.ledger_path)},
            )
            return
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        self.send_json(HTTPStatus.OK, client_ledger(mutated, self.server.ledger_path))
        self.server.schedule_title_refresh()


def state_path_for(ledger: pathlib.Path) -> pathlib.Path:
    return ledger.with_name(f".{ledger.stem}.ledger-ui-state.json")


def connection_path_for(ledger: pathlib.Path) -> pathlib.Path:
    return ledger.with_name(f".{ledger.stem}.ledger-ui-connection.json")


def log_path_for(ledger: pathlib.Path) -> pathlib.Path:
    return ledger.with_name(f".{ledger.stem}.ledger-ui.log")


def health(url: str, token: str, timeout: float = 0.5) -> dict[str, Any] | None:
    parsed = urllib.parse.urlsplit(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    request = urllib.request.Request(f"{base}/api/health?token={urllib.parse.quote(token)}")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return None


def ui_health(
    url: str,
    token: str,
    timeout: float = 0.5,
    expected_ui_assets_sha256: str | None = None,
    expected_runtime_sha256: str | None = None,
) -> dict[str, Any] | None:
    """Return identity only when the complete browser UI and runtime match."""
    probe = health(url, token, timeout=timeout)
    if not probe:
        return None
    if (
        expected_ui_assets_sha256 is not None
        and probe.get("ui_assets_sha256") != expected_ui_assets_sha256
    ):
        return None
    if (
        expected_runtime_sha256 is not None
        and probe.get("runtime_sha256") != expected_runtime_sha256
    ):
        return None
    parsed = urllib.parse.urlsplit(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    quoted_token = urllib.parse.quote(token)
    paths = ("/", "/assets/ledger.css", "/assets/ledger.js")
    try:
        for path in paths:
            request = urllib.request.Request(f"{base}{path}?token={quoted_token}")
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status != HTTPStatus.OK or not response.read():
                    return None
    except urllib.error.HTTPError as exc:
        exc.close()
        return None
    except (OSError, urllib.error.URLError):
        return None
    return probe


def load_ui_assets(assets_path: pathlib.Path) -> dict[str, bytes]:
    """Snapshot the generic UI before the long-running process begins serving."""
    loaded: dict[str, bytes] = {}
    for name in UI_ASSET_NAMES:
        path = assets_path / name
        if not path.is_file():
            raise ValueError(f"ledger UI asset is missing: {path}")
        body = path.read_bytes()
        if not body:
            raise ValueError(f"ledger UI asset is empty: {path}")
        loaded[name] = body
    return loaded


def ui_assets_sha256(assets: dict[str, bytes]) -> str:
    """Return one stable fingerprint for the complete generic browser shell."""
    digest = hashlib.sha256()
    for name in UI_ASSET_NAMES:
        body = assets[name]
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(len(body).to_bytes(8, "big"))
        digest.update(body)
    return digest.hexdigest()


def current_ui_assets_sha256() -> str:
    assets_path = pathlib.Path(__file__).resolve().parent.parent / "assets"
    return ui_assets_sha256(load_ui_assets(assets_path))


def current_runtime_sha256() -> str:
    """Fingerprint the installed local server implementation used by this process."""
    return hashlib.sha256(pathlib.Path(__file__).resolve().read_bytes()).hexdigest()


def load_state(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return state if isinstance(state, dict) else None


def write_private_state(path: pathlib.Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary = pathlib.Path(handle.name)
        json.dump(state, handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.chmod(0o600)
    os.replace(temporary, path)


def reusable_connection(path: pathlib.Path, ledger: pathlib.Path) -> dict[str, Any] | None:
    state = load_state(path)
    if not state or state.get("ledger") != str(ledger):
        return None
    port = state.get("port")
    token = state.get("token")
    if not isinstance(port, int) or not 1 <= port <= 65535:
        return None
    if not isinstance(token, str) or len(token) < 16:
        return None
    return {
        "port": port,
        "token": token,
        "url": f"http://127.0.0.1:{port}/?token={urllib.parse.quote(token)}",
        "ledger": str(ledger),
    }


def command_serve(args: argparse.Namespace) -> int:
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    reconcile_ledger_file(ledger)
    token = args.token or secrets.token_urlsafe(24)
    instance_id = args.instance_id or secrets.token_hex(12)
    assets_path = pathlib.Path(__file__).resolve().parent.parent / "assets"
    assets = load_ui_assets(assets_path)
    server = LedgerHTTPServer(("127.0.0.1", args.port), LedgerHandler, ledger, assets, token, instance_id)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/?token={urllib.parse.quote(token)}"
    state_path = pathlib.Path(args.state_file).resolve() if args.state_file else state_path_for(ledger)
    connection_path = (
        pathlib.Path(args.connection_file).resolve()
        if args.connection_file
        else connection_path_for(ledger)
    )
    state = {
        "pid": os.getpid(),
        "port": port,
        "url": url,
        "token": token,
        "instance_id": instance_id,
        "ledger": str(ledger),
        "started_at": utc_now(),
    }
    atomic_state = dict(state)
    write_private_state(state_path, atomic_state)
    write_private_state(
        connection_path,
        {"port": port, "url": url, "token": token, "ledger": str(ledger)},
    )
    print(f"LEDGER_URL={url}", flush=True)

    def request_shutdown(_signum: int, _frame: Any) -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
        current = load_state(state_path)
        if current and current.get("instance_id") == instance_id:
            state_path.unlink(missing_ok=True)
    return 0


def command_start(args: argparse.Namespace) -> int:
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    reconcile_ledger_file(ledger)
    expected_ui_assets_sha256 = current_ui_assets_sha256()
    expected_runtime_sha256 = current_runtime_sha256()
    state_path = state_path_for(ledger)
    existing = load_state(state_path)
    if existing:
        probe = ui_health(
            existing.get("url", ""),
            existing.get("token", ""),
            expected_ui_assets_sha256=expected_ui_assets_sha256,
            expected_runtime_sha256=expected_runtime_sha256,
        )
        if probe and probe.get("instance_id") == existing.get("instance_id") and probe.get("ledger") == str(ledger):
            print(f"LEDGER_URL={existing['url']}")
            print(f"LEDGER_PID={existing['pid']}")
            return 0
        api_probe = health(existing.get("url", ""), existing.get("token", ""))
        if (
            api_probe
            and api_probe.get("instance_id") == existing.get("instance_id")
            and api_probe.get("ledger") == str(ledger)
        ):
            # Stop only the exact matching runtime when its browser shell is
            # missing or older than the currently installed plugin. Preserve
            # its port and token so existing links reconnect after replacement.
            command_stop(argparse.Namespace(ledger=str(ledger)))
    connection_path = connection_path_for(ledger)
    connection = reusable_connection(connection_path, ledger)
    preferred_port = args.port or (connection["port"] if connection else 0)
    token = args.token or (connection["token"] if connection else secrets.token_urlsafe(24))
    instance_id = secrets.token_hex(12)
    log_path = log_path_for(ledger)
    command = [
        sys.executable,
        str(pathlib.Path(__file__).resolve()),
        "serve",
        "--ledger",
        str(ledger),
        "--port",
        str(preferred_port),
        "--token",
        token,
        "--instance-id",
        instance_id,
        "--state-file",
        str(state_path),
        "--connection-file",
        str(connection_path),
    ]
    with log_path.open("ab") as log:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
            close_fds=True,
        )
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        state = load_state(state_path)
        if state and state.get("instance_id") == instance_id:
            probe = ui_health(
                state.get("url", ""),
                token,
                expected_ui_assets_sha256=expected_ui_assets_sha256,
                expected_runtime_sha256=expected_runtime_sha256,
            )
            if probe and probe.get("ledger") == str(ledger):
                print(f"LEDGER_URL={state['url']}")
                print(f"LEDGER_PID={process.pid}")
                print(f"LEDGER_LOG={log_path}")
                # The child deliberately outlives this short launcher command.
                # Mark the local Popen wrapper as detached to avoid a misleading
                # ResourceWarning when its Python object is collected.
                process.returncode = 0
                return 0
        if process.poll() is not None:
            break
        time.sleep(0.1)
    if process.poll() is None:
        process.terminate()
    raise ValueError(f"ledger UI failed to start; inspect {log_path}")


def command_status(args: argparse.Namespace) -> int:
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    expected_ui_assets_sha256 = current_ui_assets_sha256()
    expected_runtime_sha256 = current_runtime_sha256()
    state = load_state(state_path_for(ledger))
    if not state:
        print("stopped")
        return 1
    probe = ui_health(
        state.get("url", ""),
        state.get("token", ""),
        expected_ui_assets_sha256=expected_ui_assets_sha256,
        expected_runtime_sha256=expected_runtime_sha256,
    )
    if not probe or probe.get("instance_id") != state.get("instance_id") or probe.get("ledger") != str(ledger):
        print("stale state")
        return 1
    print("running")
    print(f"LEDGER_URL={state['url']}")
    print(f"LEDGER_PID={state['pid']}")
    return 0


def command_stop(args: argparse.Namespace) -> int:
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    state_path = state_path_for(ledger)
    state = load_state(state_path)
    if not state:
        print("already stopped")
        return 0
    probe = health(state.get("url", ""), state.get("token", ""))
    if not probe or probe.get("instance_id") != state.get("instance_id") or probe.get("ledger") != str(ledger):
        raise ValueError("refusing to stop: runtime state does not match a live ledger UI")
    pid = state.get("pid")
    if not isinstance(pid, int) or pid <= 1:
        raise ValueError("refusing to stop: invalid pid")
    connection = reusable_connection(state_path, ledger)
    if connection:
        write_private_state(connection_path_for(ledger), connection)
    os.kill(pid, signal.SIGTERM)
    for _ in range(40):
        if not health(state.get("url", ""), state.get("token", ""), timeout=0.15):
            print("stopped")
            return 0
        time.sleep(0.1)
    raise ValueError("ledger UI did not stop after SIGTERM")


def command_migrate(args: argparse.Namespace) -> int:
    source = pathlib.Path(args.source).expanduser().resolve()
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    if ledger.exists() and not args.force:
        raise ValueError(f"refusing to overwrite existing ledger without --force: {ledger}")
    data = migrate_markdown(source, args.title, args.task_id)
    atomic_write_json(ledger, data)
    print(f"migrated {len(data['items'])} item(s) to {ledger}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    data = read_json(ledger)
    transferred_count = sum(item.get("tracking_state") == "transferred" for item in data["items"])
    open_count = sum(
        not item["completed"] and item.get("tracking_state", "active") == "active"
        for item in data["items"]
    )
    done_count = sum(
        item["completed"] and item.get("tracking_state", "active") == "active"
        for item in data["items"]
    )
    print(
        f"valid schema={SCHEMA_VERSION} revision={data['revision']} "
        f"open={open_count} transferred={transferred_count} done={done_count}"
    )
    return 0


def command_project_ledger(args: argparse.Namespace) -> int:
    if not args.project_storage:
        print("PROJECT_STORAGE_ENABLED=false")
        return 0
    requested_root = pathlib.Path(args.project_root).expanduser().resolve()
    project_root = git_project_root(requested_root)
    task_id = args.task_id or os.environ.get("CODEX_THREAD_ID") or os.environ.get(
        "CLAUDE_SESSION_ID"
    )
    if not task_id:
        raise ValueError(
            "project storage needs --task-id, CODEX_THREAD_ID, or CLAUDE_SESSION_ID"
        )
    if not TASK_STORAGE_KEY_RE.fullmatch(task_id):
        raise ValueError(
            "task ID must use 1-128 letters, digits, dots, underscores, or hyphens"
        )
    gitignore = ensure_project_gitignore(project_root)
    storage_root = project_root / PROJECT_LEDGER_DIRECTORY
    chat_storage_root = storage_root / task_id
    storage_root.mkdir(mode=0o700, exist_ok=True)
    chat_storage_root.mkdir(mode=0o700, exist_ok=True)
    storage_root.chmod(0o700)
    chat_storage_root.chmod(0o700)
    ledger = chat_storage_root / "outstanding-items.json"
    if ledger.exists():
        data, _ = reconcile_ledger_file(ledger)
        if data.get("task_id") != task_id:
            raise ValueError(
                f"existing project ledger belongs to {data.get('task_id')!r}, not {task_id!r}"
            )
    else:
        atomic_write_json(ledger, empty_ledger(args.title, task_id, project_root))
    print("PROJECT_STORAGE_ENABLED=true")
    print(f"PROJECT_ROOT={project_root}")
    print(f"LEDGER_PATH={ledger}")
    print(f"GITIGNORE={gitignore}")
    return 0


def reconcile_ledger_file(ledger: pathlib.Path) -> tuple[dict[str, Any], bool]:
    data = read_json(ledger)
    changed = reconcile_order(data)
    if changed:
        data["revision"] += 1
        data["updated_at"] = utc_now()
        atomic_write_json(ledger, data)
    return data, changed


def command_reconcile_order(args: argparse.Namespace) -> int:
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    data, changed = reconcile_ledger_file(ledger)
    active = sorted(
        (
            item
            for item in data["items"]
            if not item["completed"] and item.get("tracking_state", "active") == "active"
        ),
        key=lambda item: item["position"],
    )
    print(
        f"{'reconciled' if changed else 'unchanged'} revision={data['revision']} "
        f"order={','.join(display_id(item) for item in active)}"
    )
    return 0


def command_upsert(args: argparse.Namespace) -> int:
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    data = read_json(ledger)
    item_id, reference_priority = split_item_reference(args.id)
    requested_priority = getattr(args, "priority", None)
    item = next((entry for entry in data["items"] if entry["id"] == item_id), None)
    if item is None and reference_priority and requested_priority and reference_priority != requested_priority:
        raise ValueError(
            f"--id priority {reference_priority} disagrees with --priority {requested_priority}"
        )
    if item is not None and reference_priority and reference_priority != item["priority"]:
        raise ValueError(
            f"{args.id} has stale priority; current reference is {display_id(item)}"
        )
    if item is not None and item.get("tracking_state") == "transferred":
        raise ValueError(f"{display_id(item)} is transferred history and cannot be updated in this task")
    provenance = getattr(args, "provenance", None)
    if item is None:
        if not args.title:
            raise ValueError("--title is required when adding a new item")
        if provenance is None:
            raise ValueError(
                "--provenance is required when adding a new item; choose "
                "user-requested, agent-added, or unknown-legacy"
            )
        initial_status = args.status or "requested"
        initial_completed = initial_status in DONE_STATUSES
        initial_position = sum(
            entry["completed"] == initial_completed for entry in data["items"]
        )
        changed_at = utc_now()
        item = {
            "id": item_id,
            "priority": requested_priority or reference_priority or DEFAULT_PRIORITY,
            "title": args.title.strip(),
            "status": initial_status,
            "completed": initial_completed,
            "position": initial_position,
            "group": args.group or "Outstanding for you",
            "state_text": initial_status,
            "details_markdown": "",
            "explanation": "",
            "provenance": provenance,
            "order_intent": automatic_order_intent(changed_at),
            "completed_at": changed_at if initial_completed else None,
            "completed_session_id": args.session_id if initial_completed else None,
        }
        data["items"].append(item)
    elif provenance is not None and provenance != item["provenance"]:
        raise ValueError(
            f"{display_id(item)} provenance is immutable ({item['provenance']}); "
            "use correct-provenance with an evidence-based reason"
        )
    substantive_update = any(
        value is not None
        for value in (
            args.title,
            args.status,
            requested_priority,
            args.group,
            args.explanation,
            args.notes_file,
        )
    )
    changed_at = utc_now()
    if args.title:
        item["title"] = args.title.strip()
    if args.explanation is not None:
        explanation = " ".join(args.explanation.split())
        if len(explanation) > MAX_EXPLANATION_CHARS:
            raise ValueError(
                f"--explanation must be at most {MAX_EXPLANATION_CHARS} characters"
            )
        item["explanation"] = explanation
    if args.status:
        item["status"] = args.status
        item["completed"] = args.status in DONE_STATUSES
        item["state_text"] = args.status
        item["completed_at"] = changed_at if item["completed"] else None
        item["completed_session_id"] = args.session_id if item["completed"] else None
    if requested_priority:
        item["priority"] = requested_priority
    if args.group:
        item["group"] = args.group
    if args.notes_file:
        item["details_markdown"] = pathlib.Path(args.notes_file).read_text(encoding="utf-8").strip()
    if substantive_update:
        touch_relevance(item, changed_at)
    if args.title or args.status or requested_priority:
        clear_suggestion_for(data, item_id)
    normalize_positions(data)
    reconcile_order(data)
    data["revision"] += 1
    data["updated_at"] = utc_now()
    atomic_write_json(ledger, data)
    print(f"saved {display_id(item)} at revision {data['revision']}")
    return 0


def command_correct_provenance(args: argparse.Namespace) -> int:
    """Correct demonstrably wrong origin metadata without changing item state."""
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    data = read_json(ledger)
    by_id = {item["id"]: item for item in data["items"]}
    requested = list(
        dict.fromkeys(item_for_reference(data["items"], reference)["id"] for reference in args.ids)
    )
    if not requested:
        raise ValueError("--ids must name at least one item")
    reason = " ".join(args.reason.split())
    if not reason:
        raise ValueError("--reason must explain the evidence for this correction")
    if len(reason) > MAX_PROVENANCE_REASON_CHARS:
        raise ValueError(
            f"--reason must be at most {MAX_PROVENANCE_REASON_CHARS} characters"
        )
    unchanged = [item_id for item_id in requested if by_id[item_id]["provenance"] == args.provenance]
    if unchanged:
        raise ValueError(
            f"already {args.provenance}: {', '.join(unchanged)}; no correction was written"
        )

    corrected_at = utc_now()
    for item_id in requested:
        item = by_id[item_id]
        old = item["provenance"]
        correction = {
            "from": old,
            "to": args.provenance,
            "corrected_at": corrected_at,
            "reason": reason,
        }
        if args.session_id:
            correction["session_id"] = args.session_id
        item.setdefault("provenance_history", []).append(correction)
        item["provenance"] = args.provenance

    reconcile_order(data)
    data["revision"] += 1
    data["updated_at"] = corrected_at
    atomic_write_json(ledger, data)
    print(
        f"corrected provenance for {len(requested)} item(s) to {args.provenance} "
        f"at revision {data['revision']}"
    )
    return 0


def command_transfer(args: argparse.Namespace) -> int:
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    data = read_json(ledger)
    by_id = {item["id"]: item for item in data["items"]}
    requested = list(
        dict.fromkeys(item_for_reference(data["items"], reference)["id"] for reference in args.ids)
    )
    transferred_at = utc_now()
    destination = {
        "task_id": args.task_id,
        "title": args.destination_title,
        "transferred_at": transferred_at,
        "title_source": "provided-at-transfer",
        "title_updated_at": transferred_at,
    }
    if args.handoff_path:
        destination["handoff_path"] = str(pathlib.Path(args.handoff_path).expanduser().resolve())
    for item_id in requested:
        item = by_id[item_id]
        item["tracking_state"] = "transferred"
        item["transferred_to"] = dict(destination)
    normalize_positions(data)
    reconcile_order(data)
    data["revision"] += 1
    data["updated_at"] = transferred_at
    atomic_write_json(ledger, data)
    print(
        f"transferred {len(requested)} item(s) to {args.destination_title} "
        f"at revision {data['revision']}"
    )
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Outstanding Items canonical ledger and local HTML UI")
    sub = root.add_subparsers(dest="command", required=True)

    project_ledger = sub.add_parser(
        "project-ledger",
        help="create or resolve this chat's default Git-project ledger",
    )
    project_ledger.add_argument("--project-root", default=".")
    project_ledger.add_argument("--task-id")
    project_ledger.add_argument("--title", default="Outstanding items")
    project_ledger.add_argument(
        "--project-storage",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="store the chat ledger under the project (enabled by default)",
    )
    project_ledger.set_defaults(func=command_project_ledger)

    migrate = sub.add_parser("migrate-markdown", help="migrate a legacy Markdown ledger into canonical JSON")
    migrate.add_argument("--source", required=True)
    migrate.add_argument("--ledger", required=True)
    migrate.add_argument("--title", required=True)
    migrate.add_argument("--task-id")
    migrate.add_argument("--force", action="store_true")
    migrate.set_defaults(func=command_migrate)

    validate = sub.add_parser("validate", help="validate one canonical JSON ledger")
    validate.add_argument("--ledger", required=True)
    validate.set_defaults(func=command_validate)

    reconcile = sub.add_parser(
        "reconcile-order",
        help="sort automatic items by status, priority, and relevance while preserving manual placement",
    )
    reconcile.add_argument("--ledger", required=True)
    reconcile.set_defaults(func=command_reconcile_order)

    upsert = sub.add_parser("upsert", help="add or update one canonical ledger item")
    upsert.add_argument("--ledger", required=True)
    upsert.add_argument("--id", required=True)
    upsert.add_argument("--title")
    upsert.add_argument("--status", choices=sorted(STATUSES))
    upsert.add_argument(
        "--priority",
        choices=sorted(PRIORITIES),
        help=f"P0 (highest) through P3 (lowest); new items default to {DEFAULT_PRIORITY}",
    )
    upsert.add_argument(
        "--provenance",
        choices=sorted(PROVENANCES),
        help="required for a new item; records who caused the item to enter the ledger",
    )
    upsert.add_argument("--group")
    upsert.add_argument(
        "--explanation",
        help="one short plain-language paragraph shown as the item's tooltip in the UI",
    )
    upsert.add_argument("--notes-file")
    upsert.add_argument("--session-id")
    upsert.set_defaults(func=command_upsert)

    correct_provenance = sub.add_parser(
        "correct-provenance",
        help="correct demonstrably wrong item provenance and append an audit record",
    )
    correct_provenance.add_argument("--ledger", required=True)
    correct_provenance.add_argument("--ids", nargs="+", required=True)
    correct_provenance.add_argument("--provenance", choices=sorted(PROVENANCES), required=True)
    correct_provenance.add_argument("--reason", required=True)
    correct_provenance.add_argument("--session-id")
    correct_provenance.set_defaults(func=command_correct_provenance)

    transfer = sub.add_parser("transfer", help="retain items as read-only history owned by another task")
    transfer.add_argument("--ledger", required=True)
    transfer.add_argument("--ids", nargs="+", required=True)
    transfer.add_argument("--task-id", required=True)
    transfer.add_argument("--task-title", dest="destination_title", required=True)
    transfer.add_argument("--handoff-path")
    transfer.set_defaults(func=command_transfer)

    serve = sub.add_parser("serve", help="serve one ledger in the foreground")
    serve.add_argument("--ledger", required=True)
    serve.add_argument("--port", type=int, default=0)
    serve.add_argument("--token")
    serve.add_argument("--instance-id")
    serve.add_argument("--state-file")
    serve.add_argument("--connection-file")
    serve.set_defaults(func=command_serve)

    start = sub.add_parser("start", help="start or reuse a background ledger UI")
    start.add_argument("--ledger", required=True)
    start.add_argument("--port", type=int, default=0)
    start.add_argument("--token", help=argparse.SUPPRESS)
    start.set_defaults(func=command_start)

    status = sub.add_parser("status", help="show whether a ledger UI is running")
    status.add_argument("--ledger", required=True)
    status.set_defaults(func=command_status)

    stop = sub.add_parser("stop", help="stop the exact verified ledger UI process")
    stop.add_argument("--ledger", required=True)
    stop.set_defaults(func=command_stop)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
