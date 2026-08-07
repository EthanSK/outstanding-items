#!/bin/sh
# Validate this repository: required files, frontmatter, YAML basics, internal
# links, site base paths, asset integrity, privacy rules, honesty guards.
# Requires only sh and python3. Makes no network requests.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$script_dir/.." && pwd)

usage() {
  cat <<'EOF'
Usage: scripts/check.sh [options]

Options:
  --installed   Also validate installed copies under ~/.codex and ~/.claude.
  -v, --verbose Print every check, not just failures.
  -h, --help    Show this help.

Exit status is 0 when every check passes.
EOF
}

pass_extra=""
for arg in "$@"; do
  case "$arg" in
    -h | --help)
      usage
      exit 0
      ;;
    --installed | -v | --verbose | --list)
      pass_extra="$pass_extra $arg"
      ;;
    *)
      printf 'error: unknown option: %s (try --help)\n' "$arg" >&2
      exit 2
      ;;
  esac
done

command -v python3 >/dev/null 2>&1 || {
  printf 'error: python3 is required\n' >&2
  exit 2
}

failures=0

printf '== shell syntax\n'
for f in "$REPO_ROOT"/scripts/*.sh "$REPO_ROOT"/tests/*.sh; do
  [ -f "$f" ] || continue
  if sh -n "$f"; then
    printf '   ok    %s\n' "${f#"$REPO_ROOT"/}"
  else
    printf '   FAIL  %s\n' "${f#"$REPO_ROOT"/}"
    failures=$((failures + 1))
  fi
done

# ast.parse rather than py_compile, so no __pycache__ appears in the checkout.
PY_SYNTAX='import ast, sys; ast.parse(open(sys.argv[1], encoding="utf-8").read())'

printf '== python syntax\n'
for f in "$REPO_ROOT"/scripts/*.py "$REPO_ROOT"/tests/*.py; do
  [ -f "$f" ] || continue
  if python3 -c "$PY_SYNTAX" "$f" >/dev/null 2>&1; then
    printf '   ok    %s\n' "${f#"$REPO_ROOT"/}"
  else
    printf '   FAIL  %s\n' "${f#"$REPO_ROOT"/}"
    python3 -c "$PY_SYNTAX" "$f" || true
    failures=$((failures + 1))
  fi
done

if command -v node >/dev/null 2>&1; then
  printf '== javascript syntax\n'
  for f in "$REPO_ROOT"/docs/assets/*.js "$REPO_ROOT"/skill/outstanding-items/assets/*.js; do
    [ -f "$f" ] || continue
    if node --check "$f" >/dev/null 2>&1; then
      printf '   ok    %s\n' "${f#"$REPO_ROOT"/}"
    else
      printf '   FAIL  %s\n' "${f#"$REPO_ROOT"/}"
      node --check "$f" || true
      failures=$((failures + 1))
    fi
  done
else
  printf '== javascript syntax\n   skip  node not installed\n'
fi

printf '== repository checks\n'
# shellcheck disable=SC2086
if python3 "$REPO_ROOT/tests/run_checks.py" $pass_extra; then
  :
else
  failures=$((failures + 1))
fi

printf '== ledger UI tests\n'
if python3 "$REPO_ROOT/tests/test_ledger_ui.py"; then
  :
else
  failures=$((failures + 1))
fi

printf '\n'
if [ "$failures" -eq 0 ]; then
  printf 'All checks passed.\n'
  exit 0
fi
printf '%d check group(s) failed.\n' "$failures"
exit 1
