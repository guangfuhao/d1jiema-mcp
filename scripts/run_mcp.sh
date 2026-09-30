#!/bin/sh
set -eu
PLUGIN_ROOT="${PLUGIN_ROOT:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
if [ -x "$PLUGIN_ROOT/.venv/bin/d1jiema-mcp" ]; then
  exec "$PLUGIN_ROOT/.venv/bin/d1jiema-mcp" "$@"
fi
if command -v uv >/dev/null 2>&1; then
  exec uv run --project "$PLUGIN_ROOT" d1jiema-mcp "$@"
fi
exec python3 -m d1jiema_mcp.server "$@"
