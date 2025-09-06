from shared.config import SERVER_IP, SERVER_PORT
from shared.common import parse_message, build_message, current_timestamp, send_msg, recv_msg
from shared.encrypt import encrypt_message, decrypt_message
import json
import threading
import socket
import base64
import os
import sys
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# from shared.common import parse_message, build_message, current_timestamp

clients = {}  # username → client socket
lock = threading.Lock()

FILE_STORAGE_DIR = "server_storage"
os.makedirs(FILE_STORAGE_DIR, exist_ok=True)


def setup_logging():
    """Configures logging to output to both a file and the console."""
    # To prevent duplicate handlers if this is ever called more than once
    if logging.getLogger().hasHandlers():
        logging.getLogger().handlers.clear()

    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = logging.FileHandler("server.log")
    file_handler.setFormatter(log_formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(log_formatter)

    logger = logging.getLogger()
    # Change to logging.DEBUG to see debug messages
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def broadcast(message_dict, exclude=None):  # Renamed for clarity
    """
    Takes a dictionary, converts it to JSON, and sends it to all users.
    """
    # Always convert to JSON inside the function for consistency
    json_data_to_send = json.dumps(message_dict)

    for user, conn in clients.items():
        if user != exclude:
            try:
                send_msg(conn, encrypt_message(json_data_to_send))
            except:
                print(f"[ERROR] Failed to send to {user}")


def broadcast_user_list():
    user_list = ",".join(clients.keys())
    message = build_message("system", "server", f"user_list:{user_list}")
    for conn in clients.values():
        try:
            send_msg(conn, encrypt_message(message))
        except:
            pass


def recv_full_message(conn):
    try:
        data = recv_msg(conn)
        if not data:
            return None
        decrypted = decrypt_message(data)
        msg = parse_message(decrypted)
        return msg
    # try:
    #     data = recv_msg(conn)
    #     if not data:
    #         return None

    #     print(f"\nSERVER RECEIVED (Encrypted): {data}")
    #     decrypted = decrypt_message(data)
    #     print(f"SERVER RECEIVED (Decrypted): {decrypted}\n")

    #     msg = parse_message(decrypted)
    #     return msg
    except Exception as e:
        print(f"[RECV ERROR] {e}")
        return None


def handle_client(conn, addr):
    username = None

    try:
        msg = recv_full_message(conn)
        if not msg:
            conn.close()
            return

        temp_name = msg.get("sender")

        with lock:
            if temp_name in clients:
                rejection = build_message(
                    "system", "server", "username_rejected")
                # This line was already correct
                send_msg(conn, encrypt_message(rejection))
                logging.warning(
                    f"[REJECTED] {temp_name} already exists")
                # logging.warning(
                #     f"Rejected duplicate username '{temp_name}' from {addr}")
                conn.close()
                return
            else:
                clients[temp_name] = conn
                username = temp_name
                # Send user list directly to the new user as well
                user_list = ",".join(clients.keys())
                message = build_message(
                    "system", "server", f"user_list:{user_list}")
                # ✅ Direct message to new client
                send_msg(conn, encrypt_message(message))
                broadcast_user_list()

                # print(f"[CLIENTS] Now connected: {list(clients.keys())}")
                logging.info(
                    f"[CLIENTS] Now connected: {list(clients.keys())}")

        # print(f"[CONNECTED] {username} from {addr}")
        logging.info(f"[CONNECTED] {username} from {addr}")

        join_msg = build_message(
            "system", "server", f"{username} has joined the chat.")
        broadcast(json.loads(join_msg), exclude=username)

        while True:
            msg = recv_full_message(conn)
            if not msg:
                break

            msg_type = msg.get("type")
            sender = msg.get("sender")
            timestamp = msg.get("timestamp", current_timestamp())
            text = msg.get("message", "")

            print(f"[DEBUG] Received message type: {msg_type} from {sender}")

            if msg_type == "public":
                # print(f"[PUBLIC] {sender}: {text}")
                logging.info(f"[PUBLIC] {sender}: {text}")
                # This correctly calls the fixed broadcast function
                broadcast(msg)

            elif msg_type == "private":
                receiver = msg.get("receiver")
                if receiver in clients:
                    # print(f"[PRIVATE] {sender} → {receiver}: {text}")
                    logging.info(f"[PRIVATE] {sender} -> {receiver}: {text}")
                    # This line was already correct
                    send_msg(clients[receiver],
                             encrypt_message(json.dumps(msg)))
                else:
                    error = build_message(
                        "system", "server", f"User '{receiver}' not found.")
                    # FIXED: Replaced .send() with send_msg()
                    send_msg(conn, encrypt_message(error))

            elif msg_type == "file_upload":
                filename = msg.get("filename")
                file_data_b64 = msg.get("file_data")
                timestamp = msg.get("timestamp")

                if not file_data_b64:
                    print(f"[ERROR] No file data received for {filename}")
                    continue

                try:
                    file_data = base64.b64decode(file_data_b64)
                    file_id = f"{timestamp.replace(':', '-')}_{filename}"
                    filepath = os.path.join(FILE_STORAGE_DIR, file_id)

                    with open(filepath, "wb") as f:
                        f.write(file_data)

                    # print(
                    #     f"[UPLOAD] Saved file '{filename}' as '{file_id}' ({len(file_data)} bytes)")
                    logging.info(
                        f"[UPLOAD] Saved file '{filename}' as '{file_id}' ({len(file_data)} bytes)")

                    confirm_msg = build_message(
                        "system", "server", f"File '{filename}' uploaded successfully")
                    send_msg(conn, encrypt_message(confirm_msg))

                except Exception as e:
                    # print(
                    #     f"[ERROR] Failed to save uploaded file '{filename}': {e}")
                    logging.error(
                        f"[ERROR] Failed to save uploaded file '{filename}': {e}")
                    error_msg = build_message(
                        "system", "server", f"Failed to upload file: {e}")
                    send_msg(conn, encrypt_message(error_msg))

            elif msg_type == "file":
                receiver = msg.get("receiver")
                filename = msg.get("message")
                file_id = msg.get("file_id")

                logging.info(
                    f"[FILE] {sender} sharing file '{filename}' (ID: {file_id})")

                if receiver:
                    if receiver in clients:
                        # print(f"[FILE] {sender} → {receiver}: {filename}")
                        logging.info(
                            f"[FILE] {sender} -> {receiver}: {msg.get('message')}")
                        send_msg(clients[receiver],
                                 encrypt_message(json.dumps(msg)))
                    else:
                        error = build_message(
                            "system", "server", f"User '{receiver}' not found.")
                        send_msg(conn, encrypt_message(error))
                else:
                    # print(f"[FILE] {sender} shared file publicly: {filename}")
                    logging.info(
                        f"[FILE] {sender} shared publicly: {msg.get('message')}")
                    broadcast(msg, exclude=sender)

            elif msg_type == "file_download_request":
                file_id = msg.get("file_id")
                requester = msg.get("sender")
                filepath = os.path.join(FILE_STORAGE_DIR, file_id)

                # print(f"[DOWNLOAD] {requester} requesting file '{file_id}'")
                logging.info(
                    f"[DOWNLOAD] {requester} requesting file '{file_id}'")

                if not os.path.exists(filepath):
                    # print(f"[ERROR] File '{file_id}' not found")
                    logging.error(
                        f"[ERROR] File '{file_id}' not found'")
                    error_msg = build_message(
                        "system", "server", f"File '{file_id}' not found")
                    send_msg(conn, encrypt_message(error_msg))
                    continue

                try:
                    with open(filepath, "rb") as f:
                        file_data = f.read()

                    file_data_b64 = base64.b64encode(file_data).decode("utf-8")
                    original_filename = "_".join(file_id.split("_")[1:])

                    download_msg = {
                        "type": "file_download",
                        "sender": "server",
                        "timestamp": current_timestamp(),
                        "message": original_filename,
                        "file_data": file_data_b64
                    }

                    send_msg(clients[requester], encrypt_message(
                        json.dumps(download_msg)))
                    # print(
                    #     f"[DOWNLOAD] Sent file '{file_id}' to {requester} ({len(file_data)} bytes)")
                    logging.info(
                        f"[DOWNLOAD] Sent file '{file_id}' to {requester} ({len(file_data)} bytes)")

                except Exception as e:
                    # print(f"[ERROR] Could not send file '{file_id}': {e}")
                    logging.error(
                        f"[ERROR] Could not send file '{file_id}': {e}")
                    error_msg = build_message(
                        "system", "server", f"Error downloading file: {e}")
                    send_msg(conn, encrypt_message(error_msg))

    except Exception as e:
        # print(f"[EXCEPTION] {username}: {e}")
        logging.exception(f"[EXCEPTION] {username}: {e}")

    finally:
        if username:
            with lock:
                clients.pop(username, None)
                broadcast_user_list()
                # print(f"[CLIENTS] Now connected: {list(clients.keys())}")
                logging.info(
                    f"[CLIENTS] Now connected: {list(clients.keys())}")
            leave_msg = build_message(
                "system", "server", f"{username} has left the chat.")
            broadcast(json.loads(leave_msg), exclude=username)
            # print(f"[DISCONNECTED] {username} from {addr}")
            logging.info(f"[DISCONNECTED] {username} from {addr}")
        conn.close()


def start_server():
    setup_logging()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((SERVER_IP, SERVER_PORT))
    server.listen(5)
    # print(f"[STARTED] Chat server on {SERVER_IP}:{SERVER_PORT}")
    logging.info(f"[STARTED] Chat server on {SERVER_IP}:{SERVER_PORT}")

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(
                conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        logging.info("[SHUTDOWN] Server shutting down...")
    finally:
        server.close()


if __name__ == "__main__":
    start_server()
