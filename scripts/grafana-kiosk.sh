#!/bin/bash
# Auto-open Grafana dashboard in fullscreen kiosk mode on Raspberry Pi
# Install as: ~/.config/openbox/autostart or as a systemd user service
# Or add to /etc/rc.local: sudo -u pi /path/to/grafana-kiosk.sh &

set -e

GRAFANA_URL="http://localhost:3000"
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

# Optional: Auto-login (create API token in Grafana and use it)
# For now, just open the public dashboard
DASHBOARD_URL="$GRAFANA_URL/d/opcua-overview?kiosk=tv&refresh=5s"

# Kill any existing Chromium instances
pkill -f chromium-browser || true
pkill -f /usr/bin/chromium || true

sleep 1

# Start Chromium in kiosk mode
echo "Opening Grafana dashboard in kiosk mode..."
DISPLAY=:0 chromium-browser \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-extensions \
    --disable-component-update \
    --disable-default-apps \
    --disable-preconnect \
    --kiosk "$DASHBOARD_URL" &

echo "✓ Grafana kiosk started"
