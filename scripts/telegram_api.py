#!/usr/bin/env python3
"""
OpenClaw Telegram User API — CLI Tool

Provides Telegram User API capabilities via Telethon.
Designed to be called from OpenClaw skills with {baseDir}/scripts/telegram_api.py.

Usage:
    python3 telegram_api.py <command> [args...]

Commands:
    check-session               Verify session is valid and authenticated
    get-me                      Get current user info
    create-group <title> [bot]  Create a new group, optionally add a bot username
    list-groups [--limit N]     List recent groups/chats
    lookup-group <name>         Find a group by name (fuzzy match)
    send-message <chat_id> <text>  Send a message to a chat
    add-member <chat_id> <username>  Add a member to a group
    get-members <chat_id>       List members of a group
    set-group-photo <chat_id> <path>  Set group photo from file
    leave-group <chat_id>       Leave a group
    get-chat-info <chat_id>     Get detailed chat info

Environment Variables (required):
    TELEGRAM_API_ID     — Telegram API ID from my.telegram.org
    TELEGRAM_API_HASH   — Telegram API Hash from my.telegram.org
    TELEGRAM_PHONE      — Phone number for the account

Environment Variables (optional):
    TELEGRAM_SESSION_DIR — Directory for session file (default: {baseDir}/data)
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Determine base directory (skill install dir)
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
SESSION_DIR = os.environ.get("TELEGRAM_SESSION_DIR", str(BASE_DIR / "data"))
SESSION_FILE = os.path.join(SESSION_DIR, "session")

# Load .env file if it exists in the skill's data directory
def load_env():
    """Load environment from .env file if present."""
    env_locations = [
        os.path.join(SESSION_DIR, ".env"),
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


def get_credentials():
    """Get Telegram API credentials from environment."""
    load_env()
    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    phone = os.environ.get("TELEGRAM_PHONE")

    if not all([api_id, api_hash, phone]):
        missing = []
        if not api_id:
            missing.append("TELEGRAM_API_ID")
        if not api_hash:
            missing.append("TELEGRAM_API_HASH")
        if not phone:
            missing.append("TELEGRAM_PHONE")
        print(json.dumps({
            "ok": False,
            "error": f"Missing credentials: {', '.join(missing)}",
            "hint": "Configure in openclaw.json under skills.entries.telegram-userapi.env"
        }))
        sys.exit(1)

    return int(api_id), api_hash, phone


def get_client():
    """Create a Telethon client instance."""
    try:
        from telethon import TelegramClient
    except ImportError:
        print(json.dumps({
            "ok": False,
            "error": "telethon not installed",
            "hint": f"Run: bash {BASE_DIR}/scripts/setup.sh"
        }))
        sys.exit(1)

    api_id, api_hash, phone = get_credentials()
    os.makedirs(SESSION_DIR, exist_ok=True)
    return TelegramClient(SESSION_FILE, api_id, api_hash), phone


def output(data):
    """Print JSON output."""
    print(json.dumps(data, ensure_ascii=False, default=str))


# ─── Commands ──────────────────────────────────────────────


async def cmd_check_session():
    """Check if the Telethon session is valid."""
    client, phone = get_client()
    try:
        await client.connect()
        if await client.is_user_authorized():
            me = await client.get_me()
            output({
                "ok": True,
                "authorized": True,
                "user_id": me.id,
                "username": me.username,
                "name": f"{me.first_name or ''} {me.last_name or ''}".strip(),
                "phone": me.phone,
            })
        else:
            output({
                "ok": True,
                "authorized": False,
                "hint": f"Run: python3 {BASE_DIR}/scripts/web_login.py"
            })
    finally:
        await client.disconnect()


async def cmd_get_me():
    """Get current user info."""
    client, phone = get_client()
    try:
        await client.start(phone=phone)
        me = await client.get_me()
        output({
            "ok": True,
            "user_id": me.id,
            "username": me.username,
            "first_name": me.first_name,
            "last_name": me.last_name,
            "phone": me.phone,
        })
    finally:
        await client.disconnect()


async def cmd_create_group(title, bot_username=None):
    """Create a new Telegram group."""
    from telethon.tl.functions.messages import CreateChatRequest

    client, phone = get_client()
    try:
        await client.start(phone=phone)

        users = []
        if bot_username:
            username = bot_username.lstrip("@")
            try:
                bot = await client.get_entity(username)
                users.append(bot)
            except Exception as e:
                output({"ok": False, "error": f"Could not find user @{username}: {e}"})
                return

        result = await client(CreateChatRequest(users=users, title=title))
        chat = result.chats[0]

        output({
            "ok": True,
            "title": title,
            "chat_id": -chat.id,
            "members_added": [bot_username] if bot_username else [],
        })
    finally:
        await client.disconnect()


async def cmd_list_groups(limit=20):
    """List recent groups/chats."""
    from telethon.tl.types import Chat, Channel

    client, phone = get_client()
    try:
        await client.start(phone=phone)

        groups = []
        async for dialog in client.iter_dialogs(limit=limit):
            entity = dialog.entity
            if isinstance(entity, (Chat, Channel)):
                groups.append({
                    "title": dialog.title,
                    "chat_id": dialog.id,
                    "type": "channel" if isinstance(entity, Channel) else "group",
                    "unread": dialog.unread_count,
                })

        output({"ok": True, "groups": groups, "count": len(groups)})
    finally:
        await client.disconnect()


async def cmd_lookup_group(name):
    """Find a group by name (case-insensitive partial match)."""
    from telethon.tl.types import Chat, Channel

    client, phone = get_client()
    try:
        await client.start(phone=phone)

        name_lower = name.lower()
        matches = []
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            if isinstance(entity, (Chat, Channel)):
                if name_lower in (dialog.title or "").lower():
                    matches.append({
                        "title": dialog.title,
                        "chat_id": dialog.id,
                        "type": "channel" if isinstance(entity, Channel) else "group",
                    })

        output({"ok": True, "query": name, "matches": matches, "count": len(matches)})
    finally:
        await client.disconnect()


async def cmd_send_message(chat_id, text):
    """Send a message to a chat."""
    client, phone = get_client()
    try:
        await client.start(phone=phone)
        chat_id = int(chat_id)
        message = await client.send_message(chat_id, text)
        output({
            "ok": True,
            "chat_id": chat_id,
            "message_id": message.id,
        })
    finally:
        await client.disconnect()


async def cmd_add_member(chat_id, username):
    """Add a member to a group."""
    from telethon.tl.functions.messages import AddChatUserRequest

    client, phone = get_client()
    try:
        await client.start(phone=phone)
        chat_id = int(chat_id)
        username = username.lstrip("@")
        user = await client.get_entity(username)

        await client(AddChatUserRequest(
            chat_id=abs(chat_id),
            user_id=user,
            fwd_limit=0,
        ))

        output({
            "ok": True,
            "chat_id": chat_id,
            "added": username,
        })
    finally:
        await client.disconnect()


async def cmd_get_members(chat_id):
    """List members of a group."""
    client, phone = get_client()
    try:
        await client.start(phone=phone)
        chat_id = int(chat_id)
        entity = await client.get_entity(chat_id)
        participants = await client.get_participants(entity)

        members = []
        for p in participants:
            members.append({
                "user_id": p.id,
                "username": p.username,
                "name": f"{p.first_name or ''} {p.last_name or ''}".strip(),
                "bot": p.bot,
            })

        output({"ok": True, "chat_id": chat_id, "members": members, "count": len(members)})
    finally:
        await client.disconnect()


async def cmd_set_group_photo(chat_id, photo_path):
    """Set a group's photo."""
    from telethon.tl.functions.messages import EditChatPhotoRequest
    from telethon.tl.types import InputChatUploadedPhoto

    client, phone = get_client()
    try:
        await client.start(phone=phone)
        chat_id = int(chat_id)

        if not os.path.exists(photo_path):
            output({"ok": False, "error": f"File not found: {photo_path}"})
            return

        uploaded = await client.upload_file(photo_path)
        await client(EditChatPhotoRequest(
            chat_id=abs(chat_id),
            photo=InputChatUploadedPhoto(file=uploaded),
        ))

        output({"ok": True, "chat_id": chat_id, "photo_set": True})
    finally:
        await client.disconnect()


