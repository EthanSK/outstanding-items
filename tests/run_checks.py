#!/usr/bin/env python3
"""Deterministic checks for the outstanding-items repository.

Python standard library only. No network access. Every check is structural, so
it keeps working after the prose is rewritten.

    python3 tests/run_checks.py            # run everything
    python3 tests/run_checks.py -v         # print every check
    python3 tests/run_checks.py --list     # list the checks
    python3 tests/run_checks.py --installed  # also inspect installed copies
"""

from __future__ import annotations

import argparse
import html
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SKILL_DIR = ROOT / "skill" / "outstanding-items"
SKILL_MD = SKILL_DIR / "SKILL.md"

SITE_BASE = "https://ethansk.github.io/outstanding-items/"
REPO_URL = "https://github.com/EthanSK/outstanding-items"
SKILL_NAME = "outstanding-items"
TAGLINE = "Outsource your memory — a curated work experience."
TAGLINE_1 = "Outsource your memory"
TAGLINE_2 = "— a curated work experience."

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".idea"}
# The build prompt is local source material, not a repository artifact. It is
# git-ignored and deliberately excluded from every content check.
SKIP_FILES = {".DS_Store"}
# This file has to spell out the phrases it forbids, so it is exempt from the
# prose blocklist. It is still covered by every other check.
POLICY_EXEMPT = {"tests/run_checks.py"}

TEXT_SUFFIXES = {
    "",
    ".css",
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".svg",
    ".txt",
    ".webmanifest",
    ".xml",
    ".yaml",
    ".yml",
}

STATUSES = [
    "requested",
    "planned",
    "in-progress",
    "implemented",
    "verified",
    "waiting-on-you",
    "blocked",
    "reminder",
    "dropped",
]

# Statuses that retire an item into the ledger's Done group. They never appear
# in the conversation footer.
RETIRING = {"verified", "dropped"}

MARKS = {
    "requested": "\u00b7",
    "planned": "\u2013",
    "in-progress": "\u2192",
    "implemented": "\u25aa",
    "verified": "\u2713",
    "waiting-on-you": "\u00bb",
    "blocked": "!",
    "reminder": "\u25e6",
    "dropped": "\u00d7",
}

REQUIRED_FILES = [
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "CLAUDE.md",
    "LICENSE",
    "README.md",
    "docs/.nojekyll",
    "docs/404.html",
    "docs/assets/app.js",
    "docs/assets/favicon.svg",
    "docs/assets/icon-maskable.svg",
    "docs/assets/styles.css",
    "docs/index.html",
    "docs/manifest.webmanifest",
    "docs/robots.txt",
    "docs/sitemap.xml",
    "examples/README.md",
    "examples/delta-messages.md",
    "examples/global-rules/claude-code-claude-md.md",
    "examples/global-rules/codex-agents-md.md",
    "examples/global-rules/project-instructions.md",
    "examples/outstanding-items.json",
    "examples/outstanding-items.md",
    "examples/transcript.md",
    "scripts/check.sh",
    "scripts/install.sh",
    "scripts/serve.sh",
    "scripts/uninstall.sh",
    "skill/outstanding-items/SKILL.md",
    "skill/outstanding-items/agents/openai.yaml",
    "skill/outstanding-items/assets/ledger.css",
    "skill/outstanding-items/assets/ledger.html",
    "skill/outstanding-items/assets/ledger.js",
    "skill/outstanding-items/references/authority.md",
    "skill/outstanding-items/references/backlog-artifact.md",
    "skill/outstanding-items/references/ledger-ui.md",
    "skill/outstanding-items/references/next-action.md",
    "skill/outstanding-items/references/related-tasks.md",
    "skill/outstanding-items/references/status-labels.md",
    "skill/outstanding-items/references/worked-examples.md",
    "skill/outstanding-items/scripts/ledger_ui.py",
    "tests/test_ledger_ui.py",
    "tests/run_checks.py",
    "tests/run_tests.sh",
]

CHECKS: list[tuple[str, str, object]] = []


def check(name: str, description: str):
    def decorate(fn):
        CHECKS.append((name, description, fn))
        return fn

    return decorate


# ------------------------------------------------------------------ helpers


