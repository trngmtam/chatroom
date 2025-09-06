import json
from datetime import datetime
import struct


def current_timestamp():
    return datetime.now().strftime("%H:%M:%S")


def build_message(msg_type, sender, message, receiver=None, file_data=None, timestamp=None):
    if not timestamp:
        timestamp = current_timestamp()
    msg = {
        "type": msg_type,
        "sender": sender,
        "timestamp": timestamp,
        "message": message
    }
    if receiver:
        msg["receiver"] = receiver
    if file_data:
        msg["file_data"] = file_data
    return json.dumps(msg)


def parse_message(message):
    return json.loads(message)

# New helper function to send a message with a header


def send_msg(sock, message):
    """
    Encodes a message and prepends a 4-byte header with the message length.
    """
    # Pack the length of the message into a 4-byte integer
    msg_len = struct.pack('>I', len(message))
    # Send the header followed by the message
    sock.sendall(msg_len + message)

# New helper function to receive a message with a header


def recv_msg(sock):
    """
    Receives a message by first reading the 4-byte length header.
    """
    # Read the 4-byte header to get the message length
    raw_msg_len = sock.recv(4)
    if not raw_msg_len:
        return None
    msg_len = struct.unpack('>I', raw_msg_len)[0]

    # Read the full message data based on the length
    data = b''
    while len(data) < msg_len:
        packet = sock.recv(msg_len - len(data))
        if not packet:
            return None
        data += packet
    return data
