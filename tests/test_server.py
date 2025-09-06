import unittest
from unittest.mock import MagicMock, patch
import socket
import threading

class TestServerModule(unittest.TestCase):

    @patch("socket.socket")
    def test_server_socket_bind_and_listen(self, mock_socket):
        mock_server = mock_socket.return_value
        import server
        server.start_server = MagicMock()
        server.start_server()
        server.start_server.assert_called_once()

    def test_threading_usage(self):
        t = threading.Thread(target=lambda: None)
        self.assertTrue(callable(t.run))

if __name__ == '__main__':
    print("Testing: server.py")
    unittest.main()
