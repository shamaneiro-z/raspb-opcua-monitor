import argparse
import logging
import sys
from datetime import datetime, timezone

from opcua import Client


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("opcua-anonymous-read")


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Connect anonymously to OPC UA server and read one node value."
    )
    parser.add_argument(
        "--endpoint",
        required=True,
        help="OPC UA endpoint, e.g. opc.tcp://192.168.1.100:4840",
    )
    parser.add_argument(
        "--node-id",
        required=True,
        help="NodeId to read, e.g. ns=2;s=Machine.Temperature",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=5.0,
        help="Socket timeout for OPC UA calls (default: 5.0)",
    )
    return parser.parse_args()


def main() -> int:
    args = build_args()

    logger.info("Starting anonymous OPC UA read test")
    logger.info("Endpoint: %s", args.endpoint)
    logger.info("NodeId: %s", args.node_id)

    client = Client(args.endpoint, timeout=args.timeout_seconds)

    try:
        logger.info("Connecting as Anonymous...")
        client.connect()
        logger.info("Connected")

        node = client.get_node(args.node_id)
        value = node.get_value()

        logger.info("Read successful")
        logger.info("Timestamp (UTC): %s", datetime.now(timezone.utc).isoformat())
        logger.info("NodeId: %s", args.node_id)
        logger.info("Value: %r", value)
        return 0

    except Exception as exc:  # noqa: BLE001
        logger.exception("Anonymous OPC UA read failed: %s", exc)
        return 1

    finally:
        try:
            client.disconnect()
            logger.info("Disconnected")
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    sys.exit(main())
