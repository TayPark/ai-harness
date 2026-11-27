#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is required." >&2; exit 1; }
exec python3 "$SCRIPT_DIR/harness/scripts/harness.py" install "$@"
