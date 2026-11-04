import json
import sys
import socket
from datetime import datetime
from packet import create_packet, parse_packet, REQUEST, RESPONSE

if len(sys.argv) > 4:
    config_file = sys.argv[4]
else:
    config_file = "config.json"

with open(config_file, "r") as file:
    config = json.load(file)

if len(sys.argv) < 2:
    print("Usage: python3 host.py <device_name> <send|listen> [probe_count] [config_file]")
    sys.exit()

device_name = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else "listen"
probe_count = int(sys.argv[3]) if len(sys.argv) > 3 else 1
devices = config["devices"]
run_id = config.get("run_id", "default-run")

if device_name not in devices:
    print(f"Error: device '{device_name}' not found in config")
    sys.exit()

device = devices[device_name]

if device["type"] != "host":
    print("Error: selected device is not a host")
    sys.exit()

virtual_address = device["virtual_address"]
udp_port = device["UDP_port"]

if device_name == "Host1":
    peer_address = 2
    peer_name = "Host2"
else:
    peer_address = 1
    peer_name = "Host1"

def log_event(event, packet=None, details=None):
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

    if details is not None:
        parts.append(f"details={details}")

    print(" | ".join(parts))

neighbors = device["neighbors"]
neighbor_name = neighbors[0]
neighbor = devices[neighbor_name]

neighbor_port = neighbor["UDP_port"]
neighbor_host = neighbor.get("UDP_host", "127.0.0.1")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", udp_port))
sock.settimeout(5.0)

if mode == "send":
    # The selected host sends requests to its peer.
    message = b"hello router"

    for msg_id in range(1, probe_count + 1):
        packet_data = create_packet(
            src=virtual_address,
            dst=peer_address,
            hop_limit=16,
            msg_type=REQUEST,
            msg_id=msg_id,
            payload=message
        )

        sock.sendto(packet_data, (neighbor_host, neighbor_port))

        log_event(
            "send",
            {
                "msg_id": msg_id,
                "msg_type": REQUEST,
                "src": virtual_address,
                "dst": peer_address,
                "hop_limit": 16,
            },
            details=f"sent request to {neighbor_name}"
        )

        try:
            data, address = sock.recvfrom(1200)
            packet = parse_packet(data)

            log_event(
                "receive",
                packet,
                details=f"received from UDP endpoint {address}"
            )

            if packet["dst"] != virtual_address:
                print(f"{device_name}: received a packet for another host")
            elif packet["msg_type"] == RESPONSE:
                print(f"{device_name} received:", packet["payload"].decode("utf-8"))

        except socket.timeout:
            log_event(
                "timeout",
                details=f"probe {msg_id} did not receive a reply within 5 seconds"
            )

elif mode == "listen":
    # The selected host waits for a request from its peer.
    print(f"{device_name}: waiting for a request")

    while True:
        try:
            data, address = sock.recvfrom(1200)
            packet = parse_packet(data)

            log_event(
                "receive",
                packet,
                details=f"received from UDP endpoint {address}"
            )

            if packet["dst"] != virtual_address:
                print(f"{device_name}: packet is not addressed to me")
                continue

            if packet["msg_type"] != REQUEST:
                print(f"{device_name}: ignoring a non-request packet")
                continue

            print(
                f"{device_name} received:",
                packet["payload"].decode("utf-8")
            )

            response_data = create_packet(
                src=virtual_address,
                dst=packet["src"],
                hop_limit=16,
                msg_type=RESPONSE,
                msg_id=packet["msg_id"],
                payload=f"Hello back from {device_name}!".encode("utf-8")
            )

            sock.sendto(
                response_data,
                ("127.0.0.1", neighbor_port)
            )

            log_event(
                "send",
                {
                    "msg_id": packet["msg_id"],
                    "msg_type": RESPONSE,
                    "src": virtual_address,
                    "dst": packet["src"],
                    "hop_limit": 16,
                },
                details=f"sent response to {neighbor_name}"
            )

        except socket.timeout:
            print(f"{device_name}: still waiting for a request")

        except ValueError as error:
            print(f"{device_name}: discarded malformed packet: {error}")