async def cmd_leave_group(chat_id):
    """Leave a group."""
    from telethon.tl.functions.messages import DeleteChatUserRequest

    client, phone = get_client()
    try:
        await client.start(phone=phone)
        chat_id = int(chat_id)
        me = await client.get_me()
        await client(DeleteChatUserRequest(chat_id=abs(chat_id), user_id=me))
        output({"ok": True, "chat_id": chat_id, "left": True})
    finally:
        await client.disconnect()


async def cmd_get_chat_info(chat_id):
    """Get detailed info about a chat."""
    client, phone = get_client()
    try:
        await client.start(phone=phone)
        chat_id = int(chat_id)
        entity = await client.get_entity(chat_id)

        info = {
            "ok": True,
            "chat_id": chat_id,
            "title": getattr(entity, "title", None),
            "username": getattr(entity, "username", None),
        }

        # Get participant count
        try:
            participants = await client.get_participants(entity)
            info["member_count"] = len(participants)
        except Exception:
            info["member_count"] = getattr(entity, "participants_count", None)

        output(info)
    finally:
        await client.disconnect()


# ─── CLI Router ────────────────────────────────────────────


COMMANDS = {
    "check-session": (cmd_check_session, []),
    "get-me": (cmd_get_me, []),
    "create-group": (cmd_create_group, ["title"], {"bot_username": None}),
    "list-groups": (cmd_list_groups, [], {"limit": 20}),
    "lookup-group": (cmd_lookup_group, ["name"]),
    "send-message": (cmd_send_message, ["chat_id", "text"]),
    "add-member": (cmd_add_member, ["chat_id", "username"]),
    "get-members": (cmd_get_members, ["chat_id"]),
    "set-group-photo": (cmd_set_group_photo, ["chat_id", "photo_path"]),
    "leave-group": (cmd_leave_group, ["chat_id"]),
    "get-chat-info": (cmd_get_chat_info, ["chat_id"]),
}


