import sys
import socket
import threading
import base64
import os
import datetime
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk
from customtkinter import CTkFont

from shared.encrypt import encrypt_message, decrypt_message
from shared.common import build_message, parse_message, send_msg, recv_msg
from shared.config import SERVER_IP, SERVER_PORT, BUFFER_SIZE
from PIL import Image, ImageTk
import io


class ChatWindow:
    def __init__(self):
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")  # "dark" or "light"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

        # Create main window
        self.root = ctk.CTk()
        self.root.title("Modern Chatroom")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Configure grid weights for responsive design
        self.root.grid_columnconfigure(0, weight=3)  # Chat area (bigger)
        self.root.grid_columnconfigure(1, weight=1)  # User list (smaller)
        self.root.grid_rowconfigure(0, weight=1)

        # Initialize variables
        self.username = None
        self.client = None
        self.pending_download_path = None
        self.pending_preview_filename = None
        self.image_cache = {}  # Cache for downloaded images

        self.EMOJI_MAP = {
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
        self.emoji_picker_frame = None
        self.picker_hide_job = None
        self.tooltip_label = None

        self.setup_ui()
        self.setup_connection()

        # Start receiving messages in background thread
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def setup_ui(self):
        # Left panel - Chat area
        self.chat_frame = ctk.CTkFrame(self.root, corner_radius=10)
        self.chat_frame.grid(row=0, column=0, padx=(
            20, 10), pady=20, sticky="nsew")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(1, weight=1)

        self.download_frame = ctk.CTkScrollableFrame(
            self.chat_frame, height=120, corner_radius=10)
        self.download_frame.grid(
            row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Chat title
        self.chat_title = ctk.CTkLabel(
            self.chat_frame,
            text="💬 Chat Messages",
            font=CTkFont(size=18, weight="bold")
        )
        self.chat_title.grid(row=0, column=0, padx=20,
                             pady=(20, 10), sticky="w")

        # Chat display area
        self.chat_display = ctk.CTkTextbox(
            self.chat_frame,
            wrap="word",
            font=CTkFont(size=12),
            corner_radius=8
        )
        self.chat_display.grid(row=1, column=0, padx=20,
                               pady=(0, 20), sticky="nsew")

        # Message input area frame
        self.input_frame = ctk.CTkFrame(self.chat_frame, corner_radius=8)
        self.input_frame.grid(row=2, column=0, padx=20,
                              pady=(0, 20), sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        # Receiver input
        self.receiver_label = ctk.CTkLabel(
            self.input_frame, text="To:", font=CTkFont(size=12))
        self.receiver_label.grid(
            row=0, column=0, padx=(15, 5), pady=10, sticky="w")

        self.receiver_input = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Leave blank for public chat",
            font=CTkFont(size=12),
            height=35
        )
        self.receiver_input.grid(
            row=0, column=1, padx=(0, 15), pady=10, sticky="ew")

        # Message input
        self.message_label = ctk.CTkLabel(
            self.input_frame, text="Message:", font=CTkFont(size=12))
        self.message_label.grid(row=1, column=0, padx=(
            15, 5), pady=(0, 10), sticky="w")

        # Message input and buttons frame
        self.message_frame = ctk.CTkFrame(
            self.input_frame, fg_color="transparent")
        self.message_frame.grid(row=1, column=1, padx=(
            0, 15), pady=(0, 10), sticky="ew")
        self.message_frame.grid_columnconfigure(0, weight=1)

        self.input_box = ctk.CTkEntry(
            self.message_frame,
            placeholder_text="Type your message here...",
            font=CTkFont(size=12),
            height=35
        )
        self.input_box.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.input_box.bind("<Return>", lambda e: self.send_message())
        self.input_box.bind(
            "<Button-1>", lambda e: self._destroy_emoji_picker())

        self.emoji_button = ctk.CTkButton(
            self.message_frame,
            text="😄",
            width=35,
            height=35,
            font=CTkFont(size=18)
            # The command is removed
        )
        self.emoji_button.grid(row=0, column=1)  # No padding here
        self.emoji_button.bind("<Enter>", self._show_emoji_picker)
        self.emoji_button.bind("<Leave>", self._hide_emoji_picker_after_delay)

        self.send_button = ctk.CTkButton(
            self.message_frame,
            text="Send",
            width=80,
            height=35,
            font=CTkFont(size=12, weight="bold"),
            command=self.send_message
        )
        # 5px padding on BOTH sides
        self.send_button.grid(row=0, column=2, padx=5)

        self.send_file_button = ctk.CTkButton(
            self.message_frame,
            text="📎 File",
            width=80,
            height=35,
            font=CTkFont(size=12),
            command=self.send_file
        )
        self.send_file_button.grid(row=0, column=3)  # No padding here

        # Right panel - Active users
        self.users_frame = ctk.CTkFrame(self.root, corner_radius=10)
        self.users_frame.grid(row=0, column=1, padx=(
            10, 20), pady=20, sticky="nsew")
        self.users_frame.grid_columnconfigure(0, weight=1)
        self.users_frame.grid_rowconfigure(1, weight=1)

        # Users title
        self.users_title = ctk.CTkLabel(
            self.users_frame,
            text="👥 Active Users",
            font=CTkFont(size=16, weight="bold")
        )
        self.users_title.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Users list
        self.active_users_list = ctk.CTkTextbox(
            self.users_frame,
            font=CTkFont(size=11),
            corner_radius=8,
            width=200
        )
        self.active_users_list.grid(
            row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

    def setup_connection(self):
        self.username_rejected = False  # used to trigger retry

        while True:
            dialog = ctk.CTkInputDialog(
                text="Enter your username:",
                title="Login to Chatroom"
            )
            username = dialog.get_input()

            if not username:
                messagebox.showerror("Error", "No username provided.")
                continue  # re-show dialog

            self.username = username.strip()
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                self.client.connect((SERVER_IP, SERVER_PORT))
                login_msg = build_message(
                    "system", self.username, "login_request")
                send_msg(self.client, encrypt_message(login_msg))

                # Wait for server response
                response = self.client.recv(BUFFER_SIZE)
                decrypted = decrypt_message(response)
                msg = parse_message(decrypted)

                if msg.get("message") == "username_rejected":
                    messagebox.showerror(
                        "Username Taken", "This username is already taken. Please choose another.")
                    self.client.close()
                    continue  # re-show dialog

                break  # login accepted

            except Exception as e:
                messagebox.showerror("Connection Failed", str(e))
                return

        self.root.title(f"Modern Chatroom - {self.username}")
        self.append_to_chat(f"🟢 Connected as {self.username}", "system")

    def is_image_file(self, filename):
        """Check if file is an image based on extension"""
        image_extensions = {'.png', '.jpg', '.jpeg',
                            '.gif', '.bmp', '.tiff', '.webp'}
        return os.path.splitext(filename.lower())[1] in image_extensions

    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

    def append_to_chat(self, message, msg_type="normal", image_data=None, image_filename=None, file_info=None):
        """Append message to chat display with proper formatting and color coding"""
        self.chat_display.configure(state="normal")

        # Add timestamp and formatting based on message type
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # Configure text tags for colors if not already done
        # Blue for public messages
        self.chat_display.tag_config("blue", foreground="#4A9EFF")
        # Red for private messages
        self.chat_display.tag_config("red", foreground="#FF4A4A")
        # Green for normal messages
        self.chat_display.tag_config("green", foreground="#4AFF4A")
        # Orange for file messages
        self.chat_display.tag_config("orange", foreground="#FFA54A")
        # Gray for system messages
        self.chat_display.tag_config("gray", foreground="#AAAAAA")

        # Configure file link styles
        self.chat_display.tag_config(
            "file_link", foreground="#4A9EFF", underline=False)
        self.chat_display.tag_config(
            "file_link_hover", foreground="#4A9EFF", underline=True)

        if msg_type == "system":
            formatted_msg = f"[{timestamp}] {message}\n"
            self.chat_display.insert("end", formatted_msg, "gray")
        elif msg_type == "private_sent":
            formatted_msg = f"[{timestamp}] 🔒 You → {message}\n"
            self.chat_display.insert("end", formatted_msg, "red")
        elif msg_type == "private_received":
            formatted_msg = f"[{timestamp}] 🔒 {message}\n"
            self.chat_display.insert("end", formatted_msg, "red")
        elif msg_type == "public":
            formatted_msg = f"[{timestamp}] {message}\n"
            self.chat_display.insert("end", formatted_msg, "blue")
        elif msg_type == "file":
            # Special handling for file messages with clickable filename
            if file_info:
                sender = file_info.get("sender", "")
                filename = file_info.get("filename", "")
                file_id = file_info.get("file_id", "")
                file_size = file_info.get("file_size", 0)
                receiver = file_info.get("receiver", "")

                # Format the message parts
                if receiver:
                    prefix_msg = f"[{timestamp}] 📎 {sender} sent a file to {receiver}: "
                else:
                    prefix_msg = f"[{timestamp}] 📎 {sender} sent a file: "

                size_text = f" ({self.format_file_size(file_size)})" if file_size > 0 else ""

                # Insert the prefix
                self.chat_display.insert("end", prefix_msg, "orange")

                # Insert clickable filename
                start_pos = self.chat_display.index("end-1c")
                self.chat_display.insert("end", filename, "file_link")
                end_pos = self.chat_display.index("end-1c")

                # Create unique tag for this file link
                link_tag = f"file_link_{file_id}"
                self.chat_display.tag_add(link_tag, start_pos, end_pos)

                # Bind click and hover events
                self.chat_display.tag_bind(link_tag, "<Button-1>",
                                           lambda e, fid=file_id, fn=filename: self.download_file_from_chat(fn, fid))
                self.chat_display.tag_bind(link_tag, "<Enter>",
                                           lambda e, tag=link_tag: self.on_file_link_enter(tag))
                self.chat_display.tag_bind(link_tag, "<Leave>",
                                           lambda e, tag=link_tag: self.on_file_link_leave(tag))

                # Add size info and newline
                self.chat_display.insert("end", f"{size_text}\n", "orange")
            else:
                # Fallback for old format
                formatted_msg = f"[{timestamp}] 📎 {message}\n"
                self.chat_display.insert("end", formatted_msg, "orange")
        else:
            formatted_msg = f"{message}\n"
            self.chat_display.insert("end", formatted_msg, "green")

        # Add image if provided
        if image_data and image_filename:
            try:
                # Create image from data
                img = Image.open(io.BytesIO(image_data))

                # Resize image to fit in chat (max width 300px, maintain aspect ratio)
                max_width = 300
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height),
                                     Image.Resampling.LANCZOS)

                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(img)

                # Insert image into text widget
                self.chat_display.image_create("end", image=photo)
                self.chat_display.insert(
                    "end", f"\n[Image: {image_filename}]\n")

                # Keep reference to prevent garbage collection
                if not hasattr(self.chat_display, 'images'):
                    self.chat_display.images = []
                self.chat_display.images.append(photo)

            except Exception as e:
                print(f"Error displaying image: {e}")

        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def on_file_link_enter(self, tag):
        self.chat_display.tag_config(tag, underline=True)
        self.chat_display.configure(cursor="hand2")  # <-- Correct

    def on_file_link_leave(self, tag):
        self.chat_display.tag_config(tag, underline=False)
        self.chat_display.configure(cursor="")  # <-- Correct

    def download_file_from_chat(self, filename, file_id):
        """Download file when clicking on filename in chat"""
        save_path = filedialog.asksaveasfilename(
            title="Save File As",
            initialfile=filename,
            filetypes=[("All Files", "*.*")]
        )
        if save_path:
            try:
                request_msg = {
                    "type": "file_download_request",
                    "sender": self.username,
                    "file_id": file_id,
                }

                # --- ADD THIS LINE ---
                print(
                    f"[DIAGNOSTIC] Attempting to send download request for file_id: {file_id}")

                send_msg(self.client, encrypt_message(json.dumps(request_msg)))

                # --- AND ADD THIS LINE ---
                print("[DIAGNOSTIC] Download request sent successfully!")

                self.pending_download_path = save_path
                self.append_to_chat(f"Downloading {filename}...", "system")
            except Exception as e:
                messagebox.showerror("Download Error", str(e))

    def handle_file_message(self, msg):
        sender = msg["sender"]
        filename = msg["message"]
        file_id = msg["file_id"]
        timestamp = msg.get("timestamp", "")
        receiver = msg.get("receiver", "")
        file_size = msg.get("file_size", 0)

        # Create file info dictionary for clickable link
        file_info = {
            "sender": sender,
            "filename": filename,
            "file_id": file_id,
            "file_size": file_size,
            "receiver": receiver
        }

        # Add clickable file message to chat
        self.append_to_chat("", "file", file_info=file_info)

        # Place download button in the scrollable download frame
        file_widget = self.create_file_widget(
            sender, filename, file_id, file_size)
        file_widget.pack(fill="x", padx=5, pady=4)

        # Auto-download and preview images if they're small enough (< 2MB)
        if self.is_image_file(filename) and file_size < 2 * 1024 * 1024:
            self.auto_preview_image(filename, file_id)

    def auto_preview_image(self, filename, file_id):
        """Automatically download and preview small images"""
        try:
            request_msg = {
                "type": "file_download_request",
                "sender": self.username,
                "file_id": file_id,
            }
            self.client.send(encrypt_message(json.dumps(request_msg)))
            self.pending_preview_filename = filename
        except Exception as e:
            print(f"Error auto-previewing image: {e}")

    def send_message(self):
        text = self.input_box.get().strip()
        receiver = self.receiver_input.get().strip()
        if not text:
            return

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        if receiver == "":
            msg = build_message("public", self.username,
                                text, timestamp=timestamp)
        else:
            msg = build_message("private", self.username,
                                text, receiver=receiver, timestamp=timestamp)
            self.append_to_chat(f"{receiver}: {text}", "private_sent")

        send_msg(self.client, encrypt_message(msg))  # FIXED
        self.input_box.delete(0, "end")
        # print(f"\nCLIENT SENDING (Plain Text): {msg}")
        # encrypted_data = encrypt_message(msg)
        # print(f"CLIENT SENDING (Encrypted): {encrypted_data}\n")

        # send_msg(self.client, encrypted_data)
        # self.input_box.delete(0, "end")

    def _show_emoji_picker(self, event=None):
        """Creates the emoji picker or cancels the hide job if it already exists."""
        self._cancel_hide_picker()
        if self.emoji_picker_frame is None:
            self._create_emoji_picker()

    def _hide_emoji_picker_after_delay(self, event=None):
        """Schedules the destruction of the emoji picker after a short delay."""
        self.picker_hide_job = self.root.after(500, self._destroy_emoji_picker)

    def _cancel_hide_picker(self, event=None):
        """Cancels a pending hide job."""
        if self.picker_hide_job:
            self.root.after_cancel(self.picker_hide_job)
            self.picker_hide_job = None

    def _create_emoji_picker(self):
        """Creates and displays the emoji picker frame."""
        # (This function's content remains the same, but it's included for completeness)
        self.emoji_picker_frame = ctk.CTkFrame(self.root, border_width=1)

        # Bind events to the frame itself to cancel hiding
        self.emoji_picker_frame.bind("<Enter>", self._cancel_hide_picker)
        self.emoji_picker_frame.bind(
            "<Leave>", self._hide_emoji_picker_after_delay)

        x = self.input_frame.winfo_rootx()
        y = self.input_frame.winfo_rooty() - 155
        self.emoji_picker_frame.place(x=x, y=y)

        row, col = 0, 0
        # Create a mapping of emoji characters back to their codes for the tooltip
        self.emoji_code_map = {v: k for k, v in self.EMOJI_MAP.items()}

        for emoji in self.EMOJI_MAP.values():
            emoji_btn = ctk.CTkButton(self.emoji_picker_frame, text=emoji, width=40, height=30,
                                      font=CTkFont(size=20), fg_color="transparent",
                                      command=lambda e=emoji: self._on_emoji_select(e))
            emoji_btn.grid(row=row, column=col, padx=2, pady=2)

            # This part adds the tooltip from request #3
            emoji_code = self.emoji_code_map[emoji]
            emoji_btn.bind("<Enter>", lambda event, text=emoji_code: (
                self._cancel_hide_picker(), self._show_tooltip(event, text)))
            emoji_btn.bind("<Leave>", self._hide_tooltip)

            col += 1
            if col >= 5:
                col = 0
                row += 1

    def _destroy_emoji_picker(self):
        if self.emoji_picker_frame:
            self.emoji_picker_frame.destroy()
            self.emoji_picker_frame = None
        self._hide_tooltip()

    def _on_emoji_select(self, emoji_char):
        """Inserts the selected emoji into the input box."""
        self.input_box.insert("end", emoji_char)
        self.input_box.focus()

    def _show_tooltip(self, event, text):
        """Creates and displays a tooltip label."""
        self._hide_tooltip()
        self.tooltip_label = ctk.CTkLabel(self.root, text=text, fg_color="#2B2B2B",
                                          corner_radius=4, text_color="white",
                                          font=CTkFont(size=12))

        # Get the main window's position on the screen
        window_x = self.root.winfo_rootx()
        window_y = self.root.winfo_rooty()

        # Calculate the correct position inside the window
        x = event.x_root - window_x + 20  # Position 20px to the right of the cursor
        y = event.y_root - window_y + 10  # Position 10px below the cursor

        self.tooltip_label.place(x=x, y=y)

    def _hide_tooltip(self, event=None):
        """Destroys the tooltip label."""
        if self.tooltip_label:
            self.tooltip_label.destroy()
            self.tooltip_label = None

    def send_file(self):
        filepath = filedialog.askopenfilename(
            title="Select File to Send",
            filetypes=[
                ("All Files", "*.*"),
                ("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Video Files", "*.mp4 *.mov *.avi"),
                ("Document Files", "*.pdf *.docx *.doc *.txt"),
                ("Jupyter Notebooks", "*.ipynb"),
                ("Compressed Files", "*.zip *.rar *.7z"),
                ("Audio Files", "*.mp3 *.wav"),
            ]
        )
        if not filepath:
            return

        # Check file size (100MB limit)
        file_size = os.path.getsize(filepath)
        if file_size > 100 * 1024 * 1024:  # 100MB in bytes
            messagebox.showerror(
                "File Too Large", "File size must be less than 100MB")
            return

        try:
            # Read file in binary mode
            with open(filepath, "rb") as f:
                file_data = f.read()

            # Encode to base64
            encoded = base64.b64encode(file_data).decode("utf-8")
            filename = os.path.basename(filepath)
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

            self.append_to_chat(
                f"Uploading {filename}... ({self.format_file_size(file_size)})", "system")

            # Step 1: Send actual file data to server (upload step)
            upload_msg = {
                "type": "file_upload",
                "sender": self.username,
                "timestamp": timestamp,
                "filename": filename,
                "file_data": encoded
            }

            upload_data = encrypt_message(json.dumps(upload_msg))
            send_msg(self.client, upload_data)

            # Step 2: Notify others with file metadata (broadcast step)
            file_id = f"{timestamp.replace(':', '-')}_{filename}"
            receiver = self.receiver_input.get().strip()

            metadata_msg = {
                "type": "file",
                "sender": self.username,
                "timestamp": timestamp,
                "message": filename,
                "file_id": file_id,
                "file_size": file_size
            }
            if receiver:
                metadata_msg["receiver"] = receiver

            metadata_data = encrypt_message(json.dumps(metadata_msg))
            send_msg(self.client, metadata_data)

            # Display in UI for the sender
            file_info = {
                "sender": self.username,
                "filename": filename,
                "file_id": file_id,
                "file_size": file_size,
                "receiver": receiver
            }
            self.append_to_chat("", "file", file_info=file_info)

        except Exception as e:
            messagebox.showerror(
                "File Send Error", f"Error sending file: {str(e)}")
            print(f"[FILE SEND ERROR] {e}")

    def create_file_widget(self, sender, filename, file_id, file_size=0):
        """Create a file download widget to insert into the download area"""
        file_frame = ctk.CTkFrame(
            self.download_frame, corner_radius=8, height=60)  # Increased height
        file_frame.pack_propagate(False)

        # File info with size
        size_text = f" ({self.format_file_size(file_size)})" if file_size > 0 else ""
        file_info = f"{filename}{size_text} from {sender}"

        file_label = ctk.CTkLabel(
            file_frame,
            text=file_info,
            font=CTkFont(size=11)
        )
        file_label.pack(side="left", padx=10, fill="x",
                        expand=True, anchor="n", pady=(5, 0))

        # Add hint label
        hint_label = ctk.CTkLabel(
            file_frame,
            text="💡 Click filename in chat to download",
            font=CTkFont(size=9),
            text_color="#888888"
        )
        hint_label.pack(side="left", padx=(10, 0), anchor="n", pady=(25, 0))

        # Buttons frame
        btn_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=10, anchor="n", pady=(5, 0))

        download_btn = ctk.CTkButton(
            btn_frame,
            text="Download",
            width=80,
            height=30,
            font=CTkFont(size=10),
            command=lambda: self.download_file_from_chat(filename, file_id)
        )
        download_btn.pack(side="right", padx=5)

        # Add preview button for images
        if self.is_image_file(filename):
            preview_btn = ctk.CTkButton(
                btn_frame,
                text="Preview",
                width=80,
                height=30,
                font=CTkFont(size=10),
                command=lambda: self.preview_image(filename, file_id)
            )
            # preview_btn.pack(side="right", padx=5)

        return file_frame

    def download_file(self, filename, file_id):
        """Download a file from the server"""
        save_path = filedialog.asksaveasfilename(
            title="Save File As",
            initialname=filename,
            filetypes=[("All Files", "*.*")]
        )
        if save_path:
            try:
                request_msg = {
                    "type": "file_download_request",
                    "sender": self.username,
                    "file_id": file_id,
                }
                send_msg(self.client, encrypt_message(
                    json.dumps(request_msg)))  # FIXED
                self.pending_download_path = save_path
                self.append_to_chat(f"Downloading {filename}...", "system")
            except Exception as e:
                messagebox.showerror("Download Error", str(e))

    def preview_image(self, filename, file_id):
        """Preview an image without downloading"""
        try:
            request_msg = {
                "type": "file_download_request",
                "sender": self.username,
                "file_id": file_id,
            }
            self.client.send(encrypt_message(json.dumps(request_msg)))
            self.pending_preview_filename = filename
            self.append_to_chat(f"Loading preview of {filename}...", "system")
        except Exception as e:
            messagebox.showerror("Preview Error", str(e))

    def update_users_list(self, users):
        """Update the active users list"""
        self.active_users_list.configure(state="normal")
        self.active_users_list.delete("1.0", "end")

        for i, user in enumerate(users, 1):
            user = user.strip()
            if user == self.username:
                self.active_users_list.insert("end", f"{i}. {user} (You)\n")
            else:
                self.active_users_list.insert("end", f"{i}. {user}\n")

        self.active_users_list.configure(state="disabled")

    def _apply_emojis(self, text):
        """Replaces all emoji codes in a string with their emoji characters."""
        for code, emoji in self.EMOJI_MAP.items():
            text = text.replace(code, emoji)
        return text

    def receive_messages(self):
        while True:
            try:
                # Use the new robust receiving function
                data = recv_msg(self.client)
                if not data:
                    break
                decrypted = decrypt_message(data)
                msg = parse_message(decrypted)

                msg_type = msg.get("type")
                sender = msg.get("sender")
                message = msg.get("message")
                timestamp = msg.get("timestamp")
                receiver = msg.get("receiver", "")

                if msg_type == "public":
                    # Translate the message before displaying
                    translated_message = self._apply_emojis(message)
                    self.append_to_chat(
                        f"{sender}: {translated_message}", "public")

                elif msg_type == "private":
                    if sender == self.username:
                        # This part handles messages you send, which don't need translation here
                        self.append_to_chat(
                            f"{receiver}: {message}", "private_sent")
                    else:
                        # Translate the message before displaying
                        translated_message = self._apply_emojis(message)
                        self.append_to_chat(
                            f"{sender}: {translated_message}", "private_received")

                elif msg_type == "system":
                    if message.startswith("user_list:"):
                        users = message.split(":", 1)[1].split(",")
                        # Use after() to safely update GUI from thread
                        self.root.after(
                            0, lambda u=users: self.update_users_list(u))
                    else:
                        self.root.after(
                            0, lambda m=message: self.append_to_chat(m, "system"))

                elif msg_type == "file":
                    # Use after() to safely handle file message from thread
                    self.root.after(
                        0, lambda m=msg: self.handle_file_message(m))

                elif msg_type == "file_download":
                    filename = msg.get("message")
                    file_data_b64 = msg.get("file_data")

                    if file_data_b64:
                        file_data = base64.b64decode(file_data_b64)

                        # Check if this is for preview or download
                        if hasattr(self, 'pending_preview_filename') and self.pending_preview_filename == filename:
                            # This is for preview
                            if self.is_image_file(filename):
                                self.root.after(0, lambda: self.append_to_chat(
                                    f"Image from server: {filename}",
                                    "file",
                                    image_data=file_data,
                                    image_filename=filename
                                ))
                            self.pending_preview_filename = None

                        elif hasattr(self, 'pending_download_path') and self.pending_download_path:
                            # This is for download
                            try:
                                with open(self.pending_download_path, "wb") as f:
                                    f.write(file_data)
                                self.root.after(0, lambda: self.append_to_chat(
                                    f"Downloaded: {filename}", "system"))
                                self.pending_download_path = None
                            except Exception as e:
                                self.root.after(0, lambda: messagebox.showerror(
                                    "Download Error", str(e)))

            except Exception as e:
                print(f"[RECEIVE ERROR] {e}")
                break

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = ChatWindow()
    app.run()
