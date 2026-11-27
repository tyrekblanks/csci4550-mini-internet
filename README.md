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
          RouterB
         /       \
Host1 -- RouterA   RouterD -- Host2
         \       /
          RouterC
```

RouterA connects to both RouterB and RouterC, creating two possible paths toward RouterD.

Router-to-router links have configurable positive costs. These costs are used by the routing algorithm to determine the shortest forwarding path.

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

## Dynamic Routing and Packet Forwarding

Router-to-router forwarding paths are computed from the shared network topology using Dijkstra's shortest-path algorithm.

The topology is defined in `config.json` using configurable positive link costs.

Example:

```json
"topology": {
    "links": [
        {
            "node1": "RouterA",
            "node2": "RouterB",
            "cost": 1
        },
        {
            "node1": "RouterA",
            "node2": "RouterC",
            "cost": 1
        },
        {
            "node1": "RouterB",
            "node2": "RouterD",
            "cost": 1
        },
        {
            "node1": "RouterC",
            "node2": "RouterD",
            "cost": 1
        }
    ]
}
```

The destination addresses are JSON string keys. The router selects the next hop for the packet's destination and forwards the packet to that neighbor's UDP port. Routers forward the original source address, destination address, message type, message ID, and payload without interpreting the application payload.

## Hop-Limit Rule

When a router receives a packet, it checks the hop limit before forwarding:

- If the incoming hop limit is less than or equal to 1, the router discards the packet.
- Otherwise, the router decreases the hop limit by 1 and forwards the packet.
- Discarded packets are logged with the timestamp, router name, reason, and available packet details.

This prevents packets caught in a routing loop from circulating indefinitely.

## Running the Static Upper Path

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

## Running the Static Lower Path

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

### Dynamic Router-to-Router Link Failure
**Reproduction Note:** The original tests were performed using static routing. Set `adaptive_routing` to `false` in `config.json` before reproducing these tests. Restore it to
`true` afterward to enable automatic route recomputation.

The network supports dynamic router-to-router link
failures through a shared `link_failures.json` file. Routers monitor this file during operation, allowing links to be disabled or restored without restarting any network devices.

Each failed link is treated as bidirectional. Routers check the status of a link before forwarding packets and again before transmitting queued delayed packets. If the link is disabled, the packet is dropped and the failure is recorded in the router's log.

Changes to the failed-links list are recorded using the `link_state_change` event.

The default contents of `link_failures.json` are:

    {
        "failed_links": []
    }

To disable the connection between RouterA and RouterB, update the file to:

    {
        "failed_links": [
            {
                "from": "RouterA",
                "to": "RouterB"
            }
        ]
    }

To restore the connection, reset the failed-links
list to an empty list.

This implementation handles link failure detection
and prevents packet transmission across failed links.

#### Testing Instructions

Run all commands from the project root directory.

**Test 1: Dynamic Link Failure**

1. Ensure `link_failures.json` contains an empty
   failed-links list.
2. Start each router in a separate terminal:

   ```powershell
   py router.py RouterA config.json
   py router.py RouterB config.json
   py router.py RouterC config.json
   py router.py RouterD config.json
   ```

3. Start Host2 as the listener:

   ```powershell
   py host.py Host2 listen 1 config.json
   ```

4. Send three baseline probes from Host1:

   ```powershell
   py host.py Host1 send 3 config.json
   ```

5. Disable the RouterA-RouterB link by updating
   `link_failures.json` as described above.
6. Confirm that the routers log a `link_state_change` event.
7. Repeat the Host1 send command and verify that
   all three probes time out and RouterA logs
   link-failure drops.

**Test 2: Reverse-Direction Link Failure**

1. Keep the RouterA-RouterB link disabled.
2. Stop the Host2 listener.
3. Start Host1 as the listener:

   ```powershell
   py host.py Host1 listen 1 config.json
   ```

4. Send three probes from Host2:

   ```powershell
   py host.py Host2 send 3 config.json
   ```

5. Verify that all three probes time out and
   RouterB logs link-failure drops.

**Test 3: Link Restoration**

1. Keep all routers and the Host1 listener      running.
2. Reset `link_failures.json` to an empty
   failed-links list.
3. Confirm that the routers detect the change.
4. Repeat the Host2 send command.
5. Verify that communication resumes without
   restarting the routers.

**Test 4: Queued Delayed-Packet Failure**

1. Stop all running network processes.
2. Reset `link_failures.json` to an empty
   failed-links list.
3. Restart all four routers using
   `config_delayed_failure.json`.
4. Start Host2 as the listener using the same
   configuration.
5. Run the following PowerShell commands from
   the Host1 terminal:

   ```powershell
   $probe = Start-Process py -ArgumentList "host.py Host1 send 1 config_delayed_failure.json" -NoNewWindow -PassThru
   Start-Sleep -Milliseconds 1000
   '{"failed_links":[{"from":"RouterA","to":"RouterB"}]}' | Set-Content -Encoding ascii link_failures.json
   $probe.WaitForExit()
   ```

6. Verify that RouterA logs a scheduled delay,
   a link-state change, and a packet drop rather
   than completing the delayed transmission.
7. Stop the network and reset `link_failures.json`
   to an empty failed-links list.

#### Test Results

| Test | Successful Probes | Timeouts | Result |
|---|---:|---:|---|
| Baseline communication | 2/3 | 1 | Pass |
| Forward-direction failure | 0/3 | 3 | Pass |
| Reverse-direction failure | 0/3 | 3 | Pass |
| Link restoration | 3/3 | 0 | Pass |
| Queued delayed-packet failure | 0/1 | 1 | Pass |

The baseline timeout was caused by the configured
5% random packet loss rather than an intentional
link failure.

These results demonstrate that failed links prevent packet transmission in both directions, including packets already queued for delayed transmission. Communication resumes when the failed link is restored.

Supporting logs are available in
`test-evidence/4.1e-link-failure/`.

### Automatic Route Recomputation

#### Implementation

Routers automatically recompute their forwarding tables when a router-to-router link fails or is restored.

- Updated `build_graph()` in `routing.py` to exclude failed links while preserving disconnected routers in the graph.
- Routers monitor the shared `link_failures.json` file for changes in link status.
- When a change is detected, routers rebuild the topology graph and rerun Dijkstra's shortest-path algorithm.
- Added an `adaptive_routing` configuration option to allow comparison between static and adaptive routing.
- Packets are discarded with an explicit unreachable-destination message when no available route exists.
- Routing initialization and recomputation events are recorded in the router logs.

#### Reproducing the Tests

Two configurations are provided:

- `config_adaptive_test.json`: Adaptive routing enabled.
- `config_static_test.json`: Adaptive routing disabled.

Both configurations use 0% random packet loss and a configured 100 ms delay from RouterA to RouterB.

Before starting, ensure `link_failures.json` contains:

```json
{
    "failed_links": []
}
```

Start each router in a separate terminal:

```powershell
py router.py RouterA config_adaptive_test.json
py router.py RouterB config_adaptive_test.json
py router.py RouterC config_adaptive_test.json
py router.py RouterD config_adaptive_test.json
```

Start the Host2 listener:

```powershell
py host.py Host2 listen 1 config_adaptive_test.json
```

Send three probes from Host1:

```powershell
py host.py Host1 send 3 config_adaptive_test.json
```

To introduce a link failure, update `link_failures.json`:

```json
{
    "failed_links": [
        {
            "from": "RouterA",
            "to": "RouterB"
        }
    ]
}
```

Send another three probes without restarting the routers. Adaptive routing should automatically switch to RouterC.

To test an unreachable destination, disable both the RouterA-RouterB and RouterA-RouterC links:

```json
{
    "failed_links": [
        {
            "from": "RouterA",
            "to": "RouterB"
        },
        {
            "from": "RouterA",
            "to": "RouterC"
        }
    ]
}
```

Send another three probes. All probes should time out because RouterA has no available route to RouterD.

Restore both links by setting `failed_links` to an empty list. Send three more probes to verify that the original route is restored.

For the static routing comparison, stop all processes, reset the failure file, and repeat the baseline and single-link failure tests using `config_static_test.json` instead.

#### Functional Test Results

| Routing Mode | Network Condition | Next Hop | Responses | Timeouts | Success Rate |
|---|---|---|---|---|---|
| Adaptive | Normal | RouterB | 3/3 | 0 | 100% |
| Adaptive | A-B failure | RouterC | 3/3 | 0 | 100% |
| Adaptive | A-B and A-C failure | None | 0/3 | 3 | 0% |
| Adaptive | Links restored | RouterB | 3/3 | 0 | 100% |
| Static | Normal | RouterB | 3/3 | 0 | 100% |
| Static | A-B failure | RouterB | 0/3 | 3 | 0% |

#### Analysis

Adaptive routing successfully maintained communication between Host1 and Host2 after the RouterA-RouterB link failed by automatically selecting the alternate path through RouterC.

Static routing continued selecting RouterB after the failure, causing all three probes to time out. When both available paths were disabled, adaptive routing correctly identified the
destination as unreachable.

Restoring the failed links allowed the adaptive routers to recompute their original forwarding tables without restarting.

These results demonstrate functional correctness. Repeated quantitative experiments and recovery-time measurements will be conducted during the experimental evaluation.

#### Test Evidence

Logs for these tests are available in:
`test-evidence/4.1f-route-recomputation/`