def repo_files() -> list[pathlib.Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name in SKIP_FILES or (
                name.startswith(".opus-") and name.endswith("-prompt.md")
            ):
                continue
            out.append(pathlib.Path(dirpath) / name)
    return out


def text_files() -> list[pathlib.Path]:
    return [p for p in repo_files() if p.suffix in TEXT_SUFFIXES]


def rel(path: pathlib.Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter(text: str) -> tuple[dict[str, str], int]:
    """Parse a leading YAML frontmatter block. Returns (fields, body_line)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, 0
    fields: dict[str, str] = {}
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return fields, index + 1
        if ":" in lines[index]:
            key, _, value = lines[index].partition(":")
            fields[key.strip()] = value.strip()
    return {}, 0


def strip_tags(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def html_files() -> list[pathlib.Path]:
    return sorted(DOCS.glob("*.html"))


LINK_RE = re.compile(r"""\b(?:href|src)\s*=\s*["']([^"']+)["']""")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def is_external(target: str) -> bool:
    return target.startswith(
        ("http://", "https://", "mailto:", "data:", "#", "tel:", "//")
    )


# ------------------------------------------------------------ footer shapes

# The compact recommendation is one suggested item, at most one line about it, and
# at most one live-UI link. Everything else — the other items, the reminders,
# the counts, and the whole Done history — stays in the ledger and its editor.
DASH = "—"
BULLET = "•"
ELLIPSIS = "…"
MIDDOT = "·"

FENCED_BLOCK_RE = re.compile(r"```[A-Za-z0-9]*\n(.*?)\n```", re.S)
FOOTER_ITEM_RE = re.compile(
    rf"^\*\*(OI-\d+) (.+)\*\* `(?:You|Agent)`(?: {DASH} ([a-z][a-z-]*))?$"
)
FOOTER_QUIET_RE = re.compile(r"^Nothing\b.*$")
FOOTER_EMPTY_RE = re.compile(r"^\*\*No outstanding items\*\*$")
FOOTER_LINK_RE = re.compile(r"^\[Full outstanding items\]\(([^)]+)\)$")
OI_ID_RE = re.compile(r"\bOI-\d+\b")
LIST_ROW_RE = re.compile(rf"^\s*(?:[-*+{BULLET}]\s|{ELLIPSIS}|\d+[.)]\s)")
OVERFLOW_RE = re.compile(rf"\+\s*\d+\s+more|{ELLIPSIS}\s*\+")

# A footer only ever suggests something the user could pick up right now.
# `verified` and `dropped` are Done, `blocked` cannot be moved by them, and
# `reminder` was parked on purpose.
SUGGESTIBLE_STATUSES = {
    "requested",
    "planned",
    "in-progress",
    "implemented",
    "waiting-on-you",
}

# Footer shapes that this project deliberately removed. None of them may come
# back in any shipped file.
STALE_FOOTER_PROMISES = [
    (re.compile(r"^\*\*Outstanding\*\*\s*—", re.M), "the retired Outstanding heading"),
    (re.compile(r"\*\*Outstanding\*\*\s*\(\s*\d"), "the retired counts header"),
    (re.compile(r"\*\*Suggested for you\*\*"), "the retired Suggested for you label"),
    (re.compile(r"link appears twice"), "the retired two-link rule"),
    (re.compile(r"again after the (?:last|final)"), "the retired second link position"),
    (re.compile(r"crossed-out Done section", re.I), "a Done section in the footer"),
    (re.compile(r"Four sections, always in this order"), "the retired four-section footer"),
    (re.compile(r"at most \d+ lines under", re.I), "the retired per-section line budget"),
]


def squash(text: str) -> str:
    """Collapse whitespace so a wrapped instruction still matches its phrase."""
    return re.sub(r"\s+", " ", text)


def footer_blocks() -> list[tuple[str, int, list[str]]]:
    """Every fenced block in the repository that documents a compact recommendation."""
    found: list[tuple[str, int, list[str]]] = []
    for path in text_files():
        if rel(path) in POLICY_EXEMPT:
            continue
        text = read(path)
        for match in FENCED_BLOCK_RE.finditer(text):
            lines = match.group(1).splitlines()
            if not lines or not (
                FOOTER_ITEM_RE.match(lines[0])
                or FOOTER_QUIET_RE.match(lines[0])
                or FOOTER_EMPTY_RE.match(lines[0])
            ):
                continue
            found.append((rel(path), text.count("\n", 0, match.start()) + 1, lines))
    return found


# ------------------------------------------------------------------- checks


@check("required-files", "every file the project promises exists")
def check_required_files() -> list[str]:
    return [f"missing required file: {name}" for name in REQUIRED_FILES if not (ROOT / name).exists()]


@check("skill-frontmatter", "SKILL.md frontmatter is valid and carries triggers")
def check_skill_frontmatter() -> list[str]:
    problems = []
    text = read(SKILL_MD)
    fields, body_line = frontmatter(text)
    if not fields:
        return ["SKILL.md has no parsable YAML frontmatter"]
    if fields.get("name") != SKILL_NAME:
        problems.append(f"SKILL.md name is {fields.get('name')!r}, expected {SKILL_NAME!r}")
    description = fields.get("description", "")
    if not description:
        problems.append("SKILL.md has no description")
    else:
        if len(description) > 1024:
            problems.append(f"SKILL.md description is {len(description)} chars, over the 1024 budget")
        if len(description) < 120:
            problems.append("SKILL.md description is too short to carry trigger conditions")
        if "use when" not in description.lower():
            problems.append("SKILL.md description must state trigger conditions with 'Use when'")
    for key in fields:
        if key not in {"name", "description", "license", "allowed-tools", "version"}:
            problems.append(f"unexpected frontmatter key in SKILL.md: {key}")
    if body_line == 0:
        problems.append("SKILL.md frontmatter is not terminated")
    return problems


@check("skill-contract", "SKILL.md keeps its safeguards and improvement contract")
def check_skill_contract() -> list[str]:
    problems = []
    text = read(SKILL_MD)
    lines = text.splitlines()

    improvement_line = None
    for index, line in enumerate(lines):
        if "continuous improvement" in line.lower():
            improvement_line = index
            break
    if improvement_line is None:
        problems.append("SKILL.md has no continuous improvement section")
    elif improvement_line > 25:
        problems.append(
            f"continuous improvement section is at line {improvement_line + 1}; it belongs near the top"
        )

    required_phrases = [
        "durable verified finding",
        "retest",
        "does not start a background daemon",
        "does not create a cross-task message bus",
        "does not create a persistent database",
        "does not guarantee automatic invocation",
        "Never refuse a reminder because it is off-topic",
        "Resolve once",
        "Report failures",
        "Prevent loops",
        "Record useful links locally",
        "Message only when separately authorized",
        "by itself it never authorizes waking, starting, messaging, reprioritising, or altering the other task",
        # User ownership and curation guards.
        "the outstanding items belong to the user",
        "never authorizes you to start",
        "Only a fresh, explicit instruction",
        "Capturing is not accepting a job",
        "Propose, never dispatch",
        "A suggestion never edits the ledger",
        "Then stop and wait for the user",
        "record and acknowledge it",
        # The two status distinctions that carry the most weight.
        "`waiting-on-you` is not `blocked`",
        "Intentional reminder",
    ]
    lowered = text.lower()
    for phrase in required_phrases:
        if phrase.lower() not in lowered:
            problems.append(f"SKILL.md no longer states: {phrase!r}")

    for status in STATUSES:
        if f"`{status}`" not in text:
            problems.append(f"SKILL.md does not define the {status!r} label")

    if len(lines) > 220:
        problems.append(
            f"SKILL.md is {len(lines)} lines; keep the always-loaded contract short and push detail into references/"
        )
    return problems


@check("authority-matrix", "Rule One denies every implicit signal and allows only a fresh named instruction")
def check_authority_matrix() -> list[str]:
    problems = []
    authority = read(SKILL_DIR / "references" / "authority.md")
    decisions = {
        key: answer
        for key, answer in re.findall(
            r"^\| `([^`]+)` \|.*?\| (Yes|No) \|",
            authority,
            re.M,
        )
    }
    denied = {
        "recommended-next",
        "suggested-next",
        "highest-priority",
        "ranked-position",
        "status-in-progress",
        "status-planned",
        "status-implemented",
        "related-task-registry",
        "cross-task-delta",
        "continue-from-backlog",
        "standing-authority",
        "pick-the-obvious-one",
        "task-age",
        "urgency",
        "dependency",
        "prerequisite-absorption",
        "add-to-outstanding",
        "remember-this",
        "agent-maintains-ledger",
        "old-instruction",
        "sync-or-summary",
        "non-user-instruction",
        "user-declined-suggestion",
    }
    for key in sorted(denied):
        if decisions.get(key) != "No":
            problems.append(f"authority decision {key!r} must be No, found {decisions.get(key)!r}")
    if decisions.get("fresh-explicit-instruction") != "Yes":
        problems.append("fresh-explicit-instruction must be the sole Yes authority case")
    unexpected_yes = sorted(key for key, answer in decisions.items() if answer == "Yes" and key != "fresh-explicit-instruction")
    if unexpected_yes:
        problems.append(f"unexpected Yes authority cases: {', '.join(unexpected_yes)}")

    core = read(SKILL_MD).lower()
    for dangerous in (
        "capture it and continue",
        "get on with it",
        "say the word",
        "tell me to send it anyway",
    ):
        if dangerous in core:
            problems.append(f"SKILL.md retains execution-shaped wording: {dangerous!r}")
    for required in (
        "current message",
        "once that turn ends, the authority ends",
        "memory propagation never uses a task-triggering send",
    ):
        combined = (read(SKILL_MD) + "\n" + authority).lower()
        if required not in combined:
            problems.append(f"authority contract no longer states: {required!r}")

    for verb in (
        "start",
        "resume",
        "continue",
        "investigate",
        "research",
        "prepare",
        "pre-work",
        "dispatch",
        "route",
        "complete",
    ):
        if verb not in core:
            problems.append(f"Rule One no longer covers the authority verb: {verb!r}")

    status_text = read(SKILL_DIR / "references" / "status-labels.md")
    artifact_text = read(SKILL_DIR / "references" / "backlog-artifact.md")
    for label in ("implemented", "planned", "requested"):
        if f"`{label}`" not in status_text or f"`{label}`" not in artifact_text:
            problems.append(f"stale in-progress reconciliation no longer covers {label!r}")

    # A footer that shows one item can only stay honest if a rejected suggestion
    # never comes back on the agent's own initiative.
    for phrase in (
        "latest_unanswered_suggestion",
        "Set `outcome` to `declined`",
        "do not suggest that ID again on your own initiative",
        "Clear it to `null`",
        "never authority",
    ):
        if phrase not in artifact_text:
            problems.append(f"backlog-artifact.md does not govern repeat suggestions: {phrase!r}")

    for phrase in (
        "Never suggested on your own initiative",
        "The footer carries no counts, no section headings, and no overflow row",
    ):
        if phrase not in status_text:
            problems.append(f"status-labels.md no longer states: {phrase!r}")

    next_action = read(SKILL_DIR / "references" / "next-action.md")
    for phrase in (
        "One `OI-n` in the footer, and no other",
        "leave the runner-up unnamed",
        "**Unanswered.**",
        "**Declined.**",
        "**Unless they ask.**",
        "no-suggestion line",
    ):
        if phrase not in next_action:
            problems.append(f"next-action.md no longer governs the single suggestion: {phrase!r}")
    if OI_ID_RE.search(next_action) is None:
        problems.append("next-action.md shows no worked suggestion")
    return problems


@check("public-examples", "copy-paste examples preserve user ownership and schema v4")
def check_public_examples() -> list[str]:
    problems = []

    deltas = read(ROOT / "examples" / "delta-messages.md")
    well_formed = deltas.partition("## Malformed")[0]
    blocks = re.findall(r"```text\n(.*?)\n```", well_formed, re.S)
    if len(blocks) < 3:
        problems.append("delta-messages.md needs at least three well-formed examples")
    for number, block in enumerate(blocks, start=1):
        lines = block.splitlines()
        mandatory = "Memory update for your ledger. It authorizes no implementation and starts nothing."
        if len(lines) < 2 or lines[1] != mandatory:
            problems.append(f"well-formed delta {number} is missing the mandatory memory-only second line")
        lowered = block.lower()
        for forbidden in ("requested:", "you can start", "start oi-"):
            if forbidden in lowered:
                problems.append(f"well-formed delta {number} contains execution-adjacent wording: {forbidden!r}")
        if not lines or lines[-1] != "Nothing else in your list changes.":
            problems.append(f"well-formed delta {number} does not preserve the rest of the destination")

    transcript = read(ROOT / "examples" / "transcript.md")
    normalized_transcript = squash(transcript)
    for required in (
        "No task-triggering send occurred",
        "A priority choice is not a start instruction",
        "The recommendation changes no item, status, order, or execution state",
        "A later turn must receive a new named instruction",
        # The compact footer's own edge cases, demonstrated end to end.
        "so it is not offered again",
        "OI-4 was declined, so it is not offered again unless you ask",
        "it is never promoted to fill a line",
        "the footer never shows a Done section",
        "The whole list goes in the answer because you asked for it, and the footer stays one line",
        "The live URL appears once, on the last line",
    ):
        if squash(required) not in normalized_transcript:
            problems.append(f"transcript.md no longer demonstrates: {required!r}")
    if "OI-5 Skip link — in-progress" in transcript:
        problems.append("transcript.md leaves a temporary in-progress label in a final reply")
    if "OI-5 Skip link — implemented" not in transcript:
        problems.append("transcript.md does not reconcile completed turn work to implemented")
    # The whole list belongs in the body of an answer when the user asks for it,
    # never in the footer. The footer checks prove no list row is inside one.
    answer_rows = [
        line for line in transcript.splitlines() if re.match(r"^- OI-\d+ ", line)
    ]
    if len(answer_rows) < 5:
        problems.append(
            "transcript.md does not show the full list answered in the body of a reply"
        )

    try:
        payload = json.loads(read(ROOT / "examples" / "outstanding-items.json"))
    except json.JSONDecodeError as exc:
        problems.append(f"example backlog JSON is invalid: {exc}")
    else:
        if payload.get("schema_version") != 4:
            problems.append("example backlog JSON must use schema version 4")
        if payload.get("owner") != "user" or payload.get("authorizes_work") is not False:
            problems.append("example backlog JSON must say owner=user and authorizes_work=false")
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            problems.append("example backlog JSON must contain items")
        else:
            ids = [item.get("id") for item in items if isinstance(item, dict)]
            if len(ids) != len(set(ids)):
                problems.append("example backlog JSON item IDs must be unique")
            for completed in (False, True):
                positions = sorted(
                    item.get("position") for item in items
                    if isinstance(item, dict) and item.get("completed") is completed
                )
                if positions != list(range(len(positions))):
                    problems.append("example backlog JSON positions must be contiguous per completion group")
        if not isinstance(payload.get("sections"), list):
            problems.append("example backlog JSON must contain a sections list")

    legacy = read(ROOT / "examples" / "outstanding-items.md")
    if "Legacy migration fixture" not in legacy or "not a writable or canonical ledger" not in legacy:
        problems.append("examples/outstanding-items.md must be labelled as a frozen legacy fixture")
    return problems


@check("item-provenance", "every item records an honest origin; only known origins add badges")
def check_item_provenance() -> list[str]:
    problems = []
    supported = {"user-requested", "agent-added", "unknown-legacy"}
    payload = json.loads(read(ROOT / "examples" / "outstanding-items.json"))
    items = payload.get("items", [])
    present = {item.get("provenance") for item in items if isinstance(item, dict)}
    if present != supported:
        problems.append(f"example ledger provenance values are {sorted(present)!r}, expected all three")

    html_text = read(SKILL_DIR / "assets" / "ledger.html")
    script = read(SKILL_DIR / "assets" / "ledger.js")
    style = read(SKILL_DIR / "assets" / "ledger.css")
    runtime = read(SKILL_DIR / "scripts" / "ledger_ui.py")
    if 'class="provenance-badge"' not in html_text:
        problems.append("ledger.html has no provenance badge in the shared row template")
    for fragment in (
        'label: "You"',
        'label: "Agent"',
        "You asked for this item.",
        "An agent added this item because it was genuinely useful to track.",
        'badge.setAttribute("aria-label"',
        "badge.dataset.tooltip",
        "attachProvenance(node, item)",
        "badge.hidden = true",
        "badge.hidden = false",
    ):
        if fragment not in script:
            problems.append(f"ledger.js is missing provenance UI wiring: {fragment!r}")
    if "Source unknown" in script:
        problems.append("ledger.js visibly labels legacy provenance instead of leaving it unobtrusive")
    for fragment in (
        ".provenance-badge",
        ".provenance-badge::after",
        ".provenance-badge:hover::after",
        "white-space: nowrap",
    ):
        if fragment not in style:
            problems.append(f"ledger.css is missing compact provenance styling: {fragment!r}")
    if "grid-template-columns: minmax(0, 1fr) auto" in style:
        problems.append("ledger.css still reserves a separate provenance column beside task text")
    for fragment in (
        "PROVENANCES",
        "unknown-legacy",
        '"--provenance"',
        "provenance is immutable",
        "migrate_schema",
    ):
        if fragment not in runtime:
            problems.append(f"ledger_ui.py is missing provenance enforcement: {fragment!r}")

    artifact = read(SKILL_DIR / "references" / "backlog-artifact.md")
    ui_reference = read(SKILL_DIR / "references" / "ledger-ui.md")
    skill = read(SKILL_MD)
    for text, phrase, name in (
        (artifact, "| `provenance` |", "backlog-artifact.md"),
        (artifact, "Version 3 migration", "backlog-artifact.md"),
        (ui_reference, "--provenance", "ledger-ui.md"),
        (skill, "Record provenance at creation", "SKILL.md"),
        (skill, "Add proactively only when genuinely useful", "SKILL.md"),
        (skill, "Do not manufacture agent-added work", "SKILL.md"),
    ):
        if phrase not in text:
            problems.append(f"{name} does not document provenance rule {phrase!r}")

    homepage = read(DOCS / "index.html")
    if 'class="reply-provenance"' not in homepage:
        problems.append("homepage demo does not show the compact provenance badge")
    if '>You</small>' not in homepage or '>You asked</small>' in homepage:
        problems.append("homepage demo must use the compact 'You' provenance label")
    if 'class="reply-title"' in homepage or ">Outstanding<" in homepage:
        problems.append("homepage demo restored the retired Outstanding header")
    return problems


@check("skill-references", "references are one level deep and all linked")
def check_skill_references() -> list[str]:
    problems = []
    text = read(SKILL_MD)
    linked = set()
    for target in MD_LINK_RE.findall(text):
        if is_external(target):
            continue
        resolved = (SKILL_DIR / target).resolve()
        if not resolved.exists():
            problems.append(f"SKILL.md links to a missing file: {target}")
            continue
        linked.add(resolved)
        if not target.startswith("references/") or target.count("/") != 1:
            problems.append(f"SKILL.md reference must be one level deep: {target}")

    ref_dir = SKILL_DIR / "references"
    for path in sorted(ref_dir.rglob("*")):
        if path.is_dir():
            problems.append(f"references/ must be flat, found directory: {rel(path)}")
            continue
        if path.resolve() not in linked:
            problems.append(f"reference is never linked from SKILL.md: {rel(path)}")
        for target in MD_LINK_RE.findall(read(path)):
            if is_external(target):
                continue
            if not (path.parent / target).resolve().exists():
                problems.append(f"{rel(path)} links to a missing file: {target}")
    return problems


@check("codex-packaging", "agents/openai.yaml uses Codex's supported interface schema")
def check_codex_packaging() -> list[str]:
    problems = []
    path = SKILL_DIR / "agents" / "openai.yaml"
    text = read(path)
    top_level = re.findall(r"^([a-z_]+):\s*$", text, re.M)
    if "interface" not in top_level:
        return ["openai.yaml is missing the top-level 'interface:' mapping"]
    for key in sorted(set(top_level) - {"interface", "dependencies", "policy"}):
        problems.append(f"openai.yaml has unsupported top-level key {key!r}")

    match = re.search(
        r"^interface:\s*\n(?P<body>(?:^[ \t]+.*(?:\n|$))*)", text, re.M
    )
    if not match:
        return problems + ["openai.yaml has no readable interface mapping"]

    fields: dict[str, str] = {}
    for number, line in enumerate(match.group("body").splitlines(), start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            problems.append(f"openai.yaml line {number} is not a key/value pair: {stripped!r}")
            continue
        key, _, value = stripped.partition(":")
        value = value.strip()
        if not (len(value) >= 2 and value[0] == '"' and value[-1] == '"'):
            problems.append(f"openai.yaml value for {key.strip()!r} must be a quoted string")
            continue
        fields[key.strip()] = value[1:-1]

    for key in ("display_name", "short_description", "default_prompt"):
        if key not in fields:
            problems.append(f"openai.yaml is missing {key!r}")

    short = fields.get("short_description", "")
    if short and not 25 <= len(short) <= 64:
        problems.append(f"short_description is {len(short)} chars; it must be 25-64")

    prompt = fields.get("default_prompt", "")
    if prompt:
        if f"${SKILL_NAME}" not in prompt:
            problems.append(f"default_prompt must mention ${SKILL_NAME}")
        sentences = [part for part in re.split(r"[.!?]+", prompt) if part.strip()]
        if len(sentences) != 1:
            problems.append("default_prompt must be exactly one sentence")
    return problems


@check("markdown-links", "every relative Markdown link resolves")
def check_markdown_links() -> list[str]:
    problems = []
    for path in text_files():
        if path.suffix != ".md":
            continue
        for target in MD_LINK_RE.findall(read(path)):
            if is_external(target):
                continue
            clean = target.split("#", 1)[0]
            if not clean:
                continue
            if not (path.parent / clean).resolve().exists():
                problems.append(f"{rel(path)} links to a missing path: {target}")
    return problems


@check("html-basics", "each page has the metadata a shared link needs")
def check_html_basics() -> list[str]:
    problems = []
    for path in html_files():
        text = read(path)
        name = rel(path)
        if not text.lower().startswith("<!doctype html>"):
            problems.append(f"{name} does not start with <!doctype html>")
        if '<html lang="en">' not in text:
            problems.append(f"{name} is missing <html lang=\"en\">")
        if '<meta charset="utf-8">' not in text:
            problems.append(f"{name} is missing a charset declaration")
        if 'name="viewport"' not in text:
            problems.append(f"{name} is missing a viewport meta tag")
        if 'name="description"' not in text:
            problems.append(f"{name} is missing a description meta tag")
        if f'<link rel="canonical" href="{SITE_BASE}"' not in text:
            problems.append(f"{name} is missing the canonical link to {SITE_BASE}")
        if 'name="theme-color"' not in text:
            problems.append(f"{name} is missing a theme-color")
        if "<title>" not in text:
            problems.append(f"{name} is missing a title")
        headings = re.findall(r"<h1\b", text)
        if len(headings) != 1:
            problems.append(f"{name} has {len(headings)} <h1> elements, expected exactly 1")
        for img in re.findall(r"<img\b[^>]*>", text):
            if "alt=" not in img:
                problems.append(f"{name} has an <img> without alt text")
        for svg in re.findall(r"<svg\b[^>]*>", text):
            if 'aria-hidden="true"' not in svg and "role=" not in svg:
                problems.append(f"{name} has an <svg> that is neither decorative nor labelled")
    index = read(DOCS / "index.html")
    if 'class="skip-link"' not in index:
        problems.append("index.html has no skip link")
    if 'href="#main"' not in index:
        problems.append("index.html skip link does not target #main")
    return problems


@check("html-anchors", "every referenced id exists on the page")
def check_html_anchors() -> list[str]:
    problems = []
    for path in html_files():
        text = read(path)
        name = rel(path)
        ids = set(re.findall(r'\bid="([^"]+)"', text))
        for target in LINK_RE.findall(text):
            if target.startswith("#") and len(target) > 1:
                if target[1:] not in ids:
                    problems.append(f"{name} links to #{target[1:]} which does not exist")
        for attribute in ("aria-labelledby", "aria-controls", "aria-describedby"):
            for value in re.findall(rf'{attribute}="([^"]+)"', text):
                for token in value.split():
                    if token not in ids:
                        problems.append(f"{name} {attribute} points at missing id: {token}")
    return problems


@check("base-paths", "nothing depends on being served from the domain root")
def check_base_paths() -> list[str]:
    problems = []
    for path in sorted(DOCS.rglob("*")):
        if path.is_dir() or path.suffix not in {".html", ".css", ".js", ".webmanifest"}:
            continue
        text = read(path)
        for target in LINK_RE.findall(text):
            if target.startswith("/") and not target.startswith("//"):
                problems.append(f"{rel(path)} uses a root-relative path: {target}")
        for target in re.findall(r"url\(\s*['\"]?([^'\")]+)", text):
            if target.startswith("/") and not target.startswith("//"):
                problems.append(f"{rel(path)} uses a root-relative url(): {target}")
    manifest = json.loads(read(DOCS / "manifest.webmanifest"))
    for key in ("start_url", "scope"):
        if manifest.get(key, "").startswith("/"):
            problems.append(f"manifest {key} must be relative, found {manifest[key]!r}")
    for icon in manifest.get("icons", []):
        if icon.get("src", "").startswith("/"):
            problems.append(f"manifest icon src must be relative, found {icon['src']!r}")
    return problems


@check("local-assets", "every local asset a page references exists")
def check_local_assets() -> list[str]:
    problems = []
    for path in sorted(DOCS.rglob("*")):
        if path.is_dir() or path.suffix not in {".html", ".css", ".js"}:
            continue
        for target in LINK_RE.findall(read(path)):
            if is_external(target):
                continue
            clean = target.split("#", 1)[0].split("?", 1)[0]
            if not clean:
                continue
            resolved = (path.parent / clean).resolve()
            if clean.endswith("/") or resolved.is_dir():
                resolved = resolved / "index.html"
            if not resolved.exists():
                problems.append(f"{rel(path)} references a missing asset: {target}")
    manifest = json.loads(read(DOCS / "manifest.webmanifest"))
    for icon in manifest.get("icons", []):
        if not (DOCS / icon["src"]).exists():
            problems.append(f"manifest icon does not exist: {icon['src']}")
    return problems


@check("no-remote-deps", "the site loads nothing from a third party at runtime")
def check_no_remote_deps() -> list[str]:
    problems = []
    allowed_rels = {"canonical", "alternate"}
    for path in html_files():
        text = read(path)
        for tag in re.findall(r"<script\b[^>]*>", text):
            match = re.search(r'src\s*=\s*["\']([^"\']+)', tag)
            if match and match.group(1).startswith(("http", "//")):
                problems.append(f"{rel(path)} loads a remote script: {match.group(1)}")
        for tag in re.findall(r"<link\b[^>]*>", text):
            href = re.search(r'href\s*=\s*["\']([^"\']+)', tag)
            rel_attr = re.search(r'rel\s*=\s*["\']([^"\']+)', tag)
            if not href or not href.group(1).startswith(("http", "//")):
                continue
            if not rel_attr or rel_attr.group(1) not in allowed_rels:
                problems.append(f"{rel(path)} loads a remote stylesheet or resource: {href.group(1)}")
        if re.search(r"<iframe\b", text):
            problems.append(f"{rel(path)} embeds an iframe")
    for path in sorted(DOCS.rglob("*.css")):
        if "@import" in read(path):
            problems.append(f"{rel(path)} uses @import")
    for path in sorted(DOCS.rglob("*.js")):
        text = read(path)
        for banned in ("fetch(", "XMLHttpRequest", "importScripts", "localStorage", "document.cookie"):
            if banned in text:
                problems.append(f"{rel(path)} uses {banned}, which the site claims not to do")
    return problems


@check("site-metadata", "robots, sitemap, and manifest agree with the canonical URL")
def check_site_metadata() -> list[str]:
    problems = []
    robots = read(DOCS / "robots.txt")
    if "User-agent: *" not in robots:
        problems.append("robots.txt has no User-agent rule")
    expected_sitemap = f"Sitemap: {SITE_BASE}sitemap.xml"
    if expected_sitemap not in robots:
        problems.append(f"robots.txt must contain {expected_sitemap!r}")

    tree = ET.parse(DOCS / "sitemap.xml")
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locs = [node.text or "" for node in tree.getroot().iter(f"{namespace}loc")]
    if not locs:
        problems.append("sitemap.xml lists no URLs")
    for loc in locs:
        if not loc.startswith(SITE_BASE):
            problems.append(f"sitemap URL is outside the site: {loc}")
            continue
        suffix = loc[len(SITE_BASE) :]
        target = DOCS / (suffix if suffix else "index.html")
        if not target.exists():
            problems.append(f"sitemap URL has no file behind it: {loc}")
    if not (DOCS / ".nojekyll").exists():
        problems.append("docs/.nojekyll is missing; GitHub Pages would run Jekyll")

    manifest = json.loads(read(DOCS / "manifest.webmanifest"))
    for key in ("name", "short_name", "description", "start_url", "icons", "theme_color"):
        if key not in manifest:
            problems.append(f"manifest is missing {key!r}")
    return problems


@check("homepage-focus", "the public homepage stays short and centred on the core workflow")
def check_homepage_focus() -> list[str]:
    problems = []
    text = read(DOCS / "index.html")
    main = re.search(r"<main\b[^>]*>(.*?)</main>", text, re.S)
    if not main:
        return ["index.html has no main content"]

    visible = strip_tags(main.group(1))
    words = re.findall(r"\b[\w’'-]+\b", visible)
    if len(words) > 900:
        problems.append(f"homepage main copy is {len(words)} words; keep it at or below 900")
    sections = len(re.findall(r"<section\b", main.group(1)))
    if sections > 6:
        problems.append(f"homepage has {sections} main sections; keep it at or below 6")

    for required in (
        'class="memory-demo"',
        "It remembers. You decide what starts.",
        "Captures every ask",
        "Shows it once per turn",
        "Suggests one next move",
        "Keeps a full ledger",
        "The list belongs to you.",
        "Install the skill",
    ):
        if required not in text:
            problems.append(f"homepage no longer carries its core message: {required!r}")
    if 'id="ledger-data"' in text or 'id="demo-toggle"' in text:
        problems.append("homepage has regained the old multi-turn interactive demo")

    # The demo reply is the product promise in miniature: one item, a reason,
    # and a link — never the list, a count, or a done pile.
    demo = re.search(r'<div class="memory-demo".*?<p class="demo-rule">', text, re.S)
    if not demo:
        problems.append("homepage has no memory demo block")
    else:
        block = demo.group(0)
        shown = sorted(set(re.findall(r"OI-\d+", block)))
        if len(shown) != 1:
            problems.append(
                f"the homepage demo reply shows {len(shown)} items ({', '.join(shown)}); it shows one"
            )
        for banned, why in (
            ("<ul", "a list"),
            ("<li", "a list row"),
            (MIDDOT, "a counts line"),
            ("~~", "a struck-through Done item"),
            ("Done", "a Done section"),
            ('class="reply-title"', "a heading row"),
            (">Outstanding<", "the retired Outstanding heading"),
        ):
            if banned in block:
                problems.append(f"the homepage demo reply still shows {why}: {banned!r}")
        for required in (
            'class="reply-item"',
            'class="reply-reason"',
            'class="reply-link"',
            "Full outstanding items",
        ):
            if required not in block:
                problems.append(f"the homepage demo reply is missing {required!r}")
    return problems


@check("footer-once-per-turn", "the footer is taught as final-response-only, never per reply")
def check_footer_once_per_turn() -> list[str]:
    """Regression guard for a live failure.

    An earlier contract said 'append the footer to every user-facing response',
    and a task rendered a full Outstanding block in fifty-five commentary and
    progress messages before its answer. No shipped file may teach that again,
    and every surface must say that commentary carries no footer at all.
    """
    problems = []
    per_reply = re.compile(r"every\s+(?:user-facing\s+)?(?:reply|response|message)", re.I)
    for path in text_files():
        if rel(path) in POLICY_EXEMPT:
            continue
        for number, line in enumerate(read(path).splitlines(), start=1):
            if "footer" not in line.lower() and "**outstanding**" not in line.lower():
                continue
            found = per_reply.search(line)
            if found:
                problems.append(
                    f"{rel(path)}:{number} still teaches a footer in {found.group(0)!r}; "
                    "it belongs only in the final response of a turn"
                )

    # Phrases are matched against whitespace-collapsed text, so a rule that
    # wraps across lines in a copyable snippet still counts.
    required = {
        "skill/outstanding-items/SKILL.md": [
            "final response of the turn",
            "One recommendation per turn, in the final response only",
            "Never put it in commentary, progress notes",
            "carry no recommendation, item, count, or link",
        ],
        "AGENTS.md": ["final response of the turn", "commentary, progress notes"],
        "CLAUDE.md": ["final response of the turn", "commentary, progress notes"],
        "README.md": ["once, in the final response", "One footer per turn"],
        "docs/index.html": ["Shows it once per turn", "Never repeated through progress messages"],
        "examples/global-rules/codex-agents-md.md": [
            "final response of the turn",
            "commentary",
        ],
        "examples/global-rules/claude-code-claude-md.md": [
            "final response of the turn",
            "commentary",
        ],
        "examples/global-rules/project-instructions.md": [
            "final response",
            "Commentary and progress messages carry none of it",
        ],
        "examples/transcript.md": [
            "No recommendation block here",
            "This is commentary, and the ledger stays silent until the answer",
        ],
        "skill/outstanding-items/references/worked-examples.md": [
            "once per turn, at the end of the final response",
            "Neither carried a recommendation, count, `OI-n`, or Full outstanding items link",
        ],
        "skill/outstanding-items/references/ledger-ui.md": ["final response of a turn"],
    }
    for name, phrases in required.items():
        text = squash(read(ROOT / name))
        for phrase in phrases:
            if squash(phrase) not in text:
                problems.append(f"{name} no longer carries the final-response rule: {phrase!r}")

    description = frontmatter(read(SKILL_MD))[0].get("description", "")
    if "final response" not in description:
        problems.append("SKILL.md description must say the footer lands in the final response")
    if "single suggested next item" not in description:
        problems.append("SKILL.md description must say the footer names a single suggested item")
    return problems


@check("compact-footer", "every documented footer is one suggested item and nothing else")
def check_compact_footer() -> list[str]:
    """Regression guard for the footer that replaced the multi-section block.

    The old footer carried a counts header, four sections, an overflow row, a
    crossed-out Done pile, and the same link twice. Every documented footer must
    now be at most three lines: one suggested item, an optional line about it,
    and at most one live Full outstanding items link on the last line.
    """
    problems = []
    blocks = footer_blocks()
    with_link = 0
    without_link = 0
    quiet = 0
    quiet_with_link = 0
    waiting_on_you = 0
    statuses: set[str] = set()
    files: set[str] = set()

    for name, number, lines in blocks:
        where = f"{name}:{number}"
        files.add(name)
        body = "\n".join(lines)
        ids = sorted(set(OI_ID_RE.findall(body)))

        if any(not line.strip() for line in lines):
            problems.append(f"{where} splits its footer with a blank line; a footer is one block")
        if len(lines) > 3:
            problems.append(f"{where} is a {len(lines)}-line footer; at most three lines are allowed")

        header = lines[0]
        item = FOOTER_ITEM_RE.match(header)
        if item:
            item_id, title, visible_status = item.groups()
            status = visible_status or "requested"
            statuses.add(status)
            if ids != [item_id]:
                problems.append(
                    f"{where} names {len(ids)} items ({', '.join(ids)}); a footer names exactly one"
                )
            if status not in SUGGESTIBLE_STATUSES:
                problems.append(f"{where} suggests a {status!r} item, which the footer never offers")
            if visible_status == "requested":
                problems.append(f"{where} visibly prints the redundant default status 'requested'")
            if len(title) > 64:
                problems.append(f"{where} uses a {len(title)}-character title; trim it to about 60")
            if status == "waiting-on-you":
                waiting_on_you += 1
        elif FOOTER_QUIET_RE.match(header) or FOOTER_EMPTY_RE.match(header):
            quiet += 1
            if ids:
                problems.append(
                    f"{where} is a no-suggestion footer but still names {', '.join(ids)}"
                )
            if len(lines) > 2:
                problems.append(
                    f"{where} is a no-suggestion footer of {len(lines)} lines; one line plus the link"
                )
        elif header.startswith("**Outstanding**"):
            problems.append(f"{where} still uses the retired counts header: {header!r}")
        else:
            problems.append(f"{where} has an unrecognised footer header: {header!r}")

        for banned, why in (
            ("**Outstanding for you**", "a section heading"),
            ("**Waiting on you**", "a section heading"),
            ("**Intentional reminders**", "a section heading"),
            ("**Done**", "a Done section"),
            ("**Suggested for you**", "the retired Suggested for you label"),
            ("~~", "a struck-through Done item"),
            ("[done]", "a Done marker"),
            (MIDDOT, "a counts separator"),
        ):
            if banned in body:
                problems.append(f"{where} carries {why} in the footer: {banned!r}")
        if OVERFLOW_RE.search(body):
            problems.append(f"{where} keeps an overflow row; the rest of the list lives in the UI")
        for line in lines[1:]:
            if LIST_ROW_RE.match(line):
                problems.append(f"{where} puts a list row inside the footer: {line!r}")

        mentions = body.count("[Full outstanding items](")
        link_positions = [
            index for index, line in enumerate(lines) if FOOTER_LINK_RE.match(line.strip())
        ]
        if mentions > 1:
            problems.append(
                f"{where} links Full outstanding items {mentions} times; the footer carries it once"
            )
        if mentions and (len(link_positions) != 1 or link_positions[0] != len(lines) - 1):
            problems.append(
                f"{where} must carry the Full outstanding items link alone on the footer's last line"
            )
        if link_positions:
            target = FOOTER_LINK_RE.match(lines[link_positions[-1]].strip()).group(1)
            if target.endswith((".json", ".md")):
                problems.append(f"{where} points the footer link at {target}")
            with_link += 1
            if not item:
                quiet_with_link += 1
        else:
            without_link += 1

    if len(blocks) < 20:
        problems.append(
            f"only {len(blocks)} documented footers; the fixtures must show the contract end to end"
        )
    if with_link < 8:
        problems.append(f"only {with_link} footer(s) demonstrate the live Full outstanding items link")
    if without_link < 8:
        problems.append(f"only {without_link} footer(s) demonstrate the no-live-URL case")
    if quiet < 4:
        problems.append(f"only {quiet} footer(s) demonstrate having nothing to suggest")
    if quiet_with_link < 2 or quiet - quiet_with_link < 2:
        problems.append("the no-suggestion footer must be shown both with and without a live link")
    if waiting_on_you < 4:
        problems.append(f"only {waiting_on_you} footer(s) suggest a waiting-on-you item")
    if len(statuses) < 4:
        problems.append(f"documented footers show only {len(statuses)} status(es); show the range")
    for name in (
        "skill/outstanding-items/SKILL.md",
        "skill/outstanding-items/references/worked-examples.md",
        "skill/outstanding-items/references/next-action.md",
        "examples/transcript.md",
        "README.md",
    ):
        if name not in files:
            problems.append(f"{name} documents no compact recommendation")

    skill = read(SKILL_MD)
    for phrase in (
        "At most three lines",
        "**Exactly one item.**",
        "**No Done section, ever.**",
        "**Never repeat a suggestion the user ignored, declined, or has not answered.**",
        "Add proactively only when genuinely useful",
        "inline-code source marker",
        "Nothing new to suggest",
        "**No outstanding items**",
        "never let it become the footer's suggestion",
        "A `blocked` item is never suggested",
    ):
        if phrase not in skill:
            problems.append(f"SKILL.md no longer states the compact-footer rule: {phrase!r}")

    for path in text_files():
        if rel(path) in POLICY_EXEMPT:
            continue
        text = read(path)
        for pattern, why in STALE_FOOTER_PROMISES:
            found = pattern.search(text)
            if found:
                problems.append(f"{rel(path)} still promises {why}: {found.group(0)!r}")
    return problems


@check("full-outstanding-items-link", "the live UI link is labelled once, on the footer's last line")
def check_full_outstanding_items_link() -> list[str]:
    problems = []
    for path in text_files():
        if rel(path) in POLICY_EXEMPT:
            continue
        text = read(path)
        if "[Full ledger](" in text:
            problems.append(f"{rel(path)} still links the old 'Full ledger' label")
        for target in re.findall(r"\[Full outstanding items\]\(([^)]*)\)", text):
            if target.endswith(".json") or target.endswith(".md"):
                problems.append(f"{rel(path)} points a Full outstanding items link at {target}")

    skill = read(SKILL_MD)
    for phrase in (
        "The Full outstanding items link appears once, or not at all",
        "as the last line of the footer",
        "write no link line at all",
        "never invent a URL",
        "never link raw JSON or Markdown",
    ):
        if phrase not in skill:
            problems.append(f"SKILL.md no longer states the link rule: {phrase!r}")

    ui_reference = read(SKILL_DIR / "references" / "ledger-ui.md")
    for phrase in ("once, as the final line of the footer", "write no link line at all"):
        if phrase not in ui_reference:
            problems.append(f"ledger-ui.md no longer states the link rule: {phrase!r}")

    # Every documented footer that carries the link must carry exactly one, and
    # every URL inside one footer must be the same URL.
    demonstrated = 0
    for name, number, lines in footer_blocks():
        block = "\n".join(lines)
        urls = set(re.findall(r"\[Full outstanding items\]\(([^)]+)\)", block))
        if not urls:
            continue
        demonstrated += 1
        if len(urls) != 1:
            problems.append(f"{name}:{number} mixes {len(urls)} different UI URLs in one footer")
        if not lines[-1].strip().startswith("[Full outstanding items]("):
            problems.append(f"{name}:{number} does not end with the Full outstanding items link")
    if demonstrated < 8:
        problems.append(
            f"only {demonstrated} worked footer(s) demonstrate the link; the contract needs at least 8"
        )

    for name in (
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
        "examples/global-rules/codex-agents-md.md",
        "examples/global-rules/claude-code-claude-md.md",
        "examples/global-rules/project-instructions.md",
    ):
        text = squash(read(ROOT / name))
        if "Full outstanding items" not in text:
            problems.append(f"{name} does not name the Full outstanding items link")
        if "footer's last line" not in text and "on the last line" not in text:
            problems.append(f"{name} does not place the link on the footer's last line")
        if "and again after" in text:
            problems.append(f"{name} still asks for the link twice")
    return problems


@check("item-explanations", "every item can carry a plain-language tooltip explanation")
def check_item_explanations() -> list[str]:
    problems = []
    assets = SKILL_DIR / "assets"
    html_text = read(assets / "ledger.html")
    script = read(assets / "ledger.js")
    style = read(assets / "ledger.css")
    runtime = read(SKILL_DIR / "scripts" / "ledger_ui.py")

    for fragment in ('class="item-tooltip"', 'role="tooltip"', "item-tooltip-label", "item-tooltip-text"):
        if fragment not in html_text:
            problems.append(f"ledger.html has no tooltip {fragment!r}")
    if "Hovering a task" not in html_text:
        problems.append("ledger.html does not describe the tooltip for assistive technology")

    if "innerHTML" in script or "insertAdjacentHTML" in script:
        problems.append("ledger.js renders markup instead of safe text")
    for fragment in (
        "item.explanation",
        'querySelector(".item-tooltip-text").textContent',
        'querySelector(".item-tooltip-label").textContent',
        'setAttribute("aria-describedby"',
        "tooltip-dismissed",
    ):
        if fragment not in script:
            problems.append(f"ledger.js is missing the tooltip wiring: {fragment!r}")
    for status in STATUSES:
        key = f'"{status}"' if "-" in status else status
        if not re.search(rf"^\s*{re.escape(key)}:", script, re.M):
            problems.append(f"ledger.js has no tooltip fallback sentence for {status!r}")

    for fragment in (".item-tooltip", ":hover .item-tooltip", "focus-visible ~ .item-tooltip"):
        if fragment not in style:
            problems.append(f"ledger.css is missing the tooltip rule: {fragment!r}")

    if "MAX_EXPLANATION_CHARS" not in runtime or '"explanation"' not in runtime:
        problems.append("ledger_ui.py does not validate the explanation field")
    if '"--explanation"' not in runtime:
        problems.append("ledger_ui.py upsert cannot populate an explanation")

    artifact = read(SKILL_DIR / "references" / "backlog-artifact.md")
    if "| `explanation` |" not in artifact:
        problems.append("backlog-artifact.md does not document the explanation field")
    if "Compatibility of `explanation`" not in artifact:
        problems.append("backlog-artifact.md does not document explanation backward compatibility")
    ui_reference = read(SKILL_DIR / "references" / "ledger-ui.md")
    for phrase in ("--explanation", "Writing the explanation", "textContent"):
        if phrase not in ui_reference:
            problems.append(f"ledger-ui.md does not cover: {phrase!r}")

    payload = json.loads(read(ROOT / "examples" / "outstanding-items.json"))
    items = payload.get("items", [])
    written = [item for item in items if item.get("explanation")]
    if not written:
        problems.append("the example ledger shows no item explanation")
    if len(written) == len(items):
        problems.append("the example ledger never shows the older-ledger fallback case")
    for item in written:
        explanation = item["explanation"]
        if len(explanation) > 600:
            problems.append(f"{item['id']} explanation is longer than 600 characters")
        for markup in ("`", "](", "<", "**"):
            if markup in explanation:
                problems.append(f"{item['id']} explanation contains markup: {markup!r}")
    return problems


@check("synthetic-ids", "no real task or session identifier can slip in")
def check_synthetic_ids() -> list[str]:
    problems = []
    field_names = {
        "task_id",
        "task_ids",
        "session_id",
        "session_ids",
        "thread_id",
        "conv_id",
        "task_owned",
        "session_only",
    }
    pattern = re.compile(r"\b(?:task|sess|session|conv|thread)_[A-Za-z0-9][A-Za-z0-9_-]{2,}\b")
    for path in text_files():
        for number, line in enumerate(read(path).splitlines(), start=1):
            for token in pattern.findall(line):
                if token in field_names or "EXAMPLE" in token:
                    continue
                problems.append(
                    f"{rel(path)}:{number} has an identifier that is not marked synthetic: {token}"
                )
    return problems


@check("no-personal-data", "no personal paths, addresses, or credential shapes")
def check_no_personal_data() -> list[str]:
    patterns = [
        (re.compile(r"/Users/[A-Za-z0-9._-]+"), "an absolute macOS home path"),
        (re.compile(r"/home/[A-Za-z0-9._-]+"), "an absolute Linux home path"),
        (re.compile(r"C:\\\\Users\\\\"), "an absolute Windows home path"),
        (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "an email address"),
        (re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"), "an API-key shape"),
        (re.compile(r"\bghp_[A-Za-z0-9]{16,}\b"), "a GitHub token shape"),
        (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "an AWS key shape"),
        (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
        (re.compile(r"\bBearer\s+[A-Za-z0-9._-]{20,}"), "a bearer token"),
    ]
    problems = []
    for path in text_files():
        for number, line in enumerate(read(path).splitlines(), start=1):
            for pattern, label in patterns:
                found = pattern.search(line)
                if found:
                    problems.append(f"{rel(path)}:{number} looks like {label}: {found.group(0)}")
    return problems


@check("honesty", "capability claims stay inside what the software does")
def check_honesty() -> list[str]:
    problems = []
    blocked_phrases = [
        "guaranteed automatic",
        "guarantees automatic",
        "automatically notifies",
        "always invoked",
        "always fires",
        "never fails",
        "100% reliable",
        "zero configuration",
        "runs 24/7",
        "real-time sync",
        "syncs automatically",
        "background service",
        "just works every time",
    ]
    for path in text_files():
        if rel(path) in POLICY_EXEMPT:
            continue
        lowered = read(path).lower()
        for phrase in blocked_phrases:
            if phrase in lowered:
                problems.append(f"{rel(path)} makes an unsupported claim: {phrase!r}")

    required = {
        "README.md": [
            "does not run a background daemon",
            "does not create a cross-task message bus",
            "does not create a persistent database",
            "does not guarantee automatic invocation",
            "no project-owned outbound application requests",
        ],
        "skill/outstanding-items/SKILL.md": [
            "does not start a background daemon",
            "does not create a cross-task message bus",
            "does not create a persistent database",
            "does not guarantee automatic invocation",
        ],
        "docs/index.html": [
            "No cloud account or background daemon",
            "No automatic authority over your work",
            "No promise that every agent harness will invoke a skill perfectly",
        ],
    }
    required["README.md"].append("does not know what you have the appetite for")
    required["skill/outstanding-items/SKILL.md"].append(
        "does not know what the user actually has the appetite for"
    )
    for name, phrases in required.items():
        text = read(ROOT / name)
        for phrase in phrases:
            if phrase not in text:
                problems.append(f"{name} no longer states the limit: {phrase!r}")

    related = read(SKILL_DIR / "references" / "related-tasks.md")
    if "registered (manual)" not in related:
        problems.append("related-tasks.md must define the 'registered (manual)' wording")
    return problems


@check("tagline", "the approved promise appears exactly everywhere")
def check_tagline() -> list[str]:
    problems = []
    for name in ("README.md", "docs/index.html"):
        text = read(ROOT / name)
        if TAGLINE not in text:
            problems.append(f"{name} does not carry the exact tagline {TAGLINE!r}")
    index = read(DOCS / "index.html")
    if f'<h1 id="hero-title">{TAGLINE_1}</h1>' not in index:
        problems.append("the hero <h1> must be exactly the first tagline")
    if f'<p class="hero-title-2">{TAGLINE_2}</p>' not in index:
        problems.append("the hero must carry the second tagline at display size")
    # The two halves must sit together in the hero, not scattered around the page.
    first = index.find(f'<h1 id="hero-title">{TAGLINE_1}</h1>')
    second = index.find(f'<p class="hero-title-2">{TAGLINE_2}</p>')
    if first == -1 or second == -1 or not 0 < second - first < 200:
        problems.append("the second tagline must directly follow the hero heading")
    return problems


@check("scripts-safe", "install and uninstall stay non-destructive and dry-runnable")
def check_scripts_safe() -> list[str]:
    problems = []
    for name in ("install.sh", "uninstall.sh", "check.sh", "serve.sh"):
        text = read(ROOT / "scripts" / name)
        if not text.startswith("#!/bin/sh"):
            problems.append(f"scripts/{name} has no POSIX shell shebang")
        if "set -eu" not in text:
            problems.append(f"scripts/{name} does not use 'set -eu'")
        for dangerous in ("rm -rf", "rm -fr", "rm -r ", "rm -Rf"):
            if dangerous in text:
                problems.append(f"scripts/{name} contains a recursive delete: {dangerous!r}")
        if "--help" not in text:
            problems.append(f"scripts/{name} has no --help")
        if "curl" in text or "wget" in text:
            problems.append(f"scripts/{name} appears to reach the network")
    for name in ("install.sh", "uninstall.sh"):
        text = read(ROOT / "scripts" / name)
        if "--dry-run" not in text:
            problems.append(f"scripts/{name} has no --dry-run")
        if "valid_relpath" not in text:
            problems.append(f"scripts/{name} does not validate the paths it touches")
        if "reject_symlink_chain" not in text:
            problems.append(f"scripts/{name} does not reject symbolic-link traversal")
    if "changed after installation; keeping it" not in read(ROOT / "scripts" / "uninstall.sh"):
        problems.append("scripts/uninstall.sh does not preserve modified installed files")
    return problems


@check("installer-behavior", "install, conflict, force, and uninstall rules work in a temp root")
def check_installer_behavior() -> list[str]:
    problems = []
    install = ROOT / "scripts" / "install.sh"
    uninstall = ROOT / "scripts" / "uninstall.sh"

    def run(script: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", str(script), *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    with tempfile.TemporaryDirectory(prefix="outstanding-items-test-") as temp:
        base = pathlib.Path(temp)

        dry_root = base / "dry-root"
        result = run(install, "--dest", str(dry_root), "--dry-run")
        if result.returncode != 0:
            problems.append(f"installer dry run failed: {result.stdout.strip()}")
        if dry_root.exists():
            problems.append("installer dry run created its destination")

        root = base / "install-root"
        result = run(install, "--dest", str(root))
        target = root / "skills" / SKILL_NAME
        if result.returncode != 0:
            problems.append(f"fresh install failed: {result.stdout.strip()}")
            return problems
        if not (target / ".install-manifest").is_file():
            problems.append("fresh install did not create its ownership manifest")
        if any(path.suffix == ".pyc" or "__pycache__" in path.parts for path in target.rglob("*")):
            problems.append("installer copied generated Python bytecode")
        for source in sorted(SKILL_DIR.rglob("*")):
            if source.is_dir() or "__pycache__" in source.parts or source.suffix == ".pyc":
                continue
            relative = source.relative_to(SKILL_DIR)
            copy = target / relative
            if not copy.is_file() or copy.read_bytes() != source.read_bytes():
                problems.append(f"installed copy differs: {relative}")

        result = run(install, "--dest", str(root))
        if result.returncode != 0 or "unchanged" not in result.stdout:
            problems.append("second install was not idempotent")

        installed_skill = target / "SKILL.md"
        modified = installed_skill.read_text(encoding="utf-8") + "\n<!-- local edit -->\n"
        installed_skill.write_text(modified, encoding="utf-8")
        result = run(install, "--dest", str(root))
        if result.returncode != 1 or installed_skill.read_text(encoding="utf-8") != modified:
            problems.append("installer did not preserve a local edit without --force")
        result = run(install, "--dest", str(root), "--force")
        if result.returncode != 0 or installed_skill.read_bytes() != SKILL_MD.read_bytes():
            problems.append("installer --force did not restore the canonical source")

        deprecated = target / "references" / "curation.md"
        deprecated.write_text("known deprecated owned file\n", encoding="utf-8")
        result = run(install, "--dest", str(root), "--dry-run")
        if result.returncode != 0 or not deprecated.is_file() or "known deprecated owned file" not in result.stdout:
            problems.append("installer dry run did not safely report the deprecated-file migration")
        result = run(install, "--dest", str(root))
        if result.returncode != 0 or deprecated.exists():
            problems.append("installer did not remove a known deprecated owned file")

        extra = target / "references" / "my-note.md"
        extra.write_text("keep me\n", encoding="utf-8")
        result = run(uninstall, "--dest", str(root), "--dry-run")
        if result.returncode != 0 or not installed_skill.exists():
            problems.append("uninstaller dry run changed or rejected a valid install")
        result = run(uninstall, "--dest", str(root))
        if result.returncode != 0 or not extra.is_file():
            problems.append("uninstaller did not preserve an unrecognised user file")
        if installed_skill.exists() or (target / ".install-manifest").exists():
            problems.append("uninstaller left hash-matching owned files behind")

        edited_root = base / "edited-root"
        result = run(install, "--dest", str(edited_root))
        edited_target = edited_root / "skills" / SKILL_NAME
        edited_skill = edited_target / "SKILL.md"
        edited_skill.write_text(
            edited_skill.read_text(encoding="utf-8") + "\n<!-- keep this edit -->\n",
            encoding="utf-8",
        )
        result = run(uninstall, "--dest", str(edited_root))
        if result.returncode != 1 or not edited_skill.is_file():
            problems.append("uninstaller removed or accepted a modified installed file")
        if not (edited_target / ".install-manifest").is_file():
            problems.append("uninstaller discarded the manifest after a modified-file conflict")

        manual_root = base / "manual-root"
        manual_target = manual_root / "skills" / SKILL_NAME
        manual_target.mkdir(parents=True)
        manual_file = manual_target / "SKILL.md"
        manual_file.write_text("manual\n", encoding="utf-8")
        result = run(uninstall, "--dest", str(manual_root))
        if result.returncode != 1 or not manual_file.is_file():
            problems.append("uninstaller guessed ownership when the manifest was missing")

        outside = base / "outside"
        outside.mkdir()
        linked_root = base / "linked-root"
        linked_root.symlink_to(outside, target_is_directory=True)
        result = run(install, "--dest", str(linked_root))
        if result.returncode != 1 or (outside / "skills").exists():
            problems.append("installer followed a symbolic-link destination")

    return problems


@check("license", "the licence is MIT and is referenced")
def check_license() -> list[str]:
    problems = []
    text = read(ROOT / "LICENSE")
    if "MIT License" not in text:
        problems.append("LICENSE is not the MIT licence")
    if "Copyright (c)" not in text:
        problems.append("LICENSE has no copyright line")
    if "MIT" not in read(ROOT / "README.md"):
        problems.append("README.md does not mention the licence")
    return problems


@check("hygiene", "text files are UTF-8, LF, and newline-terminated")
def check_hygiene() -> list[str]:
    problems = []
    for path in text_files():
        data = path.read_bytes()
        if not data:
            continue
        if data.startswith(b"\xef\xbb\xbf"):
            problems.append(f"{rel(path)} starts with a byte-order mark")
        if b"\r\n" in data:
            problems.append(f"{rel(path)} has CRLF line endings")
        if not data.endswith(b"\n"):
            problems.append(f"{rel(path)} does not end with a newline")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"{rel(path)} is not valid UTF-8")
    return problems


@check("docs-consistency", "the README and the site describe the same product")
def check_docs_consistency() -> list[str]:
    problems = []
    readme = read(ROOT / "README.md")
    index = read(DOCS / "index.html")
    for status in STATUSES:
        if status not in readme:
            problems.append(f"README.md does not document the {status!r} label")
    for summary in ("stable ID", "honest status", "Read the full documentation"):
        if summary not in index:
            problems.append(f"docs/index.html no longer links the simple story to detail: {summary!r}")
    for name in ("AGENTS.md", "CLAUDE.md"):
        text = read(ROOT / name)
        if "~/.codex" not in text and "~/.claude" not in text:
            problems.append(f"{name} does not say where the skill is installed")
        if "outstanding-items" not in text:
            problems.append(f"{name} does not name the skill")
    if REPO_URL not in index:
        problems.append("docs/index.html does not link to the repository")
    if SITE_BASE not in readme:
        problems.append("README.md does not link to the website")
    return problems


@check("installed-copies", "installed skills match this checkout (only with --installed)")
def check_installed_copies() -> list[str]:
    if not INSPECT_INSTALLED:
        return []
    problems = []
    home = pathlib.Path.home()
    found = False
    for harness in ("codex", "claude"):
        target = home / f".{harness}" / "skills" / SKILL_NAME
        if not target.exists():
            print(f"   note  {harness}: not installed at {target}")
            continue
        found = True
        expected = {
            source.relative_to(SKILL_DIR)
            for source in SKILL_DIR.rglob("*")
            if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc"
        }
        for source in sorted(SKILL_DIR.rglob("*")):
            if source.is_dir() or "__pycache__" in source.parts or source.suffix == ".pyc":
                continue
            relative = source.relative_to(SKILL_DIR)
            copy = target / relative
            if not copy.exists():
                problems.append(f"{harness}: missing {relative}")
            elif copy.read_bytes() != source.read_bytes():
                problems.append(f"{harness}: {relative} differs from this checkout")
        actual = {
            path.relative_to(target)
            for path in target.rglob("*")
            if path.is_file() and path.name != ".install-manifest"
        }
        for extra in sorted(actual - expected):
            problems.append(f"{harness}: extra installed file outside the canonical manifest: {extra}")
    if not found:
        print("   note  the skill is not installed anywhere; run scripts/install.sh")
    return problems


INSPECT_INSTALLED = False


def main(argv: list[str]) -> int:
    global INSPECT_INSTALLED
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed", action="store_true", help="also inspect installed copies")
    parser.add_argument("--list", action="store_true", help="list the checks and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="print every check")
    args = parser.parse_args(argv)
    INSPECT_INSTALLED = args.installed

    if args.list:
        for name, description, _ in CHECKS:
            print(f"{name:20s} {description}")
        return 0

    failed = 0
    for name, description, fn in CHECKS:
        problems = fn()
        if problems:
            failed += 1
            print(f"   FAIL  {name}: {description}")
            for problem in problems:
                print(f"         - {problem}")
        elif args.verbose:
            print(f"   ok    {name}: {description}")

    total = len(CHECKS)
    if failed:
        print(f"\n{failed} of {total} checks failed.")
        return 1
    print(f"   ok    {total} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
