#!/bin/sh
# Install the canonical skill bundled inside the Outstanding Items plugin into
# a standalone harness skills directory. No network access. No recursive
# deletion. Dry-runnable.
set -eu

SKILL_NAME="outstanding-items"
MANIFEST_FILE=".install-manifest"
DEPRECATED_FILES="references/backlog-format.md
references/curation.md
references/related-task-sync.md"

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$script_dir/.." && pwd)
SRC="$REPO_ROOT/plugins/$SKILL_NAME/skills/$SKILL_NAME"

TARGET="auto"
DEST=""
DRY_RUN=0
FORCE=0
QUIET=0
had_conflict=0
installed_any=0

usage() {
  cat <<'EOF'
Usage: scripts/install.sh [options]

Copies plugins/outstanding-items/skills/outstanding-items/ into a harness skills directory.

Options:
  --target <auto|codex|claude|both>
        auto    install for each harness whose home directory exists (default)
        codex   ~/.codex/skills/outstanding-items/
        claude  ~/.claude/skills/outstanding-items/
        both    both of the above, creating them if missing
  --dest <dir>
        Install into <dir>/skills/outstanding-items/ instead of a harness home.
  --dry-run   Print the per-file plan and change nothing.
  --force     Overwrite files that were modified after installation.
  --quiet     Only print warnings and errors.
  -h, --help  Show this help.

Exit status:
  0  everything installed or already up to date
  1  an error, or a conflict that needs --force

Nothing here reaches the network, and no directory is ever removed recursively.
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

# A manifest path must be a plain relative path. No absolute paths, no parent
# traversal, no shell metacharacters, no whitespace.
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
  # The caller checks each path that this installer owns (root, skills, and
  # skill directory). Do not reject platform-managed ancestor aliases such as
  # macOS /var -> /private/var.
  [ ! -L "$check_path" ] || die "refusing to follow symbolic link: $check_path"
}

# Read `name:` from the first YAML frontmatter block of a SKILL.md.
frontmatter_name() {
  awk '
    NR == 1 && $0 != "---" { exit }
    NR == 1 { next }
    /^---[[:space:]]*$/ { exit }
    /^name:[[:space:]]*/ {
      sub(/^name:[[:space:]]*/, "")
      gsub(/^["'"'"']|["'"'"'][[:space:]]*$/, "")
      sub(/[[:space:]]+$/, "")
      print
      exit
    }
  ' "$1"
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
    --force)
      FORCE=1
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

[ -d "$SRC" ] || die "cannot find the skill source at $SRC"
[ -f "$SRC/SKILL.md" ] || die "cannot find $SRC/SKILL.md"

src_name=$(frontmatter_name "$SRC/SKILL.md")
[ "$src_name" = "$SKILL_NAME" ] ||
  die "source SKILL.md declares name '$src_name', expected '$SKILL_NAME'"

# Build the file manifest from authored source, sorted for determinism. Python
# bytecode is generated test/runtime state, never a distributable skill file.
files=$(cd "$SRC" && find . -type f \
  ! -name '.DS_Store' \
  ! -name '*.pyc' \
  ! -path '*/__pycache__/*' \
  | sed 's|^\./||' | LC_ALL=C sort)
[ -n "$files" ] || die "no files found under $SRC"

for rel in $files; do
  valid_relpath "$rel" || die "refusing to install unsafe manifest path: $rel"
done

file_count=$(printf '%s\n' "$files" | wc -l | tr -d ' ')

resolve_root() {
  case "$1" in
    codex) printf '%s\n' "$HOME/.codex" ;;
    claude) printf '%s\n' "$HOME/.claude" ;;
    custom) printf '%s\n' "$DEST" ;;
  esac
}

install_to() {
  label="$1"
  root="$2"

  valid_root "$root" ||
    die "destination root must be an absolute, traversal-free path: $root"
  reject_symlink_chain "$root"
  reject_symlink_chain "$root/skills"

  skill_dir="$root/skills/$SKILL_NAME"
  case "$skill_dir" in
    */skills/"$SKILL_NAME") : ;;
    *) die "refusing to write to unexpected path: $skill_dir" ;;
  esac
  reject_symlink_chain "$skill_dir"

  log ""
  log "== $label -> $skill_dir"

  # Ownership guard: never take over a directory this project does not own.
  if [ -f "$skill_dir/SKILL.md" ]; then
    existing_name=$(frontmatter_name "$skill_dir/SKILL.md")
    if [ "$existing_name" != "$SKILL_NAME" ]; then
      warn "$skill_dir holds a different skill (name: ${existing_name:-unknown}). Skipping."
      had_conflict=1
      return 0
    fi
  elif [ -d "$skill_dir" ]; then
    if [ -n "$(ls -A "$skill_dir" 2>/dev/null || true)" ]; then
      if [ "$FORCE" -eq 0 ]; then
        warn "$skill_dir exists, is not empty, and has no SKILL.md. Skipping (use --force)."
        had_conflict=1
        return 0
      fi
      warn "$skill_dir has unrecognised content; --force given, continuing."
    fi
  fi

  # What did we install last time? Used to tell an old copy of ours apart from
  # a copy the user edited by hand.
  prev_manifest="$skill_dir/$MANIFEST_FILE"

  planned=""
  n_create=0
  n_update=0
  n_same=0
  n_skip=0
  n_remove=0

  for rel in $files; do
    src_file="$SRC/$rel"
    dst_file="$skill_dir/$rel"

    if [ ! -e "$dst_file" ]; then
      action="create"
    elif cmp -s "$src_file" "$dst_file"; then
      action="unchanged"
    else
      action="update"
      if [ -f "$prev_manifest" ]; then
        recorded=$(awk -v want="$rel" '$2 == want { print $1; exit }' "$prev_manifest" || true)
        if [ -n "$recorded" ]; then
          current=$(hash_file "$dst_file")
          [ "$current" = "$recorded" ] || action="conflict"
        else
          action="conflict"
        fi
      else
        action="conflict"
      fi
      if [ "$action" = "conflict" ] && [ "$FORCE" -eq 1 ]; then
        action="overwrite"
      fi
    fi

    case "$action" in
      create) n_create=$((n_create + 1)) ;;
      update | overwrite) n_update=$((n_update + 1)) ;;
      unchanged) n_same=$((n_same + 1)) ;;
      conflict)
        n_skip=$((n_skip + 1))
        had_conflict=1
        ;;
    esac

    log "   $action  $rel"
    planned="$planned$action $rel
