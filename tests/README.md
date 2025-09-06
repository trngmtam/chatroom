# Unit Tests for Chatroom Project

This folder contains automated unit tests for the key components of the chatroom application. These tests help ensure each module works as expected and catches regressions early.

---

## 🗂️ Test Coverage

| File                  | Module Tested         | Description |
|-----------------------|-----------------------|-------------|
| `test_common.py`      | `shared/common.py`    | Tests JSON message building/parsing and socket communication helpers. |
| `test_encrypt.py`     | `shared/encrypt.py`   | Tests AES-based encryption and decryption using Fernet. |
| `test_server.py`      | `server/server.py`    | Tests server-side message routing and file upload handling. |
| `test_client.py`      | `client/client.py`    | Tests client-side message construction and response handling. |

---

## How to Run the Tests

Make sure you are in the **root directory** of your project:

```bash
python3 -m tests.test_common
python3 -m tests.test_encrypt
python3 -m tests.test_server
python3 -m tests.test_client

