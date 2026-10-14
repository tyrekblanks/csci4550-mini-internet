import json
import sys
import socket

with open("config.json", "r") as file:
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

print(neighbor["UDP_port"])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", udp_port))

neighbor_port = neighbor["UDP_port"]

message = "hello router"
sock.sendto(message.encode(), ("127.0.0.1", neighbor_port))

data, address = sock.recvfrom(1024)

message = data.decode()

print(message)