---
name: telegram-userapi
description: Telegram User API via Telethon. Create groups, send messages, manage members, and more — all through the user's own Telegram account (not a bot). Use when you need to create Telegram groups, look up existing groups, send messages as the user, add/remove members, or manage group settings. Requires Telethon session authentication.
user-invocable: false
metadata: {"openclaw": {"requires": {"env": ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_PHONE"]}, "primaryEnv": "TELEGRAM_API_ID", "tags": ["telegram", "messaging", "groups", "communication"]}}
---

# Telegram User API

Full Telegram User API access via Telethon. Operates as the authenticated user's account (not a bot), enabling group creation, member management, and direct messaging.

## Setup

**First-time setup:**

```bash
bash {baseDir}/scripts/setup.sh
```

This creates a Python venv and installs Telethon. Then authenticate:

```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/web_login.py
```

Open the displayed URL in a browser, enter the Telegram verification code, done.

**Verify session:**

```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py check-session
```

## Commands

All commands output JSON. Use `{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py <command>`.

### check-session
Verify the Telethon session is authenticated.
```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py check-session
```
Returns: `{"ok": true, "authorized": true, "user_id": ..., "username": ...}`

### get-me
Get current authenticated user info.
```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py get-me
```

### create-group
Create a new Telegram group. Optionally add a bot as initial member.
```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py create-group "Project Alpha" @MyBotUsername
```
Returns: `{"ok": true, "title": "Project Alpha", "chat_id": -123456789, ...}`

### list-groups
List recent groups/channels.
```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py list-groups --limit 30
```

### lookup-group
Find a group by name (case-insensitive partial match).
```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py lookup-group "marketing"
```
Returns all groups containing "marketing" in the title.

### send-message
Send a message to any chat by ID.
```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py send-message -123456789 "Hello from the API!"
```

### add-member
Add a user to a group.
```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py add-member -123456789 @username
```

### get-members
List all members of a group.
```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py get-members -123456789
```

### set-group-photo
Set a group's photo from a local file.
```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py set-group-photo -123456789 /path/to/photo.jpg
```

### leave-group
Leave a group.
```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py leave-group -123456789
```

### get-chat-info
Get detailed info about a chat.
```bash
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py get-chat-info -123456789
```

## Configuration

### Via openclaw.json

```json
{
  "skills": {
    "entries": {
      "telegram-userapi": {
        "enabled": true,
        "env": {
          "TELEGRAM_API_ID": "your_api_id",
          "TELEGRAM_API_HASH": "your_api_hash",
          "TELEGRAM_PHONE": "+1234567890"
        }
      }
    }
  }
}
```

### Via .env file

Place a `.env` file in `{baseDir}/data/`:

```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
```

### Session directory

By default, session files are stored in `{baseDir}/data/`. Override with:

```
TELEGRAM_SESSION_DIR=/custom/path
```

## Common Patterns

### Create a dedicated project group

```bash
# Check if group already exists
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py lookup-group "My Project"

# If not found, create it and add the bot
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py create-group "My Project" @MyBotUsername
```

### Find a group and send a message

```bash
# Look up the group
RESULT=$({baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py lookup-group "updates")
# Parse chat_id from JSON result, then:
{baseDir}/venv/bin/python3 {baseDir}/scripts/telegram_api.py send-message <chat_id> "Status update: all systems go"
```

## Troubleshooting

- **"Missing credentials"** — Set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE in env or openclaw.json
- **"telethon not installed"** — Run `bash {baseDir}/scripts/setup.sh`
- **"authorized: false"** — Run `{baseDir}/venv/bin/python3 {baseDir}/scripts/web_login.py` to authenticate
- **Session expired** — Delete `{baseDir}/data/session.session` and re-authenticate
- **"Could not find user"** — Verify the username exists and is accessible

## Getting Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application (or use existing)
4. Copy the `api_id` and `api_hash`
5. Your phone number is the one linked to your Telegram account
