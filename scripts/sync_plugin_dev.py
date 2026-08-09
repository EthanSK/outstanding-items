#!/usr/bin/env python3
"""Validate and reinstall the local Outstanding Items plugin in one command.

The authored manifests keep their release version. During installation this
script temporarily adds a Codex cachebuster to both manifests, asks the Codex
CLI to install that exact local version, then restores the authored bytes.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN_NAME = "outstanding-items"
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_ROOT = ROOT / "plugins" / PLUGIN_NAME
CODEX_MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
CLAUDE_MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
STANDALONE_SKILL = pathlib.Path.home() / ".codex" / "skills" / PLUGIN_NAME


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run repository checks, cache-bust and reinstall the local Codex plugin, "
            "then verify the installed version while leaving source manifests unchanged."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan without running checks or changing Codex state.",
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip scripts/check.sh for a faster repeat iteration.",
    )
    parser.add_argument(
        "--cachebuster",
        help="Use a deterministic cachebuster token instead of the current UTC timestamp.",
    )
    parser.add_argument(
        "--remove-standalone",
        action="store_true",
        help=(
            "After plugin verification, run the manifest-scoped uninstaller for the "
            "standalone Codex skill. Modified or unowned files are preserved."
        ),
    )
    parser.add_argument(
        "--codex-bin",
        default="codex",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def load_object(path: pathlib.Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def sanitize_cachebuster(value: str) -> str:
    sanitized = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower())
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")
    if not sanitized:
        raise ValueError("cachebuster must contain at least one letter or digit")
    return sanitized


def next_dev_version(version: str, cachebuster: str) -> str:
    base = version.split("+", 1)[0]
    return f"{base}+codex.{sanitize_cachebuster(cachebuster)}"


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(command))
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=True,
    )


def marketplace_name() -> str:
    payload = load_object(MARKETPLACE_PATH)
    name = payload.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"{MARKETPLACE_PATH} must contain a non-empty marketplace name")
    return name


def marketplace_is_configured(payload: object, name: str) -> bool:
    if not isinstance(payload, dict) or not isinstance(payload.get("marketplaces"), list):
        raise ValueError("Codex returned an unexpected marketplace list")

    wanted_root = ROOT.resolve()
    for entry in payload["marketplaces"]:
        if not isinstance(entry, dict):
            continue
        entry_name = entry.get("name")
        raw_root = entry.get("root")
        if entry_name == name and isinstance(raw_root, str):
            actual_root = pathlib.Path(raw_root).expanduser().resolve()
            if actual_root != wanted_root:
                raise ValueError(
                    f"marketplace {name!r} already points at {actual_root}, not {wanted_root}"
                )
            return True
    return False


def installed_version(payload: object, plugin_id: str) -> str | None:
    if not isinstance(payload, dict) or not isinstance(payload.get("installed"), list):
        raise ValueError("Codex returned an unexpected plugin list")
    for entry in payload["installed"]:
        if isinstance(entry, dict) and entry.get("pluginId") == plugin_id:
            version = entry.get("version")
            return version if isinstance(version, str) else None
    return None


def validate_source() -> tuple[str, str]:
    codex = load_object(CODEX_MANIFEST)
    claude = load_object(CLAUDE_MANIFEST)
    marketplace = marketplace_name()

    if codex.get("name") != PLUGIN_NAME or claude.get("name") != PLUGIN_NAME:
        raise ValueError("both plugin manifests must use the canonical plugin name")
    codex_version = codex.get("version")
    claude_version = claude.get("version")
    if not isinstance(codex_version, str) or not codex_version:
        raise ValueError("OpenAI plugin manifest has no version")
    if codex_version != claude_version:
        raise ValueError("OpenAI and Claude Code plugin versions are not synchronized")
    return codex_version, marketplace


def write_temporary_version(version: str) -> dict[pathlib.Path, bytes]:
    originals: dict[pathlib.Path, bytes] = {}
    for path in (CODEX_MANIFEST, CLAUDE_MANIFEST):
        originals[path] = path.read_bytes()
        payload = load_object(path)
        payload["version"] = version
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return originals


def restore_manifests(originals: dict[pathlib.Path, bytes]) -> None:
    for path, content in originals.items():
        path.write_bytes(content)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    args = parse_args()
    source_version, market_name = validate_source()
    token = args.cachebuster or datetime.now(timezone.utc).strftime("local-%Y%m%d%H%M%S")
    dev_version = next_dev_version(source_version, token)
    plugin_id = f"{PLUGIN_NAME}@{market_name}"

    print(f"Repository: {ROOT}")
    print(f"Marketplace: {market_name}")
    print(f"Plugin: {plugin_id}")
    print(f"Source version: {source_version}")
    print(f"Temporary install version: {dev_version}")
    print("Source manifests will be restored byte-for-byte after installation.")

    if args.dry_run:
        if not args.skip_checks:
            print("+ ./scripts/check.sh")
        print(f"+ {args.codex_bin} plugin marketplace list --json")
        print(f"+ {args.codex_bin} plugin marketplace add {ROOT} --json  # only if missing")
        print(f"+ {args.codex_bin} plugin add {plugin_id} --json")
        print(f"+ {args.codex_bin} plugin list --marketplace {market_name} --json")
        if args.remove_standalone:
            print("+ ./scripts/uninstall.sh --target codex")
        return 0

    codex_bin = shutil.which(args.codex_bin)
    if codex_bin is None:
        raise FileNotFoundError(f"cannot find Codex CLI: {args.codex_bin}")

    if not args.skip_checks:
        run([str(ROOT / "scripts" / "check.sh")])

    listed = run(
        [codex_bin, "plugin", "marketplace", "list", "--json"], capture=True
    )
    if not marketplace_is_configured(json.loads(listed.stdout), market_name):
        run(
            [
                codex_bin,
                "plugin",
                "marketplace",
                "add",
                str(ROOT),
                "--json",
            ]
        )

    originals: dict[pathlib.Path, bytes] = {}
    try:
        originals = write_temporary_version(dev_version)
        run([codex_bin, "plugin", "add", plugin_id, "--json"])
    finally:
        if originals:
            restore_manifests(originals)

    installed = run(
        [
            codex_bin,
            "plugin",
            "list",
            "--marketplace",
            market_name,
            "--json",
        ],
        capture=True,
    )
    actual_version = installed_version(json.loads(installed.stdout), plugin_id)
    if actual_version != dev_version:
        raise RuntimeError(
            f"installed version mismatch: expected {dev_version}, found {actual_version or 'none'}"
        )

    print(f"Verified installed plugin: {plugin_id} {actual_version}")

    if args.remove_standalone and STANDALONE_SKILL.exists():
        run([str(ROOT / "scripts" / "uninstall.sh"), "--target", "codex"])
        if STANDALONE_SKILL.exists():
            raise RuntimeError(
                "standalone skill remains because the safe uninstaller preserved unowned or "
                "modified files"
            )
        print("Verified standalone Codex skill removal.")
    elif STANDALONE_SKILL.exists():
        print(
            "Standalone Codex skill still exists. Re-run with --remove-standalone only after "
            "the plugin works in a fresh task."
        )

    print("Start a new Codex task to load the refreshed plugin.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
