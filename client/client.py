import socket
import sys
import threading
from datetime import datetime
import base64
import os
import json

# Import the helper functions and config
from client import gui
from shared.encrypt import encrypt_message, decrypt_message
from shared.common import build_message, parse_message, send_msg, recv_msg
from shared.config import SERVER_IP, SERVER_PORT

# Create a directory for downloads if it doesn't exist
CLIENT_DOWNLOADS_DIR = "client_downloads"
os.makedirs(CLIENT_DOWNLOADS_DIR, exist_ok=True)

EMOJI_MAP = {
    # Faces
    ":smile:": "😄",
    ":laugh:": "😂",
    ":wink:": "😉",
    ":cry:": "😢",
    ":thinking:": "🤔",
    ":sunglasses:": "😎",
    ":party:": "🥳",

    # Gestures
    ":thumbsup:": "👍",
    ":thumbsdown:": "👎",
    ":ok_hand:": "👌",
    ":clap:": "👏",
    ":pray:": "🙏",

    # Hearts
    ":heart:": "❤️",
    ":broken_heart:": "💔",
    ":blue_heart:": "💙",

    # Objects & Symbols
    ":fire:": "🔥",
    ":rocket:": "🚀",
    ":star:": "⭐",
    ":cake:": "🍰",
    ":coffee:": "☕",
}


def apply_emoji(text):
    for code, emoji in EMOJI_MAP.items():
        text = text.replace(code, emoji)
    return text

def receive_messages(sock, username):
    while True:
        try:
            # Receiving function
            data = recv_msg(sock)
            if not data:
                print("\n[SYSTEM] Server closed the connection.")
                os._exit(0)  # Use os._exit to force exit from thread

            decrypted = decrypt_message(data)
            
            msg = parse_message(decrypted)

            msg_type = msg.get("type")
            sender = msg.get("sender")
            raw_message = msg.get("message", "")
            message = apply_emoji(raw_message)
            receiver = msg.get("receiver", None)
            timestamp = msg.get("timestamp", "")

            if msg_type == "system":
                if message.startswith("user_list:"):
                    users = message.split(":", 1)[1].split(",")
                    print(f"\n[USERS] Active users: {', '.join(users)}")
                    gui.root.after(0, lambda: gui.update_users_list(users))

                else:
                    print(f"\n[SYSTEM] {message}")
                    gui.root.after(0, lambda m=message: gui.append_to_chat(m, "system"))
            
            elif message == "username_rejected":
                gui.username_rejected = True  # Trigger flag to re-show input dialog

            elif msg_type == "public":
                print(f"\n(Global) {timestamp} {sender} > {message}")

            elif msg_type == "private":
                if sender == username:
                    print(f"\n(Private to {receiver}) {timestamp}: {message}")
                else:
                    print(f"\n(Private from {sender}) {timestamp}: {message}")

            # Handle file notifications from the server
            elif msg_type == "file":
                filename = msg.get("message")
                file_id = msg.get("file_id")
                file_size = msg.get("file_size", 0)
                if receiver:
                    print(
                        f"\n[FILE] {sender} sent you '{filename}'. To download, type: /download {file_id}")
                else:
                    print(
                        f"\n[FILE] {sender} sent '{filename}' to the chat. To download, type: /download {file_id}")

            # Handle a completed file download from the server
            elif msg_type == "file_download":
                filename = msg.get("message")
                file_data_b64 = msg.get("file_data")
                if file_data_b64:
                    try:
                        file_data = base64.b64decode(file_data_b64)
                        save_path = os.path.join(
                            CLIENT_DOWNLOADS_DIR, filename)
                        with open(save_path, "wb") as f:
                            f.write(file_data)
                        print(
                            f"\n[SUCCESS] File '{filename}' downloaded to '{CLIENT_DOWNLOADS_DIR}' folder.")
                    except Exception as e:
                        print(f"\n[ERROR] Failed to save downloaded file: {e}")

        except (ConnectionAbortedError, ConnectionResetError):
            print("\n[SYSTEM] Connection to the server was lost.")
            os._exit(0)
        except Exception as e:
            print(f"\n[RECEIVE ERROR] {e}")
            break


def current_timestamp():
    return datetime.now().strftime("%H:%M:%S")

