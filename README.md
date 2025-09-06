# Chatroom Project

This project is a feature-rich, secure chat application built with Python. It features a modern graphical user interface (GUI) built with `customtkinter`, end-to-end message encryption, and support for large file transfers. The application uses a multi-threaded server to handle concurrent client connections robustly.

## Features

- **Graphical User Interface**: A modern, theme-aware GUI built with `customtkinter`.
- **Private & Public Messaging**: Send messages to all users in the public chat or privately to specific users.
- **Secure Communication**: All messages are end-to-end encrypted using AES to ensure privacy.
- **Large File Sharing**: Reliably send and receive files of any size (e.g., PDFs, images) with a custom networking protocol.
- **Interactive File Downloads**: Clickable links in the chat window open a "Save As" dialog for easy downloading.
- **Emoji Support**: An interactive, graphical emoji picker allows users to easily add emojis to their messages.
- **Real-time User List**: See a list of all currently active users in the chatroom.
- **Concurrent Connections**: The server uses multi-threading to handle multiple clients smoothly and simultaneously.

## Tech Stack & Dependencies

This project is built entirely with Python and leverages a mix of standard and third-party libraries for GUI, networking, encryption, and file handling.

- **customtkinter** (external) – Provides a modern and theme-aware graphical user interface.
- **tkinter** (standard) – The underlying GUI framework included with Python.
- **Pillow** (external) – Used to handle and display images (e.g., emojis, media previews).
- **socket** (standard) – Powers low-level TCP communication between clients and server.
- **threading** (standard) – Enables the server to handle multiple clients concurrently.
- **pycryptodome** (external) – Provides AES encryption and decryption for secure messaging and file sharing.
- **json** (standard) – Used for serializing and parsing structured messages.
- **os** (standard) – Handles file system operations like reading, saving, and organizing uploaded files.
- **No framework** – The server and client are built entirely from scratch using core Python libraries.
- **No database** – The application stores data in-memory or directly on disk (e.g., via `server_storage/`).

## Getting Started

Follow these steps to set up and run the project on your local machine.

### 1. Prerequisites

- Python 3.8 or newer
- `pip` for installing packages
- An environment manager like `conda` or `venv`

### 2. Setup

First, clone the repository and navigate into the project's root directory.

```bash
git clone <your-repository-url>
cd chatroom-project
```

Next, create and activate a virtual environment.

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Mac/Linux
venv\Scripts\activate    # On Windows

# Or using Conda
conda create --name chatroom-env python=3.10
conda activate chatroom-env
```

Now, install the required packages.

```bash
pip install -r requirements.txt
```

Finally, ensure the project is recognized as a Python package by creating `__init__.py` files.

```bash
# On Mac/Linux
touch shared/__init__.py server/__init__.py client/__init__.py

# On Windows
type nul > shared\__init__.py
type nul > server\__init__.py
type nul > client\__init__.py
```

### 3. Running the Application

**Important:** Always run the following commands from the project's root directory (`chatroom-project/`).

**Step 1: Start the Server**
Open a terminal and run:

```bash
python -m server.server
```

You should see the confirmation message: `[STARTED] Chat server on 127.0.0.1:8888`

**Step 2: Start the Client(s)**
Open one or more new terminal windows and run:

```bash
# To run the Graphical User Interface (GUI)
python -m client.gui

# To run the Command-Line Interface (CLI)
python -m client.client
```

You can run multiple clients, and they will all connect to the same server.

## Troubleshooting

**Error: `ModuleNotFoundError: No module named 'shared'` (or similar)**

- **Cause**: You are likely running the command from the wrong directory or not using the `-m` flag.
- **Solution**:
  1. Make sure your terminal's current directory is the project root (`chatroom-project`).
  2. Always use the `python -m folder.file` syntax to run scripts. This allows Python to correctly resolve the project's internal imports.

## Project Structure

```
chatroom-project/
│
├── client/
│   ├── gui.py          # The main file for the graphical user interface.
│   └── client.py       # A secondary command-line client for testing.
│
├── server/
│   └── server.py       # The multi-threaded server application.
│
├── shared/
│   ├── common.py       # Helper functions for message building/parsing.
│   ├── config.py       # Configuration variables (IP, port).
│   └── encrypt.py      # Functions for AES encryption and decryption.
|   └── protocol.md     # Protocol used for message and file formats.
│
├── server_storage/     # Temporary storage of uploaded files.
|
├── requirements.txt    # A list of required Python packages.
├── server.log          # A log file to write events.
└── README.md           # This file.
```
