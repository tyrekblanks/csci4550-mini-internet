import json
import sys
import socket
from packet import create_packet, parse_packet, REQUEST, RESPONSE

if len(sys.argv) > 2:
    config_file = sys.argv[2]
else:
    config_file = "config.json"

with open(config_file, "r") as file:
    config = json.load(file)

if len(sys.argv) < 2:
    print("Usage: python3 host.py <device_name>")
    sys.exit()

device_name = sys.argv[1]
devices = config["devices"]

if device_name not in devices:
    print(f"Error: device '{device_name}' not found in config")
    sys.exit()

device = devices[device_name]

if device["type"] != "host":
    print("Error: selected device is not a host")
    sys.exit()

virtual_address = device["virtual_address"]
udp_port = device["UDP_port"]


neighbors = device["neighbors"]
neighbor_name = neighbors[0]
neighbor = devices[neighbor_name]

neighbor_port = neighbor["UDP_port"]
neighbor_host = neighbor.get("UDP_host", "127.0.0.1")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", udp_port))
sock.settimeout(5.0)

if device_name == "Host1":
    # Host1 sends a request to Host2.
    message = b"hello router"

    packet_data = create_packet(
        src=virtual_address,
        dst=2,
        hop_limit=16,
        msg_type=REQUEST,
        msg_id=1,
        payload=message
    )

    sock.sendto(packet_data, (neighbor_host, neighbor_port))
    print("Host1: request sent to Host2")

    try:
        data, address = sock.recvfrom(1200)
        packet = parse_packet(data)

        if packet["dst"] != virtual_address:
            print("Host1: received a packet for another host")
        elif packet["msg_type"] == RESPONSE:
            print("Host1 received:", packet["payload"].decode("utf-8"))

    except socket.timeout:
        print("TIMEOUT: Host1 did not receive a reply within 5 seconds")

elif device_name == "Host2":
    # Host2 waits for a request from Host1.
    print("Host2: waiting for a request")

    while True:
        try:
            data, address = sock.recvfrom(1200)
            packet = parse_packet(data)

            if packet["dst"] != virtual_address:
                print("Host2: packet is not addressed to me")
                continue

            if packet["msg_type"] != REQUEST:
                print("Host2: ignoring a non-request packet")
                continue

            print(
                "Host2 received:",
                packet["payload"].decode("utf-8")
            )

            response_data = create_packet(
                src=virtual_address,
                dst=packet["src"],
                hop_limit=16,
                msg_type=RESPONSE,
                msg_id=packet["msg_id"],
                payload=b"Hello back from Host2!"
            )

            sock.sendto(
                response_data,
                ("127.0.0.1", neighbor_port)
            )
            print("Host2: reply sent")

        except socket.timeout:
            print("Host2: still waiting for a request")

        except ValueError as error:
            print(f"Host2: discarded malformed packet: {error}")
