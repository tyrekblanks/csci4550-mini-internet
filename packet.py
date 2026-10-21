import struct

# Header: source, destination, hop limit, type, message ID, payload length
HEADER_FORMAT = "!HHBBHH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)        # 10 bytes

MAX_PACKET_SIZE = 1200
MAX_PAYLOAD_SIZE = MAX_PACKET_SIZE - HEADER_SIZE    # up to 1190 bytes

# Message types
REQUEST = 1
RESPONSE = 2
ERROR = 3

VALID_MESSAGE_TYPES = {REQUEST, RESPONSE, ERROR}

def create_packet(src, dst, hop_limit, msg_type, msg_id, payload):
    """Serialize packet fields into bytes"""

    if not isinstance(payload, bytes):
        raise ValueError("Payload must be bytes")
    if len(payload) > MAX_PAYLOAD_SIZE:
        raise ValueError("Paylaod is too large")

    if not 0 <= src <= 65535:
        raise ValueError("Invalid source address: out of range 0-65535")
    if type(src) is not int:
        raise ValueError("Invalid source address: not type int")

    if not 0 <= dst <= 65535:
        raise ValueError("Invalid destination address: out of range 0-65535")
    if type(dst) is not int:
        raise ValueError("Invalid destination address: not type int")

    if not 0 <= hop_limit <= 255:
        raise ValueError("Invalid hop limit: out of range 0-255")
    if type(hop_limit) is not int:
        raise ValueError("Invalid hop limit: not type int")

    if msg_type not in VALID_MESSAGE_TYPES:
        raise ValueError("Invalid message type: REQUEST=1, RESPONSE=2, ERROR=3")
    if type(msg_type) is not int:
        raise ValueError("Invalid message type: not type int")

    if not 0 <= msg_id <= 65535:
        raise ValueError("Invalid message ID: out of range 0-65535")
    if type(msg_id) is not int:
        raise ValueError("Invalid message ID: not type int")

    header = struct.pack(
        HEADER_FORMAT,
        src,
        dst,
        hop_limit,
        msg_type,
        msg_id,
        len(payload),
    )

    return header + payload

def parse_packet(data):
    """Validate and parse a packet received as bytes"""

    if not isinstance(data, bytes):
        raise ValueError("Packet must be bytes")

    if len(data) > MAX_PACKET_SIZE:
        raise ValueError("Packet is too large, max: 1200 bytes")

    if len(data) < HEADER_SIZE:
        raise ValueError("Packet is shorter than the header, < 10 bytes")

    src, dst, hop_limit, msg_type, msg_id, payloud_length = (
        struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])
    )

    if msg_type not in VALID_MESSAGE_TYPES:
        raise ValueError("Unknown message type: REQUEST=1, RESPONSE=2, ERROR=3")

    actual_payload_length = len(data) - HEADER_SIZE

    if payloud_length != actual_payload_length:
        raise ValueError("Payload length does nto match packet size")

    payload = data[HEADER_SIZE:]

    return {
        "src": src,
        "dst": dst,
        "hop_limit": hop_limit,
        "msg_type": msg_type,
        "msg_id": msg_id,
        "payload": payload,
    }