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

Your stack uses Docker restart policy in `docker-compose.yml`:

```yaml
restart: unless-stopped
```

That means once the containers are created and running, Docker will restart them when the daemon starts on boot.

Enable Docker on boot:

```bash
sudo systemctl enable docker
```

Start the stack once:

```bash
docker compose up -d
```

Verify after reboot:

```bash
docker compose ps
docker ps
```

## 5. Auto-Open Dashboard (Optional)

If you have a display attached and want fullscreen Grafana, install the official Grafana kiosk binary and run the provided launcher.

> Important: The kiosk script requires X11. Do not run this setup under Wayland.

Chromium translation prompts should be disabled using a managed policy JSON because the kiosk binary does not expose Chromium CLI flags directly.

Create one of these files on the Pi:
- `/etc/chromium/policies/managed/managed_policies.json`
- `/etc/opt/chrome/policies/managed/managed_policies.json`

Use this content:

```json
{
  "TranslateEnabled": false
}
```

If the translation prompt still appears, use:

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

chmod +x scripts/grafana-kiosk.sh
bash scripts/grafana-kiosk.sh
```

To make it start automatically on boot:

```bash
sudo cp scripts/grafana-kiosk.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now grafana-kiosk.service
```

If the kiosk binary is stored in a different folder than expected by the launcher, adjust the `KIOSK_BINARY` path in `scripts/grafana-kiosk.sh` accordingly.

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
