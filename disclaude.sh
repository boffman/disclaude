#!/bin/bash
# Start the disclaude tmux-based Discord ↔ Claude bridge.
#
# This script:
# 1. Checks for required Python modules; offers to create a venv if missing
# 2. Starts the Discord bot (bot.py) in the background
# 3. Starts the message injector (injector.py) in the background
# 4. Launches Claude CLI inside a tmux session named "disclaude"

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SESSION_NAME="disclaude"
VENV_DIR="$SCRIPT_DIR/.venv"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# --- Python / venv setup ---

# Determine which python to use
if [ -f "$VENV_DIR/bin/python" ]; then
    PYTHON="$VENV_DIR/bin/python"
else
    PYTHON="python3"
fi

check_modules() {
    "$1" -c "import discord; import dotenv" 2>/dev/null
}

if ! check_modules "$PYTHON"; then
    echo "Required Python modules (discord.py, python-dotenv) not found."
    read -rp "Create a virtual environment and install them? [Y/n] " answer
    answer="${answer:-Y}"
    if [[ "$answer" =~ ^[Yy] ]]; then
        echo "Creating venv in $VENV_DIR ..."
        python3 -m venv "$VENV_DIR"
        PYTHON="$VENV_DIR/bin/python"
        "$PYTHON" -m pip install --upgrade pip -q
        "$PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt" -q
        echo "Dependencies installed."
    else
        echo "Aborting. Install the dependencies manually or re-run and accept the venv setup."
        exit 1
    fi
fi

# --- Load bot token ---

if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
else
    echo "Error: $SCRIPT_DIR/.env not found (needs BOT_TOKEN)"
    exit 1
fi

# --- Start services ---

# Kill any existing session
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

# Start the Discord bot if not already running
if ! pgrep -f "python3.*bot\.py" > /dev/null; then
    cd "$SCRIPT_DIR"
    "$PYTHON" bot.py >> "$LOG_DIR/bot.log" 2>&1 &
    BOT_PID=$!
    echo "Started bot.py (PID $BOT_PID)"
else
    echo "bot.py already running"
fi

# Start the injector
cd "$SCRIPT_DIR"
DISCLAUDE_TMUX_SESSION="$SESSION_NAME" "$PYTHON" injector.py >> "$LOG_DIR/injector.log" 2>&1 &
INJECTOR_PID=$!
echo "Started injector.py (PID $INJECTOR_PID)"

# Create tmux session running Claude CLI
tmux new-session -d -s "$SESSION_NAME" -x 200 -y 50
tmux send-keys -t "$SESSION_NAME" "cd $SCRIPT_DIR && claude --dangerously-skip-permissions" Enter

echo "disclaude started:"
echo "  tmux session: $SESSION_NAME"
echo "  bot PID:      ${BOT_PID:-already running}"
echo "  injector PID: $INJECTOR_PID"
echo ""
echo "Attach with: tmux attach -t $SESSION_NAME"
