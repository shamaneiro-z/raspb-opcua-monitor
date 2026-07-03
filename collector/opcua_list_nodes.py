import argparse
import logging
import sys
from typing import List

from opcua import Client
from opcua.common.node import Node

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("opcua-list-nodes")


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Browse an OPC UA server namespace and write node info to a file."
    )
    parser.add_argument(
        "--endpoint",
        required=True,
        help="OPC UA endpoint, e.g. opc.tcp://192.168.1.100:4840",
    )
    parser.add_argument(
        "--output",
        default="opcua_nodes.txt",
        help="Output file path for the node tree (default: opcua_nodes.txt)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum browse depth when walking the node tree (default: 5)",
    )
    return parser.parse_args()


def format_node_line(node: Node, indent: int) -> str:
    browse_name = node.get_browse_name()
    return f"{'  ' * indent}- {browse_name} [{node.nodeid}]"


def browse_node(node: Node, depth: int, max_depth: int, visited: set) -> List[str]:
    if depth > max_depth:
        return ["  " * depth + "- ... (max depth reached)"]

    lines = []
    try:
        children = node.get_children()
    except Exception as exc:
        logger.warning("Failed to get children for %s: %s", node, exc)
        return lines

    for child in children:
        if child.nodeid in visited:
            lines.append(f"{'  ' * depth}- {child.get_browse_name()} [{child.nodeid}] (already visited)")
            continue

        visited.add(child.nodeid)
        lines.append(format_node_line(child, depth))
        lines.extend(browse_node(child, depth + 1, max_depth, visited))

    return lines


def main() -> int:
    args = build_args()
    client = Client(args.endpoint)

    try:
        logger.info("Connecting to OPC UA endpoint: %s", args.endpoint)
        client.connect()
        logger.info("Connected")

        root = client.get_root_node()
        objects = client.get_objects_node()

        lines: List[str] = []
        lines.append("Root node:")
        lines.extend(browse_node(root, 1, args.max_depth, {root.nodeid}))
        lines.append("")
        lines.append("Objects node:")
        lines.extend(browse_node(objects, 1, args.max_depth, {objects.nodeid}))

        with open(args.output, "w", encoding="utf-8") as out_file:
            out_file.write("\n".join(lines))

        logger.info("Wrote %d lines to %s", len(lines), args.output)
        return 0

    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to list OPC UA nodes: %s", exc)
        return 1

    finally:
        try:
            client.disconnect()
            logger.info("Disconnected")
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
