#!/bin/bash
# Launch the Grafana dashboard with the official Grafana kiosk binary.
# This script expects the kiosk binary at ~/grafana-kiosk/bin/grafana-kiosk.linux.armv7

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    source <(sed 's/\r$//' "$ENV_FILE")
    set +a
fi

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_ADMIN_USER:-admin}"
GRAFANA_PASS="${GRAFANA_ADMIN_PASSWORD:-admin}"
MAX_RETRIES=30
RETRY_DELAY=2

# Wait for Grafana to be ready
echo "Waiting for Grafana to start..."
for i in $(seq 1 $MAX_RETRIES); do
    if curl -f -s "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
        echo "✓ Grafana is ready"
        break
    fi
    if [ $i -eq $MAX_RETRIES ]; then
        echo "✗ Grafana failed to start after $((MAX_RETRIES * RETRY_DELAY))s"
        exit 1
    fi
    sleep $RETRY_DELAY
done

KIOSK_BINARY="$HOME/grafana-kiosk-v1.0.12/grafana-kiosk.linux.arm64"
if [ ! -x "$KIOSK_BINARY" ]; then
    echo "Grafana kiosk binary not found at $KIOSK_BINARY"
    exit 1
fi

DASHBOARD_URL="$GRAFANA_URL/d/opcua-overview"

# Start the Grafana kiosk binary with a deterministic full-screen window.
echo "Opening Grafana dashboard in kiosk mode..."
DISPLAY=:0 "$KIOSK_BINARY" \
    -URL "$DASHBOARD_URL" \
    -login-method anon \
    -kiosk-mode full \
    -hide-logo \
    -hide-time-picker \
    -hide-links \
    -hide-variables \
    -window-position 0,0 \
    -window-size 1920,1080 \
    -scale-factor 1.0 \
    -ignore-certificate-errors \
    -lxde \
    >/tmp/grafana-kiosk.log 2>&1 &

# Hide the mouse cursor in the graphical session.
( DISPLAY=:0 xsetroot -cursor_name X_cursor 2>/dev/null || true )
( DISPLAY=:0 xsetroot -solid black 2>/dev/null || true )
( DISPLAY=:0 xsetroot -cursor /dev/null 2>/dev/null || true )

echo "✓ Grafana kiosk started"
