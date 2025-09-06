import unittest
import json
import struct
from io import BytesIO
from shared.common import build_message, parse_message, send_msg, recv_msg, current_timestamp


class MockSocket:
    def __init__(self):
        self.buffer = BytesIO()

    def sendall(self, data):
        self.buffer.write(data)
        self.buffer.seek(0)  # Only seek once after full write

    def recv(self, n):
        return self.buffer.read(n)

class TestCommonModule(unittest.TestCase):

    def test_current_timestamp_format(self):
        ts = current_timestamp()
        self.assertRegex(ts, r"^\d{2}:\d{2}:\d{2}$")  # HH:MM:SS

    def test_build_message_minimal(self):
        msg_str = build_message("chat", "tam", "hello")
        msg = json.loads(msg_str)
        self.assertEqual(msg["type"], "chat")
        self.assertEqual(msg["sender"], "tam")
        self.assertEqual(msg["message"], "hello")
        self.assertIn("timestamp", msg)

    def test_build_message_with_receiver_and_file(self):
        msg_str = build_message(
            "file",
            "tam",
            "sending file",
            receiver="quynh",
            file_data={"filename": "test.txt", "content": "base64data"}
        )
        msg = json.loads(msg_str)
        self.assertEqual(msg["receiver"], "quynh")
        self.assertIn("file_data", msg)
        self.assertEqual(msg["file_data"]["filename"], "test.txt")

    def test_parse_message_valid(self):
        original = {"type": "notice", "sender": "server", "message": "Welcome"}
        json_str = json.dumps(original)
        parsed = parse_message(json_str)
        self.assertEqual(parsed, original)

    def test_parse_invalid_json_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            parse_message("{invalid json}")

    def test_send_and_receive_msg(self):
        sock = MockSocket()
        message = b"Hello, this is a test."
        send_msg(sock, message)

        # Reset buffer to simulate receiving
        sock.buffer.seek(0)
        received = recv_msg(sock)
        self.assertEqual(received, message)

    def test_recv_msg_returns_none_on_empty(self):
        empty_sock = MockSocket()
        self.assertIsNone(recv_msg(empty_sock))

if __name__ == '__main__':
    print("Testing: common.py")
    unittest.main()
