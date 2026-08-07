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

# Statuses that retire an item into the crossed-out Done section.
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
    if "latest unanswered suggestion" not in artifact_text or "Clear it after" not in artifact_text:
        problems.append("backlog artifact does not clear accepted, declined, or replaced suggestions")

    next_action = read(SKILL_DIR / "references" / "next-action.md")
    if "OI-9 reads the same token" in next_action:
        problems.append("next-action.md assigns the shared token dependency to OI-9 instead of OI-6")
    if "OI-8 is stuck upstream" in next_action:
        problems.append("next-action.md labels the available user action OI-8 as blocked")
    return problems


@check("public-examples", "copy-paste examples preserve user ownership and schema v3")
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
    for heading in (
        "**Outstanding for you**",
        "**Waiting on you**",
        "**Intentional reminders**",
        "**Done**",
    ):
        if heading not in transcript:
            problems.append(f"transcript.md does not demonstrate {heading}")
    normalized_transcript = re.sub(r"\s+", " ", transcript)
    for required in (
        "No task-triggering send occurred",
        "A priority choice is not a start instruction",
        "The recommendation changes no item, status, order, or execution state",
        "A later turn must receive a new named instruction",
    ):
        if required not in normalized_transcript:
            problems.append(f"transcript.md no longer demonstrates: {required!r}")
    if "- OI-5 Skip link — in-progress" in transcript:
        problems.append("transcript.md leaves a temporary in-progress label in a final reply")
    if "- OI-5 Skip link — implemented" not in transcript:
        problems.append("transcript.md does not reconcile completed turn work to implemented")

    try:
        payload = json.loads(read(ROOT / "examples" / "outstanding-items.json"))
    except json.JSONDecodeError as exc:
        problems.append(f"example backlog JSON is invalid: {exc}")
    else:
        if payload.get("schema_version") != 3:
            problems.append("example backlog JSON must use schema version 3")
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
        "Shows it every reply",
        "Suggests one next move",
        "Keeps a full ledger",
        "The list belongs to you.",
        "Install the skill",
    ):
        if required not in text:
            problems.append(f"homepage no longer carries its core message: {required!r}")
    if 'id="ledger-data"' in text or 'id="demo-toggle"' in text:
        problems.append("homepage has regained the old multi-turn interactive demo")
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
