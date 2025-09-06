# Shared Module Reference

This folder contains all files used across server, client, and GUI to ensure consistency.

- `protocol.md` — Message structure definition
- `config.py` — Common constants like IP/PORT, emoji map
- `encrypt.py` — AES encryption functions
- `common.py` — Helper functions to build/parse JSON messages

## How to Use

In `client.py`, `server.py`, or `gui.py`:

```python
from shared.config import SERVER_IP, SERVER_PORT
from shared.encrypt import encrypt_message, decrypt_message
from shared.common import build_message, parse_message
```
