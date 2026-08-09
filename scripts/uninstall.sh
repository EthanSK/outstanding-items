#!/bin/sh
# Remove a legacy standalone outstanding-items skill installed by releases that
# predate plugin-only distribution.
# Only files listed in the install manifest are removed. Directories are removed
# only when they are already empty. There is no recursive delete anywhere here.
set -eu

SKILL_NAME="outstanding-items"
MANIFEST_FILE=".install-manifest"

TARGET="auto"
DEST=""
DRY_RUN=0
QUIET=0
leftovers=0
had_conflict=0

usage() {
  cat <<'EOF'
Usage: scripts/uninstall.sh [options]

Removes a legacy standalone copy installed by an older repository release, and nothing else.

Options:
  --target <auto|codex|claude|both>  Which harness to clean (default: auto).
  --dest <dir>                       Clean <dir>/skills/outstanding-items/.
  --dry-run, -n                      Print what would be removed.
  --quiet, -q                        Only print warnings and errors.
  -h, --help                         Show this help.

Files you added by hand are never removed; they are reported and left in place.
EOF
}

log() {
  [ "$QUIET" -eq 1 ] || printf '%s\n' "$*"
}

warn() {
  printf 'warning: %s\n' "$*" >&2
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

valid_relpath() {
  case "$1" in
    "" | /* | */ | *..* | *//*) return 1 ;;
    *[!A-Za-z0-9._/-]*) return 1 ;;
  esac
  return 0
}

valid_root() {
  case "$1" in
    "" | / | *"/../"* | */.. | *"/./"* | */. | *//* ) return 1 ;;
    /*) return 0 ;;
    *) return 1 ;;
  esac
}

reject_symlink_chain() {
  check_path="$1"
  # The caller checks each path that this uninstaller owns. Platform-managed
  # ancestor aliases such as macOS /var -> /private/var are allowed.
  [ ! -L "$check_path" ] || die "refusing to follow symbolic link: $check_path"
}

hash_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  elif command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 "$1" | awk '{ print $NF }'
  else
    cksum "$1" | awk '{ print $1 "-" $2 }'
  fi
}

while [ $# -gt 0 ]; do
  case "$1" in
    --target)
      [ $# -ge 2 ] || die "--target needs a value"
      TARGET="$2"
      shift 2
      ;;
    --target=*)
      TARGET="${1#--target=}"
      shift
      ;;
    --dest)
      [ $# -ge 2 ] || die "--dest needs a value"
      DEST="$2"
      shift 2
      ;;
    --dest=*)
      DEST="${1#--dest=}"
      shift
      ;;
    --dry-run | -n)
      DRY_RUN=1
      shift
      ;;
    --quiet | -q)
      QUIET=1
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      die "unknown option: $1 (try --help)"
      ;;
  esac
done

case "$TARGET" in
  auto | codex | claude | both) : ;;
  *) die "--target must be auto, codex, claude, or both" ;;
esac

resolve_root() {
  case "$1" in
    codex) printf '%s\n' "$HOME/.codex" ;;
    claude) printf '%s\n' "$HOME/.claude" ;;
    custom) printf '%s\n' "$DEST" ;;
  esac
}

remove_from() {
  label="$1"
  root="$2"

  valid_root "$root" ||
    die "destination root must be an absolute, traversal-free path: $root"
  reject_symlink_chain "$root"
  reject_symlink_chain "$root/skills"

  skill_dir="$root/skills/$SKILL_NAME"
  case "$skill_dir" in
    */skills/"$SKILL_NAME") : ;;
    *) die "refusing to operate on unexpected path: $skill_dir" ;;
  esac
  reject_symlink_chain "$skill_dir"

  log ""
  log "== $label -> $skill_dir"

  if [ ! -d "$skill_dir" ]; then
    log "   not installed"
    return 0
  fi

  manifest="$skill_dir/$MANIFEST_FILE"
  if [ ! -f "$manifest" ]; then
    warn "$skill_dir has no install manifest; refusing to guess what this repository owns."
    had_conflict=1
    return 0
  fi
  rels=$(awk '{ print $2 }' "$manifest" | LC_ALL=C sort)
  log "   using install manifest"

  removed=0
  manifest_clean=1
  for rel in $rels; do
    valid_relpath "$rel" || die "refusing to remove unsafe path: $rel"
    target_file="$skill_dir/$rel"
    if [ -f "$target_file" ]; then
      recorded=$(awk -v want="$rel" '$2 == want { print $1; exit }' "$manifest")
      current=$(hash_file "$target_file")
      if [ -z "$recorded" ] || [ "$current" != "$recorded" ]; then
        warn "$rel changed after installation; keeping it."
        log "   keep    $rel (modified)"
        leftovers=1
        had_conflict=1
        manifest_clean=0
        continue
      fi
      log "   remove  $rel"
      if [ "$DRY_RUN" -eq 0 ]; then
        rm -f "$target_file"
      fi
      removed=$((removed + 1))
    fi
  done

  if [ "$manifest_clean" -eq 1 ] && [ -f "$manifest" ]; then
    log "   remove  $MANIFEST_FILE"
    if [ "$DRY_RUN" -eq 0 ]; then
      rm -f "$skill_dir/$MANIFEST_FILE"
    fi
  fi

  # Report anything we did not put there.
  kept=$(find "$skill_dir" -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "$DRY_RUN" -eq 0 ] && [ "$kept" != "0" ]; then
    leftovers=1
    warn "$skill_dir still contains $kept file(s) this repository did not install. Left in place."
    find "$skill_dir" -type f 2>/dev/null | while read -r f; do
      log "   kept    ${f#"$skill_dir/"}"
    done
  fi

  # Remove directories only if empty. rmdir refuses otherwise, which is exactly
  # the behaviour we want; failures are ignored on purpose.
  if [ "$DRY_RUN" -eq 0 ]; then
    find "$skill_dir" -depth -type d 2>/dev/null | while read -r d; do
      rmdir "$d" 2>/dev/null || true
    done
    parent="$root/skills"
    rmdir "$parent" 2>/dev/null || true
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    log "   -> would remove $removed file(s)"
  else
    log "   -> removed $removed file(s)"
  fi
}

log "outstanding-items uninstaller"
if [ "$DRY_RUN" -eq 1 ]; then
  log "mode: dry run"
fi

if [ -n "$DEST" ]; then
  remove_from "custom" "$DEST"
else
  case "$TARGET" in
    auto)
      for h in codex claude; do
        root=$(resolve_root "$h")
        if [ -d "$root/skills/$SKILL_NAME" ]; then
          remove_from "$h" "$root"
        else
          log ""
          log "== $h -> not installed, skipping"
        fi
      done
      ;;
    codex | claude)
      remove_from "$TARGET" "$(resolve_root "$TARGET")"
      ;;
    both)
      remove_from "codex" "$(resolve_root codex)"
      remove_from "claude" "$(resolve_root claude)"
      ;;
  esac
fi

log ""
if [ "$leftovers" -eq 1 ]; then
  log "Finished. Some files were kept because this repository did not install them."
else
  log "Finished."
fi
[ "$had_conflict" -eq 0 ] || exit 1
exit 0