def print_usage():
    print("Usage: telegram_api.py <command> [args...]")
    print()
    print("Commands:")
    print("  check-session                   Check if session is valid")
    print("  get-me                          Get current user info")
    print("  create-group <title> [bot]      Create group, optionally add bot")
    print("  list-groups [--limit N]         List groups (default: 20)")
    print("  lookup-group <name>             Find group by name")
    print("  send-message <chat_id> <text>   Send message to chat")
    print("  add-member <chat_id> <user>     Add member to group")
    print("  get-members <chat_id>           List group members")
    print("  set-group-photo <id> <path>     Set group photo")
    print("  leave-group <chat_id>           Leave a group")
    print("  get-chat-info <chat_id>         Get chat details")
    print()
    print("All output is JSON. Configure credentials via environment variables")
    print("or openclaw.json skills.entries.telegram-userapi.env")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_usage()
        sys.exit(0)

    cmd_name = sys.argv[1]
    args = sys.argv[2:]

    if cmd_name not in COMMANDS:
        output({"ok": False, "error": f"Unknown command: {cmd_name}"})
        sys.exit(1)

    entry = COMMANDS[cmd_name]
    func = entry[0]
    required = entry[1] if len(entry) > 1 else []
    defaults = entry[2] if len(entry) > 2 else {}

    # Parse --flag arguments
    positional = []
    flags = dict(defaults)
    i = 0
    while i < len(args):
        if args[i].startswith("--") and "=" in args[i]:
            key, val = args[i][2:].split("=", 1)
            flags[key.replace("-", "_")] = val
            i += 1
        elif args[i].startswith("--") and i + 1 < len(args):
            key = args[i][2:].replace("-", "_")
            flags[key] = args[i + 1]
            i += 2
        else:
            positional.append(args[i])
            i += 1

    # Check required positional args
    if len(positional) < len(required):
        missing = required[len(positional):]
        output({"ok": False, "error": f"Missing required arguments: {', '.join(missing)}"})
        sys.exit(1)

    # Build kwargs
    kwargs = {}
    for idx, name in enumerate(required):
        if idx < len(positional):
            kwargs[name] = positional[idx]
    # Extra positional args for optional params
    optional_names = [k for k in defaults.keys()]
    for idx, val in enumerate(positional[len(required):]):
        if idx < len(optional_names):
            kwargs[optional_names[idx]] = val
    # Flag overrides
    for k, v in flags.items():
        if k in defaults or k in required:
            kwargs[k] = v

    # Convert types
    if "limit" in kwargs:
        kwargs["limit"] = int(kwargs["limit"])

    asyncio.run(func(**kwargs))


if __name__ == "__main__":
    main()
