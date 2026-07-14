# raspb-opcua-monitor

## Offline build setup

If your Raspberry Pi must build the collector image without internet access, provide the Python dependency wheels locally.

On a machine with internet access:

```bash
cd /home/user/repos/raspb-opcua-monitor/collector
mkdir -p wheels
pip download -r requirements.txt -d wheels
```

Copy the `collector/wheels` directory to the Pi along with the project.

The Dockerfile now supports local wheels automatically. When `collector/wheels` contains downloaded packages, the build will use them:

```bash
docker compose build opcua-collector
```

If the wheels directory is empty or absent, the build still falls back to online `pip install`.
