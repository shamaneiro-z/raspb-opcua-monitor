# Quick Setup Guide

Assumes Docker and Docker Compose are already installed.

## 1. Clone & Configure

```bash
git clone <repo> /opt/rasp-maschine-monitor
cd /opt/rasp-maschine-monitor
cp .env.example .env
nano .env
```

Edit `.env`:
- `OPCUA_ENDPOINT`: Your OPC UA server
- `OPCUA_NODE_IDS`: Comma-separated node IDs
- `INFLUXDB_TOKEN`: Generate a strong random value (e.g., `openssl rand -hex 32`)
- `GRAFANA_ADMIN_PASSWORD`: Change from default

## 2. Offline Build (Optional)

If deploying to a machine without internet:

```bash
# On a machine WITH internet:
bash scripts/build-wheels-offline.sh
git add collector/wheels
git push
```

Then pull on the target machine. The Dockerfile will use local wheels automatically.

## 3. Start Services

```bash
docker compose up -d
```

Check status:

```bash
docker compose ps
docker compose logs -f
```

Access:
- **Grafana**: http://localhost:3000
- **InfluxDB**: http://localhost:8086

## 4. Auto-Start on Machine Boot (Optional)

### System Service

```bash
sudo cp scripts/rasp-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rasp-monitor.service
sudo systemctl start rasp-monitor.service
```

Check:

```bash
sudo systemctl status rasp-monitor.service
```

### Or use Docker restart policy

Already set in `docker-compose.yml`: `restart: unless-stopped` — containers auto-restart on failure and on boot.

## 5. Auto-Open Dashboard (Optional)

If you have a display attached and want fullscreen Grafana:

```bash
# Install Chromium (if not present)
sudo apt install chromium-browser  # or: brew install chromium (macOS)

# Run the kiosk script
bash scripts/grafana-kiosk.sh
```

Or register as a system service:

```bash
sudo cp scripts/grafana-kiosk.service /etc/systemd/system/
sudo systemctl enable grafana-kiosk.service
```

## Configuration

**Dashboard time range**: Default is 1 hour (`now-1h`). Edit `grafana/dashboards/opcua-overview.json` to change.

**Retention**: InfluxDB keeps 7 days of data. Edit `DOCKER_INFLUXDB_INIT_RETENTION` in `docker-compose.yml`.

**Poll interval**: Edit `OPCUA_POLL_INTERVAL_MS` in `.env` (default: 1000ms).

## Logs & Troubleshooting

View all logs:

```bash
docker compose logs -f
```

View specific service:

```bash
docker compose logs -f opcua-collector
docker compose logs -f grafana
docker compose logs -f influxdb
```

### Collector not writing data

Check OPC UA endpoint is reachable:

```bash
docker compose exec opcua-collector python -c "
from opcua import Client
c = Client('opc.tcp://YOUR_ENDPOINT:4840')
c.connect()
print('✓ Connected')
c.disconnect()
"
```

### Grafana won't open

Verify Grafana is healthy:

```bash
curl http://localhost:3000/api/health
```

## Maintenance

Stop all services:

```bash
docker compose down
```

Restart everything:

```bash
docker compose restart
```

Backup InfluxDB data:

```bash
docker compose exec influxdb influx backup /tmp/backup
docker cp influxdb:/tmp/backup ./backup-$(date +%Y%m%d)
```

## Performance

- InfluxDB + Grafana: ~500MB RAM
- Collector: ~100MB RAM
- Storage: ~10GB for 7 days (5 nodes @ 1Hz)
