import json
import sys
import socket
import random
import time
import heapq
from datetime import datetime
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

run_id = config.get("run_id", "default-run")

network_conditions = config.get("network_conditions", {})
random_seed = network_conditions.get("seed")
link_conditions = network_conditions.get("links", [])

if random_seed is not None:
    random.seed(random_seed)

device = devices[device_name]

if device["type"] != "router":
    print("Error: selected device is not a router")
    sys.exit()

virtual_address = device["virtual_address"]
udp_port = device["UDP_port"]
neighbors = device["neighbors"]
routing_table = device.get("routes", {})

def log_event(event, packet=None, next_hop=None, details=None):
    timestamp = datetime.now().isoformat(timespec="seconds")

    parts = [
        f"run_id={run_id}",
        f"device={device_name}",
        f"timestamp={timestamp}",
        f"event={event}",
    ]

    if packet is not None:
        parts.extend([
            f"msg_id={packet['msg_id']}",
            f"msg_type={packet['msg_type']}",
            f"src={packet['src']}",
            f"dst={packet['dst']}",
            f"hop_limit={packet['hop_limit']}",
        ])

    if next_hop is not None:
        parts.append(f"next_hop={next_hop}")

    if details is not None:
        parts.append(f"details={details}")

    print(" | ".join(parts))

#logging helper
def log_discard(reason, packet=None):
    log_event(
        "drop",
        packet,
        details=reason
    )

#socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", udp_port))
sock.settimeout(0.05)

delayed_sends = []

print(f"{device_name} listening on port {udp_port}")

# Keep receiving packets until the router is stopped
while True:
    while delayed_sends and delayed_sends[0][0] <= time.monotonic():
        (
            send_time,
            packet_to_send,
            target_host,
            target_port,
            target_name,
            original_packet,
        ) = heapq.heappop(delayed_sends)

        try:
            sock.sendto(packet_to_send, (target_host, target_port))

            log_event(
                "send",
                original_packet,
                next_hop=target_name,
                details=f"delayed send completed"
            )
        except OSError as error:
            log_event(
                "drop",
                original_packet,
                next_hop=target_name,
                details=f"delayed send failed: {error}"
            )
        
    try:
        data, address = sock.recvfrom(1200)
    except socket.timeout:
        continue
    except OSError as error:
        print(f"{device_name}: socket receive error: {error}")
        continue

    # 1. Parse the incoming packet
    try:
        packet = parse_packet(data)
    except (ValueError, KeyError, TypeError) as error:
        log_discard(f"malformed packet: {error}")
        continue

    log_event(
        "receive",
        packet,
        details=f"received from UDP endpoint {address}"
    )

    destination = packet["dst"]
    hop_limit = packet["hop_limit"]

    # 2. Check the hop limit before forwarding
    if hop_limit <= 1:
        log_discard("hop limit exhausted", packet)
        continue

    # 3. Find the destination in the routing table.
    # JSON object keys are strings, so convert the address.
    next_hop = routing_table.get(str(destination))

    if next_hop is None:
        log_discard("unknown destination", packet)
        continue

    # 4. Get and validate the next-hop neighbor
    if not isinstance(next_hop, list) or len(next_hop) == 0:
        log_discard("invalid next hop", packet)
        continue

    next_hop_name = next_hop[0]

    if next_hop_name not in neighbors:
        log_discard("invalid next hop", packet)
        continue

    next_hop_device = devices.get(next_hop_name)

    if next_hop_device is None:
        log_discard("next hop missing from configuration", packet)
        continue

    link_condition = None

    for condition in link_conditions:
        if (
            condition.get("from") == device_name
            and condition.get("to") == next_hop_name
        ):
            link_condition = condition
            break

    if link_condition is not None:
        loss_probability = link_condition.get("loss_probability", 0)

        if random.random() < loss_probability:
            log_event(
                "drop",
                packet,
                next_hop=next_hop_name,
                details=f"injected loss on {device_name}->{next_hop_name}"
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
        delay_ms = 0

        if link_condition is not None:
            delay_ms = link_condition.get("delay_ms", 0)

        if delay_ms > 0:
            send_time = time.monotonic() + (delay_ms / 1000.0)

            heapq.heappush(
                delayed_sends,
                (
                    send_time,
                    forwarded_packet,
                    next_host,
                    next_port,
                    next_hop_name,
                    {
                        **packet,
                        "hop_limit": hop_limit - 1,
                    }
                )
            )

            log_event(
                "delay",
                packet,
                next_hop=next_hop_name,
                details=f"scheduled with {delay_ms} ms delay"
            )

        else:
            sock.sendto(forwarded_packet, (next_host, next_port))

            log_event(
                "forward",
                {
                    **packet,
                    "hop_limit": hop_limit - 1,
                },
                next_hop=next_hop_name,
                details="packet forwarded"
            )

    except (ValueError, KeyError, TypeError, OSError) as error:
        log_event(
            "drop",
            packet,
            next_hop=next_hop_name,
            details=f"forwarding failed: {error}"
        )
