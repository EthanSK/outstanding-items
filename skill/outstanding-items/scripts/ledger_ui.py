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
import re
import secrets
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


SCHEMA_VERSION = 4
PREVIOUS_SCHEMA_VERSION = 3
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
ID_RE = re.compile(r"^OI-\d+$")
ITEM_HEADING_RE = re.compile(r"^###\s+(OI-\d+)\s+(.+?)\s*$")
DONE_ITEM_RE = re.compile(r"^-\s+~~(OI-\d+)\s+(.+?)~~\s*(.*?)\s*$")
SECTION_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
STATE_RE = re.compile(r"^-\s+\*\*State:\*\*\s*(.+?)\s*$", re.I)
MAX_BODY_BYTES = 1_000_000
# One short, plain-language paragraph shown as the item's hover/focus tooltip.
MAX_EXPLANATION_CHARS = 600


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


def migrate_schema(data: Any) -> bool:
    """Upgrade the one supported prior schema without inventing provenance."""
    if not isinstance(data, dict):
        raise ValueError("ledger root must be an object")
    version = data.get("schema_version")
    if version == SCHEMA_VERSION:
        validate_ledger(data)
        return False
    if version != PREVIOUS_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version must be {SCHEMA_VERSION} or supported legacy version "
            f"{PREVIOUS_SCHEMA_VERSION}"
        )
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("items must be an array")
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("every legacy item must be an object")
        item["provenance"] = "unknown-legacy"
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
        completed = item.get("completed")
        if not isinstance(completed, bool):
            raise ValueError(f"{item_id} completed must be boolean")
        if completed != (status in DONE_STATUSES):
            raise ValueError(f"{item_id} completed and status disagree")
        provenance = item.get("provenance")
        if provenance not in PROVENANCES:
            raise ValueError(f"{item_id} has unsupported provenance {provenance!r}")
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
            title_text = done_match.group(2).strip()
            if title_text.endswith("."):
                title_text = title_text[:-1]
            state = done_match.group(3).strip()
            current_item = {
                "id": done_match.group(1),
                "title": title_text,
                "_from_done_bullet": True,
            }
            item_lines = [f"- **State:** {state}"] if state else []
            continue
        item_match = ITEM_HEADING_RE.match(line)
        if item_match:
            flush_item()
            current_item = {"id": item_match.group(1), "title": item_match.group(2).strip()}
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


def clear_suggestion_for(data: dict[str, Any], item_id: str) -> None:
    suggestion = data.get("latest_unanswered_suggestion")
    if isinstance(suggestion, dict) and suggestion.get("id") == item_id:
        data["latest_unanswered_suggestion"] = None


def mutate(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    base_revision = payload.get("base_revision")
    if base_revision != data["revision"]:
        raise ConflictError("The ledger changed elsewhere. Reloaded the newest version; retry your edit.")
    action = payload.get("action")
    item_id = payload.get("id")
    item = next((entry for entry in data["items"] if entry["id"] == item_id), None)
    if action in {"edit", "toggle"} and item is None:
        raise ValueError(f"unknown item id: {item_id!r}")
    if action in {"edit", "toggle"} and item.get("tracking_state") == "transferred":
        raise ValueError(f"{item_id} is transferred history and is read-only here")
    if action == "edit":
        title = payload.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be non-empty")
        if len(title.strip()) > 500:
            raise ValueError("title must be at most 500 characters")
        item["title"] = title.strip()
        clear_suggestion_for(data, item_id)
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
        clear_suggestion_for(data, item_id)
        normalize_positions(data)
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
        by_id = {entry["id"]: entry for entry in data["items"]}
        for position, ordered_id in enumerate(order):
            by_id[ordered_id]["position"] = position
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


class ConflictError(ValueError):
    pass


class LedgerHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        handler: type[BaseHTTPRequestHandler],
        ledger_path: pathlib.Path,
        assets_path: pathlib.Path,
        token: str,
        instance_id: str,
    ) -> None:
        super().__init__(address, handler)
        self.ledger_path = ledger_path
        self.assets_path = assets_path
        self.token = token
        self.instance_id = instance_id
        self.write_lock = threading.Lock()


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
        path = self.server.assets_path / name
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
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
                },
            )
            return
        if parsed.path == "/api/ledger":
            if not self.token_ok(query):
                self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "invalid token"})
                return
            try:
                data = read_json(self.server.ledger_path)
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


def state_path_for(ledger: pathlib.Path) -> pathlib.Path:
    return ledger.with_name(f".{ledger.stem}.ledger-ui-state.json")


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


