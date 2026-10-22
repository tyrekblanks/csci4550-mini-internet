import json
import sys
import socket
from packet import parse_packet, create_packet

if len(sys.argv) < 2:
    print("Usage: python3 router.py <device_name> [config_file]")
    sys.exit()

device_name = sys.argv[1]

if len(sys.argv) > 2:
    config_file = sys.argv[2]
else:
    config_file = "config.json"

try:
    with open(config_file, "r") as file:
        config = json.load(file)

except FileNotFoundError:
    print(f"Error: config file '{config_file}' not found")
    sys.exit()

except json.JSONDecodeError:
    print(f"Error: config file '{config_file}' contains invalid JSON")
    sys.exit()

devices = config["devices"]

if device_name not in devices:
    print(f"Error: device '{device_name}' not found in config")
    sys.exit()

device = devices[device_name]

if device["type"] != "router":
    print("Error: selected device is not a router")
    sys.exit()

virtual_address = device["virtual_address"]
udp_port = device["UDP_port"]
neighbors = device["neighbors"]
routing_table = device.get("routes", {})

#socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", udp_port))

print(f"{device_name} listening on port {udp_port}")

# Keep receiving packets until the router is stopped
while True:
    try:
        data, address = sock.recvfrom(1200)
    except OSError as error:
        print(f"{device_name}: socket receive error: {error}")
        continue

    # 1. Parse the incoming packet
    try:
        packet = parse_packet(data)
    except (ValueError, KeyError, TypeError) as error:
        print(f"DISCARD: malformed packet at {device_name}: {error}")
        continue

    destination = packet["dst"]
    hop_limit = packet["hop_limit"]

    # 2. Check the hop limit before forwarding
    if hop_limit <= 1:
        print(
            f"DISCARD: hop limit exhausted at {device_name}, "
            f"destination={destination}"
        )
        continue

    # 3. Find the destination in the routing table.
    # JSON object keys are strings, so convert the address.
    next_hop = routing_table.get(str(destination))

    if next_hop is None:
        print(
            f"DISCARD: unknown destination {destination} "
            f"at {device_name}"
        )
        continue

    # 4. Get and validate the next-hop neighbor
    if not isinstance(next_hop, list) or len(next_hop) == 0:
        print(f"DISCARD: invalid next hop at {device_name}")
        continue

    next_hop_name = next_hop[0]

    if next_hop_name not in neighbors:
        print(
            f"DISCARD: invalid next hop {next_hop_name} "
            f"at {device_name}"
        )
        continue

    next_hop_device = devices.get(next_hop_name)

    if next_hop_device is None:
        print(
            f"DISCARD: next hop {next_hop_name} "
            f"is missing from configuration"
        )
        continue

    # 5. Create the forwarded packet with a decremented hop limit
    try:
        forwarded_packet = create_packet(
            src=packet["src"],
            dst=packet["dst"],
            hop_limit=hop_limit - 1,
            msg_type=packet["msg_type"],
            msg_id=packet["msg_id"],
            payload=packet["payload"]
        )

        next_host = next_hop_device.get("UDP_host", "127.0.0.1")
        next_port = next_hop_device["UDP_port"]

        # 6. Forward the packet to the next hop
        sock.sendto(forwarded_packet, (next_host, next_port))

        print(
            f"{device_name}: forwarded packet to {next_hop_name}, "
            f"destination={destination}, "
            f"hop_limit={hop_limit - 1}"
        )

    except (ValueError, KeyError, TypeError, OSError) as error:
        print(
            f"ERROR: forwarding failed at {device_name}: {error}"
        )
