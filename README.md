# openclaw-telegram-userapi

OpenClaw skill for Telegram User API via [Telethon](https://github.com/LonamiWebs/Telethon). Gives your OpenClaw agent full Telegram capabilities through your own user account — not just a bot.

## What it does

- **Create groups** — Programmatically create Telegram groups and add members
- **Manage groups** — Set photos, add/remove members, get member lists
- **Send messages** — Send messages to any chat as your user account
- **Look up groups** — Find existing groups by name
- **Session management** — Web-based login flow, persistent sessions

## Install

### Via ClawHub

```bash
clawhub install telegram-userapi
```

### Manual

```bash
cd ~/.openclaw/workspace/skills
git clone https://github.com/schobidotdev/openclaw-telegram-userapi telegram-userapi
```

## Setup

### 1. Get Telegram API credentials

Go to [my.telegram.org/apps](https://my.telegram.org/apps) and get your `api_id` and `api_hash`.

### 2. Install dependencies

```bash
bash ~/.openclaw/workspace/skills/telegram-userapi/scripts/setup.sh
```

### 3. Configure credentials

Add to `~/.openclaw/openclaw.json`:

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

Or create a `.env` file in the skill's `data/` directory.

### 4. Authenticate

```bash
~/.openclaw/workspace/skills/telegram-userapi/venv/bin/python3 \
  ~/.openclaw/workspace/skills/telegram-userapi/scripts/web_login.py
```

Open the URL shown in the terminal, enter the verification code Telegram sends you.

### 5. Verify

```bash
~/.openclaw/workspace/skills/telegram-userapi/venv/bin/python3 \
  ~/.openclaw/workspace/skills/telegram-userapi/scripts/telegram_api.py check-session
```

## Commands

| Command | Description |
|---------|-------------|
| `check-session` | Verify session is valid |
| `get-me` | Get current user info |
| `create-group <title> [bot]` | Create group, optionally add bot |
| `list-groups [--limit N]` | List groups (default: 20) |
| `lookup-group <name>` | Find group by name |
| `send-message <chat_id> <text>` | Send message to chat |
| `add-member <chat_id> <user>` | Add member to group |
| `get-members <chat_id>` | List group members |
| `set-group-photo <id> <path>` | Set group photo |
| `leave-group <chat_id>` | Leave a group |
| `get-chat-info <chat_id>` | Get chat details |

All commands output JSON for easy parsing by the agent.

## How it works

This skill uses [Telethon](https://github.com/LonamiWebs/Telethon) to connect to Telegram's MTProto API as a **user account** (not a bot). This enables operations that bots can't do, like creating groups.

The agent calls the Python CLI scripts referenced in SKILL.md via `{baseDir}`. OpenClaw resolves `{baseDir}` to wherever the skill is installed.

## License

MIT
