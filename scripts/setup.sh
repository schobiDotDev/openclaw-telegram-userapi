#!/bin/bash
# Setup script for openclaw-telegram-userapi
# Creates a Python virtual environment and installs dependencies.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$BASE_DIR/venv"
DATA_DIR="$BASE_DIR/data"

echo "Setting up Telegram User API skill..."
echo "  Base directory: $BASE_DIR"

# Create data directory
mkdir -p "$DATA_DIR"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Install dependencies
echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install -q -r "$BASE_DIR/requirements.txt"

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Set your credentials (one of):"
echo "     - Create $DATA_DIR/.env with TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE"
echo "     - Or configure in openclaw.json under skills.entries.telegram-userapi.env"
echo ""
echo "  2. Authenticate with Telegram:"
echo "     $VENV_DIR/bin/python3 $SCRIPT_DIR/web_login.py"
echo ""
echo "  3. Test the connection:"
echo "     $VENV_DIR/bin/python3 $SCRIPT_DIR/telegram_api.py check-session"
