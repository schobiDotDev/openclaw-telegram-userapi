#!/usr/bin/env python3
"""
Telegram User API — Web-based Login

Opens a local web server where the user can enter their Telegram verification code.
Creates a Telethon session file for subsequent API calls.

Usage:
    python3 web_login.py [--port 8234] [--session-dir /path/to/dir]
"""

import os
import sys
import time
import asyncio
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

# Determine paths
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent

# Parse CLI args
port = 8234
session_dir = os.environ.get("TELEGRAM_SESSION_DIR", str(BASE_DIR / "data"))

args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == "--port" and i + 1 < len(args):
        port = int(args[i + 1])
        i += 2
    elif args[i] == "--session-dir" and i + 1 < len(args):
        session_dir = args[i + 1]
        i += 2
    else:
        i += 1

os.makedirs(session_dir, exist_ok=True)
session_file = os.path.join(session_dir, "session")
code_file = os.path.join(session_dir, "_login_code.txt")

# Load env
def load_env():
    env_locations = [
        os.path.join(session_dir, ".env"),
        os.path.join(str(BASE_DIR), ".env"),
    ]
    for env_file in env_locations:
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, val = line.split("=", 1)
                        if key.strip() not in os.environ:
                            os.environ[key.strip()] = val.strip()
            break

load_env()

API_ID = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
PHONE = os.environ.get("TELEGRAM_PHONE")

if not all([API_ID, API_HASH, PHONE]):
    print("ERROR: Missing TELEGRAM_API_ID, TELEGRAM_API_HASH, or TELEGRAM_PHONE")
    print("Set them in environment or in a .env file")
    sys.exit(1)

API_ID = int(API_ID)

# Clean up old code file
if os.path.exists(code_file):
    os.remove(code_file)

status = {"state": "waiting", "message": ""}

HTML_FORM = """<!DOCTYPE html>
<html><head><title>Telegram Login</title>
<style>
body { font-family: -apple-system, sans-serif; max-width: 400px; margin: 100px auto; text-align: center; }
input { font-size: 24px; padding: 10px; width: 200px; text-align: center; border: 2px solid #0088cc; border-radius: 8px; }
button { font-size: 18px; padding: 10px 30px; background: #0088cc; color: white; border: none; border-radius: 8px; cursor: pointer; margin-top: 10px; }
button:hover { background: #006699; }
.status { margin-top: 20px; padding: 15px; border-radius: 8px; }
.waiting { background: #fff3cd; }
.success { background: #d4edda; color: #155724; }
.error { background: #f8d7da; color: #721c24; }
</style></head><body>
<h2>Telegram Login</h2>
<p>Enter the verification code sent to <b>PHONE_PLACEHOLDER</b></p>
<form method="POST" action="/code">
<input type="text" name="code" placeholder="12345" autofocus autocomplete="off"><br>
<button type="submit">Submit</button>
</form>
<div class="status STATUS_CLASS">STATUS_MSG</div>
</body></html>""".replace("PHONE_PLACEHOLDER", PHONE)

HTML_SUCCESS = """<!DOCTYPE html>
<html><head><title>Logged In</title>
<style>
body { font-family: -apple-system, sans-serif; max-width: 400px; margin: 100px auto; text-align: center; }
.success { background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; font-size: 18px; }
</style></head><body>
<h2>Success!</h2>
<div class="success">RESULT_MSG</div>
<p style="margin-top:20px;color:#666;">You can close this window.</p>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        html = HTML_FORM.replace("STATUS_CLASS", status["state"]).replace("STATUS_MSG", status["message"])
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        data = parse_qs(self.rfile.read(length).decode())
        code = data.get("code", [""])[0].strip()

        if code:
            with open(code_file, "w") as f:
                f.write(code)

            # Wait for Telethon to process
            for _ in range(30):
                time.sleep(0.5)
                if status["state"] == "success":
                    html = HTML_SUCCESS.replace("RESULT_MSG", status["message"])
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(html.encode())
                    return
                elif status["state"] == "error":
                    break

            html = HTML_FORM.replace("STATUS_CLASS", status["state"]).replace("STATUS_MSG", status["message"])
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())

    def log_message(self, format, *args):
        pass  # Suppress HTTP logs


def wait_for_code():
    """Block until user submits code via web form."""
    print(f"WAITING_FOR_CODE - Open http://localhost:{port}", flush=True)
    status["state"] = "waiting"
    status["message"] = "Waiting for verification code..."
    while True:
        if os.path.exists(code_file):
            with open(code_file) as f:
                code = f.read().strip()
            if code:
                os.remove(code_file)
                return code
        time.sleep(0.3)


async def telegram_login():
    """Perform Telegram login flow."""
    from telethon import TelegramClient

    try:
        client = TelegramClient(session_file, API_ID, API_HASH)
        await client.start(phone=PHONE, code_callback=wait_for_code)

        me = await client.get_me()
        name = f"{me.first_name or ''} {me.last_name or ''}".strip()
        print(f"Logged in as: {name} (@{me.username})", flush=True)
        status["state"] = "success"
        status["message"] = f"Logged in as {name} (@{me.username})"

        await client.disconnect()
    except Exception as e:
        status["state"] = "error"
        status["message"] = f"Error: {e}"
        print(f"ERROR: {e}", flush=True)


def run_telegram():
    asyncio.run(telegram_login())


# Start Telegram auth in background thread
t = threading.Thread(target=run_telegram, daemon=True)
t.start()

# Start web server
print(f"Login server running on http://localhost:{port}", flush=True)
print(f"Session will be saved to: {session_file}.session", flush=True)
server = HTTPServer(("0.0.0.0", port), Handler)

try:
    while t.is_alive():
        server.handle_request()
    # Serve a few more requests so user sees success page
    for _ in range(10):
        server.handle_request()
except KeyboardInterrupt:
    pass

print("Done.", flush=True)
