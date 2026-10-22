import json
import sys
import socket

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

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", udp_port))

data, address = sock.recvfrom(1024)

message = data.decode()
print(message)