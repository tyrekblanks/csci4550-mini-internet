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
python3 host.py Host1
python3 host.py Host2
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

```powershell
py router.py RouterA config_upper.json
py router.py RouterB config_upper.json
py router.py RouterC config_upper.json
py router.py RouterD config_upper.json
```

Then start Host2 in a separate terminal:

```powershell
py host.py Host2 config_upper.json
```

Finally, start Host1:

```powershell
py host.py Host1 config_upper.json
```

The expected request path is Host1 → RouterA → RouterB → RouterD → Host2. The response should return through RouterD → RouterB → RouterA to Host1.

## Running the Lower Path

Stop all running routers and hosts before starting the next test. Start all four routers using the lower configuration:

```powershell
py router.py RouterA config_lower.json
py router.py RouterB config_lower.json
py router.py RouterC config_lower.json
py router.py RouterD config_lower.json
```

Then start Host2:

```powershell
py host.py Host2 config_lower.json
```

Start Host1 last:

```powershell
py host.py Host1 config_lower.json
```

The expected request path is Host1 → RouterA → RouterC → RouterD → Host2. The response should return through RouterD → RouterC → RouterA to Host1.

**Important:** Every device in a given test run must use the same configuration file. Stop the previous run before switching configurations.

## Timeout Behavior

Host1 waits up to 5 seconds for a response. If no response arrives within that period, it prints a timeout message. This allows the source host to detect a failed or unreachable path instead of waiting forever.
