import logging
import sys
from datetime import datetime, timezone

from opcua import Client


# Machine-specific configuration: adjust these two values.
OPCUA_ENDPOINT = "opc.tcp://10.195.222.80:4840"
OPCUA_NODE_ID = 'ns=3;s="OPCUA_Dataset"."Prozessdaten"."ST02_Wanne_01"."Temperatur_IST"'
OPCUA_TIMEOUT_SECONDS = 5.0


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("opcua-maschine-read")


def main() -> int:
    logger.info("Starting machine-specific anonymous OPC UA read test")
    logger.info("Endpoint: %s", OPCUA_ENDPOINT)
    logger.info("NodeId: %s", OPCUA_NODE_ID)

    client = Client(OPCUA_ENDPOINT, timeout=OPCUA_TIMEOUT_SECONDS)

    try:
        logger.info("Connecting as Anonymous...")
        client.connect()
        logger.info("Connected")

        node = client.get_node(OPCUA_NODE_ID)
        value = node.get_value()

        logger.info("Read successful")
        logger.info("Timestamp (UTC): %s", datetime.now(timezone.utc).isoformat())
        logger.info("NodeId: %s", OPCUA_NODE_ID)
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
