#!/bin/sh
# Preview the GitHub Pages site locally. Serves docs/ over plain HTTP on
# localhost. No build step, no dependencies beyond python3.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$script_dir/.." && pwd)
PORT="${PORT:-8099}"

usage() {
  cat <<'EOF'
Usage: scripts/serve.sh [port]

Serves docs/ at http://127.0.0.1:<port>/ (default 8099).
Every internal link in the site is relative, so what you see locally is what
GitHub Pages serves under /outstanding-items/.
EOF
}

case "${1:-}" in
  -h | --help)
    usage
    exit 0
    ;;
  "") : ;;
  *)
    case "$1" in
      *[!0-9]*)
        printf 'error: port must be a number\n' >&2
        exit 2
        ;;
    esac
    PORT="$1"
    ;;
esac

command -v python3 >/dev/null 2>&1 || {
  printf 'error: python3 is required\n' >&2
  exit 2
}

printf 'Serving %s at http://127.0.0.1:%s/\n' "$REPO_ROOT/docs" "$PORT"
printf 'Press Ctrl-C to stop.\n\n'
exec python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$REPO_ROOT/docs"
