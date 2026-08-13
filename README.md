# raspb-opcua-monitor

Real-time OPC UA data collection → InfluxDB → Grafana dashboard for industrial process monitoring.

## Quick Start

See **[RASPI_SETUP.md](RASPI_SETUP.md)** for complete Raspberry Pi deployment guide, including:
- Offline builds without internet
- Auto-start containers on boot
- Auto-open Grafana fullscreen kiosk mode
- Configuration & troubleshooting

## Raspberry Pi Kiosk Setup

For a fullscreen dashboard on a Raspberry Pi, install the official Grafana kiosk binary and launch the provided helper script.

> Important: This kiosk setup requires an X11 session. It will not work correctly on Wayland.

When Chromium is launched through the kiosk binary, you generally cannot inject GUI flags from the launcher. Use a Chromium managed policy JSON to disable translation prompts.

Create one of these files on the Pi:
- `/etc/chromium/policies/managed/managed_policies.json`
- `/etc/opt/chrome/policies/managed/managed_policies.json`

Add the following content:

```json
{
  "TranslateEnabled": false
}
```

If the prompt continues, also include:

```json
{
  "TranslateEnabled": false,
  "TranslateAllowedLanguages": "",
  "TranslateBlockedLanguages": ["*"]
}
```

Then restart the kiosk session.

```bash
sudo apt update
sudo apt install -y unclutter

cd ~
wget https://github.com/grafana/grafana-kiosk/releases/download/v1.0.1/grafana-kiosk-1.0.1.zip
unzip grafana-kiosk-1.0.1.zip && rm grafana-kiosk-1.0.1.zip

chmod +x /opt/rasp-maschine-monitor/scripts/grafana-kiosk.sh
bash /opt/rasp-maschine-monitor/scripts/grafana-kiosk.sh
```

Optional: make it start automatically on boot:

```bash
sudo cp /opt/rasp-maschine-monitor/scripts/grafana-kiosk.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now grafana-kiosk.service
```

## Overview

- **Collector**: Python service polling OPC UA nodes → InfluxDB
- **InfluxDB**: Time-series database (7-day retention)
- **Grafana**: Dashboard with 1-hour default view, 5s refresh
- **All containerized** for easy deployment

## Configuration

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
nano .env
```

Key values:
- `OPCUA_ENDPOINT`: OPC UA server URL
- `OPCUA_NODE_IDS`: Comma-separated list of nodes to poll
- `INFLUXDB_TOKEN`: Generate a strong random token
- `INFLUX_TAG_MACHINE`: Machine identifier tag

## Docker Compose

Start all services:

```bash
docker compose up -d
```

Access:
- Grafana: http://localhost:3000 (admin / admin)
- InfluxDB: http://localhost:8086

View logs:

```bash
docker compose logs -f
```

## Offline Builds

If your Raspberry Pi has no internet, pre-build Python wheels on a machine with connectivity:

```bash
bash scripts/build-wheels-offline.sh
```

This creates `collector/wheels/` with all dependencies. The Dockerfile automatically uses them if present.

## Development

For testing OPC UA connectivity:

```bash
python -c "
from opcua import Client
c = Client('opc.tcp://10.195.222.80:4840')
c.connect()
node = c.get_node('ns=3;s=\"OPCUA_Dataset\"...')
print(node.get_data_value())
c.disconnect()
"
```

See `collector/opcua_maschine_read_legacy.py` for more examples.
