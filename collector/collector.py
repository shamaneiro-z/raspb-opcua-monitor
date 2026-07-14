import logging
import os
import time

from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from opcua import Client
from opcua import ua


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("opcua-collector")


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def parse_node_ids(raw: str) -> list[str]:
    node_ids = [item.strip() for item in raw.split(",") if item.strip()]
    if not node_ids:
        raise ValueError("OPCUA_NODE_IDS is empty. Provide at least one NodeId.")
    return node_ids


def to_float(value):
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def configure_security(client: Client, mode_name: str, policy_name: str) -> None:
    mode_map = {
        "None": ua.MessageSecurityMode.None_,
        "Sign": ua.MessageSecurityMode.Sign,
        "SignAndEncrypt": ua.MessageSecurityMode.SignAndEncrypt,
    }
    policy_map = {
        "None": ua.SecurityPolicyType.NoSecurity,
        "Basic256Sha256": ua.SecurityPolicyType.Basic256Sha256,
    }

    mode = mode_map.get(mode_name, ua.MessageSecurityMode.None_)
    policy = policy_map.get(policy_name, ua.SecurityPolicyType.NoSecurity)

    # This prototype assumes anonymous/basic auth and no certificate files.
    # For production with Sign/SignAndEncrypt, provide cert/key and trust store.
    client.set_security(policy, certificate_path=None, private_key_path=None, mode=mode)


def create_influx_writer(url: str, token: str, org: str):
    influx = InfluxDBClient(url=url, token=token, org=org)
    write_api = influx.write_api(write_options=SYNCHRONOUS)
    return influx, write_api


def main() -> None:
    endpoint = env("OPCUA_ENDPOINT", "opc.tcp://127.0.0.1:4840")
    security_mode = env("OPCUA_SECURITY_MODE", "None")
    security_policy = env("OPCUA_SECURITY_POLICY", "None")
    username = env("OPCUA_USERNAME")
    password = env("OPCUA_PASSWORD")
    node_ids = parse_node_ids(env("OPCUA_NODE_IDS", "ns=2;s=Machine.Temperature"))
    poll_interval_ms = int(env("OPCUA_POLL_INTERVAL_MS", "1000"))

    influx_url = env("INFLUX_URL", "http://influxdb:8086")
    influx_token = env("INFLUX_TOKEN")
    influx_org = env("INFLUX_ORG", "rasp-monitor")
    influx_bucket = env("INFLUX_BUCKET", "machine-data")
    measurement = env("INFLUX_MEASUREMENT", "opcua_metrics")
    machine_tag = env("INFLUX_TAG_MACHINE", "machine_1")

    if not influx_token:
        raise ValueError("INFLUX_TOKEN is required.")

    client = Client(endpoint)
    if security_mode != "None" or security_policy != "None":
        configure_security(client, security_mode, security_policy)

    if username and password:
        client.set_user(username)
        client.set_password(password)

    influx_client, influx_writer = create_influx_writer(influx_url, influx_token, influx_org)

    logger.info("Starting OPC UA collector")
    logger.info("Endpoint: %s", endpoint)
    logger.info("NodeIds: %s", ", ".join(node_ids))

    try:
        client.connect()
        logger.info("Connected to OPC UA server")

        nodes = {node_id: client.get_node(node_id) for node_id in node_ids}

        while True:
            points = []

            for node_id, node in nodes.items():
                try:
                    data_value = node.get_data_value()
                    value = data_value.Value.Value
                    source_ts = data_value.SourceTimestamp
                    server_ts = data_value.ServerTimestamp
                    # Prefer source timestamp (PLC), fall back to server timestamp
                    timestamp = source_ts or server_ts
                    value_float = to_float(value)

                    if value_float is not None:
                        point = (
                            Point(measurement)
                            .tag("machine", machine_tag)
                            .tag("node_id", node_id)
                            .field("value", value_float)
                            .time(timestamp)
                        )
                    elif isinstance(value, str):
                        point = (
                            Point(measurement)
                            .tag("machine", machine_tag)
                            .tag("node_id", node_id)
                            .field("value_str", value)
                            .time(timestamp)
                        )
                    else:
                        logger.warning("Skipping unsupported value for node %s: %r", node_id, value)
                        continue

                    points.append(point)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed reading node %s: %s", node_id, exc)

            if points:
                influx_writer.write(bucket=influx_bucket, org=influx_org, record=points)
                logger.info("Wrote %d points", len(points))

            time.sleep(max(poll_interval_ms, 100) / 1000.0)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Collector failed: %s", exc)
        raise
    finally:
        try:
            client.disconnect()
        except Exception:  # noqa: BLE001
            pass
        influx_client.close()


if __name__ == "__main__":
    main()
