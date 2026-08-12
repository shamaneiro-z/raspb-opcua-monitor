import ctypes
import logging
import os
import sys
import time
from datetime import datetime, timezone

from asyncua import ua
from asyncua.sync import Client


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("opcua-timesync")

# Standard OPC UA node, present on every server: Server/ServerStatus/CurrentTime (UTC).
SERVER_CURRENT_TIME_NODE = "ns=0;i=2258"

CLOCK_REALTIME = 0


class _timespec(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long), ("tv_nsec", ctypes.c_long)]


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


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

    if mode != ua.MessageSecurityMode.None_ or policy != ua.SecurityPolicyType.NoSecurity:
        client.set_security(policy, certificate_path=None, private_key_path=None, mode=mode)


def fetch_server_time(
    endpoint: str,
    security_mode: str,
    security_policy: str,
    username: str,
    password: str,
    connect_timeout_s: float,
) -> datetime:
    client = Client(endpoint, timeout=connect_timeout_s)
    if security_mode != "None" or security_policy != "None":
        configure_security(client, security_mode, security_policy)
    if username and password:
        client.set_user(username)
        client.set_password(password)

    with client:
        node = client.get_node(SERVER_CURRENT_TIME_NODE)
        value = node.read_value()

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def set_system_time(new_time: datetime) -> None:
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    timestamp = new_time.timestamp()
    ts = _timespec()
    ts.tv_sec = int(timestamp)
    ts.tv_nsec = int((timestamp - ts.tv_sec) * 1_000_000_000)
    if libc.clock_settime(CLOCK_REALTIME, ctypes.byref(ts)) != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, f"clock_settime failed: {os.strerror(errno)}")


def main() -> int:
    endpoint = env("OPCUA_ENDPOINT", "opc.tcp://127.0.0.1:4840")
    security_mode = env("OPCUA_SECURITY_MODE", "None")
    security_policy = env("OPCUA_SECURITY_POLICY", "None")
    username = env("OPCUA_USERNAME")
    password = env("OPCUA_PASSWORD")

    threshold_s = float(env("TIME_SYNC_THRESHOLD_S", "2"))
    max_attempts = int(env("TIME_SYNC_MAX_RETRIES", "10"))
    retry_delay_s = float(env("TIME_SYNC_RETRY_DELAY_S", "5"))
    connect_timeout_s = float(env("TIME_SYNC_CONNECT_TIMEOUT_S", "5"))
    required = env("TIME_SYNC_REQUIRED", "false").lower() == "true"

    logger.info("Syncing system time from OPC UA server at %s", endpoint)

    for attempt in range(1, max_attempts + 1):
        try:
            server_time = fetch_server_time(
                endpoint, security_mode, security_policy, username, password, connect_timeout_s
            )
            local_time = datetime.now(timezone.utc)
            drift_s = (server_time - local_time).total_seconds()
            logger.info(
                "OPC UA server time: %s | local time: %s | drift: %.3fs",
                server_time.isoformat(), local_time.isoformat(), drift_s,
            )

            if abs(drift_s) < threshold_s:
                logger.info("Drift within threshold (%.3fs); leaving system clock unchanged.", threshold_s)
                return 0

            set_system_time(server_time)
            logger.info("System clock updated to OPC UA server time (previous drift: %.3fs).", drift_s)
            return 0
        except Exception as exc:
            logger.warning("Attempt %d/%d to sync time from OPC UA server failed: %s", attempt, max_attempts, exc)
            if attempt < max_attempts:
                time.sleep(retry_delay_s)

    message = f"Could not sync system time from OPC UA server after {max_attempts} attempts."
    if required:
        logger.error("%s TIME_SYNC_REQUIRED=true, failing startup.", message)
        return 1

    logger.warning("%s Continuing with current system clock.", message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
