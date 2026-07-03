from opcua import Client

endpoint = "opc.tcp://10.195.222.80:4840"
client = Client(endpoint)
client.connect()

root = client.get_root_node()
objects = client.get_objects_node()

def browse(node, depth=0):
    prefix = "  " * depth
    for child in node.get_children():
        print(f"{prefix}- {child.get_browse_name()} [{child.nodeid}]")
        browse(child, depth + 1)

print("Root children:")
browse(root)

print("Objects children:")
browse(objects)

client.disconnect()