#!/bin/bash
# Start the disclaude tmux-based Discord ↔ Claude bridge.
#
# This script:
# 1. Starts the Discord bot (bot.py) in the background
# 2. Starts the message injector (injector.py) in the background
# 3. Launches Claude CLI inside a tmux session named "disclaude"

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SESSION_NAME="disclaude"

# Load bot token
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
else
    echo "Error: $SCRIPT_DIR/.env not found (needs BOT_TOKEN)"
    exit 1
fi

# Kill any existing session
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

# Start the Discord bot if not already running
if ! pgrep -f "python3.*bot\.py" > /dev/null; then
    cd "$SCRIPT_DIR"
    python3 bot.py &
    BOT_PID=$!
    echo "Started bot.py (PID $BOT_PID)"
else
    echo "bot.py already running"
fi

# Start the injector
cd "$SCRIPT_DIR"
DISCLAUDE_TMUX_SESSION="$SESSION_NAME" python3 injector.py &
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
