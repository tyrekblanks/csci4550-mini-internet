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
