# Chatroom Message Protocol (JSON Format)

This document defines the structure of all messages exchanged between clients and the server.

---

## Common Fields

| Field       | Type   | Required | Description                                             |
| ----------- | ------ | -------- | ------------------------------------------------------- |
| `type`      | string | Yes      | `public`, `private`, `file`, `system`                   |
| `sender`    | string | Yes      | Sender's username                                       |
| `receiver`  | string | No       | Recipient username (only for private or file)           |
| `timestamp` | string | Yes      | Message time (HH:MM:SS)                                 |
| `message`   | string | Yes      | The text content or file name                           |
| `file_data` | string | No       | Base64 encoded file content (only for `type == "file"`) |

---

## Examples

### Public

```json
{
  "type": "public",
  "sender": "Alice",
  "timestamp": "12:00:01",
  "message": "Hello everyone!"
}
```

### Private

```json
{
  "type": "private",
  "sender": "Alice",
  "receiver": "Bob",
  "timestamp": "12:01:01",
  "message": "Hi Bob"
}
```

### File - Private

```json
{
  "type": "file",
  "sender": "Alice",
  "receiver": "Bob",
  "timestamp": "12:02:01",
  "message": "report.pdf",
  "file_data": "aGVsbG8gd29ybGQK..." // Base64
}
```

### File - Public

```json
{
  "type": "file",
  "sender": "Alice",
  "timestamp": "12:02:01",
  "message": "report.pdf",
  "file_data": "aGVsbG8gd29ybGQK..." // Base64
}
```

### System Notifications

```json
{
  "type": "system",
  "sender": "server",
  "timestamp": "12:03:01",
  "message": "Alice joined the chat"
}
```
