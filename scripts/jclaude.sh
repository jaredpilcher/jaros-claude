#!/usr/bin/env bash
# Launch the jaros-claude REPL. Requires ANTHROPIC_API_KEY in the environment.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "warning: ANTHROPIC_API_KEY is not set — model calls will fail (the control tests still run with 'python -m pytest -q')." >&2
fi
exec python -m harness.cli "$@"
