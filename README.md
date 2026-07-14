# raspb-opcua-monitor

Real-time OPC UA data collection → InfluxDB → Grafana dashboard for industrial process monitoring.

## Quick Start

See **[RASPI_SETUP.md](RASPI_SETUP.md)** for complete Raspberry Pi deployment guide, including:
- Offline builds without internet
- Auto-start containers on boot
- Auto-open Grafana fullscreen kiosk mode
- Configuration & troubleshooting

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
