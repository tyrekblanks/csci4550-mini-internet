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

## Packet Format
Packets consist of a fixed 10-byte header followed by a payload with length 0-1,190 bytes. The maximum packet size is 1,200 bytes.
<table>
  <tr>
    <td colspan="2" align="center">
      <strong>Header</strong><br>
      10 bytes
    </td>
  </tr>
  <tr>
    <td align="center">
      Source Address<br>
      2 bytes
    </td>
    <td align="center">
      Destination Address<br>
      2 bytes
    </td>
  </tr>
  <tr>
    <td align="center">
      Hop Limit<br>
      1 byte
    </td>
    <td align="center">
      Message Type<br>
      1 byte
    </td>
  </tr>
  <tr>
    <td align="center">
      Message Identifier (ID)<br>
      2 bytes
    </td>
    <td align="center">
      Payload Length<br>
      2 bytes
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <strong>Payload</strong><br>
      0-1190 bytes
    </td>
  </tr>
</table>

### Header Fields
- **Source Address:** Virtual address of the sender.
- **Destination Address:** Virtual address of the receiver.
- **Hop Limit:** Maximum number of forwarding hops allowed before the packet is discarded.
- **Message Type:** Identifies the kind of message, such as a request(`1`), response(`2`), or error(`3`). Only message types defined by the implementation are accepted.
- **Message Identifier (ID):** A 16-bit identifier used to correlate messages, responses, and log records.
- **Payload Length:** Number of payload bytes, excluding the 10-byte header.

### Packet Encoding & Parsing
All header fields are represented by unsigned integers with big-endian encoding. The payload is represented as bytes and may contain UTF-8 text.

During packet creation, header field ranges and types are checked. During packet parsing, the receiver checks the total packet size, minimum header length, message type, and consistency between the declared payload length and the actual payload size. Packets exceeding the maximum size or failing size and type checks are rejected without terminating the process.

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
# Start one host as the listener
python3 host.py Host2 listen 1

# Start the other host as the sender
python3 host.py Host1 send 1
```

The host command format is:

```bash
python3 host.py <device_name> <send|listen> [probe_count] [config_file]
```

## Static Routing and Packet Forwarding

Each router uses a static routing table from its configuration file. The routing table maps a destination virtual address to a list containing the name of the next-hop neighbor.

Example:

```json
"routes": {
    "1": ["Host1"],
    "2": ["RouterB"]
}
```

The destination addresses are JSON string keys. The router selects the next hop for the packet's destination and forwards the packet to that neighbor's UDP port. Routers forward the original source address, destination address, message type, message ID, and payload without interpreting the application payload.

## Hop-Limit Rule

When a router receives a packet, it checks the hop limit before forwarding:

- If the incoming hop limit is less than or equal to 1, the router discards the packet.
- Otherwise, the router decreases the hop limit by 1 and forwards the packet.
- Discarded packets are logged with the timestamp, router name, reason, and available packet details.

This prevents packets caught in a routing loop from circulating indefinitely.

## Running the Upper Path

Open separate terminals in the project directory. Start all four routers first:

```bash
python3 router.py RouterA config_upper.json
python3 router.py RouterB config_upper.json
python3 router.py RouterC config_upper.json
python3 router.py RouterD config_upper.json
```

Then start Host2 in a separate terminal:

```bash
python3 host.py Host2 listen 1 config_upper.json
```

Finally, start Host1:

```bash
python3 host.py Host1 send 1 config_upper.json
```

The expected request path is Host1 → RouterA → RouterB → RouterD → Host2. The response should return through RouterD → RouterB → RouterA to Host1.

## Running the Lower Path

Stop all running routers and hosts before starting the next test. Start all four routers using the lower configuration:

```bash
python3 router.py RouterA config_lower.json
python3 router.py RouterB config_lower.json
python3 router.py RouterC config_lower.json
python3 router.py RouterD config_lower.json
```

Then start Host2:

```bash
python3 host.py Host2 listen 1 config_lower.json
```

Start Host1 last:

```bash
python3 host.py Host1 send 1 config_lower.json
```

The expected request path is Host1 → RouterA → RouterC → RouterD → Host2. The response should return through RouterD → RouterC → RouterA to Host1.

**Important:** Every device in a given test run must use the same configuration file. Stop the previous run before switching configurations.

## Timeout Behavior

A host operating in `send` mode waits up to 5 seconds for the response to each probe. If no response arrives within that period, the host records a structured timeout log containing the probe identifier.

This behavior applies to either Host1 or Host2 when operating as the sender and allows the source host to detect missing responses or unreachable paths instead of waiting indefinitely.

## Network Conditions and Core Checkpoint Testing

Network conditions may be configured in `config.json`. A selected directed link may specify a packet-loss probability and additional delivery delay.

Example:

```json
"network_conditions": {
    "seed": 42,
    "links": [
        {
            "from": "RouterA",
            "to": "RouterB",
            "loss_probability": 0.05,
            "delay_ms": 100
        }
    ]
}
```

The random seed makes packet-loss behavior reproducible. Delayed packets are scheduled for later delivery without blocking unrelated packet handling.

Network events use structured logs that include the run ID, device, timestamp, message ID, message type, source, destination, hop limit, next hop, event type, and additional details.

The core network checkpoint was tested for:

- 20 request/response probes initiated by Host1
- 20 request/response probes initiated by Host2
- Upper static route through RouterB
- Lower static route through RouterC
- Forwarding-loop termination using the hop limit
- Unknown-destination packet handling
- Malformed-packet handling
- Missing-response timeout behavior
- Forced packet loss
- Seeded random packet loss
- Configurable delivery delay
