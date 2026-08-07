#!/bin/sh
# Run the deterministic repository checks directly.
# `scripts/check.sh` is the fuller entry point: it adds shell and JavaScript
# syntax checks on top of these. This script exists so the checks can be run
# on their own, and so the skill's continuous-improvement contract has a
# stable command to name.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$script_dir/.." && pwd)

case "${1:-}" in
  -h | --help)
    cat <<'EOF'
Usage: tests/run_tests.sh [--installed] [-v] [--list]

Passes its arguments through to tests/run_checks.py.
Requires python3 and nothing else. Makes no network requests.
EOF
    exit 0
    ;;
esac

command -v python3 >/dev/null 2>&1 || {
  printf 'error: python3 is required\n' >&2
  exit 2
}

python3 "$REPO_ROOT/tests/run_checks.py" "$@"
exec python3 "$REPO_ROOT/tests/test_ledger_ui.py"