def load_state(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return state if isinstance(state, dict) else None


def command_serve(args: argparse.Namespace) -> int:
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    read_json(ledger)
    token = args.token or secrets.token_urlsafe(24)
    instance_id = args.instance_id or secrets.token_hex(12)
    assets = pathlib.Path(__file__).resolve().parent.parent / "assets"
    server = LedgerHTTPServer(("127.0.0.1", args.port), LedgerHandler, ledger, assets, token, instance_id)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/?token={urllib.parse.quote(token)}"
    state_path = pathlib.Path(args.state_file).resolve() if args.state_file else state_path_for(ledger)
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
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(atomic_state, indent=2) + "\n", encoding="utf-8")
    state_path.chmod(0o600)
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
    read_json(ledger)
    state_path = state_path_for(ledger)
    existing = load_state(state_path)
    if existing:
        probe = health(existing.get("url", ""), existing.get("token", ""))
        if probe and probe.get("instance_id") == existing.get("instance_id") and probe.get("ledger") == str(ledger):
            print(f"LEDGER_URL={existing['url']}")
            print(f"LEDGER_PID={existing['pid']}")
            return 0
    token = secrets.token_urlsafe(24)
    instance_id = secrets.token_hex(12)
    log_path = log_path_for(ledger)
    command = [
        sys.executable,
        str(pathlib.Path(__file__).resolve()),
        "serve",
        "--ledger",
        str(ledger),
        "--port",
        str(args.port),
        "--token",
        token,
        "--instance-id",
        instance_id,
        "--state-file",
        str(state_path),
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
            probe = health(state.get("url", ""), token)
            if probe and probe.get("ledger") == str(ledger):
                print(f"LEDGER_URL={state['url']}")
                print(f"LEDGER_PID={process.pid}")
                print(f"LEDGER_LOG={log_path}")
                return 0
        if process.poll() is not None:
            break
        time.sleep(0.1)
    if process.poll() is None:
        process.terminate()
    raise ValueError(f"ledger UI failed to start; inspect {log_path}")


def command_status(args: argparse.Namespace) -> int:
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    state = load_state(state_path_for(ledger))
    if not state:
        print("stopped")
        return 1
    probe = health(state.get("url", ""), state.get("token", ""))
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


def command_upsert(args: argparse.Namespace) -> int:
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    data = read_json(ledger)
    item = next((entry for entry in data["items"] if entry["id"] == args.id), None)
    if item is not None and item.get("tracking_state") == "transferred":
        raise ValueError(f"{args.id} is transferred history and cannot be updated in this task")
    provenance = getattr(args, "provenance", None)
    if item is None:
        if not args.title:
            raise ValueError("--title is required when adding a new item")
        if not ID_RE.fullmatch(args.id):
            raise ValueError("--id must look like OI-35")
        if provenance is None:
            raise ValueError(
                "--provenance is required when adding a new item; choose "
                "user-requested, agent-added, or unknown-legacy"
            )
        open_position = sum(not entry["completed"] for entry in data["items"])
        item = {
            "id": args.id,
            "title": args.title.strip(),
            "status": args.status or "requested",
            "completed": (args.status or "requested") in DONE_STATUSES,
            "position": open_position,
            "group": args.group or "Outstanding for you",
            "state_text": args.status or "requested",
            "details_markdown": "",
            "explanation": "",
            "provenance": provenance,
            "completed_at": utc_now() if (args.status or "requested") in DONE_STATUSES else None,
            "completed_session_id": args.session_id if (args.status or "requested") in DONE_STATUSES else None,
        }
        data["items"].append(item)
    elif provenance is not None and provenance != item["provenance"]:
        raise ValueError(
            f"{args.id} provenance is immutable ({item['provenance']}); "
            "do not rewrite item origin"
        )
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
        item["completed_at"] = utc_now() if item["completed"] else None
        item["completed_session_id"] = args.session_id if item["completed"] else None
    if args.group:
        item["group"] = args.group
    if args.notes_file:
        item["details_markdown"] = pathlib.Path(args.notes_file).read_text(encoding="utf-8").strip()
    if args.title or args.status:
        clear_suggestion_for(data, args.id)
    normalize_positions(data)
    data["revision"] += 1
    data["updated_at"] = utc_now()
    atomic_write_json(ledger, data)
    print(f"saved {args.id} at revision {data['revision']}")
    return 0


def command_transfer(args: argparse.Namespace) -> int:
    ledger = pathlib.Path(args.ledger).expanduser().resolve()
    data = read_json(ledger)
    by_id = {item["id"]: item for item in data["items"]}
    requested = list(dict.fromkeys(args.ids))
    missing = [item_id for item_id in requested if item_id not in by_id]
    if missing:
        raise ValueError(f"unknown item id(s): {', '.join(missing)}")
    transferred_at = utc_now()
    destination = {
        "task_id": args.task_id,
        "title": args.destination_title,
        "transferred_at": transferred_at,
    }
    if args.handoff_path:
        destination["handoff_path"] = str(pathlib.Path(args.handoff_path).expanduser().resolve())
    for item_id in requested:
        item = by_id[item_id]
        item["tracking_state"] = "transferred"
        item["transferred_to"] = dict(destination)
    normalize_positions(data)
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

    upsert = sub.add_parser("upsert", help="add or update one canonical ledger item")
    upsert.add_argument("--ledger", required=True)
    upsert.add_argument("--id", required=True)
    upsert.add_argument("--title")
    upsert.add_argument("--status", choices=sorted(STATUSES))
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
    serve.set_defaults(func=command_serve)

    start = sub.add_parser("start", help="start or reuse a background ledger UI")
    start.add_argument("--ledger", required=True)
    start.add_argument("--port", type=int, default=0)
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
