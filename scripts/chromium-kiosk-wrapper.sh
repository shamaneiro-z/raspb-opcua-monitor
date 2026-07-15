#!/bin/bash
set -euo pipefail

BROWSER_BIN="${CHROMIUM_REAL_BROWSER:-$(command -v chromium-browser 2>/dev/null || command -v chromium 2>/dev/null || true)}"
if [ -z "$BROWSER_BIN" ]; then
    echo "No Chromium browser found" >&2
    exit 1
fi

PROFILE_DIR="/tmp/grafana-kiosk-profile"
mkdir -p "$PROFILE_DIR"

exec "$BROWSER_BIN" \
    --user-data-dir="$PROFILE_DIR" \
    --no-first-run \
    --no-default-browser-check \
    --disable-translate \
    --disable-features=Translate,TranslateUI \
    "$@"
