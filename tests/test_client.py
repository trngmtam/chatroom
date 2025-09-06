import unittest
import base64
import os
import json
from unittest.mock import MagicMock, patch
from client import client


class DummySocket:
    def __init__(self):
        self.sent_data = []

    def sendall(self, data):
        self.sent_data.append(data)

    def get_last_sent(self):
        return self.sent_data[-1] if self.sent_data else None


class TestClientModule(unittest.TestCase):

    def test_apply_emoji(self):
        text = "Hello :smile: world :rocket:"
        result = client.apply_emoji(text)
        self.assertIn("😄", result)
        self.assertIn("🚀", result)

    def test_current_timestamp_format(self):
        ts = client.current_timestamp()
        self.assertRegex(ts, r"^\d{2}:\d{2}:\d{2}$")

    @patch("client.client.send_msg")
    def test_request_file_download_sends_correct_message(self, mock_send_msg):
        mock_sock = DummySocket()
        client.request_file_download(mock_sock, "file123", "tam")
        args, _ = mock_send_msg.call_args
        encrypted_json = args[1]
        decrypted_json = client.decrypt_message(encrypted_json)
        msg = json.loads(decrypted_json)
        self.assertEqual(msg["type"], "file_download_request")
        self.assertEqual(msg["file_id"], "file123")
        self.assertEqual(msg["sender"], "tam")

    @patch("client.client.send_msg")
    def test_send_file_rejects_large_file(self, mock_send_msg):
        # Simulate a 200MB file
        with patch("os.path.getsize", return_value=200 * 1024 * 1024):
            result = client.send_file(DummySocket(), "fakefile.txt", None, "tam")
            self.assertFalse(mock_send_msg.called)

    @patch("client.client.send_msg")
    def test_send_file_success(self, mock_send_msg):
        test_content = b"Sample file content"
        fake_path = "fake.txt"

        with patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=len(test_content)), \
             patch("builtins.open", new_callable=unittest.mock.mock_open, read_data=test_content):

            client.send_file(DummySocket(), fake_path, "quynh", "tam")

            # Expect 2 messages: file_upload and file notification
            self.assertEqual(mock_send_msg.call_count, 2)

            encrypted_msg = mock_send_msg.call_args_list[0][0][1]
            decrypted_msg = client.decrypt_message(encrypted_msg)
            msg = json.loads(decrypted_msg)
            self.assertEqual(msg["type"], "file_upload")
            self.assertEqual(msg["sender"], "tam")
            self.assertEqual(msg["filename"], "fake.txt")


if __name__ == "__main__":
    print("Testing: client.py")
    unittest.main()