"
  done

  # Files present in the destination that this repository no longer ships.
  if [ -d "$skill_dir" ]; then
    # Ignore Python's replaceable runtime cache. Running the installed ledger
    # may create it, but it is neither authored content nor an ownership conflict.
    existing=$(cd "$skill_dir" && find . -type f \
      ! -name '*.pyc' \
      ! -path '*/__pycache__/*' \
      | sed 's|^\./||' | LC_ALL=C sort)
    for rel in $existing; do
      [ "$rel" = "$MANIFEST_FILE" ] && continue
      case "
$files
" in
        *"
$rel
"*) continue ;;
      esac
      case "
$DEPRECATED_FILES
" in
        *"
$rel
"*)
          valid_relpath "$rel" || die "refusing to remove unsafe deprecated path: $rel"
          log "   remove    $rel (known deprecated owned file)"
          planned="$planned""remove-deprecated $rel
"
          n_remove=$((n_remove + 1))
          ;;
        *) log "   stale     $rel (left in place)" ;;
      esac
    done
  fi

  log "   -> $n_create create, $n_update update, $n_same unchanged, $n_remove deprecated remove, $n_skip skipped"

  if [ "$n_skip" -gt 0 ]; then
    warn "$label: $n_skip file(s) differ from what was installed. Re-run with --force to overwrite."
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    log "   (dry run: nothing written)"
    return 0
  fi

  mkdir -p "$skill_dir"
  reject_symlink_chain "$skill_dir"
  root_real=$(CDPATH= cd -- "$root" && pwd -P)
  skill_real=$(CDPATH= cd -- "$skill_dir" && pwd -P)
  [ "$skill_real" = "$root_real/skills/$SKILL_NAME" ] ||
    die "resolved destination escaped its root: $skill_real"

  printf '%s' "$planned" | while IFS=' ' read -r action rel; do
    [ -n "${rel:-}" ] || continue
    case "$action" in
      create | update | overwrite) ;;
      remove-deprecated)
        case "$rel" in
          references/backlog-format.md | references/curation.md | references/related-task-sync.md) : ;;
          *) die "refusing to remove unrecognised deprecated path: $rel" ;;
        esac
        dst_file="$skill_dir/$rel"
        reject_symlink_chain "$dst_file"
        [ ! -e "$dst_file" ] || [ -f "$dst_file" ] ||
          die "refusing to remove non-file deprecated path: $dst_file"
        [ ! -e "$dst_file" ] || rm -f -- "$dst_file"
        continue
        ;;
      *) continue ;;
    esac
    dst_file="$skill_dir/$rel"
    dst_parent=$(dirname "$dst_file")
    mkdir -p "$dst_parent"
    cp "$SRC/$rel" "$dst_file"
    chmod 644 "$dst_file"
  done

  # Record what we installed, so a later run can tell our own older copy from a
  # file the user edited.
  tmp_manifest="$skill_dir/$MANIFEST_FILE.tmp"
  : >"$tmp_manifest"
  for rel in $files; do
    if [ -f "$skill_dir/$rel" ] && cmp -s "$SRC/$rel" "$skill_dir/$rel"; then
      printf '%s %s\n' "$(hash_file "$skill_dir/$rel")" "$rel" >>"$tmp_manifest"
    fi
  done
  mv "$tmp_manifest" "$skill_dir/$MANIFEST_FILE"
  chmod 644 "$skill_dir/$MANIFEST_FILE"

  installed_any=1
  log "   installed $file_count file(s)"
}

log "outstanding-items installer"
log "source: $SRC ($file_count files)"
if [ "$DRY_RUN" -eq 1 ]; then
  log "mode:   dry run"
fi

if [ -n "$DEST" ]; then
  install_to "custom" "$DEST"
else
  case "$TARGET" in
    auto)
      found=0
      for h in codex claude; do
        root=$(resolve_root "$h")
        if [ -d "$root" ]; then
          found=1
          install_to "$h" "$root"
        else
          log ""
          log "== $h -> not found ($root does not exist), skipping"
        fi
      done
      if [ "$found" -eq 0 ]; then
        log ""
        die "neither ~/.codex nor ~/.claude exists. Use --target codex, --target claude, --target both, or --dest <dir>."
      fi
      ;;
    codex | claude)
      install_to "$TARGET" "$(resolve_root "$TARGET")"
      ;;
    both)
      install_to "codex" "$(resolve_root codex)"
      install_to "claude" "$(resolve_root claude)"
      ;;
  esac
fi

log ""
if [ "$DRY_RUN" -eq 1 ]; then
  log "Dry run complete. Nothing was written."
elif [ "$installed_any" -eq 1 ]; then
  log "Done. Verify with: ./scripts/check.sh --installed"
  log "Optional: add the global rule from examples/global-rules/ so the skill fires without being asked."
fi

[ "$had_conflict" -eq 0 ] || exit 1
exit 0
