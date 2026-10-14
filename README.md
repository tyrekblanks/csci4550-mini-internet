# csci4550-mini-internet

First-day research:
- Relevant Python libraries: import socket, threading, json, time
- need client, server, router, packet, and config files
- links:
  - https://docs.python.org/3/library/socket.html
  - https://wiki.python.org/moin/UdpCommunication.html

## Topology

The network uses the following topology:

```text
Host1 -- RouterA -- RouterB -- RouterD -- Host2
                  \         /
                   RouterC
```

RouterA connects to both RouterB and RouterC, creating two possible paths toward RouterD.

## Starting the Network

Each device runs as its own process. Open a separate terminal window for each device and run the following commands from the project directory.

### Routers

```bash
python3 router.py RouterA
python3 router.py RouterB
python3 router.py RouterC
python3 router.py RouterD
```

### Hosts

```bash
python3 host.py Host1
python3 host.py Host2
```