def send_file(sock, filepath, receiver, username):
    if not os.path.exists(filepath):
        print("[ERROR] File not found.")
        return

    # Check file size (100MB limit for safety)
    file_size = os.path.getsize(filepath)
    if file_size > 100 * 1024 * 1024:
        print("[ERROR] File size cannot exceed 100MB.")
        return

    try:
        with open(filepath, "rb") as f:
            file_data = f.read()

        encoded_data = base64.b64encode(file_data).decode("utf-8")
        filename = os.path.basename(filepath)
        timestamp = current_timestamp()

        print(f"[SYSTEM] Uploading {filename}...")

        # Step 1: Send the entire file in one message (as expected by the server)
        upload_msg_dict = {
            "type": "file_upload",
            "sender": username,
            "timestamp": timestamp,
            "filename": filename,
            "file_data": encoded_data
        }
        upload_msg_json = json.dumps(upload_msg_dict)

        send_msg(sock, encrypt_message(upload_msg_json))

        # Step 2: Send the notification message for broadcast
        file_id = f"{timestamp.replace(':', '-')}_{filename}"
        metadata_msg_dict = {
            "type": "file",
            "sender": username,
            "timestamp": timestamp,
            "message": filename,
            "file_id": file_id,
            "file_size": file_size,
            "receiver": receiver or ""
        }
        metadata_msg_json = json.dumps(metadata_msg_dict)
        send_msg(sock, encrypt_message(metadata_msg_json))

        print(f"[SYSTEM] File '{filename}' sent successfully.")

    except Exception as e:
        print(f"[ERROR] File upload failed: {e}")

def request_file_download(sock, file_id, username):
    try:
        request_msg = {
            "type": "file_download_request",
            "sender": username,
            "file_id": file_id,
        }
        send_msg(sock, encrypt_message(json.dumps(request_msg)))
        print(f"[SYSTEM] Requesting download for file ID: {file_id}")
    except Exception as e:
        print(f"[ERROR] Download request failed: {e}")


def main():
    username = input("Enter your username: ").strip()
    if not username:
        print("[ERROR] Username cannot be empty.")
        return

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((SERVER_IP, SERVER_PORT))
    except Exception as e:
        print(f"[ERROR] Could not connect: {e}")
        return

    login_message = build_message(
        "system", username, "login_request", timestamp=current_timestamp())
    send_msg(client, encrypt_message(login_message))
    print(f"[SYSTEM] Connected to {SERVER_IP}:{SERVER_PORT} as '{username}'")
    print("[INFO] Type /sendfile <filepath> [username] to send a file.")
    print("[INFO] Type /download <file_id> to download a file.")
    print("[INFO] Type /w <username> <message> for a private message.")
    print("-" * 50)

    threading.Thread(target=receive_messages, args=(
        client, username), daemon=True).start()

    while True:
        try:
            text = input().strip()
            if not text:
                continue

            timestamp = current_timestamp()

            # Commands for file handling
            if text.lower().startswith("/sendfile "):
                parts = text.split(" ", 3)
                if len(parts) < 2:
                    print("[ERROR] Usage: /sendfile <filepath> [optional_username]")
                    continue
                filepath = parts[1]
                receiver = parts[2] if len(parts) > 2 else None
                send_file(client, filepath, receiver, username)
                continue

            elif text.lower().startswith("/download "):
                parts = text.split(" ", 2)
                if len(parts) < 2:
                    print("[ERROR] Usage: /download <file_id>")
                    continue
                file_id = parts[1]
                request_file_download(client, file_id, username)
                continue

            elif text.startswith("/w "):
                parts = text.split(" ", 2)
                if len(parts) < 3:
                    print(
                        "[ERROR] Invalid private message format. Use /w username message")
                    continue
                receiver, msg_content = parts[1], parts[2]
                msg_content_with_emoji = apply_emoji(msg_content)
                msg = build_message(
                    "private", username, msg_content_with_emoji, receiver=receiver, timestamp=timestamp)
                print(
                    f"(Private to {receiver}) {timestamp}: {msg_content_with_emoji}")
            else:
                text_with_emoji = apply_emoji(text)
                msg = build_message("public", username,
                                    text_with_emoji, timestamp=timestamp)

            send_msg(client, encrypt_message(msg))

        except KeyboardInterrupt:
            print("\n[SYSTEM] Exiting chat...")
            break
        except Exception as e:
            print(f"[SEND ERROR] {e}")
            break

    try:
        disconnect_msg = build_message(
            "system", username, "disconnect", timestamp=current_timestamp())
        send_msg(client, encrypt_message(disconnect_msg))
    except:
        pass

    client.close()
    print("[SYSTEM] Connection closed.")


if __name__ == "__main__":
    main()
